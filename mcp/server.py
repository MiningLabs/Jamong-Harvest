#!/usr/bin/env python3
import json
import os
import secrets
import time
import uvicorn
from pathlib import Path
from pydantic import AnyHttpUrl
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from mcp.server.fastmcp import FastMCP as MCPServer
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

import storage

SKILLS_DIR = Path(__file__).parent.parent / "skills"
DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).parent / "data")
WIKI_DATA_DIR = DATA_DIR / "wiki"
OAUTH_STATE_FILE = DATA_DIR / "oauth-state.json"

ACCESS_TOKEN_TTL = 3600  # 1시간 — 탈취 시 노출 최소화, 만료되면 refresh token으로 조용히 갱신
WIKI_CATEGORIES = ", ".join(sorted(storage.VALID_CATEGORIES))


class JamongOAuthProvider(OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]):
    """토큰을 디스크에 영속화하는 OAuth provider.

    access token은 짧게(1시간), refresh token은 만료 없이 발급한다.
    클라이언트가 access token 만료 시 refresh token으로 조용히 갱신하므로
    서버 재시작이나 access token 만료로 인한 재로그인이 발생하지 않는다.
    명시적으로 /revoke 하기 전까지는 인증이 유지된다.
    """

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self.username = os.environ.get("MCP_USERNAME", "admin")
        self.password = os.environ.get("MCP_PASSWORD", "changeme")
        self.clients: dict[str, OAuthClientInformationFull] = {}
        self.tokens: dict[str, AccessToken] = {}
        self.refresh_tokens: dict[str, RefreshToken] = {}
        # 로그인 진행 중 상태(단명, 영속화 대상 아님)
        self.auth_codes: dict[str, AuthorizationCode] = {}
        self.state_mapping: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not OAUTH_STATE_FILE.exists():
            return
        data = json.loads(OAUTH_STATE_FILE.read_text(encoding="utf-8"))
        self.clients = {
            cid: OAuthClientInformationFull.model_validate(c)
            for cid, c in data.get("clients", {}).items()
        }
        self.tokens = {
            t: AccessToken.model_validate(v) for t, v in data.get("tokens", {}).items()
        }
        self.refresh_tokens = {
            t: RefreshToken.model_validate(v) for t, v in data.get("refresh_tokens", {}).items()
        }

    def _save(self) -> None:
        data = {
            "clients": {cid: c.model_dump(mode="json") for cid, c in self.clients.items()},
            "tokens": {t: v.model_dump(mode="json") for t, v in self.tokens.items()},
            "refresh_tokens": {t: v.model_dump(mode="json") for t, v in self.refresh_tokens.items()},
        }
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = OAUTH_STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.replace(OAUTH_STATE_FILE)

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull):
        if not client_info.client_id:
            raise ValueError("No client_id")
        self.clients[client_info.client_id] = client_info
        self._save()

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        state = params.state or secrets.token_hex(16)
        self.state_mapping[state] = {
            "redirect_uri": str(params.redirect_uri),
            "code_challenge": params.code_challenge,
            "redirect_uri_provided_explicitly": str(params.redirect_uri_provided_explicitly),
            "client_id": client.client_id,
            "resource": params.resource,
        }
        return f"{self.server_url}/login?state={state}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        return self.auth_codes.get(authorization_code)

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        if authorization_code.code not in self.auth_codes:
            raise ValueError("Invalid authorization code")
        del self.auth_codes[authorization_code.code]

        access = f"tok_{secrets.token_hex(32)}"
        refresh = f"ref_{secrets.token_hex(32)}"
        self.tokens[access] = AccessToken(
            token=access,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
            expires_at=int(time.time()) + ACCESS_TOKEN_TTL,
            resource=authorization_code.resource,
            subject=authorization_code.subject,
        )
        self.refresh_tokens[refresh] = RefreshToken(
            token=refresh,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
            expires_at=None,
            subject=authorization_code.subject,
        )
        self._save()
        return OAuthToken(
            access_token=access,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_TTL,
            refresh_token=refresh,
            scope=" ".join(authorization_code.scopes),
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        t = self.tokens.get(token)
        if not t:
            return None
        if t.expires_at and t.expires_at < time.time():
            del self.tokens[token]
            self._save()
            return None
        return t

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        return self.refresh_tokens.get(refresh_token)

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # refresh token은 회전시키지 않는다 — access token만 새로 발급
        access = f"tok_{secrets.token_hex(32)}"
        effective_scopes = scopes or refresh_token.scopes
        self.tokens[access] = AccessToken(
            token=access,
            client_id=client.client_id,
            scopes=effective_scopes,
            expires_at=int(time.time()) + ACCESS_TOKEN_TTL,
            resource=None,
            subject=refresh_token.subject,
        )
        self._save()
        return OAuthToken(
            access_token=access,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_TTL,
            refresh_token=refresh_token.token,
            scope=" ".join(effective_scopes),
        )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        self.tokens.pop(token.token, None)
        self.refresh_tokens.pop(token.token, None)
        self._save()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp_host = os.environ.get("MCP_HOST", "localhost")
    server_url = os.environ.get("SERVER_URL", f"http://{mcp_host}:{port}")

    provider = JamongOAuthProvider(server_url=server_url)

    mcp = MCPServer(
        "jamong-skills",
        auth_server_provider=provider,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(server_url),
            resource_server_url=None,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["mcp"],
                default_scopes=["mcp"],
            ),
            revocation_options=RevocationOptions(enabled=True),
            required_scopes=["mcp"],
        ),
    )

    @mcp.resource("skills://list")
    def list_skills() -> str:
        """사용 가능한 스킬 목록"""
        names = sorted(
            d.name for d in SKILLS_DIR.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )
        return "\n".join(names)

    @mcp.resource("skill://{name}")
    def get_skill(name: str) -> str:
        """스킬 내용 반환"""
        path = SKILLS_DIR / name / "SKILL.md"
        if not path.exists():
            raise ValueError(f"Skill not found: {name}")
        return path.read_text(encoding="utf-8")

    def _page_dict(page: storage.Page) -> dict:
        return {
            "slug": page.slug,
            "title": page.title,
            "tags": page.tags,
            "category": page.category,
            "created": page.created,
            "updated": page.updated,
            "content": page.content,
        }

    @mcp.tool()
    def wiki_list_wikis() -> list[str]:
        """사용 가능한 wiki_id 목록을 반환한다.

        어떤 wiki_id를 써야 할지 모르면 추측하지 말고 이 tool로 먼저 확인한다.
        프로젝트의 CLAUDE.md/AGENTS.md에 wiki_id가 선언돼 있으면 그 값을 우선 사용한다.
        """
        return storage.list_wikis(WIKI_DATA_DIR)

    @mcp.tool()
    def wiki_list_pages(wiki_id: str) -> list[dict]:
        """지정한 wiki의 페이지 인덱스(slug, title, tags, category, updated)를 반환한다."""
        pages = storage.list_pages(WIKI_DATA_DIR, wiki_id)
        return [
            {"slug": p.slug, "title": p.title, "tags": p.tags, "category": p.category, "updated": p.updated}
            for p in pages
        ]

    @mcp.tool()
    def wiki_get_page(wiki_id: str, slug: str) -> dict:
        """페이지 전체(본문 포함)를 조회한다. slug는 최초 생성 시 title로부터 확정되며 이후 불변이다."""
        return _page_dict(storage.read_page(WIKI_DATA_DIR, wiki_id, slug))

    @mcp.tool()
    def wiki_create_page(
        wiki_id: str, title: str, content: str, category: str, tags: list[str] | None = None
    ) -> dict:
        """신규 페이지를 생성한다.

        category는 다음 중 하나여야 한다: architecture, decision, pattern, debugging,
        environment, session-log.
        """
        return _page_dict(
            storage.create_page(WIKI_DATA_DIR, wiki_id, title=title, content=content, tags=tags, category=category)
        )

    @mcp.tool()
    def wiki_update_page(
        wiki_id: str,
        slug: str,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """기존 페이지를 부분 수정한다. 지정하지 않은 필드는 기존 값을 유지한다."""
        return _page_dict(
            storage.update_page(WIKI_DATA_DIR, wiki_id, slug, title=title, content=content, tags=tags, category=category)
        )

    @mcp.tool()
    def wiki_delete_page(wiki_id: str, slug: str) -> dict:
        """페이지를 삭제한다."""
        storage.delete_page(WIKI_DATA_DIR, wiki_id, slug)
        return {"deleted": True, "slug": slug}

    @mcp.tool()
    def wiki_search(
        wiki_id: str, q: str | None = None, tags: list[str] | None = None, category: str | None = None
    ) -> list[dict]:
        """제목/본문 substring 검색 + tags/category 필터. 벡터 임베딩 없이 단순 매칭이다."""
        results = storage.search_pages(WIKI_DATA_DIR, wiki_id, q=q, tags=tags, category=category)
        return [
            {"slug": p.slug, "title": p.title, "tags": p.tags, "category": p.category, "updated": p.updated}
            for p in results
        ]

    @mcp.custom_route("/login", methods=["GET"])
    async def login_page(request: Request) -> Response:
        state = request.query_params.get("state", "")
        if not state or state not in provider.state_mapping:
            raise HTTPException(400, "Invalid or missing state")
        html = f"""<!DOCTYPE html>
<html><head><title>Jamong MCP Login</title>
<style>
  body{{font-family:sans-serif;max-width:380px;margin:80px auto;padding:20px}}
  input{{width:100%;padding:10px;margin:6px 0;box-sizing:border-box;border:1px solid #ccc;border-radius:4px}}
  button{{background:#2563eb;color:#fff;padding:10px;border:none;border-radius:4px;width:100%;cursor:pointer;margin-top:8px}}
  button:hover{{background:#1d4ed8}}
</style>
</head><body>
<h2>Jamong MCP Server</h2>
<form method="post" action="/login/callback">
  <input type="hidden" name="state" value="{state}">
  <input type="text" name="username" placeholder="Username" required autofocus>
  <input type="password" name="password" placeholder="Password" required>
  <button type="submit">Login</button>
</form>
</body></html>"""
        return HTMLResponse(html)

    @mcp.custom_route("/login/callback", methods=["POST"])
    async def login_callback(request: Request) -> Response:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        state = str(form.get("state", ""))

        state_data = provider.state_mapping.get(state)
        if not state_data:
            raise HTTPException(400, "Invalid state")
        if username != provider.username or password != provider.password:
            raise HTTPException(401, "Invalid credentials")

        code = f"code_{secrets.token_hex(16)}"
        provider.auth_codes[code] = AuthorizationCode(
            code=code,
            client_id=state_data["client_id"],
            redirect_uri=AnyHttpUrl(state_data["redirect_uri"]),
            redirect_uri_provided_explicitly=state_data["redirect_uri_provided_explicitly"] == "True",
            expires_at=time.time() + 300,
            scopes=["mcp"],
            code_challenge=state_data["code_challenge"],
            resource=state_data.get("resource"),
            subject=username,
        )
        del provider.state_mapping[state]
        redirect = construct_redirect_uri(state_data["redirect_uri"], code=code, state=state)
        return RedirectResponse(url=redirect, status_code=302)

    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[mcp_host],
    )
    mcp.settings.host = mcp_host
    mcp.settings.port = port
    uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=port)

# Changelog

All notable changes to Jamong-Harvest will be documented in this file.

이 프로젝트는 Jamong의 AI 개발 운영 템플릿, 공통 스킬, safety hook, 글로벌 적용 가이드를 관리합니다.

버전 형식: `YY.메이저.마이너` (메이저: 새 기능 추가, 마이너: 버그 수정·내부 변경)

---

## [26.10.0] - 2026-10-08

### Changed

- 스킬 구조를 단일 스킬 `skills/jamong/`으로 통합 (`skill_for_vmfort`와 동일 구조)
  - `SKILL.md`: 항상 적용되는 공통 규칙 — 관리자 권한 금지(구 `admin-safety`), 코딩 규율(구 `code-discipline`), 완료 보고(구 `completion-report`), 상황별 참고 파일 표
  - `references/git-workflow.md`, `references/versioning.md`, `references/deploy.md`: 상황별 규칙 (구 동명 스킬 본문, frontmatter 제거·상호 참조 경로 갱신)
- 설치 방식을 curl + tar로 변경 — GitHub Release의 `jamong.tar.gz`를 스킬 경로에 바로 풀어 설치 (재설치 시 `jamong/` 폴더를 지운 뒤 설치)
- `.github/workflows/release.yml`: 릴리스 자산을 `install.zip`/`install.sh`/`install.bat` 대신 `jamong.tar.gz` 하나로 변경
- `README.md`, `docs/guide.md`, `SPEC.md`: 단일 스킬 구조·curl 설치·이전 스킬 정리 방법으로 갱신, 저장소 URL을 `MiningLabs/Jamong-Harvest`로 변경

### Removed

- MCP 서버(`mcp/` 전체: `server.py`, `storage.py`, `install.sh`, `verify.sh`, systemd unit, env 예시, `requirements.txt`)와 관련 문서·`.gitignore` 항목
- `install.sh`, `install.bat`
- 개별 스킬 6종 디렉터리 (`admin-safety`, `code-discipline`, `completion-report`, `git-workflow`, `versioning`, `deploy`)
- `templates/CLAUDE.md`, `templates/AGENTS.md`, `docs/guide.md`의 `<WIKI_ID>` placeholder

### Fixed

- `.github/workflows/release.yml`: GitHub Release 본문 참조를 `steps.changelog.notes` → `steps.changelog.outputs.notes`로 수정 — step output 경로가 잘못되어 릴리스 본문에 CHANGELOG 내용이 들어가지 않던 문제

---

## [26.9.1] - 2026-09-09

### Changed

- 완료 보고 형식에서 `사용량` 블록 제거 — 이 환경에서 Claude Code/Codex·OMX 사용량을 조회할 수 없어 항상 `확인불가`로만 출력되던 항목. `skills/completion-report/SKILL.md`, `AGENTS.md`, `templates/AGENTS.md`, `templates/CLAUDE.md`에서 사용량 보고 지시·`확인불가` 표기 규칙 삭제 (사용량 기반 툴 라우팅 규칙은 유지)

---

## [26.9.0] - 2026-08-06

### Added

- `.github/workflows/release.yml`: `install.zip`에 `mcp/` 디렉터리 포함 — MCP 서버를 설치할 대상 서버에서 git 없이 curl만으로 `mcp/install.sh`·`mcp/verify.sh`까지 받을 수 있음 (`mcp/__pycache__` 제외, `install.sh`/`verify.sh` 실행 권한 부여)

### Changed

- `README.md`: MCP 서버 설치 섹션에 curl로 `install.zip` 받는 방법 추가 (기존 git clone 방식과 병행)

---

## [26.8.0] - 2026-08-06

### Added

- `mcp/verify.sh`: OAuth 전체 흐름(동적 클라이언트 등록 → PKCE 로그인 → access/refresh token 발급 → refresh_token 갱신 → 서버 강제 재시작 후 재로그인 없이 유지 → `/revoke` 무효화)을 로컬에서 curl로 자동 검증하는 스크립트 추가 — 지금까지 "구현은 됐지만 실기동 검증 전"이었던 refresh token 흐름과 재시작 시 토큰 복원을 실제 mcp SDK로 9단계 전부 통과 확인

### Changed

- `mcp/requirements.txt`: `mcp[cli]>=1.28.0` → `mcp[cli]~=1.28.0` — 과거 `revoke_token` 시그니처 불일치 버그가 SDK 버전 문제로 재발하지 않도록 patch 버전(`1.28.x`)만 허용
- `SPEC.md`: 4장 구현 상태를 "로컬 기동 검증 전"에서 "`mcp/verify.sh`로 로컬 검증 완료"로 갱신, 검증 명령어를 실행 가능한 스크립트 참조로 교체, 프로젝트 구조 트리에 `verify.sh` 반영, 현재 버전 갱신

---

## [26.7.0] - 2026-07-14

### Added

- `mcp/server.py`: `JamongOAuthProvider`에 OAuth 토큰 디스크 영속화(`DATA_DIR/oauth-state.json`, 원자적 쓰기) 추가 — 서버 재시작에도 클라이언트 등록 정보·토큰이 복원됨
- `mcp/server.py`: refresh token 신규 구현 (`load_refresh_token`, `exchange_refresh_token`) — access token(1시간) 만료 시 조용히 갱신, refresh token은 만료 없이 발급되어 명시적 `/revoke` 전까지 유지
- `mcp/server.py`: `wiki_list_wikis`, `wiki_list_pages`, `wiki_get_page`, `wiki_create_page`, `wiki_update_page`, `wiki_delete_page`, `wiki_search` MCP tool 6종 추가 — 별도 REST 서버 없이 스킬/지식 CRUD·검색을 MCP tool로 흡수
- `mcp/storage.py`: `wiki/storage.py`를 이동 (내용 변경 없음, flat markdown + frontmatter 읽기/쓰기)

### Fixed

- `mcp/server.py`: `revoke_token` 시그니처를 `mcp[cli]==1.28.1` 실제 콜사이트(`revoke_token(token: AccessToken | RefreshToken)`)에 맞게 수정 — 기존 `revoke_token(token: str, ...)` 시그니처는 토큰 객체를 문자열 키로 취급해 조용히 no-op 상태였음
- `mcp/server.py`: `AuthSettings.revocation_options=RevocationOptions(enabled=True)` 추가 — 기본값(`enabled=False`)이면 `/revoke` 라우트 자체가 등록되지 않아 명시적 인증 해제가 불가능했음 (로컬 curl 테스트로 발견: revoke 전 404 → 활성화 후 200 + 토큰 삭제 + 이후 요청 401 확인)

### Removed

- `wiki/` 디렉터리 전체 제거 (`server.py`, `storage.py`는 `mcp/`로 이동, 나머지 배포 스캐폴딩은 삭제) — MCP 서버로 기능 단일화
- `skills/wiki-client/SKILL.md` 제거 — curl 사용법 대신 MCP tool docstring으로 규칙 전달

### Changed

- `mcp/jamong-mcp.env.example`: `DATA_DIR` 항목 추가
- `mcp/install.sh`: `mkdir -p mcp/data` 단계 추가
- `.gitignore`: `wiki/*.env`, `wiki/data/`, `wiki/__pycache__/` 제거, `mcp/data/`, `mcp/__pycache__/` 추가
- `SPEC.md`: 1장 배경 설명을 "OAuth 토큰 영속화로 재인증 문제 해결 + wiki는 MCP tool로 흡수"로 교체, 4장을 "Wiki 서버 설계"에서 "MCP 서버 설계"로 재작성, 3장 트리에서 `wiki/`·`wiki-client` 제거
- `README.md`: "Wiki 서버"/"(레거시) MCP 서버" 절을 "MCP 서버" 절 하나로 통합 (설치·`MCP_HOST` 설정·Claude Code/Codex 연결·wiki tool 사용법)
- `docs/guide.md`: "9. Wiki 서버 적용" 절을 "9. MCP 서버 적용"으로 되돌리고 토큰 영속화 내용 반영, 체크리스트 갱신

### Notes

- 이번 결정으로 26.6.0의 "MCP 폐기, Wiki로 대체" 방향을 재차 뒤집었다 — 근본 원인(인메모리 토큰)을 직접 고쳐서 OAuth를 유지하는 쪽이 REST 서버를 병행 운영하는 것보다 단순하다고 판단
- commit, tag, push, release, deploy는 수행하지 않았습니다.

---

## [26.6.0] - 2026-07-09

### Added

- `wiki/server.py`: Wiki 서버 신규 구현 — starlette+uvicorn 기반 무인증 stateless REST API, 다중 wiki_id 네임스페이스 지원 (`GET /wikis`, `GET/POST /wikis/{wiki_id}/pages`, `GET/PUT/DELETE /wikis/{wiki_id}/pages/{slug}`, `GET /wikis/{wiki_id}/search`)
- `wiki/storage.py`: flat markdown + frontmatter 읽기/쓰기 (stdlib만 사용, PyYAML 미사용)
- `wiki/install.sh`, `wiki/jamong-wiki.service`, `wiki/jamong-wiki.env.example`, `wiki/requirements.txt`: systemd 배포 스캐폴딩 (`mcp/` 패턴 재사용, 별도 venv로 mcp와 공존)
- `skills/wiki-client/SKILL.md`: Wiki 서버 curl 호출 규칙 신규 스킬 — MCP 도구 호출 대체
- `.gitignore`: `wiki/*.env`, `wiki/data/`, `wiki/__pycache__/` 추가

### Changed

- `templates/CLAUDE.md`, `templates/AGENTS.md`: `<WIKI_ID>` 플레이스홀더 추가 (프로젝트별 Wiki 참조 선언, 미사용 시 생략 가능)
- `SPEC.md`: 4장에 Wiki 서버 설계 신규 작성, MCP → Wiki 마이그레이션 배경 명시
- `README.md`: "MCP 서버" 절을 "Wiki 서버" 절로 교체 (설치·환경변수·Claude Code/Codex 연결·사용 예시), 저장소 구조 트리·제공 스킬 표 갱신, MCP는 레거시로 축약, `WIKI_BASE_URL` 셸 프로필 영구 설정 절차 추가
- `docs/guide.md`: "9. Wiki 서버 적용" 절 신규 추가(설치/환경변수/클라이언트 연결/레거시 MCP 정리), 구성 요소·제공 스킬·템플릿 placeholder·체크리스트에 Wiki 항목 반영, 기존 9번 체크리스트는 10번으로 이동
- `.github/workflows/release.yml`: `install.sh`, `install.bat`을 `install.zip`과 별도로 개별 Release 에셋으로도 첨부 — `curl -LO .../releases/latest/download/install.sh`로 압축 해제 없이 단일 파일 다운로드 가능
- `README.md`: "스킬 설치" 절에 curl 기반 다운로드 방법(zip/개별 스크립트) 안내 추가

### Notes

- `mcp/`는 그대로 유지 — 트래픽 이전 후 별도 커밋으로 제거 예정
- Wiki 서버는 인증 없음, 내부망/방화벽 전용 — `HOST=0.0.0.0` 설정 시 기동 자체를 거부하도록 구현
- commit, tag, push, release, deploy는 수행하지 않았습니다.

---

## [26.5.0] - 2026-06-22

### Added

- `skills/deploy/SKILL.md`: Docker 이미지 배포 규칙 신규 스킬 — Watchtower 금지, digest 기반 자동 업데이트 방식 명시

### Changed

- `skills/versioning/SKILL.md`: 버전 결정 기준 표 추가, Unreleased 항목 사용 금지 규칙 추가
- `skills/git-workflow/SKILL.md`: commit/push/deploy 절대 금지 규칙 세분화

> 릴리즈 패키지(`install.zip`): `install.sh` · `install.bat` · `skills/` — MCP 서버(`mcp/`)는 미포함

---

## [26.4.4] - 2026-06-22

### Fixed

- `mcp/server.py`: `streamable_http_app()` 인자에서 `host`, `transport_security` 제거 — PyPI 1.28.0 FastMCP는 해당 파라미터 미지원, `mcp.settings`로 분리

---

## [26.4.3] - 2026-06-22

### Fixed

- `mcp/server.py`: `AuthSettings` 생성 시 `resource_server_url=None` 누락 오류 수정 — PyPI 1.28.0의 `AuthSettings`는 해당 필드가 필수

---

## [26.4.2] - 2026-06-22

### Fixed

- `mcp/server.py`: `mcp.server.mcpserver` → `mcp.server.fastmcp.FastMCP`로 import 수정 — PyPI 1.28.0에는 `mcpserver` 모듈이 없고 `fastmcp`가 동일한 `auth_server_provider` API를 지원함

---

## [26.4.1] - 2026-06-22

### Added

- `mcp/jamong-mcp.env.example`: 환경변수 템플릿 파일 추가 — `PORT`, `MCP_HOST`, `SERVER_URL`, `MCP_USERNAME`, `MCP_PASSWORD` 일괄 관리
- `.gitignore`: `mcp/*.env` 추가 — 실제 환경변수 파일 커밋 방지

### Changed

- `mcp/jamong-mcp.service`: 인라인 `Environment=` 제거, `EnvironmentFile=__ENV_FILE__` 방식으로 변경
- `mcp/install.sh`: `jamong-mcp.env` 자동 생성 및 권한(600) 설정 단계 추가, service 파일 치환 시 `__ENV_FILE__` 경로 반영

---

## [26.4.0] - 2026-06-22

### Added

- `mcp/server.py`: MCP OAuth 2.0 인증 추가 — `FastMCP` → `MCPServer`(mcp 1.28+) 마이그레이션, `JamongOAuthProvider` 구현으로 `/.well-known/oauth-authorization-server`, `/register`, `/authorize`, `/token` 엔드포인트 자동 마운트
- `mcp/server.py`: `/login`, `/login/callback` 커스텀 라우트 추가 — 브라우저 기반 로그인 페이지 제공
- `mcp/jamong-mcp.service`: `SERVER_URL`, `MCP_USERNAME`, `MCP_PASSWORD` 환경변수 추가

### Changed

- `mcp/requirements.txt`: `mcp[cli]>=1.9.0` → `mcp[cli]>=1.28.0` (MCPServer / auth 모듈 포함 버전)

---

## [26.3.6] - 2026-06-22

### Fixed

- `mcp/server.py`: DNS rebinding 보호 설정 수정 — `TransportSecuritySettings.allowed_hosts`에 `MCP_HOST` 등록하여 리버스 프록시 환경에서 Host 헤더 검증 통과

---

## [26.3.5] - 2026-06-22

### Fixed

- `mcp/server.py`: FastMCP host 검증과 uvicorn 바인딩 분리 — `MCP_HOST` 환경변수로 외부 도메인 설정, uvicorn은 `0.0.0.0` 고정
- `mcp/jamong-mcp.service`: `MCP_HOST` 환경변수 추가 (플레이스홀더, VM에서 직접 수정 필요)

---

## [26.3.4] - 2026-06-22

### Fixed

- `mcp/server.py`: MCP 트랜스포트를 `sse` → `streamable-http`로 변경 — SDK 1.9+ deprecated SSE 대응

---

## [26.3.3] - 2026-06-22

### Fixed

- `mcp/server.py`: `FastMCP.run()` host/port 인자 미지원 오류 해결 — `mcp.settings`로 설정 방식 변경

---

## [26.3.2] - 2026-06-22

### Fixed

- `mcp/install.sh`: `REPO_DIR` 변수 정의 위치를 스크립트 상단으로 이동 — venv 생성 전 미정의 오류 해결

---

## [26.3.1] - 2026-06-22

### Fixed

- `mcp/install.sh`: venv 생성 후 패키지 설치로 변경 — 시스템 python과 서비스 실행 환경 불일치 문제 해결
- `mcp/jamong-mcp.service`: venv python 경로로 ExecStart 수정

---

## [26.3.0] - 2026-06-22

### Added

- `mcp/server.py`: FastMCP 기반 MCP 서버 — `skills://list`, `skill://{name}` 리소스 서빙
- `mcp/requirements.txt`: Python 의존성 (`mcp[cli]>=1.9.0`)
- `mcp/install.sh`: 패키지 설치 및 systemd 서비스 등록 안내 스크립트
- `mcp/jamong-mcp.service`: systemd 유닛 파일 (Rocky Linux / RHEL 계열)

---

## [26.2.0] - 2026-06-22

### Added

- `skills/deploy/SKILL.md`: Docker 이미지 배포 규칙 신규 스킬 — Watchtower 금지, digest 기반 자동 업데이트 방식 명시

### Changed

- `skills/versioning/SKILL.md`: 버전 결정 기준 표 추가 (기능 추가 → 메이저, 버그/수정 → 마이너), Unreleased 항목 사용 금지 규칙 추가
- `skills/git-workflow/SKILL.md`: commit/push/deploy 절대 금지 규칙 세분화 — 작업 완료 후 자동 실행 금지, 매번 명시적 요청 필요
- `CLAUDE.md`: 제공 스킬 목록에 `deploy` 항목 추가

---

## [26.1.6] - 2026-06-14

### Fixed

- `install.bat`: Windows CMD 실행 오류 수정 — LF 전용 라인 엔딩을 CRLF로 변환
- `.gitattributes` 추가 — `*.bat` 파일이 항상 CRLF로 체크아웃되도록 보장

---

## [26.1.5] - 2026-06-12

### Changed

- `skills/git-workflow/SKILL.md`: 관련 스킬 섹션 추가 (versioning, completion-report)
- `skills/versioning/SKILL.md`: 관련 스킬 섹션 추가 (git-workflow, completion-report)
- `skills/code-discipline/SKILL.md`: 관련 스킬 섹션 추가 (completion-report)
- `skills/admin-safety/SKILL.md`: 금지 명령 목록에 `su -`, `runuser` 추가

---

## [26.1.4] - 2026-06-12

### Changed

- `install.sh`: 기존 스킬 디렉터리가 있으면 삭제 후 재설치하도록 `install_one` 개선
- `install.bat`: 동일 변경 (Windows)

---

## [26.1.3] - 2026-06-12

### Changed

- `skills/git-workflow/SKILL.md`: main 직접 커밋·푸시 허용 방식으로 재정의
  - 보호 브랜치 직접 푸시 금지 규칙 제거
  - PR 필수·squash merge 강제 규칙 제거
  - 브랜치 작업은 선택 사항으로 변경
  - 커밋 prefix·한국어·명사형 종결 규칙 유지
- `skills/versioning/SKILL.md`: 메이저/마이너 버전 기준 명확화
  - 메이저: 새로운 기능 추가 시 증가 (하위 호환 불가 변경 기준 제거)
  - 마이너: 버그 수정 또는 내부 코드 수정 시 증가 명시
- `CHANGELOG.md`: 버전 형식 설명 문구 현행화
- `CLAUDE.md`, `README.md`, `docs/guide.md`, `SPEC.md`: git-workflow 스킬 설명 문구 현행화

---

## [26.1.2] - 2026-06-05

### Changed

- `README.md`: 스킬 설치(`install.sh` / `install.bat`) 위주로 재작성, 상세 가이드 내용은 `docs/guide.md` 링크로 대체
- `docs/guide.md`: 스킬 설치 섹션 신설 및 구버전 내용 현행화
  - 구성요소 테이블에 `skills/`, `install.sh`, `install.bat` 추가
  - Linux/macOS/Windows 스킬 설치 절차 추가
  - 전역 설정, hook 적용, RTK 주의사항, 점검 체크리스트 정리

---

## [26.1.1] - 2026-06-05

### Added

- 공통 스킬 구조 신설 (`skills/`)
  - `skills/git-workflow/SKILL.md`: 브랜치/커밋/PR 규칙
  - `skills/admin-safety/SKILL.md`: sudo/doas/pkexec 차단 규칙
  - `skills/completion-report/SKILL.md`: 작업 완료 보고 형식
  - `skills/code-discipline/SKILL.md`: Karpathy 스타일 코딩 규율
  - `skills/versioning/SKILL.md`: CHANGELOG.md 기반 버전 관리 및 릴리즈 규칙
- 스킬 설치 스크립트 추가
  - `install.sh`: Linux/macOS — Claude Code / Codex 경로 자동 설치 (`skills/` 동적 스캔)
  - `install.bat`: Windows — 동일 기능
- `.editorconfig` 추가: UTF-8 / LF / BOM 없음 강제 적용 (한글 깨짐 방지)
- `README.md` 업데이트: 저장소 구조, 스킬 설치 가이드, 인코딩 주의사항 추가
- `CLAUDE.md` 업데이트: 스킬 목록 및 설치 경로 섹션 추가
- 초기 프로젝트 구성
  - `templates/CLAUDE.md`: Claude Code 프로젝트 운영 템플릿
  - `templates/AGENTS.md`: Codex/OMX 및 범용 에이전트 운영 템플릿
  - `hooks/claude/block-sudo-bash.mjs`: Claude Code sudo 차단 hook
  - `hooks/codex/block-sudo-bash.mjs`: Codex sudo 차단 hook
  - `docs/guide.md`: 글로벌 개발 환경 적용 가이드

### Fixed

- Codex 스킬 경로 이중 등록 (`~/.agents/skills/`, `~/.codex/skills/`) — Codex 버전별 경로 차이 대응

### Notes

- 스킬 파일은 Claude Code / Codex 공통 YAML frontmatter 형식 사용. 파일 분리 없이 단일 소스로 양쪽 설치.
- 새 스킬 추가 시 `skills/<name>/SKILL.md`만 작성하면 `install.sh`가 자동 인식.
- commit, tag, push, release, deploy는 수행하지 않았습니다.

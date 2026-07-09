# Changelog

All notable changes to Jamong-Harvest will be documented in this file.

이 프로젝트는 Jamong의 AI 개발 운영 템플릿, 공통 스킬, safety hook, 글로벌 적용 가이드를 관리합니다.

버전 형식: `YY.메이저.마이너` (메이저: 새 기능 추가, 마이너: 버그 수정·내부 변경)

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

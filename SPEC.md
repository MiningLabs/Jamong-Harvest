# Jamong-Harvest SPEC

> 이 문서는 Jamong-Harvest의 현재 상태를 있는 그대로 기술한 레퍼런스 명세입니다.
> 신규 기여자 또는 AI 에이전트가 프로젝트를 빠르게 파악하는 용도로 사용합니다.
> **예외**: 4장(MCP 서버 설계)은 코드 구현까지 완료됐고, 실제 로컬 기동 검증과 systemd 운영 배포는 아직입니다. 해당 절 상단에 구현 상태를 명시합니다.

---

## 1. 목표 (Objective)

Jamong의 AI 개발 환경에서 반복적으로 쓰이는 **공통 스킬, 운영 템플릿, safety hook**을 단일 저장소에서 관리하고, 새 머신·새 프로젝트에 `install.sh` 한 번으로 즉시 적용할 수 있게 한다.
추가로 **MCP 서버**를 통해 행동 강령(스킬)과 업무별 지식(wiki tool)을 여러 머신·여러 에이전트(Claude Code, Codex)에 중앙 제공한다.

**대상 사용자**
- Jamong (저장소 소유자) — 새 프로젝트 시작 시 또는 환경 재구성 시 사용
- AI 에이전트 (Claude Code, Codex/OMX) — 저장소 작업 시 이 파일을 운영 지침으로 참조

**현재 버전**: `26.8.0`
**버전 형식**: `YY.메이저.마이너`

**설계 변경 배경**: 기존 `mcp/server.py`(FastMCP + OAuth 2.0 PKCE)는 토큰을 인메모리 dict에만 저장해서 서버 재시작·access token 만료(24시간)마다 Claude Code/Codex 양쪽에서 재로그인이 필요했다. 이 문제로 한때 무인증 stateless REST API(Wiki 서버)로 갈아탄 적이 있으나, OAuth 인증 자체는 유지하되 **토큰을 디스크에 영속화하고 refresh token을 지원**하는 방향으로 되돌렸다 — 최초 1회만 로그인하면 명시적으로 `/revoke`하기 전까지 세션이 유지된다. Wiki 서버가 제공하던 기능(페이지 CRUD/검색)은 별도 서버 없이 MCP tool로 흡수했으므로 `wiki/`는 제거했다.

---

## 2. 명령어 (Commands)

| 명령어 | 설명 |
|--------|------|
| `./install.sh claude` | Claude Code에 전체 스킬 설치 (`~/.claude/skills/`) |
| `./install.sh codex` | Codex에 전체 스킬 설치 (`~/.agents/skills/`, `~/.codex/skills/`) |
| `./install.sh all` | Claude Code + Codex 모두 설치 |
| `./install.sh claude <skill>` | 특정 스킬만 Claude Code에 설치 |
| `install.bat all` | Windows — Claude Code + Codex 모두 설치 |
| `./mcp/install.sh` | MCP 서버 systemd 서비스 설치 및 시작 |
| `git tag <version>` | 버전 태그 생성 (push하면 GitHub Actions가 Release 자동 생성) |

**검증 명령어** (변경 후 필수 실행)

```bash
# hook 문법 검사
node --check hooks/claude/block-sudo-bash.mjs
node --check hooks/codex/block-sudo-bash.mjs

# 설치 스크립트 문법 검사
bash -n install.sh
bash -n mcp/install.sh

# sudo 차단 동작 확인
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"sudo apt update"}}' \
  | node hooks/claude/block-sudo-bash.mjs
# 예상: permissionDecision:"deny" + 한국어 안내 출력

# safe command 통과 확인
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | node hooks/claude/block-sudo-bash.mjs
# 예상: 아무 출력 없이 종료 코드 0

# MCP 서버 구문 검사
python3 -m py_compile mcp/server.py mcp/storage.py

# MCP 서버 OAuth 전체 흐름 검증 (등록 → PKCE 로그인 → refresh → 재시작 후 유지 → revoke)
# mcp[cli] 설치된 venv 필요 (./mcp/install.sh 로 생성되는 venv를 자동으로 사용, 없으면 PYTHON=/path/to/python 지정)
./mcp/verify.sh
# 예상: 9단계 전부 PASS, 마지막에 "모든 검증 통과" 출력
```

---

## 3. 프로젝트 구조 (Project Structure)

```text
Jamong-Harvest/
├── install.sh              # Linux/macOS 스킬 설치 스크립트 (동적 스캔)
├── install.bat             # Windows 스킬 설치 스크립트
├── skills/                 # Claude Code / Codex 공통 스킬
│   ├── git-workflow/SKILL.md       # 브랜치/커밋 규칙 (main 직접 푸시 허용)
│   ├── admin-safety/SKILL.md       # sudo/doas/pkexec 차단 규칙
│   ├── completion-report/SKILL.md  # 작업 완료 보고 형식
│   ├── code-discipline/SKILL.md    # Karpathy 스타일 코딩 규율
│   ├── versioning/SKILL.md         # CHANGELOG 기반 버전·릴리즈 규칙
│   └── deploy/SKILL.md             # Docker 이미지 배포 규칙 (digest 기반)
├── mcp/                    # MCP 서버 — OAuth 토큰 영속화 + wiki tool (4장 참조)
│   ├── server.py               # FastMCP, OAuth 2.0 PKCE + refresh token, wiki tool 6종
│   ├── storage.py              # flat markdown + frontmatter 읽기/쓰기 (wiki tool 백엔드)
│   ├── install.sh              # systemd 서비스 설치 스크립트
│   ├── verify.sh                # OAuth 전체 흐름(등록·PKCE·refresh·재시작·revoke) 로컬 검증 스크립트
│   ├── jamong-mcp.service      # systemd unit 템플릿
│   ├── jamong-mcp.env.example  # 환경변수 템플릿 (PORT, MCP_HOST, DATA_DIR 등)
│   └── requirements.txt        # mcp[cli] (compatible release로 고정)
├── templates/
│   ├── CLAUDE.md           # Claude Code 프로젝트 운영 템플릿
│   └── AGENTS.md           # Codex/OMX 및 범용 에이전트 운영 템플릿
├── hooks/
│   ├── claude/block-sudo-bash.mjs  # Claude Code Bash PreToolUse hook
│   └── codex/block-sudo-bash.mjs   # Codex Bash PreToolUse hook
├── docs/
│   └── guide.md            # 글로벌 환경 적용 가이드
├── .github/workflows/
│   └── release.yml         # 버전 태그 push → install.zip + GitHub Release 자동 생성
├── CLAUDE.md               # 이 저장소의 AI 에이전트 운영 지침
├── AGENTS.md               # Codex/OMX 운영 지침
├── CHANGELOG.md            # 버전 히스토리
└── .editorconfig           # UTF-8 / LF / BOM 없음 강제
```

**핵심 설계 결정**

- 스킬은 단일 파일(`SKILL.md`)로 관리 — Claude Code / Codex 공통 YAML frontmatter 사용, 플랫폼별 파일 분리 없음
- `install.sh`는 `skills/` 디렉터리를 동적으로 스캔 — 새 스킬 추가 시 스크립트 수정 불필요
- MCP 서버는 OAuth 토큰을 디스크에 영속화 — 서버 재시작·access token 만료에도 재로그인이 필요 없음 (4장 참조)
- 스킬 배포와 wiki 지식 관리를 MCP 서버 하나로 단일화 — 별도 REST 서버(구 `wiki/`)를 두지 않음
- GitHub Actions는 `YY.N.N` 패턴 태그에만 트리거됨

---

## 4. MCP 서버 설계 (구현 상태: 구현 완료, `mcp/verify.sh`로 로컬 OAuth 전체 흐름 검증 완료 / 운영 배포 전)

### 4.1 OAuth 토큰 영속화

`JamongOAuthProvider`(`mcp/server.py`)가 클라이언트 등록 정보·access token·refresh token을 `DATA_DIR/oauth-state.json`에 원자적으로(tmp 파일 후 rename) 저장한다.

- **access token**: 수명 1시간. 탈취 시 노출을 최소화하기 위해 짧게 유지한다.
- **refresh token**: 수명 없음(`expires_at=None`). 클라이언트가 access token 만료 시 이 refresh token으로 조용히 갱신하며, 회전(rotate)시키지 않는다 — 클라이언트가 refresh token을 재저장할 필요가 없도록 단순화했다.
- 로그인 진행 중 상태(`auth_codes`, `state_mapping`)는 5분 내 완료되는 단명 데이터라 영속화 대상에서 제외한다(YAGNI) — 로그인 도중 서버가 재시작되는 극단적 케이스는 다시 로그인하면 된다.
- 결과: 최초 1회 브라우저 로그인 후에는 서버 재시작·access token 만료와 무관하게 세션이 유지되고, 명시적으로 `/revoke` 하기 전까지 재인증이 발생하지 않는다.

### 4.2 Wiki tool (스킬/지식 조회·기록)

`mcp/storage.py`(순수 stdlib, flat markdown + frontmatter)를 백엔드로 하는 MCP tool 6종을 제공한다. 페이지 포맷은 `SKILL.md`와 동일한 스타일을 재사용한다.

```markdown
---
title: <제목>
tags: [tag1, tag2]
category: architecture|decision|pattern|debugging|environment|session-log
created: <ISO8601>
updated: <ISO8601>
---

본문...
```

| Tool | 설명 |
|---|---|
| `wiki_list_wikis` | 사용 가능한 wiki_id 목록 |
| `wiki_list_pages(wiki_id)` | 페이지 인덱스 (slug, title, tags, category, updated) |
| `wiki_get_page(wiki_id, slug)` | 페이지 전체 조회 |
| `wiki_create_page(wiki_id, title, content, category, tags)` | 신규 페이지 생성 |
| `wiki_update_page(wiki_id, slug, ...)` | 페이지 부분 수정 |
| `wiki_delete_page(wiki_id, slug)` | 페이지 삭제 |
| `wiki_search(wiki_id, q, tags, category)` | 제목/본문 substring 검색 + tags/category 필터 |

- 다중 wiki 네임스페이스: `DATA_DIR/wiki/<wiki_id>/` 디렉터리가 존재하면 그 자체로 하나의 wiki (`skills/` 동적 스캔과 동일한 패턴). 각 프로젝트의 `CLAUDE.md`/`AGENTS.md`가 자신이 참조할 `wiki_id`를 선언한다.
- 검색은 substring 매칭만 사용 — **벡터 임베딩 없음** (OMC 내장 wiki와 동일 원칙, 스킬 레퍼런스 용도로 충분)
- tool docstring 자체에 카테고리 6종·wiki_id 추측 금지·slug 불변 규칙을 명시해서, 별도 클라이언트 스킬 파일 없이도 MCP tool 설명만으로 사용 규칙이 전달되게 한다.

### 4.3 보안

- OAuth 2.0 PKCE로 인증 — `MCP_USERNAME`/`MCP_PASSWORD` 로그인 후 access/refresh token 발급.
- `DATA_DIR`(토큰·wiki 페이지 콘텐츠)은 `.gitignore` 처리 — 저장소에는 스캐폴딩만 존재.
- 공인 도메인에 노출하는 경우 OAuth가 유일한 방어선이므로 `MCP_USERNAME`/`MCP_PASSWORD`를 반드시 강한 값으로 설정한다.

---

## 5. 코드 스타일 (Code Style)

### 스킬 파일 (`SKILL.md`)

```markdown
---
name: <skill-name>
description: >
  트리거 조건 설명.
  (1) 상황1
  (2) 상황2
allowed_tools: []
run_as: inline
---

# <Title>
...본문...
```

- 인코딩: **UTF-8 / BOM 없음 / LF**
- 언어: 한국어 본문, YAML key는 영어

### 쉘 스크립트 (`install.sh`, `mcp/install.sh`)

- 첫 줄: `#!/usr/bin/env bash`
- 두 번째 줄: `set -euo pipefail`
- 함수명: snake_case
- 지역 변수: `local` 명시

### Hook (`*.mjs`)

- Node.js ESM 모듈
- stdin JSON 파싱 → `permissionDecision` 결과 stdout 출력 구조
- `sudo`, `doas`, `pkexec`, `su -`, `runuser` 탐지 시 deny

### MCP 서버 (`mcp/server.py`, `mcp/storage.py`)

- Python 3.10+, 타입 힌트 필수
- `mcp[cli]`(FastMCP) + `uvicorn` 사용
- 환경변수: `PORT`, `MCP_HOST`, `SERVER_URL`, `MCP_USERNAME`, `MCP_PASSWORD`, `DATA_DIR`
- 실제 환경변수 파일(`mcp/*.env`)은 `.gitignore` 처리 — `jamong-mcp.env.example`만 커밋
- `DATA_DIR` 하위 실데이터(`mcp/data/` — OAuth 토큰, wiki 페이지)는 `.gitignore` 처리 — 저장소에는 스캐폴딩만 존재

### 템플릿 (`templates/*.md`)

- 프로젝트 고유 값은 `<PROJECT_NAME>`, `<PROJECT_ROOT>` placeholder 사용
- 다른 프로젝트에 복사해도 자체 설명이 되어야 함

---

## 6. 테스트 전략 (Testing Strategy)

이 저장소는 별도의 테스트 프레임워크가 없음. 검증은 아래 수동 절차로 수행:

| 대상 | 검증 방법 |
|------|-----------|
| `install.sh` 문법 | `bash -n install.sh` |
| `mcp/install.sh` 문법 | `bash -n mcp/install.sh` |
| hook 문법 | `node --check <hook>.mjs` |
| hook sudo 차단 | `printf` + `node` pipe 테스트 (deny 확인) |
| hook safe pass | `printf` + `node` pipe 테스트 (무출력 확인) |
| 스킬 설치 결과 | `./install.sh claude` 후 `ls ~/.claude/skills/` |
| 인코딩 | `.editorconfig` 준수 여부 — `file <skill>.md` 로 확인 |
| MCP 서버 구문 | `python3 -m py_compile mcp/server.py mcp/storage.py` |
| OAuth 토큰 영속화 | 로그인 → 서버 재기동 → `oauth-state.json`에서 토큰 복원 확인 |
| OAuth refresh | refresh token으로 `/token`(grant_type=refresh_token) 호출 시 새 access token 발급 확인 |
| Wiki tool CRUD | MCP tool call로 `wiki_create_page` → `wiki_get_page` → `wiki_search` 왕복 확인 |
| 다중 wiki 격리 | 서로 다른 `wiki_id`에 같은 slug로 생성해도 충돌 없는지 확인 |

**향후 과제**: GitHub Actions에 자동 검증 step 추가 고려 (hook 동작 + MCP 서버 smoke test)

---

## 7. 경계 (Boundaries)

### Always Do (항상 수행)
- 변경 후 `git diff`로 변경 범위 확인
- 스킬 파일 수정 시 UTF-8 / LF 인코딩 유지
- 새 스킬 추가 시 `CHANGELOG.md`에 Added 항목 기록
- SKILL.md YAML frontmatter 형식 준수
- `mcp/*.env`, `mcp/data/` 실제 파일은 절대 커밋하지 않음 (`.gitignore` 보호)

### Ask First (먼저 확인)
- 기존 스킬 내용을 실질적으로 변경하는 경우
- 새 설치 경로(플랫폼) 추가
- GitHub Actions 워크플로우 변경
- 전역 설정 파일(`~/.claude/`, `~/.codex/`) 수정
- MCP 서버 인증 방식 변경 (OAuth PKCE 유지가 기본 전제)

### Never Do (절대 금지)
- 명시 요청 없이 `commit / tag / push / deploy`
- `sudo`, `doas`, `pkexec` 직접 실행
- 스킬 파일을 LLM별로 분리 (단일 소스 원칙 위반)
- 테스트 없이 hook 로직 변경
- `install.sh`를 동적 스캔에서 정적 목록 방식으로 퇴행
- `mcp/*.env`, `mcp/data/` 파일을 git에 커밋

---

*최종 갱신: 2026-08-06 (v26.8.0 기준, `mcp/verify.sh`로 OAuth 전체 흐름 로컬 검증 완료)*

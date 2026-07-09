# Jamong-Harvest SPEC

> 이 문서는 Jamong-Harvest의 현재 상태를 있는 그대로 기술한 레퍼런스 명세입니다.
> 신규 기여자 또는 AI 에이전트가 프로젝트를 빠르게 파악하는 용도로 사용합니다.
> **예외**: 4장(Wiki 서버 설계)은 코드 구현·로컬 검증까지 완료됐고, systemd 운영 배포는 아직입니다. 해당 절 상단에 구현 상태를 명시합니다.

---

## 1. 목표 (Objective)

Jamong의 AI 개발 환경에서 반복적으로 쓰이는 **공통 스킬, 운영 템플릿, safety hook**을 단일 저장소에서 관리하고, 새 머신·새 프로젝트에 `install.sh` 한 번으로 즉시 적용할 수 있게 한다.
추가로 **Wiki 서버**를 통해 행동 강령(스킬)과 업무별 지식을 무인증 내부망 REST API로 여러 머신·여러 에이전트(Claude Code, Codex)에 중앙 제공한다.

**대상 사용자**
- Jamong (저장소 소유자) — 새 프로젝트 시작 시 또는 환경 재구성 시 사용
- AI 에이전트 (Claude Code, Codex/OMX) — 저장소 작업 시 이 파일을 운영 지침으로 참조

**현재 버전**: `26.6.0`
**버전 형식**: `YY.메이저.마이너`

**MCP → Wiki 마이그레이션 배경**: 기존 `mcp/server.py`(FastMCP + OAuth 2.0 PKCE)는 인메모리 토큰 저장 구조라 서버 재시작 시 세션이 초기화되고, 클라이언트마다 OAuth 로그인 플로우를 다시 타야 했다. 이 연결 끊김·갱신 어려움을 구조적으로 없애기 위해 무상태(stateless) REST API 기반 Wiki 서버로 대체한다. MCP는 폐기하고 `mcp/`는 마이그레이션 완료 후 제거한다.

---

## 2. 명령어 (Commands)

| 명령어 | 설명 |
|--------|------|
| `./install.sh claude` | Claude Code에 전체 스킬 설치 (`~/.claude/skills/`) |
| `./install.sh codex` | Codex에 전체 스킬 설치 (`~/.agents/skills/`, `~/.codex/skills/`) |
| `./install.sh all` | Claude Code + Codex 모두 설치 |
| `./install.sh claude <skill>` | 특정 스킬만 Claude Code에 설치 |
| `install.bat all` | Windows — Claude Code + Codex 모두 설치 |
| `./wiki/install.sh` | Wiki 서버 systemd 서비스 설치 및 시작 |
| `git tag <version>` | 버전 태그 생성 (push하면 GitHub Actions가 Release 자동 생성) |

**검증 명령어** (변경 후 필수 실행)

```bash
# hook 문법 검사
node --check hooks/claude/block-sudo-bash.mjs
node --check hooks/codex/block-sudo-bash.mjs

# 설치 스크립트 문법 검사
bash -n install.sh
bash -n wiki/install.sh

# sudo 차단 동작 확인
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"sudo apt update"}}' \
  | node hooks/claude/block-sudo-bash.mjs
# 예상: permissionDecision:"deny" + 한국어 안내 출력

# safe command 통과 확인
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | node hooks/claude/block-sudo-bash.mjs
# 예상: 아무 출력 없이 종료 코드 0

# Wiki 서버 구문 검사
python3 -m py_compile wiki/server.py wiki/storage.py

# Wiki 서버 기동 확인 (로컬, PORT=8080)
PORT=8080 python3 wiki/server.py &
sleep 1
curl -s http://localhost:8080/wikis | python3 -m json.tool
curl -s -X POST http://localhost:8080/wikis/jamong-harvest/pages \
  -H 'Content-Type: application/json' \
  -d '{"title":"test","content":"hello","tags":["smoke"],"category":"pattern"}'
curl -s http://localhost:8080/wikis/jamong-harvest/search?q=hello | python3 -m json.tool
kill %1
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
│   ├── deploy/SKILL.md             # Docker 이미지 배포 규칙 (digest 기반)
│   └── wiki-client/SKILL.md        # Wiki 서버 curl 호출 규칙 (NEW, 4장 참조)
├── wiki/                   # Wiki 서버 — mcp/ 대체 (NEW, 4장 참조)
│   ├── server.py               # starlette + uvicorn, 무인증 stateless REST API
│   ├── storage.py              # flat markdown + YAML frontmatter 읽기/쓰기
│   ├── install.sh              # systemd 서비스 설치 스크립트
│   ├── jamong-wiki.service     # systemd unit 템플릿
│   ├── jamong-wiki.env.example # 환경변수 템플릿 (PORT, HOST, DATA_DIR)
│   └── requirements.txt        # starlette, uvicorn
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

> **마이그레이션 노트**: `mcp/` 디렉터리(OAuth 기반 구서버)는 저장소에 아직 남아 있다. `wiki/` 구현·검증이 끝나고 실제 트래픽이 이전된 뒤 별도 커밋으로 제거한다.

**핵심 설계 결정**

- 스킬은 단일 파일(`SKILL.md`)로 관리 — Claude Code / Codex 공통 YAML frontmatter 사용, 플랫폼별 파일 분리 없음
- `install.sh`는 `skills/` 디렉터리를 동적으로 스캔 — 새 스킬 추가 시 스크립트 수정 불필요
- Wiki 서버는 무상태(stateless) REST — 세션/토큰을 서버가 들고 있지 않으므로 재시작·재연결 이슈가 구조적으로 없음
- Wiki 서버는 무인증 — **내부망/방화벽 전용**, 공인 도메인에 노출 금지 (5장 참조)
- Wiki는 다중 네임스페이스 — `wiki_id`별로 디렉터리·URL 경로가 분리되어 서버 코드 변경 없이 새 wiki 추가 가능
- GitHub Actions는 `YY.N.N` 패턴 태그에만 트리거됨

---

## 4. Wiki 서버 설계 (구현 상태: 구현 완료, 로컬 검증 통과 / 운영 배포 전)

### 4.1 다중 wiki 네임스페이스

동일 서버에 여러 wiki를 독립적으로 운영한다. 예: `jamong-harvest`(행동 강령), `<업무명>`(업무별 데이터). 서버 코드는 `wiki_id`를 몰라도 되며, `DATA_DIR/<wiki_id>/` 디렉터리가 존재하면 그 자체로 하나의 wiki가 된다 (`skills/` 동적 스캔과 동일한 패턴).

```text
DATA_DIR/
├── jamong-harvest/
│   ├── git-workflow-notes.md
│   └── ...
└── <업무명>/
    └── ...
```

### 4.2 페이지 포맷

기존 `SKILL.md`와 동일한 스타일(YAML frontmatter + 마크다운 본문)을 재사용한다. 새 포맷을 만들지 않는다.

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

파일명은 title을 kebab-case로 변환한 slug (`<slug>.md`).

### 4.3 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET | `/wikis` | 사용 가능한 wiki_id 목록 |
| GET | `/wikis/{wiki_id}/pages` | 페이지 인덱스 (slug, title, tags, category, updated) |
| GET | `/wikis/{wiki_id}/pages/{slug}` | 페이지 전체 조회 |
| POST | `/wikis/{wiki_id}/pages` | 신규 페이지 생성 (body: title, content, tags, category) |
| PUT | `/wikis/{wiki_id}/pages/{slug}` | 페이지 갱신 |
| DELETE | `/wikis/{wiki_id}/pages/{slug}` | 페이지 삭제 |
| GET | `/wikis/{wiki_id}/search?q=&tags=&category=` | 키워드/태그/카테고리 검색 |

- 검색은 제목·본문 substring 매칭 + tags/category 필터 — **벡터 임베딩 없음** (OMC 내장 wiki와 동일 원칙, 스킬 레퍼런스 용도로 충분)
- 모든 요청은 독립적(stateless) — 이전 요청 상태를 서버가 기억하지 않음. `wiki_id`를 바꿔 호출하면 그게 곧 다른 wiki 조회

### 4.4 클라이언트 연동 (`skills/wiki-client/SKILL.md`)

MCP 도구 대신 일반 `curl` 호출로 대체한다. 새 스킬 하나로 "이 API를 이렇게 쓴다"를 규칙화하고, 기존 `install.sh` 배포 파이프라인에 그대로 얹는다 (새 배포 채널 불필요).

- 각 프로젝트의 `CLAUDE.md`/`AGENTS.md`가 자신이 참조할 `wiki_id`를 선언 (예: `wiki: jamong-harvest`)
- `WIKI_BASE_URL` 환경변수로 서버 주소 지정
- 여러 wiki 동시 검색(`?wikis=a,b`)은 현재 요구사항에 없어 제외 — 필요해지면 추가

### 4.5 보안

- 인증 없음 — **내부망/VPN 전용**으로만 바인딩 (`HOST=0.0.0.0` 금지, 내부 인터페이스 또는 방화벽으로 제한)
- 공인 도메인·포트포워딩 노출 절대 금지 (읽기+쓰기 API이므로 외부 노출 시 임의 쓰기 가능)
- 추후 외부 노출이 필요해지면 그 시점에 별도 인증 계층을 추가 (YAGNI — 지금은 만들지 않음)

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

### 쉘 스크립트 (`install.sh`, `wiki/install.sh`)

- 첫 줄: `#!/usr/bin/env bash`
- 두 번째 줄: `set -euo pipefail`
- 함수명: snake_case
- 지역 변수: `local` 명시

### Hook (`*.mjs`)

- Node.js ESM 모듈
- stdin JSON 파싱 → `permissionDecision` 결과 stdout 출력 구조
- `sudo`, `doas`, `pkexec`, `su -`, `runuser` 탐지 시 deny

### Wiki 서버 (`wiki/server.py`, `wiki/storage.py`)

- Python 3.10+, 타입 힌트 필수
- `starlette` + `uvicorn` 사용 — OAuth/세션 관련 의존성(`mcp[cli]`) 사용 안 함
- 환경변수: `PORT`, `HOST`, `DATA_DIR`
- 실제 환경변수 파일(`wiki/*.env`)은 `.gitignore` 처리 — `jamong-wiki.env.example`만 커밋
- `DATA_DIR` 하위 실데이터(`wiki/data/`)는 `.gitignore` 처리 — 저장소에는 스캐폴딩만 존재

### 템플릿 (`templates/*.md`)

- 프로젝트 고유 값은 `<PROJECT_NAME>`, `<PROJECT_ROOT>` placeholder 사용
- 다른 프로젝트에 복사해도 자체 설명이 되어야 함

---

## 6. 테스트 전략 (Testing Strategy)

이 저장소는 별도의 테스트 프레임워크가 없음. 검증은 아래 수동 절차로 수행:

| 대상 | 검증 방법 |
|------|-----------|
| `install.sh` 문법 | `bash -n install.sh` |
| `wiki/install.sh` 문법 | `bash -n wiki/install.sh` |
| hook 문법 | `node --check <hook>.mjs` |
| hook sudo 차단 | `printf` + `node` pipe 테스트 (deny 확인) |
| hook safe pass | `printf` + `node` pipe 테스트 (무출력 확인) |
| 스킬 설치 결과 | `./install.sh claude` 후 `ls ~/.claude/skills/` |
| 인코딩 | `.editorconfig` 준수 여부 — `file <skill>.md` 로 확인 |
| Wiki 서버 구문 | `python3 -m py_compile wiki/server.py wiki/storage.py` |
| Wiki CRUD | 로컬 기동 후 POST/GET/PUT/DELETE `curl` 왕복 확인 (2장 예시) |
| Wiki 검색 | 페이지 생성 후 `GET /wikis/{id}/search?q=` 로 매칭 확인 |
| 다중 wiki 격리 | 서로 다른 `wiki_id`에 같은 slug로 생성해도 충돌 없는지 확인 |

**향후 과제**: GitHub Actions에 자동 검증 step 추가 고려 (hook 동작 + Wiki 서버 smoke test)

---

## 7. 경계 (Boundaries)

### Always Do (항상 수행)
- 변경 후 `git diff`로 변경 범위 확인
- 스킬 파일 수정 시 UTF-8 / LF 인코딩 유지
- 새 스킬 추가 시 `CHANGELOG.md`에 Added 항목 기록
- SKILL.md YAML frontmatter 형식 준수
- `wiki/*.env`, `wiki/data/` 실제 파일은 절대 커밋하지 않음 (`.gitignore` 보호)

### Ask First (먼저 확인)
- 기존 스킬 내용을 실질적으로 변경하는 경우
- 새 설치 경로(플랫폼) 추가
- GitHub Actions 워크플로우 변경
- 전역 설정 파일(`~/.claude/`, `~/.codex/`) 수정
- Wiki 서버 인증 방식 도입/변경 (현재는 의도적으로 무인증)
- `mcp/` 디렉터리 제거 시점

### Never Do (절대 금지)
- 명시 요청 없이 `commit / tag / push / deploy`
- `sudo`, `doas`, `pkexec` 직접 실행
- 스킬 파일을 LLM별로 분리 (단일 소스 원칙 위반)
- 테스트 없이 hook 로직 변경
- `install.sh`를 동적 스캔에서 정적 목록 방식으로 퇴행
- `wiki/*.env`, `wiki/data/` 파일을 git에 커밋
- Wiki 서버를 인증 없이 공인 IP/도메인에 노출

---

*최종 갱신: 2026-07-09 (v26.6.0 기준, Wiki 서버 구현 완료 / mcp/ 병행 운영 중)*

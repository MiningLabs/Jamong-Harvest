# Jamong-Harvest SPEC

> 이 문서는 Jamong-Harvest의 현재 상태를 있는 그대로 기술한 레퍼런스 명세입니다.
> 신규 기여자 또는 AI 에이전트가 프로젝트를 빠르게 파악하는 용도로 사용합니다.

---

## 1. 목표 (Objective)

Jamong의 AI 개발 환경에서 반복적으로 쓰이는 **공통 스킬, 운영 템플릿, safety hook**을 단일 저장소에서 관리하고, 새 머신·새 프로젝트에 curl 한 줄로 즉시 적용할 수 있게 한다.

**대상 사용자**
- Jamong (저장소 소유자) — 새 프로젝트 시작 시 또는 환경 재구성 시 사용
- AI 에이전트 (Claude Code, Codex/OMX) — 저장소 작업 시 이 파일을 운영 지침으로 참조

**현재 버전**: `26.10.1`
**버전 형식**: `YY.메이저.마이너`

**설계 변경 배경**: 26.10.0에서 6개 개별 스킬과 MCP 서버(OAuth + wiki tool)를 정리하고 단일 스킬 `jamong`으로 통합했다. `skill_for_vmfort`와 같은 구조(단일 스킬 + references)이며, 스킬은 GitHub Release의 `jamong.tar.gz`를 curl로 받아 바로 설치한다.

---

## 2. 명령어 (Commands)

| 명령어 | 설명 |
|--------|------|
| `curl -fsSL <release>/jamong.tar.gz \| tar xz -C ~/.claude/skills` | Claude Code에 스킬 설치 (README "스킬 설치" 참조) |
| `curl ... \| tar xz -C ~/.codex/skills` (`~/.agents/skills`도 동일) | Codex에 스킬 설치 |
| `git tag <version>` | 버전 태그 생성 (push하면 GitHub Actions가 `jamong.tar.gz` + Release 자동 생성) |

**검증 명령어** (변경 후 필수 실행)

```bash
# hook 문법 검사
node --check hooks/claude/block-sudo-bash.mjs
node --check hooks/codex/block-sudo-bash.mjs

# 릴리스 아카이브 구조 확인 (release.yml과 동일 명령)
tar czf /tmp/jamong.tar.gz -C skills jamong && tar tzf /tmp/jamong.tar.gz
# 예상: jamong/SKILL.md, jamong/references/*.md

# sudo 차단 동작 확인
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"sudo apt update"}}' \
  | node hooks/claude/block-sudo-bash.mjs
# 예상: permissionDecision:"deny" + 한국어 안내 출력

# safe command 통과 확인
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | node hooks/claude/block-sudo-bash.mjs
# 예상: 아무 출력 없이 종료 코드 0

```

---

## 3. 프로젝트 구조 (Project Structure)

```text
Jamong-Harvest/
├── skills/
│   └── jamong/                     # Claude Code / Codex 공통 단일 스킬
│       ├── SKILL.md                # 공통 규칙: 관리자 권한 금지, 코딩 규율, 완료 보고
│       └── references/
│           ├── git-workflow.md     # 브랜치/커밋 규칙 (main 직접 푸시 허용)
│           ├── versioning.md       # CHANGELOG 기반 버전·릴리즈 규칙
│           └── deploy.md           # Docker 이미지 배포 규칙 (digest 기반)
├── templates/
│   ├── CLAUDE.md           # Claude Code 프로젝트 운영 템플릿
│   └── AGENTS.md           # Codex/OMX 및 범용 에이전트 운영 템플릿
├── hooks/
│   ├── claude/block-sudo-bash.mjs  # Claude Code Bash PreToolUse hook
│   └── codex/block-sudo-bash.mjs   # Codex Bash PreToolUse hook
├── docs/
│   └── guide.md            # 글로벌 환경 적용 가이드
├── .github/workflows/
│   └── release.yml         # 버전 태그 push → jamong.tar.gz + GitHub Release 자동 생성
├── CLAUDE.md               # 이 저장소의 AI 에이전트 운영 지침
├── AGENTS.md               # Codex/OMX 운영 지침
├── CHANGELOG.md            # 버전 히스토리
└── .editorconfig           # UTF-8 / LF / BOM 없음 강제
```

**핵심 설계 결정**

- 스킬은 단일 스킬 `jamong`으로 관리 — 항상 적용되는 공통 규칙은 `SKILL.md`, 상황별 규칙은 `references/`로 분리해 필요한 파일만 읽음 (Claude Code / Codex 공통, 플랫폼별 파일 분리 없음)
- 설치는 스크립트 없이 curl + tar — 재설치 시 `jamong/` 폴더를 지운 뒤 풀어 이전 파일이 남지 않게 함
- GitHub Actions는 `YY.N.N` 패턴 태그에만 트리거됨

---

## 4. 코드 스타일 (Code Style)

### 스킬 파일 (`skills/jamong/SKILL.md`)

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
- `references/*.md`는 frontmatter 없이 본문만 작성하고, `SKILL.md`의 상황별 참고 파일 표에 등록

### Hook (`*.mjs`)

- Node.js ESM 모듈
- stdin JSON 파싱 → `permissionDecision` 결과 stdout 출력 구조
- `sudo`, `doas`, `pkexec`, `su -`, `runuser` 탐지 시 deny

### 템플릿 (`templates/*.md`)

- 프로젝트 고유 값은 `<PROJECT_NAME>`, `<PROJECT_ROOT>` placeholder 사용
- 다른 프로젝트에 복사해도 자체 설명이 되어야 함

---

## 5. 테스트 전략 (Testing Strategy)

이 저장소는 별도의 테스트 프레임워크가 없음. 검증은 아래 수동 절차로 수행:

| 대상 | 검증 방법 |
|------|-----------|
| 릴리스 아카이브 | `tar czf` 후 `tar tzf`로 `jamong/SKILL.md`, `jamong/references/*` 포함 확인 |
| hook 문법 | `node --check <hook>.mjs` |
| hook sudo 차단 | `printf` + `node` pipe 테스트 (deny 확인) |
| hook safe pass | `printf` + `node` pipe 테스트 (무출력 확인) |
| 스킬 설치 결과 | 임시 HOME에 `tar xz` 후 `ls -R $HOME/.claude/skills/jamong` |
| 인코딩 | `.editorconfig` 준수 여부 — `file <skill>.md` 로 확인 |
**향후 과제**: GitHub Actions에 자동 검증 step 추가 고려 (hook 동작)

---

## 6. 경계 (Boundaries)

### Always Do (항상 수행)
- 변경 후 `git diff`로 변경 범위 확인
- 스킬 파일 수정 시 UTF-8 / LF 인코딩 유지
- 규칙 추가 시 `CHANGELOG.md`에 Added 항목 기록
- SKILL.md YAML frontmatter 형식 준수

### Ask First (먼저 확인)
- 기존 스킬 내용을 실질적으로 변경하는 경우
- 새 설치 경로(플랫폼) 추가
- GitHub Actions 워크플로우 변경
- 전역 설정 파일(`~/.claude/`, `~/.codex/`) 수정

### Never Do (절대 금지)
- 명시 요청 없이 `commit / tag / push / deploy`
- `sudo`, `doas`, `pkexec` 직접 실행
- 스킬 파일을 LLM별로 분리 (단일 소스 원칙 위반)
- 테스트 없이 hook 로직 변경
- `skills/jamong/` 외에 별도 스킬을 추가해 단일 스킬 구조를 깨뜨림 (규칙은 `SKILL.md` 또는 `references/`에 추가)

---

*최종 갱신: 2026-10-08 (v26.10.0 기준, 단일 스킬 `jamong` 통합 · MCP 서버 제거 · curl 설치)*

# Jamong-Harvest

**AI로 키우는 개발농장** — Jamong의 AI 개발 환경에서 반복적으로 쓰이는 공통 스킬, 운영 템플릿, safety hook을 모아두는 저장소입니다.

Claude Code와 Codex에서 curl 한 줄로 스킬을 설치하고, 새 프로젝트에는 템플릿을 복사해서 바로 사용합니다.

## 저장소 구조

```text
Jamong-Harvest/
├── skills/
│   └── jamong/             # Claude Code / Codex 공통 단일 스킬
│       ├── SKILL.md        # 공통 규칙 (관리자 권한 금지, 코딩 규율, 완료 보고)
│       └── references/     # 상황별 규칙
│           ├── git-workflow.md
│           ├── versioning.md
│           └── deploy.md
├── templates/
│   ├── CLAUDE.md           # Claude Code 프로젝트 운영 템플릿
│   └── AGENTS.md           # Codex/OMX 에이전트 운영 템플릿
├── hooks/
│   ├── claude/
│   │   └── block-sudo-bash.mjs
│   └── codex/
│       └── block-sudo-bash.mjs
└── docs/
    └── guide.md            # 글로벌 환경 적용 가이드
```

## 스킬 설치

GitHub Release의 `jamong.tar.gz`를 받아 스킬 경로에 바로 풉니다. 재설치(업데이트)도 같은 명령이며, 기존 `jamong` 폴더를 먼저 지워 이전 파일이 남지 않게 합니다.

**Claude Code**

```bash
rm -rf ~/.claude/skills/jamong && mkdir -p ~/.claude/skills && \
curl -fsSL https://github.com/MiningLabs/Jamong-Harvest/releases/latest/download/jamong.tar.gz | tar xz -C ~/.claude/skills
```

**Codex** (`~/.codex/skills`, `~/.agents/skills` 두 경로 모두 설치)

```bash
for d in ~/.codex/skills ~/.agents/skills; do
  rm -rf "$d/jamong" && mkdir -p "$d" && \
  curl -fsSL https://github.com/MiningLabs/Jamong-Harvest/releases/latest/download/jamong.tar.gz | tar xz -C "$d"
done
```

**Windows** (PowerShell, Windows 10 이상 기본 내장 `curl.exe`/`tar.exe` 사용)

```powershell
curl.exe -fsSL -o "$env:TEMP\jamong.tar.gz" https://github.com/MiningLabs/Jamong-Harvest/releases/latest/download/jamong.tar.gz
foreach ($d in "$HOME\.claude\skills", "$HOME\.codex\skills", "$HOME\.agents\skills") {
  Remove-Item -Recurse -Force "$d\jamong" -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force $d | Out-Null
  tar.exe xzf "$env:TEMP\jamong.tar.gz" -C $d
}
```

설치 결과:

```text
~/.claude/skills/jamong/
├── SKILL.md
└── references/
    ├── git-workflow.md
    ├── versioning.md
    └── deploy.md
```

### 이전 버전 스킬 정리 (1회)

26.10.0 이전의 개별 스킬 6개가 설치되어 있다면 삭제합니다.

```bash
for d in ~/.claude/skills ~/.codex/skills ~/.agents/skills; do
  rm -rf "$d"/{admin-safety,code-discipline,completion-report,git-workflow,versioning,deploy}
done
```

MCP 서버(`jamong-skills`)를 연결해 두었다면 함께 해제합니다.

```bash
claude mcp remove jamong-skills
# Codex: ~/.codex/config.yaml 의 mcp_servers 에서 jamong-skills 항목 삭제
```

## 스킬 구성

`jamong` 스킬 하나가 모든 규칙을 다룹니다. 공통 규칙은 `SKILL.md`에, 상황별 규칙은 `references/`에 있으며 Agent는 해당 상황의 참고 파일만 읽습니다.

| 영역 | 적용 상황 | 위치 |
|------|-----------|------|
| 관리자 권한 금지 | sudo/doas/pkexec 실행 시도 시 | `SKILL.md` |
| 코딩 규율 | 코드 작성·수정 시 | `SKILL.md` |
| 완료 보고 | 작업 완료 보고 시 | `SKILL.md` |
| git 규칙 | git 명령, 커밋·푸시, 브랜치 전환 시 | `references/git-workflow.md` |
| 버전 관리 | 버전 올리기, CHANGELOG 작성, tag/릴리즈 시 | `references/versioning.md` |
| 배포 | Docker 이미지 빌드·배포, digest 기반 자동 업데이트 시 | `references/deploy.md` |

## 인코딩 기준

모든 스킬 파일은 **UTF-8 / BOM 없음 / LF** 기준으로 저장합니다. `.editorconfig`가 이 기준을 자동 적용합니다.

Windows에서 수정 시 VS Code 하단 인코딩이 `UTF-8`인지 확인하세요. `UTF-8 with BOM`이면 한글 깨짐이 발생합니다.

## 상세 가이드

스킬 설치 이후 전역 환경 적용, safety hook 설정, 새 프로젝트 템플릿 적용 절차는 아래 문서를 참고하세요.

→ [docs/guide.md](docs/guide.md)

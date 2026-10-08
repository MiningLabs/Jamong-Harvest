# Jamong-Harvest

**AI로 키우는 개발농장** — Jamong의 AI 개발 환경에서 반복적으로 쓰이는 공통 스킬, 운영 템플릿, safety hook을 모아두는 저장소입니다.

Claude Code와 Codex에서 curl 한 줄로 단일 스킬 `jamong`을 설치하고, 새 프로젝트에는 템플릿을 복사해서 바로 사용합니다.

- 최신 릴리스: [GitHub Releases](https://github.com/MiningLabs/Jamong-Harvest/releases/latest) (릴리스 자산: `jamong.tar.gz`)
- 변경 이력: [CHANGELOG.md](CHANGELOG.md)

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
├── docs/
│   └── guide.md            # 글로벌 환경 적용 가이드 (전역 지침·hook·템플릿)
├── .github/workflows/
│   └── release.yml         # 버전 태그 push → jamong.tar.gz + GitHub Release 자동 생성
├── AGENTS.md               # 이 저장소의 에이전트 운영 지침
├── SPEC.md                 # 프로젝트 명세
└── CHANGELOG.md            # 버전 히스토리
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
```

Codex는 `~/.codex/config.toml`에서 아래 블록을 삭제합니다.

```toml
[mcp_servers.jamong-skills]
url = "https://<your-domain>/mcp"
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

## 규칙이 적용되는 방식

스킬은 항상 로드되지 않습니다. 세션 시작 시 `name`/`description`만 컨텍스트에 올라가고, 모델이 작업이 description에 해당한다고 판단할 때 `SKILL.md` 본문을 읽습니다. 그래서 항상 지켜야 하는 핵심 규칙은 전역 지침 파일에 두고, sudo 차단은 hook으로 강제합니다.

| 계층 | Claude Code | Codex | 로드 시점 |
|------|-------------|-------|-----------|
| 전역 지침 (한국어, git·관리자 권한 경계, 코딩 규율) | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | 매 세션 항상 |
| `jamong` 스킬 (완료 보고, 커밋 형식, 버전·배포 규칙) | `~/.claude/skills/jamong/` | `~/.codex/skills/jamong/`, `~/.agents/skills/jamong/` | 모델 판단 시 (직접 호출: Claude `/jamong`, Codex `$jamong`) |
| safety hook (sudo/doas/pkexec 차단) | `~/.claude/hooks/block-sudo-bash.mjs` | `~/.codex/hooks/block-sudo-bash.mjs` | 모든 Bash 실행 전 강제 |

전역 지침과 hook 적용 절차는 [docs/guide.md](docs/guide.md) 4~7장을 참고하세요.

## 릴리스

`CHANGELOG.md`에 버전 항목을 작성하고 `YY.메이저.마이너` 태그를 push하면 GitHub Actions가 `skills/jamong/`을 `jamong.tar.gz`로 묶어 GitHub Release를 만들고, 해당 버전의 CHANGELOG 내용을 릴리스 본문으로 사용합니다. 위 설치 명령은 항상 최신 릴리스를 받습니다.

## 인코딩 기준

모든 스킬 파일은 **UTF-8 / BOM 없음 / LF** 기준으로 저장합니다. `.editorconfig`가 이 기준을 자동 적용합니다.

Windows에서 수정 시 VS Code 하단 인코딩이 `UTF-8`인지 확인하세요. `UTF-8 with BOM`이면 한글 깨짐이 발생합니다.

## 상세 가이드

스킬 설치 이후 새 프로젝트 템플릿 적용, Claude Code `CLAUDE.md`·Codex `AGENTS.md` 전역 규칙 반영, safety hook 설정 절차는 아래 문서를 참고하세요.

→ [docs/guide.md](docs/guide.md)

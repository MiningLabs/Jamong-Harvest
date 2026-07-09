# Jamong-Harvest

**AI로 키우는 개발농장** — Jamong의 AI 개발 환경에서 반복적으로 쓰이는 공통 스킬, 운영 템플릿, safety hook을 모아두는 저장소입니다.

Claude Code와 Codex에서 `install.sh` / `install.bat` 한 번으로 스킬을 설치하고, 새 프로젝트에는 템플릿을 복사해서 바로 사용합니다.

## 저장소 구조

```text
Jamong-Harvest/
├── install.sh              # Linux/macOS 스킬 설치 스크립트
├── install.bat             # Windows 스킬 설치 스크립트
├── skills/                 # Claude Code / Codex 공통 스킬
│   ├── git-workflow/
│   ├── admin-safety/
│   ├── completion-report/
│   ├── code-discipline/
│   ├── versioning/
│   ├── deploy/
│   └── wiki-client/
├── wiki/                   # Wiki 서버 (무인증 stateless REST, 다중 wiki_id 지원)
│   ├── server.py
│   ├── storage.py
│   ├── requirements.txt
│   ├── install.sh
│   └── jamong-wiki.service
├── mcp/                    # (레거시) MCP 서버 — Wiki 서버로 대체, 마이그레이션 후 제거 예정
│   ├── server.py
│   ├── requirements.txt
│   ├── install.sh
│   └── jamong-mcp.service
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

아래 세 가지 방법 중 하나로 받습니다.

```bash
# 1) git clone (권장 — skills/까지 항상 함께 받음)
git clone https://github.com/HelloJamong/Jamong-Harvest.git

# 2) curl로 install.zip 받기 (skills/ 포함, 압축 해제 필요)
curl -fsSLO https://github.com/HelloJamong/Jamong-Harvest/releases/latest/download/install.zip
unzip install.zip

# 3) curl로 install.sh만 받기 (skills/ 없이 스크립트만 필요할 때)
curl -fsSLO https://github.com/HelloJamong/Jamong-Harvest/releases/latest/download/install.sh
```

> 3번은 `install.sh` 파일만 받습니다. `skills/` 디렉터리가 옆에 없으면 설치할 스킬이 없으므로, 스크립트 내용을 확인하거나 다른 위치의 `skills/`와 함께 쓸 때만 사용하세요. 실제 설치는 1번 또는 2번으로 `skills/`까지 받은 뒤 실행하는 걸 권장합니다.

[GitHub Releases](https://github.com/HelloJamong/Jamong-Harvest/releases/latest) 페이지에서도 동일한 파일을 받을 수 있습니다.

```bash
# Claude Code + Codex 모두 설치
./install.sh all

# Claude Code만
./install.sh claude

# Codex만
./install.sh codex
```

Windows:

```bat
install.bat all
```

### 설치 경로

| LLM | 경로 |
|-----|------|
| Claude Code | `~/.claude/skills/<skill>/SKILL.md` |
| Codex | `~/.agents/skills/<skill>/SKILL.md` |
| Codex (호환) | `~/.codex/skills/<skill>/SKILL.md` |

## 제공 스킬

| 스킬 | 트리거 상황 |
|------|------------|
| `git-workflow` | git 명령, 커밋·푸시, 브랜치 전환 시 |
| `admin-safety` | sudo/doas/pkexec 실행 시도 시 |
| `completion-report` | 작업 완료 보고 시 |
| `code-discipline` | 코드 작성 전 원칙 확인 시 |
| `versioning` | 버전 올리기, CHANGELOG 작성, tag/릴리즈 시 |
| `deploy` | Docker 이미지 빌드·배포, digest 기반 자동 업데이트 시 |
| `wiki-client` | Wiki 서버에서 지식을 조회·기록할 때 |

## Wiki 서버

여러 머신·여러 프로젝트에서 지식(행동 강령, 업무별 데이터)을 공유하고 싶을 때, MCP 연결 대신 **무인증 stateless REST API**로 조회·기록합니다. 매 요청이 독립적이라 세션이 끊길 일이 없고, `wiki_id` 경로 세그먼트만 바꾸면 여러 wiki(예: 행동강령용 `jamong-harvest`, 업무별 wiki)를 자유롭게 오갈 수 있습니다. (MCP OAuth 세션 기반 연결이 겪던 재연결·재인증 문제를 구조적으로 없애기 위한 대체입니다 — 자세한 배경은 [SPEC.md](SPEC.md#1-목표-objective) 참고.)

### 서버 설치 (Rocky Linux / RHEL 계열)

```bash
git clone https://github.com/HelloJamong/Jamong-Harvest.git /opt/jamong-harvest
cd /opt/jamong-harvest
bash wiki/install.sh

# install.sh 안내에 따라 systemd 서비스 등록
sudo cp /tmp/jamong-wiki.service /etc/systemd/system/jamong-wiki.service
sudo systemctl daemon-reload
sudo systemctl enable --now jamong-wiki
```

### 환경변수 설정 (필수)

`wiki/jamong-wiki.env`에서 실제 값으로 수정합니다. **인증이 없는 서버이므로 `HOST=0.0.0.0`은 절대 설정하지 마세요** — 서버가 기동 자체를 거부합니다.

```bash
sudo vi /opt/jamong-harvest/wiki/jamong-wiki.env
```

```ini
PORT=8001
HOST=127.0.0.1   # 내부망 인터페이스 IP로 변경 (0.0.0.0 금지)
```

### Claude Code / Codex 연결

MCP처럼 별도 등록 절차가 없습니다. 접속하려는 각 클라이언트 머신에서 아래 두 가지만 하면 됩니다. (서버까지의 네트워크 경로 — VPN, SSH 터널 등 — 는 환경마다 다르므로 별도로 구성되어 있다고 가정합니다. 서버는 무인증이므로 신뢰된 경로로만 접근하세요.)

1. `./install.sh all`로 `wiki-client` 스킬을 설치합니다 (스킬 목록에 포함되어 자동 설치됨).
2. `WIKI_BASE_URL`을 셸 프로필에 영구 설정합니다 (터미널을 새로 열 때마다 다시 지정하지 않도록).

```bash
echo 'export WIKI_BASE_URL=http://내부IP:8001' >> ~/.bashrc   # zsh면 ~/.zshrc
source ~/.bashrc
```

이후 Claude Code/Codex는 `wiki-client` 스킬의 지시에 따라 `curl`로 직접 조회·기록합니다. 사용 예시와 엔드포인트 레퍼런스는 [skills/wiki-client/SKILL.md](skills/wiki-client/SKILL.md) 참고.

### 지식 갱신

무상태 서버라 별도 재시작·재인증이 필요 없습니다. 페이지를 바로 `POST`/`PUT`하면 즉시 반영됩니다.

```bash
curl -s -X POST "$WIKI_BASE_URL/wikis/jamong-harvest/pages" \
  -H 'Content-Type: application/json' \
  -d '{"title":"제목","content":"본문","tags":["tag"],"category":"pattern"}'
```

### (레거시) MCP 서버

`mcp/`는 OAuth 2.0 기반 구서버로, 트래픽이 Wiki 서버로 이전될 때까지만 유지됩니다. 신규 사용은 권장하지 않습니다. 기존 설치 절차는 `mcp/install.sh` 및 저장소 히스토리를 참고하세요.

## 인코딩 기준

모든 스킬 파일은 **UTF-8 / BOM 없음 / LF** 기준으로 저장합니다. `.editorconfig`가 이 기준을 자동 적용합니다.

Windows에서 수정 시 VS Code 하단 인코딩이 `UTF-8`인지 확인하세요. `UTF-8 with BOM`이면 한글 깨짐이 발생합니다.

## 상세 가이드

스킬 설치 이후 전역 환경 적용, safety hook 설정, 새 프로젝트 템플릿 적용 절차는 아래 문서를 참고하세요.

→ [docs/guide.md](docs/guide.md)

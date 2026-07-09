# Jamong-Harvest 글로벌 개발 환경 적용 가이드

이 문서는 Jamong-Harvest의 스킬, 템플릿, safety hook을 Jamong의 글로벌 AI 개발 환경에 적용하는 방법을 설명합니다.

> 원칙: 전역 설정은 영향 범위가 크므로 먼저 백업하고, 검증을 통과한 뒤 적용합니다.

---

## 1. 구성 요소

| 경로 | 용도 |
|------|------|
| `skills/` | Claude Code / Codex 공통 스킬 모음 |
| `install.sh` | Linux/macOS 스킬 설치 스크립트 |
| `install.bat` | Windows 스킬 설치 스크립트 |
| `templates/CLAUDE.md` | Claude Code 프로젝트별 운영 규칙 템플릿 |
| `templates/AGENTS.md` | Codex/OMX 및 범용 에이전트 운영 규칙 템플릿 |
| `hooks/claude/block-sudo-bash.mjs` | Claude Code Bash PreToolUse 관리자 명령 차단 hook |
| `hooks/codex/block-sudo-bash.mjs` | Codex/OMX Bash PreToolUse 관리자 명령 차단 hook |
| `wiki/` | Wiki 서버 (무인증 stateless REST, 다중 wiki_id 지원) — MCP(`mcp/`) 대체 |
| `skills/wiki-client/` | Wiki 서버 curl 호출 규칙 스킬 |

---

## 2. 스킬 설치

`install.sh` 또는 `install.bat`을 실행하면 `skills/` 아래의 스킬이 각 LLM 경로에 자동 설치됩니다.

### Linux / macOS

```bash
cd /home/dev/project/Jamong-Harvest

# Claude Code + Codex 모두 설치
./install.sh all

# Claude Code만 설치
./install.sh claude

# Codex만 설치
./install.sh codex

# 특정 스킬만 설치
./install.sh claude git-workflow
```

### Windows

```bat
cd C:\Users\<사용자계정>\project\Jamong-Harvest

install.bat all
install.bat claude
install.bat codex
install.bat claude git-workflow
```

### 설치 경로

| LLM | 경로 |
|-----|------|
| Claude Code | `~/.claude/skills/<skill>/SKILL.md` |
| Codex | `~/.agents/skills/<skill>/SKILL.md` |
| Codex (호환) | `~/.codex/skills/<skill>/SKILL.md` |

### 제공 스킬

| 스킬 | 트리거 상황 |
|------|------------|
| `git-workflow` | git 명령, 커밋·푸시, 브랜치 전환 시 |
| `admin-safety` | sudo/doas/pkexec 실행 시도 시 |
| `completion-report` | 작업 완료 보고 시 |
| `code-discipline` | 코드 작성 전 원칙 확인 시 |
| `versioning` | 버전 올리기, CHANGELOG 작성, tag/릴리즈 시 |
| `wiki-client` | Wiki 서버에서 지식을 조회·기록할 때 |

---

## 3. 새 프로젝트에 템플릿 적용

대상 프로젝트가 `/home/dev/project/<project>`에 있다고 가정합니다.

```bash
PROJECT=/home/dev/project/<project>
cp /home/dev/project/Jamong-Harvest/templates/CLAUDE.md "$PROJECT/CLAUDE.md"
cp /home/dev/project/Jamong-Harvest/templates/AGENTS.md "$PROJECT/AGENTS.md"
```

그 다음 대상 파일에서 placeholder를 교체합니다.

- `<PROJECT_NAME>` → 실제 프로젝트 이름
- `<PROJECT_ROOT>` → 실제 프로젝트 경로
- `<WIKI_ID>` → 이 프로젝트가 참조할 Wiki 네임스페이스 (Wiki를 안 쓰면 해당 줄을 생략)

권장 확인:

```bash
cd "$PROJECT"
git diff -- CLAUDE.md AGENTS.md
```

---

## 4. Claude Code 글로벌 메모리에 Jamong 규칙 반영

Claude Code 글로벌 설정 파일:

```text
/home/dev/.claude/CLAUDE.md
```

적용 원칙:

1. 기존 파일을 먼저 백업합니다.
2. OMC 같은 도구가 관리하는 블록이 있다면 내부를 수정하지 않습니다.
3. Jamong 전용 규칙은 관리 블록 바깥에 별도 섹션으로 추가합니다.

포함할 핵심 규칙:

- 한국어 기본 응답
- 프로젝트 루트는 `/home/dev/project/<project>`
- `sudo`/관리자 명령 직접 실행 금지
- 명시 요청 없는 commit/tag/push/deploy/restart 금지
- 변경 후 diff/test/lint/security 검증
- Claude Code 사용량 70% 근처 경고, 90% 이상이면 Codex/OMX 고려

---

## 5. Codex/OMX 글로벌 AGENTS에 Jamong 규칙 반영

Codex/OMX 글로벌 지침 파일:

```text
/home/dev/.codex/AGENTS.md
```

적용 원칙은 Claude와 동일합니다.

- 기존 OMX/도구 생성 블록을 보존합니다.
- Jamong 전용 운영 규칙을 별도 섹션으로 추가합니다.

---

## 6. Claude Code safety hook 적용

### 6.1 hook 파일 복사

```bash
mkdir -p /home/dev/.claude/hooks
cp /home/dev/project/Jamong-Harvest/hooks/claude/block-sudo-bash.mjs /home/dev/.claude/hooks/block-sudo-bash.mjs
```

### 6.2 settings.json 예시

대상 파일: `/home/dev/.claude/settings.json`

권장 hook 순서: Jamong 관리자 권한 차단 → RTK rewrite

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node /home/dev/.claude/hooks/block-sudo-bash.mjs",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "rtk hook claude",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

이미 다른 hook이 있다면 덮어쓰지 말고 병합합니다.

### 6.3 Claude hook 검증

```bash
node --check /home/dev/.claude/hooks/block-sudo-bash.mjs
python3 -m json.tool /home/dev/.claude/settings.json >/dev/null
```

sudo 차단 시뮬레이션:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"sudo apt update"}}' \
  | node /home/dev/.claude/hooks/block-sudo-bash.mjs
```

예상 결과: `"permissionDecision":"deny"` 포함, 한국어 안내 문구 포함

safe command 통과 확인:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | node /home/dev/.claude/hooks/block-sudo-bash.mjs
```

예상 결과: 아무 출력 없이 통과

---

## 7. Codex/OMX safety hook 적용

### 7.1 hook 파일 복사

```bash
mkdir -p /home/dev/.codex/hooks
cp /home/dev/project/Jamong-Harvest/hooks/codex/block-sudo-bash.mjs /home/dev/.codex/hooks/block-sudo-bash.mjs
```

### 7.2 hooks.json 예시

대상 파일: `/home/dev/.codex/hooks.json`

권장 hook 순서: OMX native policy → Jamong 관리자 권한 차단 → RTK rewrite

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node /home/dev/.codex/hooks/block-sudo-bash.mjs",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

기존 `hooks.json`이 있으면 덮어쓰지 말고 병합합니다.

### 7.3 Codex hook 검증

```bash
node --check /home/dev/.codex/hooks/block-sudo-bash.mjs
```

sudo 차단 시뮬레이션:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"sudo apt update"}}' \
  | node /home/dev/.codex/hooks/block-sudo-bash.mjs
```

---

## 8. RTK 적용 시 주의사항

- 관리자 권한 차단 hook은 항상 RTK rewrite보다 먼저 둡니다.
- `rtk hook codex`가 없을 수 있습니다. 확인 없이 설정에 넣지 않습니다.
- Claude/Codex 내장 파일 읽기 도구는 Bash hook을 거치지 않을 수 있습니다.
- hook timeout은 짧게 유지합니다 (권장: `5`초).

---

## 9. Wiki 서버 적용

Wiki 서버는 MCP 서버를 대체하는 무인증 stateless REST API입니다. 세션이 없어 연결이 끊기지 않고, `wiki_id` 경로만 바꾸면 여러 wiki(행동강령용 `jamong-harvest`, 업무별 wiki 등)를 오갈 수 있습니다. 설계 배경은 [SPEC.md](../SPEC.md) 4장 참고.

### 9.1 서버 설치 (Rocky Linux / RHEL 계열)

```bash
cd /home/dev/project/Jamong-Harvest
bash wiki/install.sh
```

`install.sh`는 venv 생성, 의존성 설치, `wiki/jamong-wiki.env` 생성, systemd unit 치환까지 자동으로 하고, root 권한이 필요한 마지막 단계만 명령으로 출력합니다 (직접 실행하지 않음).

```bash
sudo cp /tmp/jamong-wiki.service /etc/systemd/system/jamong-wiki.service
sudo systemctl daemon-reload
sudo systemctl enable --now jamong-wiki
```

### 9.2 환경변수 설정 (필수)

```bash
vi /home/dev/project/Jamong-Harvest/wiki/jamong-wiki.env
```

```ini
PORT=8001
HOST=127.0.0.1   # 내부망 인터페이스 IP로 설정 — 0.0.0.0 절대 금지 (기동 자체를 거부함)
```

무인증 서버이므로 **절대 공인 도메인/포트포워딩으로 노출하지 않습니다.**

### 9.3 Claude Code / Codex에서 사용

MCP처럼 별도 서버 등록이 필요 없습니다.

1. `./install.sh all`로 `wiki-client` 스킬을 설치합니다.
2. 클라이언트 환경에 `WIKI_BASE_URL` 환경변수를 설정합니다 (예: `export WIKI_BASE_URL=http://내부IP:8001`).
3. 프로젝트의 `CLAUDE.md`/`AGENTS.md`에 `<WIKI_ID>`를 선언해 어떤 wiki를 참조할지 명시합니다 (3장 참고).

이후 사용법(엔드포인트, curl 예시, 에러 처리)은 [skills/wiki-client/SKILL.md](../skills/wiki-client/SKILL.md)를 참고하세요.

### 9.4 (레거시) MCP 서버 정리

`mcp/`는 트래픽이 Wiki 서버로 이전될 때까지만 유지됩니다. 이전이 끝났다면 서비스를 내리고 저장소에서 제거를 검토합니다.

```bash
sudo systemctl disable --now jamong-mcp   # 이전 완료 후, root로 직접 실행
```

---

## 10. 적용 후 점검 체크리스트

- [ ] `./install.sh all` 실행 후 스킬이 Claude Code / Codex 경로에 설치되었다.
- [ ] 새 프로젝트에 `CLAUDE.md`, `AGENTS.md`가 복사되었다.
- [ ] `<PROJECT_NAME>`, `<PROJECT_ROOT>`, `<WIKI_ID>` placeholder가 실제 값으로 교체되었다 (Wiki 미사용 시 `<WIKI_ID>` 줄 생략).
- [ ] `/home/dev/.claude/CLAUDE.md`에 Jamong 글로벌 규칙이 반영되었다.
- [ ] `/home/dev/.codex/AGENTS.md`에 Jamong 글로벌 규칙이 반영되었다.
- [ ] Claude hook: `sudo apt update` payload가 deny 된다.
- [ ] Claude hook: `git status` payload는 통과한다.
- [ ] Codex hook: `sudo apt update` payload가 deny 된다.
- [ ] 기존 OMC/OMX/RTK 설정을 덮어쓰지 않고 병합했다.
- [ ] Wiki 서버 사용 시: `HOST`가 `0.0.0.0`이 아닌 내부망 IP로 설정되었다.
- [ ] Wiki 서버 사용 시: `WIKI_BASE_URL` 환경변수가 클라이언트 쪽에 설정되었다.

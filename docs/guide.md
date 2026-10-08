# Jamong-Harvest 글로벌 개발 환경 적용 가이드

이 문서는 Jamong-Harvest의 스킬, 템플릿, safety hook을 Jamong의 글로벌 AI 개발 환경에 적용하는 방법을 설명합니다.

> 원칙: 전역 설정은 영향 범위가 크므로 먼저 백업하고, 검증을 통과한 뒤 적용합니다.

---

## 1. 구성 요소

| 경로 | 용도 |
|------|------|
| `skills/jamong/` | Claude Code / Codex 공통 단일 스킬 (`SKILL.md` + `references/`) |
| `templates/CLAUDE.md` | Claude Code 프로젝트별 운영 규칙 템플릿 |
| `templates/AGENTS.md` | Codex/OMX 및 범용 에이전트 운영 규칙 템플릿 |
| `hooks/claude/block-sudo-bash.mjs` | Claude Code Bash PreToolUse 관리자 명령 차단 hook |
| `hooks/codex/block-sudo-bash.mjs` | Codex/OMX Bash PreToolUse 관리자 명령 차단 hook |

---

## 2. 스킬 설치

GitHub Release의 `jamong.tar.gz`를 curl로 받아 각 LLM 스킬 경로에 바로 풉니다. Linux/macOS·Windows 명령과 이전 버전 스킬 정리 방법은 [README.md](../README.md#스킬-설치)를 참고하세요.

```bash
# 예: Claude Code
rm -rf ~/.claude/skills/jamong && mkdir -p ~/.claude/skills && \
curl -fsSL https://github.com/MiningLabs/Jamong-Harvest/releases/latest/download/jamong.tar.gz | tar xz -C ~/.claude/skills
```

### 설치 경로

| LLM | 경로 |
|-----|------|
| Claude Code | `~/.claude/skills/jamong/` |
| Codex | `~/.agents/skills/jamong/` |
| Codex (호환) | `~/.codex/skills/jamong/` |

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
3. Jamong 전용 규칙은 관리 블록 바깥(`<!-- User customizations -->` 아래)에 `# Jamong Global Project Working Guidelines` 섹션으로 추가합니다.

섹션 구성:

| 절 | 핵심 규칙 |
|----|-----------|
| Language and Communication | 한국어 기본 응답, 근거 있는 간결한 보고, 모호하면 질문 |
| Project Location and Git Boundaries | 프로젝트 루트 `/home/dev/project/<project>`, 명시 요청 없는 commit/tag/push/release/deploy 금지, 변경 후 diff·검증 보고 |
| Administrator Privilege Boundary | `sudo`/관리자 명령 직접 실행 금지, 정해진 중지 문구 + 실행할 명령 안내 |
| Karpathy-Style Coding Discipline | Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution |
| Claude Code / Agent Usage | Claude Code 우선 사용, 사용량 한도 근처면 Codex로 전환, compact는 요청 시에만 |

이 섹션은 세션마다 항상 로드됩니다. `jamong` 스킬은 모델이 필요하다고 판단할 때만 로드되므로, 항상 지켜야 하는 핵심 규칙은 여기에 두고 세부 규칙(커밋 메시지 형식, 버전·CHANGELOG, 배포)은 스킬에 둡니다.

---

## 5. Codex/OMX 글로벌 AGENTS에 Jamong 규칙 반영

Codex/OMX 글로벌 지침 파일:

```text
/home/dev/.codex/AGENTS.md
```

Codex는 `~/.codex/AGENTS.md`를 세션마다 항상 로드합니다. 이 파일에 Jamong 규칙이 없으면 Codex에서는 sudo 차단 hook을 제외한 모든 규칙이 `jamong` 스킬 로드 여부에 의존하게 되므로, 4장의 Jamong 섹션을 그대로 옮겨 둡니다.

### 5.1 적용 절차

1. 기존 파일을 백업합니다.

   ```bash
   cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.bak
   ```

2. 파일 끝(OMX 생성 내용 뒤)에 `<!-- User customizations -->` 마커와 함께 4장의 Jamong 섹션을 붙입니다. OMX 블록(`<!-- OMX:...:START/END -->`) 내부는 수정하지 않습니다.

   ```bash
   {
     printf '\n<!-- User customizations -->\n---\n\n'
     awk '/^# Jamong Global/{f=1} /^## Claude Code \/ Agent Usage/{f=0} f' ~/.claude/CLAUDE.md
   } >> ~/.codex/AGENTS.md
   ```

3. 마지막에 Codex 전용 절을 추가합니다. OMX 지침에는 "되돌릴 수 있는 작업은 사람에게 미루지 말고 직접 실행"하라는 내용이 있으므로, Jamong 경계 규칙이 우선한다는 점을 명시합니다.

   ```markdown
   ## Codex / Agent Usage
   - Jamong uses Codex/OMX when Claude Code is unavailable or near its usage limit; follow the same rules as in Claude Code.
   - The Git boundary and Administrator Privilege Boundary above take precedence over OMX guidance to execute reversible actions autonomously: commit, tag, push, release, deploy, service restart, and administrator commands always require Jamong's explicit request.
   - Detailed rules (commit message format, versioning/CHANGELOG, deploy) live in the `jamong` skill (`~/.codex/skills/jamong/`); load it for those tasks.
   ```

### 5.2 검증

```bash
# 추가만 되고 기존 OMX 내용은 그대로인지 확인 (출력이 모두 '>' 줄이어야 함)
diff ~/.codex/AGENTS.md.bak ~/.codex/AGENTS.md

# Jamong 본문이 Claude 쪽과 동일한지 확인 (출력 없음이면 동일)
ext(){ awk -v stop="$2" '/^# Jamong Global/{f=1} $0==stop{f=0} f' "$1"; }
diff <(ext ~/.claude/CLAUDE.md '## Claude Code / Agent Usage') <(ext ~/.codex/AGENTS.md '## Codex / Agent Usage')

# 마커 중복 여부 (1이어야 함)
grep -c 'User customizations' ~/.codex/AGENTS.md
```

### 5.3 주의사항

- `~/.codex/AGENTS.md`는 `omx setup`이 생성한 파일(`<!-- omx:generated:agents-md -->`)입니다. `omx setup`을 다시 실행하면 파일이 재생성되어 Jamong 섹션이 사라질 수 있으니, 실행 후 5.2로 확인하고 없으면 5.1을 다시 적용합니다.
- Jamong 규칙을 수정할 때는 `~/.claude/CLAUDE.md`와 `~/.codex/AGENTS.md`를 함께 수정합니다.
- 적용 후 Codex를 재시작해야 반영됩니다.

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

## 9. 적용 후 점검 체크리스트

- [ ] curl 설치 후 `jamong/SKILL.md`와 `references/`가 Claude Code / Codex 경로에 설치되었다.
- [ ] 새 프로젝트에 `CLAUDE.md`, `AGENTS.md`가 복사되었다.
- [ ] `<PROJECT_NAME>`, `<PROJECT_ROOT>` placeholder가 실제 값으로 교체되었다.
- [ ] `/home/dev/.claude/CLAUDE.md`에 Jamong 글로벌 규칙이 반영되었다.
- [ ] `/home/dev/.codex/AGENTS.md`에 Jamong 글로벌 규칙과 `Codex / Agent Usage` 절이 반영되었다 (5.2 검증 통과).
- [ ] Claude hook: `sudo apt update` payload가 deny 된다.
- [ ] Claude hook: `git status` payload는 통과한다.
- [ ] Codex hook: `sudo apt update` payload가 deny 된다.
- [ ] 기존 OMC/OMX/RTK 설정을 덮어쓰지 않고 병합했다.

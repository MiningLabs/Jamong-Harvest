# <PROJECT_NAME> Agent Operating Guide

> Jamong 전용 Codex/OMX 및 범용 코딩 에이전트 운영 템플릿입니다. 이 파일을 대상 프로젝트 루트의 `AGENTS.md`로 복사한 뒤 `<PROJECT_NAME>`, `<PROJECT_ROOT>`, `<WIKI_ID>`를 실제 값으로 바꿔 사용합니다.

## 0. Scope

- Project: `<PROJECT_NAME>`
- Root: `<PROJECT_ROOT>`
- Wiki: `<WIKI_ID>` (optional, omit if unused)
- Default language: Korean
- Primary goal: small, safe, verified development changes

## 1. Priority

Follow instructions in this order:

1. Latest explicit user request
2. Project-local `AGENTS.md`, `CLAUDE.md`, `.cursorrules`
3. Repository docs: `README.md`, `docs/*`, `CHANGELOG.md`
4. Jamong global operating rules
5. General language/framework conventions

If rules conflict, choose the safer and more specific instruction.

## 2. Communication

- Reply in Korean by default.
- State assumptions when they matter.
- Do not guess about files, system state, versions, or git state; inspect them.
- Ask only when ambiguity materially changes the implementation.
- Keep progress and completion reports concise but verifiable.

## 3. Workspace

- Jamong projects live under `/home/dev/project/<project>`.
- Run commands from `<PROJECT_ROOT>` unless a task explicitly targets another directory.
- Read existing files before editing them.
- Avoid unrelated formatting churn or broad rewrites.

## 4. Administrator Commands Are Forbidden

Do not run:

- `sudo`
- `doas`
- `pkexec`
- any administrator-level package/system/service command

If administrator permission is required, stop and output exactly:

```text
관리자 권한이 필요한 작업이라 중지했습니다, 아래 명령어를 실행 후 이어서 진행해주세요
```

Then provide the exact command Jamong should run manually.

## 5. Git and Remote-State Safety

Do not do these without explicit user request:

- commit
- tag
- push
- deploy
- create/merge/close PRs
- create GitHub Releases
- restart/reload services
- destructive remote changes

Safe by default:

- inspect status/diff/log
- create or edit local files for the requested task
- run local tests/lints/security checks

## 6. Codex / OMX Rules

Jamong often launches Codex through OMX:

```bash
omx --madmax --high
```

Rules for Codex/OMX or other autonomous agents:

- Work inside a git repository.
- Prefer small, surgical changes.
- Use tracked/background sessions for long-running work.
- Do not use high-risk full-auto/yolo behavior unless explicitly approved.

## 7. Development Discipline

- Think before coding: understand the task and success criteria.
- Simplicity first: implement the minimal sufficient change.
- Surgical changes: touch only related files/lines.
- Goal-driven execution: verify with tests, lint, typecheck, security checks, or clear manual inspection.

## 8. Verification After Changes

Run what is available and relevant:

```bash
# inspect changes
git status --short --branch
git diff -- <changed-files>

# examples; replace with project commands
# npm test
# npm run lint
# npm run build
# pytest
# ruff check
# tsc --noEmit
```

Also check that no secrets were introduced.

## 9. Completion Report

Use this shape:

```text
완료했습니다.

변경 사항
- <file>: <summary>

검증
- <check>: 성공/실패/미실행 사유

주의/다음 단계
- <optional>
```

## 10. Project-Specific Commands

```bash
# TODO: 대상 프로젝트에 맞게 작성
```

## 11. Project-Specific Notes

- TODO: framework/runtime/deployment notes
- TODO: local ports, test data, external services

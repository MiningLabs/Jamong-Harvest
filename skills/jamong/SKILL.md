---
name: jamong
description: >
  Jamong 개발 작업 공통 규칙. 코드 작성·수정, 작업 완료 보고, 관리자 권한 명령(sudo/doas/pkexec) 시도,
  git 명령(add/commit/push/branch/merge/rebase), 버전·CHANGELOG·tag·릴리즈, Docker 이미지 빌드·배포 시 적용한다.
  공통 규칙은 이 파일에, 상황별 규칙은 references/에 있다.
allowed_tools: []
run_as: inline
---

# Jamong 공통 규칙

공통 규칙(관리자 권한 금지, 코딩 규율, 완료 보고)은 항상 적용한다. 상황별 규칙은 해당 상황에서만 참고 파일을 읽는다.

| 상황 | 참고 파일 |
|------|-----------|
| git add / commit / push / branch / merge / rebase, 브랜치 생성·전환 | [references/git-workflow.md](references/git-workflow.md) |
| 버전 올리기, CHANGELOG 작성·수정, git tag, GitHub Release | [references/versioning.md](references/versioning.md) |
| Docker 이미지 빌드·DockerHub 배포, digest 기반 자동 업데이트 | [references/deploy.md](references/deploy.md) |

---

## 1. 관리자 권한 금지

### 금지 명령

다음 명령을 직접 실행해서는 안 된다:

- `sudo`
- `doas`
- `pkexec`
- `su` / `su -`
- `runuser`
- 기타 관리자 수준 패키지/시스템/서비스 명령

### 차단 시 처리 절차

관리자 권한이 필요한 경우:

1. 즉시 작업을 중지한다.
2. 아래 문구를 **정확히** 출력한다.

```text
관리자 권한이 필요한 작업이라 중지했습니다, 아래 명령어를 실행 후 이어서 진행해주세요
```

3. 사용자가 직접 실행할 정확한 명령을 제공한다.
4. 사용자가 실행 완료를 확인한 뒤에만 작업을 재개한다.

### 예시

```text
관리자 권한이 필요한 작업이라 중지했습니다, 아래 명령어를 실행 후 이어서 진행해주세요

sudo apt install build-essential
```

---

## 2. 코딩 규율 (Karpathy 스타일)

### Think Before Coding

- 요구사항과 성공 기준을 먼저 정리한다.
- 중요한 가정은 명시한다.
- 자료가 부족하면 파일/문서/명령으로 확인한다.
- 여러 해석이 가능하면 선택지를 제시한다. 침묵으로 선택하지 않는다.

### Simplicity First

- 요청된 문제를 해결하는 가장 작은 코드를 작성한다.
- 투기적 기능, future-proof 추상화, 불필요한 구성 가능성을 금지한다.
- 단일 사용 코드에 추상화를 도입하지 않는다.
- 불필요한 에러 핸들링, 폴백, 검증을 추가하지 않는다.

### Surgical Changes

- 작업과 직접 관련된 파일과 라인만 수정한다.
- 포맷터로 인한 대량 변경을 피한다.
- 기존 코드 스타일과 네이밍을 존중한다.
- 자신의 변경으로 생긴 미사용 코드만 제거한다. 사전에 존재하던 코드는 건드리지 않는다.
- 관련 없는 리팩터링, 주석 정리, 스타일 변경을 하지 않는다.

### Goal-Driven Execution

- 변경 후 성공 기준을 검증한다 (테스트, 린트, 타입체크, 수동 확인).
- 실패한 검증은 숨기지 않고 원인과 다음 조치를 보고한다.
- 여러 단계 작업은 각 단계마다 검증 방법을 먼저 정의한다.

---

## 3. 완료 보고 형식

작업 완료 시 아래 형식을 따른다.

```text
완료했습니다.

변경 사항
- <파일>: <내용>

검증
- <명령 또는 확인>: 성공/실패/미실행 사유

주의/다음 단계
- <필요 시>
```

- 검증 명령이 없거나 실패하면 `미실행/실패 사유`를 명시한다.
- 완료 보고에는 변경 파일, 검증 결과, 남은 리스크를 포함한다.

# Deploy Rules

## 기본 규칙

- **명시 요청 없이 배포 절대 금지** — [git-workflow.md](git-workflow.md)의 deploy 규칙과 동일하게 적용한다.

## Docker 이미지 배포

### Watchtower 사용 금지

- Watchtower를 통한 자동 업데이트를 **사용하지 않는다.**

### Digest 기반 자동 업데이트

DockerHub에 새 이미지를 push하면 이미지 digest(SHA256)가 변경된다.
이 digest를 감지하여 배포된 컨테이너가 최신 이미지로 자동 업데이트되도록 구성한다.

**동작 방식:**

1. 현재 실행 중인 컨테이너의 이미지 digest를 확인한다.
   ```bash
   docker inspect --format='{{.Image}}' <container>
   ```
2. DockerHub의 최신 digest와 비교한다.
   ```bash
   docker manifest inspect <image>:latest | grep -i digest
   ```
3. digest가 다를 경우 이미지를 pull하고 컨테이너를 재시작한다.
   ```bash
   docker compose pull && docker compose up -d
   ```

**구현 옵션:**

| 방식 | 설명 |
|------|------|
| `diun` | digest 변경을 감지해 알림 또는 재시작 트리거 |
| 커스텀 폴링 스크립트 | cron + `docker manifest inspect` 비교 |
| `docker compose pull --check` | compose 레벨에서 새 이미지 존재 여부 확인 |

### 이미지 태그 규칙

- `latest` 태그와 함께 버전 태그(`YY.메이저.마이너`)를 **함께 push**한다.
- digest 감지는 `latest` 태그를 기준으로 한다.

```bash
docker build -t <image>:latest -t <image>:26.1.0 .
docker push <image>:latest
docker push <image>:26.1.0
```

## 관련 규칙

- **[git-workflow.md](git-workflow.md)**: 배포 전 커밋·태그 규칙을 함께 확인한다.
- **[versioning.md](versioning.md)**: DockerHub push 전 버전 태그 확정을 확인한다.

---
name: wiki-client
description: >
  Wiki 서버(무상태 REST, MCP 대체)를 curl로 조회·기록할 때 반드시 확인해야 할 규칙.
  다음 상황에서 반드시 이 스킬을 먼저 확인한다:
  (1) Wiki 서버에서 지식/스킬을 조회하거나 신규 등록할 때
  (2) 프로젝트 작업 시작 시 해당 wiki_id의 기존 지식을 확인할 때
  (3) 세션 중 얻은 의사결정·패턴·디버깅 기록을 Wiki에 남길 때
allowed_tools: []
run_as: inline
---

# Wiki Client Rules

## 기본 개념

- Wiki 서버는 MCP(OAuth 세션)를 대체하는 **무상태(stateless) REST API**다. 매 요청이 독립적이라 연결 끊김·재인증 문제가 없다.
- 서버 하나에 여러 `wiki_id`(네임스페이스)가 공존할 수 있다. 예: 행동 강령용 `jamong-harvest`, 업무별 wiki.
- 페이지는 `slug` 단위로 식별되며, `slug`는 생성 시 title로부터 1회 확정되고 이후 **불변**이다(title이 바뀌어도 slug는 유지).
- 무인증·내부망 전용 서버다. 외부에 노출된 주소라면 절대 쓰기 요청을 보내지 않는다.

## 현재 프로젝트의 wiki_id 확인

1. 프로젝트 루트의 `CLAUDE.md`/`AGENTS.md`에 선언된 `<WIKI_ID>` 값을 먼저 확인한다.
2. 선언이 없으면 `GET /wikis`로 사용 가능한 wiki 목록을 조회한 뒤, **추측하지 말고** 사용자에게 어떤 wiki를 쓸지 질문한다.

## 환경변수

- `WIKI_BASE_URL`: Wiki 서버 주소. 하드코딩하지 않는다 — 값이 없으면 사용자에게 확인한다.

## 엔드포인트 레퍼런스

| Method | Path | 설명 |
|---|---|---|
| GET | `/wikis` | 사용 가능한 wiki_id 목록 |
| GET | `/wikis/{wiki_id}/pages` | 페이지 인덱스 (slug, title, tags, category, updated) |
| POST | `/wikis/{wiki_id}/pages` | 신규 페이지 생성 (title, content, category 필수 / tags 선택) |
| GET | `/wikis/{wiki_id}/pages/{slug}` | 페이지 전체 조회 |
| PUT | `/wikis/{wiki_id}/pages/{slug}` | 페이지 갱신 (필드 부분 수정) |
| DELETE | `/wikis/{wiki_id}/pages/{slug}` | 페이지 삭제 |
| GET | `/wikis/{wiki_id}/search?q=&tags=&category=` | 키워드/태그/카테고리 검색 |

`category`는 `architecture`, `decision`, `pattern`, `debugging`, `environment`, `session-log` 중 하나여야 한다.

## curl 사용 예시

```bash
# wiki 목록
curl -s "$WIKI_BASE_URL/wikis" | python3 -m json.tool

# 페이지 인덱스
curl -s "$WIKI_BASE_URL/wikis/jamong-harvest/pages" | python3 -m json.tool

# 신규 페이지 생성
curl -s -X POST "$WIKI_BASE_URL/wikis/jamong-harvest/pages" \
  -H 'Content-Type: application/json' \
  -d '{"title":"제목","content":"본문","tags":["tag1"],"category":"pattern"}' \
  | python3 -m json.tool

# 페이지 조회 (한글 slug는 URL 인코딩 필요)
SLUG_ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "<slug>")
curl -s "$WIKI_BASE_URL/wikis/jamong-harvest/pages/$SLUG_ENC" | python3 -m json.tool

# 페이지 수정 (부분 필드만 전달)
curl -s -X PUT "$WIKI_BASE_URL/wikis/jamong-harvest/pages/$SLUG_ENC" \
  -H 'Content-Type: application/json' \
  -d '{"content":"수정된 본문"}' | python3 -m json.tool

# 페이지 삭제
curl -s -X DELETE "$WIKI_BASE_URL/wikis/jamong-harvest/pages/$SLUG_ENC" | python3 -m json.tool

# 검색
curl -s "$WIKI_BASE_URL/wikis/jamong-harvest/search?q=<키워드>" | python3 -m json.tool
```

## 페이지 작성 규칙

- `title`: 사람이 읽을 제목. slug는 여기서 자동 생성되며 이후 title을 바꿔도 유지된다.
- `tags`: 검색 필터용 키워드 배열.
- `category`: 위 6종 중 정확히 하나.
- `content`: 마크다운 본문.

## 에러 처리

| 상태 코드 | 의미 | 대응 |
|---|---|---|
| 400 | 필수 필드 누락, 잘못된 category, wiki_id/slug 형식 오류 | 요청 본문/경로를 다시 확인 |
| 404 | wiki_id 또는 slug가 존재하지 않음 | `GET /wikis` 또는 페이지 인덱스로 실제 존재 여부 확인 |
| 409 | POST 시 동일 slug 페이지가 이미 존재 | PUT으로 수정하거나 title을 바꿔 재생성 |

## 관련 스킬

- **completion-report**: Wiki에 기록한 지식을 완료 보고에 반영할 때 함께 확인한다.

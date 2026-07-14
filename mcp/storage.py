#!/usr/bin/env python3
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

VALID_CATEGORIES = {
    "architecture",
    "decision",
    "pattern",
    "debugging",
    "environment",
    "session-log",
}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass
class Page:
    slug: str
    title: str
    tags: list[str]
    category: str
    created: str
    updated: str
    content: str = field(default="")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(title: str) -> str:
    out = []
    for ch in title.lower():
        out.append(ch if ch.isalnum() else "-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    if not slug:
        raise ValueError("title에서 slug를 만들 수 없습니다")
    return slug


def is_valid_wiki_id(s: str) -> bool:
    return bool(SLUG_RE.match(s))


def is_valid_slug(s: str) -> bool:
    return bool(SLUG_RE.match(s))


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter가 없습니다 (파일이 '---'로 시작해야 함)")

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("frontmatter 종료 구분선('---')을 찾을 수 없습니다")

    meta: dict = {"tags": []}
    for line in lines[1:end]:
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "tags":
            inner = value.strip("[]").strip()
            meta["tags"] = [t.strip() for t in inner.split(",") if t.strip()] if inner else []
        else:
            meta[key] = value

    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return meta, body


def render_page(page: Page) -> str:
    tags_str = "[" + ", ".join(page.tags) + "]"
    frontmatter = (
        "---\n"
        f"title: {page.title}\n"
        f"tags: {tags_str}\n"
        f"category: {page.category}\n"
        f"created: {page.created}\n"
        f"updated: {page.updated}\n"
        "---\n\n"
    )
    return frontmatter + page.content


def _wiki_dir(data_dir: Path, wiki_id: str) -> Path:
    return data_dir / wiki_id


def _page_path(data_dir: Path, wiki_id: str, slug: str) -> Path:
    return _wiki_dir(data_dir, wiki_id) / f"{slug}.md"


def _load(path: Path, slug: str) -> Page:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return Page(
        slug=slug,
        title=meta.get("title", slug),
        tags=meta.get("tags", []),
        category=meta.get("category", ""),
        created=meta.get("created", ""),
        updated=meta.get("updated", ""),
        content=body,
    )


def list_wikis(data_dir: Path) -> list[str]:
    if not data_dir.exists():
        return []
    return sorted(d.name for d in data_dir.iterdir() if d.is_dir())


def list_pages(data_dir: Path, wiki_id: str) -> list[Page]:
    wiki_dir = _wiki_dir(data_dir, wiki_id)
    if not wiki_dir.exists():
        raise FileNotFoundError(f"wiki not found: {wiki_id}")
    return sorted(
        (_load(p, p.stem) for p in wiki_dir.glob("*.md")),
        key=lambda pg: pg.slug,
    )


def read_page(data_dir: Path, wiki_id: str, slug: str) -> Page:
    path = _page_path(data_dir, wiki_id, slug)
    if not path.exists():
        raise FileNotFoundError(f"page not found: {wiki_id}/{slug}")
    return _load(path, slug)


def create_page(
    data_dir: Path,
    wiki_id: str,
    *,
    title: str,
    content: str,
    tags: list[str] | None = None,
    category: str,
) -> Page:
    if not title or not title.strip():
        raise ValueError("title은 비어 있을 수 없습니다")
    if not content or not content.strip():
        raise ValueError("content는 비어 있을 수 없습니다")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"category는 {sorted(VALID_CATEGORIES)} 중 하나여야 합니다")

    slug = slugify(title)
    wiki_dir = _wiki_dir(data_dir, wiki_id)
    path = wiki_dir / f"{slug}.md"
    if path.exists():
        raise FileExistsError(f"page already exists: {wiki_id}/{slug}")

    wiki_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso()
    page = Page(
        slug=slug,
        title=title,
        tags=tags or [],
        category=category,
        created=ts,
        updated=ts,
        content=content,
    )
    path.write_text(render_page(page), encoding="utf-8")
    return page


def update_page(
    data_dir: Path,
    wiki_id: str,
    slug: str,
    *,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
) -> Page:
    page = read_page(data_dir, wiki_id, slug)
    if title is not None:
        page.title = title
    if content is not None:
        page.content = content
    if tags is not None:
        page.tags = tags
    if category is not None:
        if category not in VALID_CATEGORIES:
            raise ValueError(f"category는 {sorted(VALID_CATEGORIES)} 중 하나여야 합니다")
        page.category = category
    page.updated = now_iso()

    path = _page_path(data_dir, wiki_id, slug)
    path.write_text(render_page(page), encoding="utf-8")
    return page


def delete_page(data_dir: Path, wiki_id: str, slug: str) -> None:
    path = _page_path(data_dir, wiki_id, slug)
    if not path.exists():
        raise FileNotFoundError(f"page not found: {wiki_id}/{slug}")
    path.unlink()


def search_pages(
    data_dir: Path,
    wiki_id: str,
    *,
    q: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
) -> list[Page]:
    pages = list_pages(data_dir, wiki_id)
    results = []
    for pg in pages:
        if q:
            haystack = f"{pg.title}\n{pg.content}".lower()
            if q.lower() not in haystack:
                continue
        if tags:
            if not set(tags).issubset(set(pg.tags)):
                continue
        if category and pg.category != category:
            continue
        results.append(pg)
    return results

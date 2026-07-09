#!/usr/bin/env python3
import os
from dataclasses import asdict
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import storage

DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).parent / "data")


def _index_projection(page: storage.Page) -> dict:
    return {
        "slug": page.slug,
        "title": page.title,
        "tags": page.tags,
        "category": page.category,
        "updated": page.updated,
    }


def _validate_ids(wiki_id: str, slug: str | None = None) -> None:
    if not storage.is_valid_wiki_id(wiki_id):
        raise ValueError(f"invalid wiki_id: {wiki_id}")
    if slug is not None and not storage.is_valid_slug(slug):
        raise ValueError(f"invalid slug: {slug}")


async def list_wikis(request: Request) -> JSONResponse:
    return JSONResponse({"wikis": storage.list_wikis(DATA_DIR)})


async def list_pages(request: Request) -> JSONResponse:
    wiki_id = request.path_params["wiki_id"]
    try:
        _validate_ids(wiki_id)
        pages = storage.list_pages(DATA_DIR, wiki_id)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    return JSONResponse({"wiki_id": wiki_id, "pages": [_index_projection(p) for p in pages]})


async def create_page(request: Request) -> JSONResponse:
    wiki_id = request.path_params["wiki_id"]
    try:
        _validate_ids(wiki_id)
        body = await request.json()
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception:
        return JSONResponse({"error": "malformed JSON body"}, status_code=400)

    try:
        page = storage.create_page(
            DATA_DIR,
            wiki_id,
            title=body.get("title", ""),
            content=body.get("content", ""),
            tags=body.get("tags"),
            category=body.get("category", ""),
        )
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except FileExistsError as e:
        return JSONResponse({"error": str(e)}, status_code=409)

    return JSONResponse(
        asdict(page),
        status_code=201,
        headers={"Location": f"/wikis/{wiki_id}/pages/{page.slug}"},
    )


async def get_page(request: Request) -> JSONResponse:
    wiki_id = request.path_params["wiki_id"]
    slug = request.path_params["slug"]
    try:
        _validate_ids(wiki_id, slug)
        page = storage.read_page(DATA_DIR, wiki_id, slug)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    return JSONResponse(asdict(page))


async def update_page(request: Request) -> JSONResponse:
    wiki_id = request.path_params["wiki_id"]
    slug = request.path_params["slug"]
    try:
        _validate_ids(wiki_id, slug)
        body = await request.json()
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception:
        return JSONResponse({"error": "malformed JSON body"}, status_code=400)

    try:
        page = storage.update_page(
            DATA_DIR,
            wiki_id,
            slug,
            title=body.get("title"),
            content=body.get("content"),
            tags=body.get("tags"),
            category=body.get("category"),
        )
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    return JSONResponse(asdict(page))


async def delete_page(request: Request) -> JSONResponse:
    wiki_id = request.path_params["wiki_id"]
    slug = request.path_params["slug"]
    try:
        _validate_ids(wiki_id, slug)
        storage.delete_page(DATA_DIR, wiki_id, slug)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    return JSONResponse({"deleted": True, "slug": slug})


async def search_pages(request: Request) -> JSONResponse:
    wiki_id = request.path_params["wiki_id"]
    q = request.query_params.get("q")
    tags_param = request.query_params.get("tags")
    tags = [t.strip() for t in tags_param.split(",") if t.strip()] if tags_param else None
    category = request.query_params.get("category")

    try:
        _validate_ids(wiki_id)
        results = storage.search_pages(DATA_DIR, wiki_id, q=q, tags=tags, category=category)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    return JSONResponse({"wiki_id": wiki_id, "results": [_index_projection(p) for p in results]})


routes = [
    Route("/wikis", list_wikis, methods=["GET"]),
    Route("/wikis/{wiki_id}/pages", list_pages, methods=["GET"]),
    Route("/wikis/{wiki_id}/pages", create_page, methods=["POST"]),
    Route("/wikis/{wiki_id}/pages/{slug}", get_page, methods=["GET"]),
    Route("/wikis/{wiki_id}/pages/{slug}", update_page, methods=["PUT"]),
    Route("/wikis/{wiki_id}/pages/{slug}", delete_page, methods=["DELETE"]),
    Route("/wikis/{wiki_id}/search", search_pages, methods=["GET"]),
]

app = Starlette(routes=routes)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    host = os.environ.get("HOST", "127.0.0.1")

    if host == "0.0.0.0":
        raise SystemExit(
            "HOST=0.0.0.0 금지 — Wiki 서버는 무인증이므로 내부망 인터페이스 IP를 지정하세요 (SPEC 4.5)"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    uvicorn.run(app, host=host, port=port)

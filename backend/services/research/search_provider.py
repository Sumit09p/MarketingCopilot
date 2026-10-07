from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.config.settings import get_settings


class SearchProvider:
    """
    Lightweight external search provider.

    Uses Tavily when SEARCH_API_KEY is configured.
    If no key is configured, returns an unavailable response so
    the Research Agent can safely fall back to qualitative research.
    """

    TAVILY_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()

        if api_key is not None:
            self.api_key = api_key
        elif settings.SEARCH_API_KEY is not None:
            self.api_key = settings.SEARCH_API_KEY.get_secret_value()
        else:
            self.api_key = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> dict[str, Any]:
        query = str(query or "").strip()

        if not query:
            return {
                "available": False,
                "results": [],
                "error": "Search query is empty.",
            }

        if not self.available:
            return {
                "available": False,
                "results": [],
                "error": "SEARCH_API_KEY is not configured.",
            }

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }

        request = Request(
            self.TAVILY_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")

            raw = json.loads(body)

            results = []

            for item in raw.get("results", []):
                if not isinstance(item, dict):
                    continue

                title = str(item.get("title") or "").strip()
                content = str(item.get("content") or "").strip()
                url = str(item.get("url") or "").strip()

                if not title and not content:
                    continue

                results.append(
                    {
                        "title": title,
                        "content": content,
                        "url": url,
                    }
                )

            return {
                "available": True,
                "results": results,
                "error": None,
            }

        except HTTPError as exc:
            return {
                "available": False,
                "results": [],
                "error": f"Search provider HTTP error: {exc.code}",
            }

        except URLError as exc:
            return {
                "available": False,
                "results": [],
                "error": f"Search provider connection error: {exc.reason}",
            }

        except TimeoutError:
            return {
                "available": False,
                "results": [],
                "error": "Search provider request timed out.",
            }

        except Exception as exc:
            return {
                "available": False,
                "results": [],
                "error": f"Search provider error: {exc}",
            }

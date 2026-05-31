import logging
import os
from pathlib import Path
from typing import Any, Dict
from urllib import parse

from hishel import AsyncSqliteStorage, BaseFilter, FilterPolicy, Request
from hishel.httpx import AsyncCacheClient

logger = logging.getLogger(__name__)


class _RequestFilters(BaseFilter[Request]):
    def needs_body(self) -> bool:
        return False

    def apply(self, item: Request, body: bytes | None) -> bool:
        logger.info("item.url: %s", item.url)
        return not item.url.endswith("/random")


class UrbanDictionary(object):
    url = "https://api.urbandictionary.com/v0"

    def __init__(self):
        self.headers = {"Accept": "application/json; charset=UTF-8"}
        cache_path = os.environ.get("HISHEL_CACHE_PATH", Path.cwd() / "hishel_cache.db")
        cache_ttl = int(os.environ.get("HISHEL_CACHE_TTL", "1209600"))
        logger.info("UrbanDictionary(cache_path=%s, cache_ttl=%s)", cache_path, cache_ttl)
        storage = AsyncSqliteStorage(database_path=cache_path, default_ttl=cache_ttl)
        policy = FilterPolicy(request_filters=[_RequestFilters()])
        self._client = AsyncCacheClient(storage=storage, policy=policy, follow_redirects=True, timeout=10)

    def __repr__(self):
        return f"UrbanDictionary(url={self.url})"

    async def close(self):
        await self._client.aclose()

    async def _get_request(self, url, **kwargs) -> Any:
        try:
            r = await self._client.get(url, headers=self.headers, **kwargs)
            r.raise_for_status()
            logger.info("hishel_from_cache: %s", r.extensions.get("hishel_from_cache"))
            return r.json()
        except Exception as error:
            logger.error("url: %s - error: %s", url, error)
            return {"error": f"API Error: {error}"}

    async def define_term(self, term: str) -> Dict[str, Any]:
        """Get the Urban Dictionary definition for provided <word>."""
        safe_word = parse.quote_plus(term.strip().lower())
        url = f"{self.url}/define"
        params = {"term": safe_word}
        result = await self._get_request(url, params=params)
        return await self._filter_list(result)

    async def random_terms(self) -> Dict[str, Any]:
        """Get random terms from Urban Dictionary."""
        url = f"{self.url}/random"
        result = await self._get_request(url)
        return await self._filter_list(result)

    @staticmethod
    async def _filter_list(result: Dict[str, Any]) -> Dict[str, Any]:
        if "list" in result:
            result["list"] = [
                {k: item[k] for k in ("word", "definition", "example", "thumbs_up", "thumbs_down")}
                for item in result["list"]
            ]
        return result

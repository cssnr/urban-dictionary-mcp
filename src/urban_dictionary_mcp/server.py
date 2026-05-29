import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent
from pydantic import Field

from ._version import __version__
from .urban import UrbanDictionary
from .utils import str_to_bool

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


@dataclass
class AppContext:
    urban: UrbanDictionary


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    logger.info("%s %s", server.name, __version__)
    urban = UrbanDictionary()
    try:
        yield AppContext(urban=urban)
    finally:
        await urban.close()


mcp = FastMCP(
    "urban-dictionary",
    lifespan=app_lifespan,
    json_response=True,
    stateless_http=str_to_bool(os.environ.get("STATELESS_HTTP", "true")),
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# noinspection PyProtectedMember
mcp._mcp_server.version = __version__


@mcp.tool()
async def urban_dictionary_lookup(
    search_term: Annotated[str, Field(description="Word, phrase or slang term to define using the Urban Dictionary")],
    ctx: Context[ServerSession, AppContext],
    limit: Annotated[int, Field(description="Maximum number of results to return", default=5, ge=1, le=20)] = 5,
) -> CallToolResult:
    """Look up the meaning of a word, phrase or slang term using the Urban Dictionary. Returns a list of definitions and examples."""
    logger.info("urban_lookup: %s", search_term)
    urban: UrbanDictionary = ctx.request_context.lifespan_context.urban
    results = await urban.define_term(search_term)
    if "list" in results:
        logger.info("length: %s", len(results["list"]))
        results["list"] = results["list"][:limit]
    logger.info("results: %s", results)
    text = json.dumps(results)
    is_error = results.get("error")
    if is_error:
        logger.error("is_error: %s - results: %s", is_error, results)
    return CallToolResult(content=[TextContent(type="text", text=text)], isError=bool(is_error))


def main():
    mcp.run(transport="stdio")


app = mcp.streamable_http_app()

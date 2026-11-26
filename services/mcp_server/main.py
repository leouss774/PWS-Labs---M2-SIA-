"""MCP server: operations of the shop, as tools an assistant can discover and call."""

import os

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://127.0.0.1:8000")

mcp = MCPServer("shop", instructions="A small shop of coffee equipment: browse the catalogue, place orders.")

READS = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def send(method: str, url: str, **kwargs) -> httpx.Response:
    """One HTTP call to the shop. A service that is down becomes a sentence the model can read."""
    try:
        return httpx.request(method, url, timeout=2, **kwargs)
    except httpx.RequestError:
        raise ToolError(f"{url.split('/')[2]} cannot be reached. Try again later.")


def reason(response: httpx.Response) -> str:
    """The detail of an error answer, in one line, whatever its shape."""
    detail = response.json().get("detail", f"status {response.status_code}")
    if isinstance(detail, list):  # a 422 from FastAPI: one entry per broken rule
        detail = "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in detail)
    return detail


def fetch_product(product_id: int) -> dict:
    response = send("GET", f"{INVENTORY_URL}/products/{product_id}")
    if response.status_code != 200:
        raise ToolError(reason(response))
    return response.json()


@mcp.tool(annotations=READS)
def list_products(in_stock: bool | None = None, limit: int = 10) -> list[dict]:
    """List the products of the shop: id, name, price in euros, units in stock.
    Set in_stock to true to see only what can be ordered now. limit is 1 to 100."""
    params = {"limit": limit}
    if in_stock is not None:
        params["in_stock"] = in_stock
    response = send("GET", f"{INVENTORY_URL}/products", params=params)
    if response.status_code != 200:
        raise ToolError(reason(response))
    return response.json()


@mcp.tool(annotations=READS)
def get_product(product_id: int) -> dict:
    """One product, by its id: name, price in euros, units in stock."""
    return fetch_product(product_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=os.environ.get("MCP_HOST", "127.0.0.1"), port=8002)

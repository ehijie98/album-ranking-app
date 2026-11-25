import httpx


async def search_artists(
    name: str,
    client: httpx.AsyncClient
) -> list[dict]:
    raise NotImplementedError
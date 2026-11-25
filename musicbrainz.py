import httpx


async def search_artists(name: str, client: httpx.AsyncClient) -> list[dict]:
    query = f'artist:"{name}"'
    response = await client.get(
        "https://musicbrainz.org/ws/2/artist/",
        params={
            "query": query,
            "fmt": "json",
        },
        headers={"User-Agent": "AlbumRankingApp/ 0.1 eaghedo1@gmail.com"},
    )

    data = response.json()

    return [{"id": artist["id"], "name": artist["name"]} for artist in data["artists"]]

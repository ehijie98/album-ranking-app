import httpx


async def search_artists(name: str, client: httpx.AsyncClient) -> list[dict]:
    query = f'artist:"{name}"'
    response = await client.get(
        "https://musicbrainz.org/ws/2/artist",
        params={
            "query": query,
            "fmt": "json",
        },
        headers={"User-Agent": "AlbumRankingApp/0.1 eaghedo1@gmail.com"},
    )
    response.raise_for_status()
    data = response.json()

    return [
        {
            "id": artist["id"],
            "name": artist["name"],
            "disambiguation": artist.get("disambiguation", ""),
        }
        for artist in data["artists"]
    ]


async def get_artist_albums(artist_id: str, client: httpx.AsyncClient) -> list[dict]:
    response = await client.get(
        "https://musicbrainz.org/ws/2/release-group",
        params={"artist": artist_id, "type": "album", "fmt": "json"},
        headers={"User-Agent": "AlbumRankingApp/0.1 eaghedo1@gmail.com"},
    )
    response.raise_for_status()
    data = response.json()

    return [
        {
            "id": release_group["id"],
            "title": release_group["title"],
            "release_date": release_group.get("first-release-date") or None,
        }
        for release_group in data["release-groups"]
        if not release_group.get("secondary-types", [])
    ]

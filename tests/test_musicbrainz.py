import httpx
import pytest

from musicbrainz import search_artists, get_artist_albums


# make_client helper function to accept mock_handler and return async HTTP client weith mock transport
def make_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_search_artists_returns_correct_artists():

    # fake MusicBrainz HTTP response
    def mock_handler(request: httpx.Request) -> httpx.Response:

        return httpx.Response(
            status_code=200,
            json={
                "artists": [
                    {
                        "id": "artist-1",
                        "name": "Artist One",
                        "disambiguation": "Canadian rapper",
                        "country": "GB",
                        "score": 100,
                    }
                ]
            },
        )

    # creating asynchronous HTTP client
    async with make_client(mock_handler) as client:
        # client is injected into function
        result = await search_artists("Artist One", client=client)

    assert result == [
        {"id": "artist-1", "name": "Artist One", "disambiguation": "Canadian rapper"}
    ]


@pytest.mark.asyncio
async def test_sends_valid_search_request():
    requests_made = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        requests_made.append(request)
        return httpx.Response(200, json={"artists": []})

    async with make_client(mock_handler) as client:
        await search_artists("Artist One", client=client)

    assert len(requests_made) == 1

    request = requests_made[0]

    assert request.method == "GET"
    assert request.url.host == "musicbrainz.org"
    assert request.url.path == "/ws/2/artist"
    assert request.url.params["query"] == 'artist:"Artist One"'
    assert request.url.params["fmt"] == "json"
    assert request.headers["User-Agent"].startswith("AlbumRankingApp/")


@pytest.mark.asyncio
async def test_sends_empty_list_for_no_artist_match():

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"artists": []},
        )

    async with make_client(mock_handler) as client:
        result = await search_artists("qqqqqq", client=client)

    assert result == []


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 429, 500, 502, 503, 504])
@pytest.mark.asyncio
async def test_search_artist_raises_on_http_errors(status_code):

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            json={"error": "Service unavailable. Please try again later"},
        )

    async with make_client(mock_handler) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await search_artists("Artist One", client=client)

    assert exc_info.value.response.status_code == status_code


@pytest.mark.asyncio
async def test_search_artists_propagates_connection_timeout():

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("Connection timed out")

    async with make_client(mock_handler) as client:
        with pytest.raises(httpx.ConnectTimeout):
            await search_artists("Artist One", client=client)


@pytest.mark.asyncio
async def test_search_artists_returns_multiple_artists_with_same_name():

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "artists": [
                    {
                        "id": "artist-1",
                        "name": "Artist One",
                        "disambiguation": "Canadian rapper",
                    },
                    {
                        "id": "artist-2",
                        "name": "Artist One",
                        "disambiguation": "English singer-songwriter",
                    },
                ]
            },
        )

    async with make_client(mock_handler) as client:
        result = await search_artists("Artist One", client=client)

    assert result == [
        {
            "id": "artist-1",
            "name": "Artist One",
            "disambiguation": "Canadian rapper",
        },
        {
            "id": "artist-2",
            "name": "Artist One",
            "disambiguation": "English singer-songwriter",
        },
    ]


@pytest.mark.asyncio
async def test_search_artists_handles_missing_disambiguation_field():

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "artists": [
                    {
                        "id": "artist-1",
                        "name": "Artist One",
                    },
                ]
            },
        )

    async with make_client(mock_handler) as client:
        result = await search_artists("Artist One", client=client)
    assert result == [{"id": "artist-1", "name": "Artist One", "disambiguation": ""}]


@pytest.mark.asyncio
async def test_artist_mbid_retrieves_valid_release_groups():

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "release-group-count": 2,
                "release-groups": [
                    {
                        "id": "album-1",
                        "title": "Album One",
                        "first-release-date": "2021-01-01",
                        "primary-type": "Album",
                        "secondary-types": [],
                    },
                    {
                        "id": "album-2",
                        "title": "Album Two",
                        "first-release-date": "2022-02-02",
                        "primary-type": "Album",
                        "secondary-types": [],
                    },
                ],
            },
        )

    async with make_client(mock_handler) as client:
        result = await get_artist_albums("artist-1", client)

    assert result == [
        {"id": "album-1", "title": "Album One", "release_date": "2021-01-01"},
        {"id": "album-2", "title": "Album Two", "release_date": "2022-02-02"},
    ]


@pytest.mark.asyncio
async def test_send_valid_get_artist_albums_request():

    requests_made = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        requests_made.append(request)

        return httpx.Response(
            200, json={"release-group-count": 0, "release-groups": []}
        )

    async with make_client(mock_handler) as client:
        await get_artist_albums("artist-1", client=client)

    assert len(requests_made) == 1

    request = requests_made[0]

    assert request.method == "GET"
    assert request.url.host == "musicbrainz.org"
    assert request.url.path == "/ws/2/release-group"
    assert request.url.params["artist"] == "artist-1"
    assert request.url.params["fmt"] == "json"
    assert request.headers["User-Agent"].startswith("AlbumRankingApp/")


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 429, 500, 502, 503, 504])
@pytest.mark.asyncio
async def test_get_artist_albums_raises_on_http_error(status_code):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            json={"error": "Service Unavailable. Please try again later"},
        )

    async with make_client(mock_handler) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await get_artist_albums("artist-1", client=client)

    assert exc_info.value.response.status_code == status_code


@pytest.mark.asyncio
async def test_get_artist_albums_handles_no_release_groups():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"release-group-count": 0, "release-groups": []},
        )

    async with make_client(mock_handler) as client:
        result = await get_artist_albums("artist-with-no-release-groups", client=client)

    assert result == []


@pytest.mark.asyncio
async def test_get_artist_albums_only_retrieves_type_album():
    requests_made = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        requests_made.append(request)
        return httpx.Response(
            status_code=200,
            json={
                "release-group-count": 2,
                "release-groups": [
                    {
                        "id": "album-1",
                        "title": "Album One",
                        "first-release-date": "2021-01-01",
                        "primary-type": "Album",
                        "secondary-types": [],
                    },
                    {
                        "id": "album-2",
                        "title": "Album Two",
                        "first-release-date": "2022-02-02",
                        "primary-type": "Album",
                        "secondary-types": [],
                    },
                ],
            },
        )

    async with make_client(mock_handler) as client:
        await get_artist_albums("artist-1", client=client)

    assert len(requests_made) == 1

    request = requests_made[0]
    assert request.url.params["type"] == "album"


@pytest.mark.asyncio
async def test_get_artist_albums_retrieves_empty_secondary_type():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "release-group-count": 4,
                "release-groups": [
                    {
                        "id": "album-1",
                        "title": "Album One",
                        "first-release-date": "2021-01-01",
                        "primary-type": "Album",
                        "secondary-types": ["Live"],
                    },
                    {
                        "id": "album-2",
                        "title": "Album Two",
                        "first-release-date": "2022-02-02",
                        "primary-type": "Album",
                        "secondary-types": ["Compilation"],
                    },
                    {
                        "id": "album-3",
                        "title": "Album Three",
                        "first-release-date": "2023-03-03",
                        "primary-type": "Album",
                        "secondary-types": ["Remix"],
                    },
                    {
                        "id": "album-4",
                        "title": "Album Four",
                        "first-release-date": "2024-04-04",
                        "primary-type": "Album",
                        "secondary-types": [],
                    },
                ],
            },
        )

    async with make_client(mock_handler) as client:
        result = await get_artist_albums("artist-1", client=client)

    assert result == [
        {
            "id": "album-4",
            "title": "Album Four",
            "release_date": "2024-04-04",
        }
    ]

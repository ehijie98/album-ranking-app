import httpx
import pytest

from musicbrainz import search_artists


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

    assert result == [{"id": "artist-1", "name": "Artist One", "disambiguation": "Canadian rapper"}]


@pytest.mark.asyncio
async def test_sends_valid_search_request():

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.host == "musicbrainz.org"
        assert request.url.path == "/ws/2/artist/"
        assert request.url.params["query"] == 'artist:"Artist One"'
        assert request.url.params["fmt"] == "json"
        assert request.headers["User-Agent"].startswith("AlbumRankingApp/")

        return httpx.Response(200, json={"artists": []})

    async with make_client(mock_handler) as client:
        await search_artists("Artist One", client=client)


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

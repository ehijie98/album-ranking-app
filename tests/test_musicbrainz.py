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
                        "country": "GB",
                        "score": 100,
                    }
                ]
            },
        )

    # creating asynchronous HTTP client
    async with make_client(mock_handler) as client:
        # client is injected into function
        result = await search_artists("Artist One", client)

    assert result == [{"id": "artist-1", "name": "Artist One"}]


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


@pytest.mark.asyncio
async def test_raises_error_on_503():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=503,
            json={"error": "Service unavailable. Please try again later"},
        )

    async with make_client(mock_handler) as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await search_artists("Artist One", client=client)

    assert exc_info.value.response.status_code == 503

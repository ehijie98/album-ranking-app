import httpx
import pytest

from musicbrainz import search_artists


# make_client helper function to accept mock_handler and return async HTTP client weith mock transport
def make_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_search_artists_returns_correct_artists():

    # fake MusicBrainz HTTP response
    def mock_handler(request: httpx.Request):
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

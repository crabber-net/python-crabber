from .context import API_KEY, crabber
import pytest

api = crabber.API(API_KEY)

class TestAPI:
    def test_connection(self):
        # Successful connection
        crabber.API(API_KEY)

        # Failure to connect
        with pytest.raises(ConnectionError):
            crabber.API(API_KEY, base_url='https://google.com')

    def test_get_crab(self):
        # Crab doesn't exist
        assert api.get_crab(-2) is None

        # Valid crab
        crab = api.get_crab(1)
        assert crab is not None
        assert isinstance(crab.username, str)
        assert isinstance(crab.id, int)

        assert api.get_crab_by_username(crab.username) is crab

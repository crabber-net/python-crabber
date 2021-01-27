from .context import ACCESS_TOKEN, API_KEY, crabber, sample_error_html
from datetime import datetime
import pytest

class TestAPI:
    def test_connection(self):
        # Successful connection
        api = crabber.API(API_KEY)

        # Failure to connect
        with pytest.raises(ConnectionError):
            crabber.API(API_KEY, base_url='https://google.com')

        # Authenticate in init
        api = crabber.API(API_KEY, access_token=ACCESS_TOKEN)
        assert api.get_current_user() is not None

    def test_get_crab(self):
        api = crabber.API(API_KEY)

        # Crab doesn't exist
        assert api.get_crab(-2) is None

        # Valid Crab
        crab = api.get_crab(1)
        assert crab is not None
        assert isinstance(crab.username, str)
        assert isinstance(crab.id, int)
        assert isinstance(crab.bio, crabber.Bio)
        assert isinstance(crab.register_time, datetime)

        # Test Crab caching
        assert api.get_crab(crab.id) is crab
        assert api.get_crab_by_username(crab.username) is crab

    def test_get_molt(self):
        api = crabber.API(API_KEY)

        # Molt doesn't exist
        assert api.get_molt(-2) is None

        # Valid Molt
        molt = api.get_molt(1)
        assert molt is not None
        assert isinstance(molt.author, crabber.Crab)
        assert isinstance(molt.id, int)
        assert isinstance(molt.likes, int)
        assert isinstance(molt.remolts, int)

        # Test Molt caching
        assert api.get_molt(molt.id) is molt

    def test_authenticated_actions(self):
        api = crabber.API(API_KEY)

        assert api.get_current_user() is None

        sample_molt = api.get_molt(1)
        auth_funcs = (
            (api.post_molt, ('Test molt. This should fail.',)),
            (sample_molt.reply, ('Test molt. This should fail.',)),
            (sample_molt.remolt, ()),
            (sample_molt.unremolt, ()),
            (sample_molt.like, ()),
            (sample_molt.unlike, ()),
            (sample_molt.author.follow, ()),
            (sample_molt.author.unfollow, ()),
        )

        # Test authentication failures
        for auth_func, args in auth_funcs:
            with pytest.raises(crabber.exceptions.RequiresAuthenticationError):
                auth_func(*args)

        assert api.authenticate(ACCESS_TOKEN)

        # Test network failures
        old_base_url = api.base_url
        api.base_url = 'http://google.com'
        for auth_func, args in auth_funcs:
            assert auth_func(*args) == False

        api.base_url = old_base_url

        test_user = api.get_current_user()
        crabber_user = api.get_crab_by_username('crabber')
        assert test_user is not None
        assert crabber_user is not None

        assert test_user.follow() == False
        assert crabber_user.follow()
        assert crabber_user in test_user.following
        assert crabber_user.unfollow()
        assert crabber_user not in test_user.following

        molt = api.post_molt('Hello, world! This is a test Molt and this ' \
                             'action was performed automatically.')
        assert isinstance(molt, crabber.Molt)

        # Check Molt character limit
        with pytest.raises(ValueError):
            api.post_molt('A' * 500)
            molt.reply('A' * 500)

        assert molt in test_user.get_molts()
        assert molt.like()
        assert molt.unlike()
        assert molt.remolt() == False
        assert molt.delete()
        assert molt not in test_user.get_molts()

        molt = api.post_molt('Hello, @PyTest! This is a test Molt and this ' \
                             'action was performed automatically. %pytest')
        reply = molt.reply('Testing replies! %pytest')
        assert molt in api.get_molts_mentioning('pytest')
        pytest_crabtag = api.get_molts_with_crabtag('pytest')
        assert molt in pytest_crabtag
        assert reply in pytest_crabtag
        assert molt.delete()
        assert reply.delete()


class TestUtils:
    def test_parse_error_message(self):
        for error in sample_error_html:
            assert crabber.models.parse_error_message(error) is not None

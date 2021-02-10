from .context import ACCESS_TOKEN, API_KEY, crabber, TEACHER_IMAGE
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
        assert api.get_crab_by_username('a') is None

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

        test_user = api.get_crab_by_username('pytest')
        followers = test_user.followers
        assert isinstance(followers, list)

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

        replies = api.get_molts_replying_to('crabber')
        assert isinstance(replies, list)

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
            assert not auth_func(*args)

        api.base_url = old_base_url

        this_user = api.get_current_user()
        test_user = api.get_crab_by_username('test_account')
        assert this_user is not None
        assert test_user is not None

        # Test bio
        old_location = this_user.bio.location
        assert this_user.bio.update(location='In a computer!')
        assert this_user.bio.location == 'In a computer!'
        assert this_user.bio.update(location=old_location)

        # Test following relationships and actions
        assert this_user.follow() == False
        assert test_user.follow()
        assert test_user in this_user.following
        assert test_user.unfollow()
        assert test_user not in this_user.following

        # Test image failures
        with pytest.raises(FileNotFoundError):
            api.post_molt('Look at this photograph!',
                          image_path='fake_image.jpg')
        with pytest.raises(FileNotFoundError):
            molt = api.get_molt(1)
            molt.reply('Look at this photograph!', image_path='fake_image.jpg')

        molt = api.post_molt('Hello, world! This is a test Molt and this ' \
                             'action was performed automatically.')
        assert isinstance(molt, crabber.Molt)

        # Check Molt character limit
        with pytest.raises(ValueError):
            api.post_molt('A' * 500)
            molt.reply('A' * 500)

        # Test molting
        assert molt in this_user.get_molts()
        assert molt.editable
        assert molt.edit('Hello, world!')
        assert molt.content == 'Hello, world!'
        assert molt.edit(image_path=TEACHER_IMAGE)
        assert molt.image
        assert molt.like()
        assert molt.unlike()
        assert molt.remolt() == False

        # Test quote-molts
        assert molt.quotes == 0
        quote = molt.quote('hello')
        assert quote.is_quote
        assert quote.quoted_molt is molt
        assert quote.delete()
        assert quote.deleted

        # Clean up molt
        assert molt.delete()
        assert molt not in this_user.get_molts()

        # Test replies
        molt = api.post_molt('Hello, @PyTest! This is a test Molt and this ' \
                             'action was performed automatically. %pytest')
        assert molt in api.get_molts_mentioning('pytest')
        reply = molt.reply('Testing replies! %pytest')
        assert reply in molt.get_replies()
        assert reply.replying_to is molt
        pytest_crabtag = api.get_molts_with_crabtag('pytest')
        assert molt in pytest_crabtag
        assert reply in pytest_crabtag
        assert molt.delete()
        assert reply.delete()

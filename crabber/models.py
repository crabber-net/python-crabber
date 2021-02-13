from datetime import datetime
from .exceptions import MaxTriesError, RequiresAuthenticationError
import os
import requests
from typing import Any, BinaryIO, Dict, List, Optional, Union

MOLT_CHARACTER_LIMIT = 280


class API:
    """ Establishes a connection with an instance of Crabber.

        This can connect to any fork of Crabber, including one running on your
        local machine.

        :param api_key: Your developer key obtained from the developer page on
            your target instance of Crabber.
        :param access_token: Your access token obtained from the developer page
            on your target instance of Crabber. This is only for authenticated
            endpoints and can be omitted. It can also be provided after
            instantiating the API using `API.authenticate`.
        :param base_url: The URL of the instance of Crabber you want to connect
            to.
        :param base_endpoint: The API endpoint to use when making requests. At
            the current time there is no reason to change this as
            '/api/v1' is the only compliant endpoint.

        .. warning::
            You must provide a protocol (either 'http://' or 'https://')
            in `base_url` otherwise connection will fail.
    """
    def __init__(self, api_key: str, access_token: Optional[str] = None,
                 base_url: str = 'https://crabber.net',
                 base_endpoint: str = '/api/v1'):
        self.api_key: str = api_key
        self.access_token: Optional[str] = None
        self.base_url: str = base_url
        self.base_endpoint: str = base_endpoint
        self.crab: Optional['Crab'] = None
        self._crabs: Dict[int, Optional['Crab']] = dict()
        self._molts: Dict[int, Optional['Molt']] = dict()

        # Remove trailing slash from base_url if exists
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]

        self._check_connection()
        if access_token:
            self.authenticate(access_token)

    def authenticate(self, access_token: str) -> bool:
        """ Establishes authentication with the server. This can be used to
            declare an `access_token` after instantiating `API`.

            :param access_token: Your access token obtained from the developer
                page on your target instance of Crabber. This is only for
                authenticated endpoints and can be omitted. It can also be
                provided after instantiating the API using `API.authenticate`.
            :returns: Bool denoting whether authentication was successful.
        """
        self.access_token = access_token
        r = self._make_request('/authenticate/')
        self.crab = self._objectify(r.json(), 'crab')
        return r.ok

    def get_current_user(self) -> Optional['Crab']:
        """ Get the current authenticated user.

            :returns: Crab if currently authenticated.
        """
        return self.crab

    def get_crab(self, crab_id: int) -> Optional['Crab']:
        """ Get a Crab by its ID.

            :param crab_id: The ID of the Crab to return.
            :returns: Crab with `crab_id` if one exists.
        """
        # Crab already cached
        if crab_id in self._crabs:
            return self._crabs[crab_id]

        r = self._make_request(f'/crabs/{crab_id}/')
        if r.ok:
            crab = self._objectify(r.json(), 'crab')
            return crab
        elif r.status_code == 404:
            self._crabs[crab_id] = None
            return None

    def get_crab_by_username(self, username: str) -> Optional['Crab']:
        """ Get a Crab by its username.

            :param username: The username of the Crab to return.
            :returns: Crab with `username` if one exists.
        """
        # Crab already cached
        for crab in self._crabs.values():
            if crab:
                if crab.username == username:
                    return crab

        r = self._make_request(f'/crabs/username/{username}/')
        if r.ok:
            crab = self._objectify(r.json(), 'crab')
            return crab

    def get_molt(self, molt_id: int) -> Optional['Molt']:
        """ Get a Molt by its ID.

            :param molt_id: The ID of the Molt to return.
            :returns: Molt with `molt_id` if one exists.
        """
        # Molt already cached
        if molt_id in self._molts:
            return self._molts[molt_id]

        r = self._make_request(f'/molts/{molt_id}/')
        if r.ok:
            molt = self._objectify(r.json(), 'molt')
            return molt
        elif r.status_code == 404:
            self._molts[molt_id] = None
            return None

    def get_molts_with_crabtag(self, crabtag: str, limit: int = 10,
                               offset: int = 0, since_ts: Optional[int] = None,
                               since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts that use a certain crabtag.

            :param crabtag: The crabtag to search for.
            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.
        """
        r = self._make_request(f'/crabtag/{crabtag}/',
                               params={'limit': limit, 'offset': offset,
                                       'since': since_ts,
                                       'since_id': since_id})
        return [self._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]

    def get_molts_mentioning(self, username: str, limit: int = 10,
                             offset: int = 0, since_ts: Optional[int] = None,
                             since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts that mention a certain username.

            :param username: The username to search for.
            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.

            .. note::
                This only searches for usernames explicitly mentioned with
                '@username' and will not return Molts that just include the
                username in their content.
        """
        r = self._make_request(f'/molts/mentioning/{username}/',
                               params={'limit': limit, 'offset': offset,
                                       'since': since_ts,
                                       'since_id': since_id})
        return [self._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]

    def get_molts_replying_to(self, username: str, limit: int = 10,
                              offset: int = 0, since_ts: Optional[int] = None,
                              since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts that are replying to Molts posted by a certain
            username.

            :param username: The username to search for.
            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.
        """
        r = self._make_request(f'/molts/replying/{username}/',
                               params={'limit': limit, 'offset': offset,
                                       'since': since_ts,
                                       'since_id': since_id})
        return [self._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]

    def post_molt(self, content: str, image_path: Optional[str] = None) \
            -> Optional['Molt']:
        """ Post new Molt as the authenticated user.

            :param content: The text content of the Molt to post.
            :param image_path: The path to a valid image file that will be
                uploaded and included in this Molt.
            :returns: The posted Molt if successful.
            :raises: FileNotFoundError, RequiresAuthenticationError, ValueError
        """
        if len(content) <= MOLT_CHARACTER_LIMIT:
            if self.access_token:
                if image_path:
                    if not os.path.exists(image_path):
                        raise FileNotFoundError('The image path provided does '
                                                'not point to a valid file.')
                    with open(image_path, 'rb') as image_file:
                        r = self._make_request('/molts/', method='POST',
                                               data={'content': content},
                                               image=image_file)
                else:
                    r = self._make_request('/molts/', method='POST',
                                           data={'content': content})
                if r.ok:
                    return self._objectify(r.json(), 'molt')
                else:
                    return None
            else:
                raise RequiresAuthenticationError(
                    'You are not properly authenticated for this request.'
                )
        else:
            raise ValueError(f'Molts cannot exceed {MOLT_CHARACTER_LIMIT} '
                             'characters.')

    def _check_connection(self) -> bool:
        """ Attempts to make a request to the server to verify that connection
            details are valid.

            :returns: Whether the request succeeded.
            :raises: ConnectionError
        """
        r = self._make_request()
        if r.ok:
            return True
        else:
            raise ConnectionError('Site responded incorrectly. '
                                  'Is your base_url accurate?')

    def _get_paginated_data(self, endpoint: str, data_key: str,
                            limit: int = 10, starting_offset: int = 0) \
            -> Dict[str, Any]:
        """ Gets all pages of data from a paginated endpoint.

            :param limit: The per-request limit.
            :param starting_offset: The offset to begin from.
            :returns: The resulting data in a dictionary.
        """
        json_data = list()
        offset = starting_offset
        while True:
            r = self._make_request(endpoint, params={'offset': offset,
                                                     'limit': limit})
            if r.ok:
                data = r.json()

                # No results returned
                if data['count'] == 0:
                    break

                json_data += data[data_key]

                # No more data to get
                if data['total'] <= data['offset'] + data['count']:
                    break
                # Still more data to get
                else:
                    offset = data['offset'] + data['count']

                attempts = 0
            else:
                attempts += 1
        return json_data

    def _make_request(self, endpoint: str = '', method: str = 'GET',
                      params: Optional[dict] = None,
                      data: Optional[dict] = None,
                      image: Optional[BinaryIO] = None,
                      max_attempts: int = 10) \
            -> requests.models.Response:
        """ Makes a request to the server.
        """
        # Ensure endpoint is encapsulated in forward-slashes
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        if not endpoint.endswith('/'):
            endpoint = endpoint + '/'

        params = params or dict()
        params['api_key'] = self.api_key
        params['access_token'] = self.access_token

        attempts = 0
        while attempts < max_attempts:
            if method.upper() == 'GET':
                r = requests.get(self.base_url + self.base_endpoint + endpoint,
                                 params)
            elif method.upper() == 'POST':
                if image:
                    files = {'image': image}
                else:
                    files = None
                r = requests.post(self.base_url + self.base_endpoint
                                  + endpoint, params=params, data=data,
                                  files=files)
            elif method.upper() == 'DELETE':
                r = requests.delete(self.base_url + self.base_endpoint
                                    + endpoint, params=params)
            else:
                raise ValueError(f'Unknown method: "{method.upper()}"')
            if r.ok or r.status_code in (404, 400):
                return r
            elif r.status_code == 401:
                raise RequiresAuthenticationError(
                    'You are not properly authenticated for this request.'
                )
        else:
            raise MaxTriesError('Failed to complete request.')

    def _objectify(self, json: dict, type: str) -> Union['Crab', 'Molt']:
        """ Makes an object from JSON or returns cached object if available to
            ensure object continuity.
        """
        if type.lower() == 'crab':
            id = json['id']
            if id in self._crabs:
                return self._crabs[id]
            crab = Crab(json, api=self)
            self._crabs[id] = crab
            return crab
        elif type.lower() == 'molt':
            id = json['id']
            if id in self._molts:
                return self._molts[id]
            molt = Molt(json, api=self)
            self._molts[id] = molt
            return molt


class Bio:
    """ Contains a Crab's bio.

        .. warning::
            Do not directly instantiate this class. You can access it through
            `Crab.bio` on whatever Crab is of interest.
    """
    def __init__(self, crab: 'Crab'):
        self.crab: 'Crab' = crab

    def __repr__(self):
        return f'<Bio @{self.crab.username} [{self.crab.id}]>'

    @property
    def _json(self) -> dict:
        return self.crab._json.get('bio')

    @property
    def age(self) -> Optional[str]:
        return self._json.get('age')

    @property
    def description(self) -> Optional[str]:
        return self._json.get('description')

    @property
    def favorite_emoji(self) -> Optional[str]:
        return self._json.get('emoji')

    @property
    def jam(self) -> Optional[str]:
        return self._json.get('jam')

    @property
    def location(self) -> Optional[str]:
        return self._json.get('location')

    @property
    def obsession(self) -> Optional[str]:
        return self._json.get('obsession')

    @property
    def pronouns(self) -> Optional[str]:
        return self._json.get('pronouns')

    @property
    def quote(self) -> Optional[str]:
        return self._json.get('quote')

    @property
    def remember_when(self) -> Optional[str]:
        return self._json.get('remember')

    def update(self, age: Optional[str] = None,
               description: Optional[str] = None,
               favorite_emoji: Optional[str] = None, jam: Optional[str] = None,
               location: Optional[str] = None, obsession: Optional[str] = None,
               pronouns: Optional[str] = None, quote: Optional[str] = None,
               remember_when: Optional[str] = None) -> bool:
        """ Updates the bio of the parent Crab.
        """
        new_bio = dict(age=age, description=description, emoji=favorite_emoji,
                       jam=jam, location=location, obsession=obsession,
                       pronouns=pronouns, quote=quote, remember=remember_when)
        r = self.crab.api._make_request(f'/crabs/{self.crab.id}/bio/', 'POST',
                                        data=new_bio)
        if r.ok:
            self.crab._json = r.json()
        return r.ok


class Crab:
    """ Represents a Crabber user.

        .. warning::
            Do not directly instantiate this class. You can access it through
            various methods of `API`.
    """
    def __init__(self, json: dict, api: 'API'):
        self.api: 'API' = api
        self._bio: Optional[Bio] = None
        self._json: dict = json
        if not self._json:
            raise ValueError('Cannot construct Crab from empty JSON.')

    def __repr__(self):
        return f'<Crab @{self.username} [{self.id}]>'

    @property
    def avatar(self) -> str:
        """ The URL of this Crab's avatar image.
        """
        return self.api.base_url + self._json['avatar']

    @property
    def bio(self) -> Bio:
        """ This Crab's bio object.
        """
        if self._bio is None:
            # Retrieve bio if not cached
            if self._json.get('bio') is None:
                r = self.api._make_request(f'/crabs/{self.id}/bio/')
                if r.ok:
                    self._json = r.json()
            self._bio = Bio(crab=self)
        return self._bio

    @property
    def display_name(self) -> str:
        """ This Crab's display name. Display names don't have to be unique and
            can include spaces, emoji, and really any Unicode characters.
        """
        return self._json['display_name']

    @property
    def bookmarks(self) -> List['Molt']:
        """ Returns a list all Molts this Crab has bookmarked in descending
            order of the time at which they were bookmarked.
        """
        bookmarks_json = self.api._get_paginated_data(
            f'/crabs/{self.id}/bookmarks/',
            'molts'
        )
        return [self.api._objectify(bookmark_json, 'molt')
                for bookmark_json in bookmarks_json]

    @property
    def followers(self) -> List['Crab']:
        """ Returns a list of all of this Crab's followers.
        """
        followers_json = self.api._get_paginated_data(
            f'/crabs/{self.id}/followers/',
            'crabs'
        )
        return [self.api._objectify(crab_json, 'crab')
                for crab_json in followers_json]

    @property
    def follower_count(self) -> int:
        """ The number of followers this Crab currently has.
        """
        return self._json['followers']

    @property
    def following(self) -> List['Crab']:
        """ Returns a list of all the Crabs this Crab currently follows.
        """
        following_json = self.api._get_paginated_data(
            f'/crabs/{self.id}/following/',
            'crabs'
        )
        return [self.api._objectify(crab_json, 'crab')
                for crab_json in following_json]

    @property
    def following_count(self) -> int:
        """ The number of Crabs this Crab currently follows.
        """
        return self._json['following']

    @property
    def id(self) -> int:
        """ This Crab's ID.
        """
        return self._json['id']

    @property
    def is_verified(self) -> bool:
        """ Whether this Crab is a verified user.

            Some accounts are verified when they have been confirmed to
            represent a person of interest who others may realistically attempt
            to impersonate.
        """
        return self._json['verified']

    @property
    def username(self) -> str:
        """ This Crab's username.
        """
        return self._json['username']

    @property
    def register_time(self) -> datetime:
        """ The time at which this Crab was registered on Crabber.
        """
        return datetime.fromtimestamp(self.timestamp)

    @property
    def timestamp(self) -> int:
        """ The same as `Crab.register_time` except returned as a UTC timestamp
            instead of a datetime object.
        """
        return self._json['register_time']

    def follow(self) -> bool:
        """ Follow this Crab as the authenticated user.

            :returns: Whether the operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/crabs/{self.id}/follow/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def unfollow(self) -> bool:
        """ Unfollow this Crab as the authenticated user.

            :returns: Whether the operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/crabs/{self.id}/unfollow/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def get_mentions(self, limit: int = 10, offset: int = 0,
                     since_ts: Optional[int] = None,
                     since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts that mention this Crab.

            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.
        """
        return self.api.get_molts_mentioning(self.username, limit=limit,
                                             offset=offset, since_ts=since_ts,
                                             since_id=since_id)

    def get_replies(self, limit: int = 10, offset: int = 0,
                    since_ts: Optional[int] = None,
                    since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts that reply to any of this Crab's Molts.

            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.
        """
        return self.api.get_molts_replying_to(self.username, limit=limit,
                                              offset=offset, since_ts=since_ts,
                                              since_id=since_id)

    def get_molts(self, limit: int = 10, offset: int = 0,
                  since_ts: Optional[int] = None,
                  since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts posted by this Crab.

            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.
        """
        r = self.api._make_request(f'/crabs/{self.id}/molts/',
                                   params={'limit': limit, 'offset': offset,
                                           'since': since_ts,
                                           'since_id': since_id})
        return [self.api._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]


class Molt:
    """ Represents a Crabber post.

        .. warning::
            Do not directly instantiate this class. You can access it through
            various methods of `API`, `Crab`, and `Molt`.
    """
    def __init__(self, json: dict, api: 'API'):
        self.api: 'API' = api
        self._json: dict = json
        if not self._json:
            raise ValueError('Cannot construct Molt from empty JSON.')
        self.deleted: bool = False

    def __repr__(self):
        return f'<Molt [{self.id}]>'

    @property
    def author(self) -> Crab:
        """ The Crab who posted this Molt.
        """
        return self.api.get_crab(self._json['author']['id'])

    @property
    def content(self) -> str:
        """ The text content of this Molt.
        """
        return self._json['content']

    @property
    def crabtags(self) -> List[str]:
        """ List of the crabtags used in this Molt.
        """
        return self._json['crabtags']

    @property
    def datetime(self) -> datetime:
        """ The time at which this Molt was posted.
        """
        return datetime.fromtimestamp(self.timestamp)

    @property
    def editable(self) -> bool:
        """ Whether this Molt is currently editable.

            Molts are editable for the first five minutes after they are
            posted. Any requests to edit received by the server after that
            point will be rejected.
        """
        return ((datetime.now() - self.datetime).seconds / 60) < 5

    @property
    def edited(self) -> bool:
        """ Whether this Molt has been edited.
        """
        return self._json['edited']

    @property
    def id(self) -> int:
        """ This Molt's ID.
        """
        return self._json['id']

    @property
    def is_quote(self) -> int:
        """ Whether this Molt is quoting another Molt.
        """
        return self._json['quoted_molt'] is not None

    @property
    def is_reply(self) -> int:
        """ Whether this Molt is replying to another Molt.
        """
        return self._json['replying_to'] is not None

    @property
    def image(self) -> Optional[str]:
        """ The URL of the image contained in this Molt if it exists.
        """
        if self._json['image']:
            return self.api.base_url + self._json['image']

    @property
    def likes(self) -> int:
        """ The number of likes this Molt has.
        """
        return self._json['likes']

    @property
    def mentions(self) -> List[str]:
        """ List of the usernames mentioned in this Molt.
        """
        return self._json['mentions']

    @property
    def quotes(self) -> int:
        """ Number of Molts that quote this Molt.
        """
        return self._json['quotes']

    @property
    def remolts(self) -> int:
        """ Number of Remolts this Molt has.
        """
        return self._json['remolts']

    @property
    def quoted_molt(self) -> Optional['Molt']:
        """ The Molt that this Molt is quoting if this Molt is quoting one.
        """
        original_molt_id = self._json['quoted_molt']
        if original_molt_id:
            return self.api.get_molt(original_molt_id)

    @property
    def replying_to(self) -> Optional['Molt']:
        """ The Molt that this Molt is replying to if this Molt is a reply.
        """
        original_molt_id = self._json['replying_to']
        if original_molt_id:
            return self.api.get_molt(original_molt_id)

    @property
    def timestamp(self) -> int:
        """ The same as `Molt.datetime` except returned as a UTC timestamp
            instead of a datetime object.
        """
        return self._json['timestamp']

    def get_replies(self, limit: int = 10, offset: int = 0,
                    since_ts: Optional[int] = None,
                    since_id: Optional[int] = None) -> List['Molt']:
        """ Get all valid Molts that reply to this Molt.

            :param limit: Maximum number of results to return, defaults to 10.
                Max: 50.
            :param offset: How many Molts to skip before applying the limit,
                defaults to 0.
            :param since_ts: Only return Molts that were posted after this
                timestamp (UTC).
            :param since_id: Only return Molts whose ID is greater than this.
            :returns: List of Molts found.
        """
        r = self.api._make_request(f'/molts/{self.id}/replies/',
                                   params={'limit': limit, 'offset': offset,
                                           'since': since_ts,
                                           'since_id': since_id})
        return [self.api._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]

    def bookmark(self) -> bool:
        """ Bookmark this Molt as the authenticated user.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/bookmark/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def unbookmark(self) -> bool:
        """ Unbookmark this Molt as the authenticated user.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/unbookmark/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def like(self) -> bool:
        """ Like this Molt as the authenticated user.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/like/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def unlike(self) -> bool:
        """ Unlike this Molt as the authenticated user.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/unlike/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def delete(self) -> bool:
        """ Delete this Molt if the authenticated user is the author.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/',
                                       method='DELETE')
            if r.ok:
                self.deleted = True
                self.api._molts[self.id] = None
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def remolt(self) -> bool:
        """ Remolt this Molt if the authenticated user is the author.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/remolt/',
                                       method='POST')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def unremolt(self) -> bool:
        """ Unremolt this Molt if the authenticated user is the author.

            :returns: Whether this operation was successful.
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/remolt/',
                                       method='DELETE')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def edit(self, content: Optional[str] = None,
             image_path: Optional[str] = None) -> Optional[bool]:
        """ Edit this Molt as the authenticated user.

            :param content: The text content to replace the current content
                with.
            :param image_path: The path to a valid image file that will be
                uploaded and replace the current image.
            :returns: Whether this operation was successful.
        """
        if not (content or image_path):
            raise TypeError('edit() requires at least one argument '
                            '\'content\' or \'image_path\'')
        if len(content or '') <= MOLT_CHARACTER_LIMIT:
            if self.api.access_token:
                if image_path:
                    if not os.path.exists(image_path):
                        raise FileNotFoundError('The image path provided does '
                                                'not point to a valid file.')
                    with open(image_path, 'rb') as image_file:
                        r = self.api._make_request(f'/molts/{self.id}/edit/',
                                                   method='POST',
                                                   data={'content': content},
                                                   image=image_file)
                else:
                    r = self.api._make_request(f'/molts/{self.id}/edit/',
                                               method='POST',
                                               data={'content': content})
                if r.ok:
                    # Update self to new content
                    self._json = r.json()
                    return True
                else:
                    return None
            else:
                raise RequiresAuthenticationError(
                    'You are not properly authenticated for this request.'
                )
        else:
            raise ValueError(f'Molts cannot exceed {MOLT_CHARACTER_LIMIT} '
                             'characters.')

    def quote(self, content: str, image_path: Optional[str] = None) \
            -> Optional['Molt']:
        """ Post a new Molt that quotes this one as the authenticated user.

            :param content: The text content of the Molt to post.
            :param image_path: The path to a valid image file that will be
                uploaded and included in this Molt.
            :returns: The posted Molt if successful.
        """
        if len(content) <= MOLT_CHARACTER_LIMIT:
            if self.api.access_token:
                if image_path:
                    if not os.path.exists(image_path):
                        raise FileNotFoundError('The image path provided does '
                                                'not point to a valid file.')
                    with open(image_path, 'rb') as image_file:
                        r = self.api._make_request(f'/molts/{self.id}/quote/',
                                                   method='POST',
                                                   data={'content': content},
                                                   image=image_file)
                else:
                    r = self.api._make_request(f'/molts/{self.id}/quote/',
                                               method='POST',
                                               data={'content': content})
                if r.ok:
                    return self.api._objectify(r.json(), 'molt')
                else:
                    return None
            else:
                raise RequiresAuthenticationError(
                    'You are not properly authenticated for this request.'
                )
        else:
            raise ValueError(f'Molts cannot exceed {MOLT_CHARACTER_LIMIT} '
                             'characters.')

    def reply(self, content: str, image_path: Optional[str] = None) \
            -> Optional['Molt']:
        """ Post a new Molt that replies to this one as the authenticated user.

            :param content: The text content of the Molt to post.
            :param image_path: The path to a valid image file that will be
                uploaded and included in this Molt.
            :returns: The posted Molt if successful.
        """
        if len(content) <= MOLT_CHARACTER_LIMIT:
            if self.api.access_token:
                if image_path:
                    if not os.path.exists(image_path):
                        raise FileNotFoundError('The image path provided does '
                                                'not point to a valid file.')
                    with open(image_path, 'rb') as image_file:
                        r = self.api._make_request(f'/molts/{self.id}/reply/',
                                                   method='POST',
                                                   data={'content': content},
                                                   image=image_file)
                else:
                    r = self.api._make_request(f'/molts/{self.id}/reply/',
                                               method='POST',
                                               data={'content': content})
                if r.ok:
                    return self.api._objectify(r.json(), 'molt')
                else:
                    return None
            else:
                raise RequiresAuthenticationError(
                    'You are not properly authenticated for this request.'
                )
        else:
            raise ValueError(f'Molts cannot exceed {MOLT_CHARACTER_LIMIT} '
                             'characters.')

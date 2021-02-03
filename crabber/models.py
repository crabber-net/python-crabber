from datetime import datetime
from .exceptions import MaxTriesError, RequiresAuthenticationError
import os
import requests
from typing import Any, BinaryIO, Dict, List, Optional, Union


class API:
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

        self._check_connection()
        if access_token:
            self.authenticate(access_token)

    def authenticate(self, access_token: str) -> bool:
        self.access_token = access_token
        r = self._make_request('/authenticate/')
        self.crab = self._objectify(r.json(), 'crab')
        return r.ok

    def get_current_user(self) -> 'Crab':
        """ Get the current authenticated user.
        """
        return self.crab

    def get_crab(self, crab_id: int) -> Optional['Crab']:
        """ Get a Crab by its ID.
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
        """ Get molts that contain the crabtag `crabtag`.
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
        """ Get Molts that explicitly mention `username`.
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
        """ Get Molts that reply to Molts submitted by `username`.
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
        """
        if len(content) <= 240:
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
            raise ValueError('Molts cannot exceed 240 characters.')

    def _check_connection(self) -> bool:
        r = self._make_request()
        if r.ok:
            return True
        else:
            raise ConnectionError('Site responded incorrectly. '
                                  'Is your base_url accurate?')

    def _get_paginated_data(self, endpoint: str, data_key: str,
                            limit: int = 10, starting_offset: int = 0) \
            -> Dict[str, Any]:
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
        new_bio = dict(age=age, description=description, emoji=favorite_emoji,
                       jam=jam, location=location, obsession=obsession,
                       pronouns=pronouns, quote=quote, remember=remember_when)
        r = self.crab.api._make_request(f'/crabs/{self.crab.id}/bio/', 'POST',
                                        data=new_bio)
        if r.ok:
            self.crab._json = r.json()
        return r.ok


class Crab:
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
        return self.api.base_url + self._json['avatar']

    @property
    def bio(self) -> Bio:
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
        return self._json['display_name']

    @property
    def followers(self) -> List['Crab']:
        followers_json = self.api._get_paginated_data(
            f'/crabs/{self.id}/followers/',
            'crabs'
        )
        return [self.api._objectify(crab_json, 'crab')
                for crab_json in followers_json]

    @property
    def follower_count(self) -> int:
        return self._json['followers']

    @property
    def following(self) -> List['Crab']:
        following_json = self.api._get_paginated_data(
            f'/crabs/{self.id}/following/',
            'crabs'
        )
        return [self.api._objectify(crab_json, 'crab')
                for crab_json in following_json]

    @property
    def following_count(self) -> int:
        return self._json['following']

    @property
    def id(self) -> int:
        return self._json['id']

    @property
    def is_verified(self) -> bool:
        return self._json['verified']

    @property
    def username(self) -> str:
        return self._json['username']

    @property
    def register_time(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

    @property
    def timestamp(self) -> int:
        return self._json['register_time']

    def follow(self) -> bool:
        """ Follow this Crab as the authenticated user.
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
        """ Get Molts that mention this user.
        """
        return self.api.get_molts_mentioning(self.username, limit=limit,
                                             offset=offset, since_ts=since_ts,
                                             since_id=since_id)

    def get_replies(self, limit: int = 10, offset: int = 0,
                    since_ts: Optional[int] = None,
                    since_id: Optional[int] = None) -> List['Molt']:
        """ Get Molts that reply to any of this user's Molts.
        """
        return self.api.get_molts_replying_to(self.username, limit=limit,
                                              offset=offset, since_ts=since_ts,
                                              since_id=since_id)

    def get_molts(self, limit: int = 10, offset: int = 0,
                  since_ts: Optional[int] = None,
                  since_id: Optional[int] = None) -> List['Molt']:
        """ Get this user's Molts.
        """
        r = self.api._make_request(f'/crabs/{self.id}/molts/',
                                   params={'limit': limit, 'offset': offset,
                                           'since': since_ts,
                                           'since_id': since_id})
        return [self.api._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]


class Molt:
    def __init__(self, json: dict, api: 'API'):
        self.api: 'API' = api
        self._json: dict = json
        if not self._json:
            raise ValueError('Cannot construct Molt from empty JSON.')

    def __repr__(self):
        return f'<Molt [{self.id}]>'

    @property
    def author(self) -> Crab:
        return self.api.get_crab(self._json['author']['id'])

    @property
    def content(self) -> str:
        return self._json['content']

    @property
    def crabtags(self) -> List[str]:
        return self._json['crabtags']

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

    @property
    def id(self) -> int:
        return self._json['id']

    @property
    def is_reply(self) -> int:
        return self._json['replying_to'] is not None

    @property
    def image(self) -> Optional[str]:
        if self._json['image']:
            return self.api.base_url + self._json['image']

    @property
    def likes(self) -> int:
        return self._json['likes']

    @property
    def mentions(self) -> List[str]:
        return self._json['mentions']

    @property
    def remolts(self) -> int:
        return self._json['remolts']

    @property
    def replying_to(self) -> Optional['Molt']:
        original_molt_id = self._json['replying_to']
        if original_molt_id:
            return self.api.get_molt(original_molt_id)

    @property
    def timestamp(self) -> int:
        return self._json['timestamp']

    def get_replies(self, limit: int = 10, offset: int = 0,
                    since_ts: Optional[int] = None,
                    since_id: Optional[int] = None) -> List['Molt']:
        """ Get this Molt's replies.
        """
        r = self.api._make_request(f'/molts/{self.id}/replies/',
                                   params={'limit': limit, 'offset': offset,
                                           'since': since_ts,
                                           'since_id': since_id})
        return [self.api._objectify(molt, 'molt')
                for molt in r.json().get('molts', list())]

    def like(self) -> bool:
        """ Like this Molt as the authenticated user.
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
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/',
                                       method='DELETE')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def remolt(self) -> bool:
        """ Remolt this Molt if the authenticated user is the author.
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
        """
        if self.api.access_token:
            r = self.api._make_request(f'/molts/{self.id}/remolt/',
                                       method='DELETE')
            return r.ok
        raise RequiresAuthenticationError(
            'You are not properly authenticated for this request.'
        )

    def reply(self, content: str, image_path: Optional[str] = None) \
            -> Optional['Molt']:
        """ Reply to this Molt as the authenticated user.
        """
        if len(content) <= 240:
            if self.api.access_token:
                if image_path:
                    if not os.path.exists(image_path):
                        raise FileNotFoundError('The image path provided does '
                                                'not point to a valid file.')
                    with open(image_path, 'rb') as image_file:
                        r = self.api._make_request(f'/molts/{self.id}/reply/',
                                                   method='POST',
                                                   data={'content': content},
                                                   iamge=image_file)
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
            raise ValueError('Molts cannot exceed 240 characters.')

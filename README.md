# python-crabber

![PyPI version](https://img.shields.io/pypi/v/python-crabber)

A Python client for the Crabber.net REST API.

## Installation

``` bash
pip install python-crabber
```

## Usage

There is not currently any documentation for this project, but you should be
able to find your way around fairly easily. Use Python's `help()` function to
view the properties and methods included this module.

``` python3
>>> import crabber
>>> help(crabber.API)
```

Authentication is done with developer/api keys and access tokens. You can get
both of these at https://crabber.net/developer/. Only an API key is needed to
access Crabber's API. 

``` python3
>>> api = crabber.API(api_key=YOUR_DEVELOPER_KEY)
>>> jake = api.get_crab_by_username('jake')
>>> jake
<Crab @jake [1]>
>>> jake.display_name
'Jake L.'
```

If you want to make actions on a user's behalf you'll need to authenticate with
an access token. Access tokens are tied to specific accounts, so if you create
an access token while logged in as '@thedude' then all applications
authenticated with that access token will act as if they are logged in as
'@thedude'. **This is why it is imperative that access tokens are kept private 
and not shared with *anyone*.**

``` python3
>>> jake = api.get_crab_by_username('jake')
>>> jake.follow()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/jake/code/python-crabber/crabber/models.py", line 342, in follow
    raise RequiresAuthenticationError(
crabber.exceptions.RequiresAuthenticationError: You are not properly authenticated for this request.
>>> api.authenticate(YOUR_ACCESS_TOKEN)
>>> jake.follow()
True
>>> api.get_current_user() in jake.followers
True
>>> api.post_molt('Hello, world!')
<Molt [683]>
```

It is also possible to authenticate while intializing the API object rather than
afterwards.

``` python3
>>> api = crabber.API(api_key=YOUR_DEVELOPER_KEY, access_token=YOUR_ACCESS_TOKEN)
>>> api.get_current_user()
<Crab @thedude [85]>
```

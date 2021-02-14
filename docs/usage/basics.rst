Basics
=====

This module was written to be simple and enjoyable to use, and hopefully should
be rather intuitive.

Keys and Tokens
---------------


Developer keys
^^^^^^^^^^^^^^

In order to use the Crabber API you must at least have a developer key.
Developer keys are created on a per-user basis and allow Crabber to keep track
of which application is making which request and rate-limit accordingly. Each
user is currently allowed a maximum of 5 developer keys.

Access tokens
^^^^^^^^^^^^^^

While you don't need an access token to do things such as read Molts and access
user information, you'll need one in order to post or modify anything on the
site. An access token provides full access to its parent account through the API
and should **never** be shared with anyone.

.. warning::
   If you suspect you may have shared an access token accidentally, immediately
   go to Crabber and delete that token so no damage can be done by others.

Obtaining tokens/keys
---------------------

Both developer keys and access tokens can be created by users at
https://crabber.net/developer. Remember that access tokens grant access to the
account that created them, so make sure you're logged into your project's
account when generating tokens.

Using the module
----------------

Let's make a quick program that posts a Molt when run.

The first thing we'll have to do is create an instance of the Crabber API.

.. code-block:: python3

   from crabber import API

   api = API(YOUR_DEVELOPER_KEY, YOUR_ACCESS_TOKEN)
   api.post_molt('Hello, world!')

Nice! Now if you were to run that interactively you would notice that
:meth:`API.post_molt` returns a :class:`Molt` object. This object is the
Molt you've just posted, you can read the contents like this:

.. code-block:: python3

   molt = api.post_molt('Hello, world!')
   print(molt.contents)


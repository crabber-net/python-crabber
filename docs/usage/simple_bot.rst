Writing a Simple Bot
====================

First steps
-----------

In this example we'll write a simple bot that likes and replies to Molts that
mention it.

Since the Crabber API doesn't use webhooks we don't structure our bots as a
continuous loop that waits for input, instead we write it to handle whatever
exists at that moment and then terminate. This way we can schedule it to run at
regular intervals with crontab or similar tools.

.. code-block:: python3
   :caption: simple_bot.py

   from crabber import API

   api = API(YOUR_DEVELOPER_KEY, YOUR_ACCESS_TOKEN)
   this_user = api.get_current_user()

   for mention in this_user.get_mentions():
       mention.like()
       mention.reply('I like your style!')

Now if you mention your bot and then run this program, it will like your Molt
and reply with "I like your style!". Well done.

Remembering states
------------------

A problem emerges when you run it again
though, as it will once again check its mentions and reply to the same Molt it
already has! Let's solve this problem by keeping track of what we've replied to.

First, create a file called :file:`bot_status.json`. We'll move your token and
key into the file as well as add a section to store the ID of the last Molt
we've processed.

.. code-block:: json
   :caption: bot_status.json

   {
       "api_key": "YOUR_DEVELOPER_KEY",
       "access_token": "YOUR_ACCESS_TOKEN",
       "last_molt_id": 0
   }

Alright, now we'll update our bot to use this new file. Most of the Molt
retrieving methods including :meth:`~crabber.models.Crab.get_mentions()` support
a parameter called `since_id` which limits the results to Molts that have an ID
greater than the one provided. We'll use that here.

.. code-block:: python3
   :caption: simple_bot.py
   :emphasize-lines: 2, 4-6, 8, 11, 14, 16-18

   from crabber import API
   import json

   # Load status JSON
   with open('bot_status.json', 'r') as f:
       bot_status = json.load(f)

   api = API(bot_status['api_key'], bot_status['access_token'])
   this_user = api.get_current_user()

   for mention in this_user.get_mentions(since_id=bot_status['last_molt_id']):
       mention.like()
       mention.reply('I like your style!')
       bot_status['last_molt_id'] = mention.id

   # Write new status JSON
   with open('bot_status.json', 'w') as f:
       json.dump(bot_status, f)

Great! Now our bot only responds to each Molt once, no matter how many times you
run the program. An added bonus is the fact that you can now share your code
without giving away your developer key and access token since they're stored in
a separate file (Just remember not to share that file.)

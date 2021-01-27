import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

import crabber
import crabber.models
import crabber.utils
# Authentication belongs to @PyTest on Crabber
API_KEY = '7f94ebd306f12fe13e983fe0fb78b696'
ACCESS_TOKEN = '16c24b2e825acfb6af191d66c46e2369'

sample_error_html = [
    '''\
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>400 Bad Request</title>
    <h1>Bad Request</h1>
    <p>API key not provided.</p>
    ''',
    '''\
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>400 Bad Request</title>
    <h1>Bad Request</h1>
    <p>API key is invalid or expired.</p>
    ''',
    '''\
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <title>401 Unauthorized</title>
    <h1>Unauthorized</h1>
    <p>This endpoint requires authentication.</p>
    '''
]
sample_json = {
    'crab': {
        'avatar': '/static/img/user_uploads/942e158f-1fba-49b3-bd4f-' \
        '209a2483cc76.jpg',
        'display_name': 'Jake L.',
        'followers': 31,
        'following': 13,
        'id': 1,
        'register_time': 1586534552,
        'username': 'jake',
        'verified': True
    },
    'bio': {
        'age': '21',
        'description': 'I made this site.',
        'emoji': '\ud83d\udda4',
        'jam': 'grant - constellations \ud83c\udf20',
        'location': 'Vermont, United States \ud83c\udf41',
        'obsession': 'SQLAlchemy',
        'pronouns': 'he/him',
        'quote': '~ a crab in the hand is worth two in the shell ~',
        'remember': 'heelys were cool?'
    }
}


import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
))

import crabber
import crabber.models
# Authentication belongs to @PyTest on Crabber
API_KEY = '7f94ebd306f12fe13e983fe0fb78b696'
ACCESS_TOKEN = '16c24b2e825acfb6af191d66c46e2369'
TEACHER_IMAGE = os.path.abspath(os.path.join('tests', 'teacher.jpg'))
assert os.path.exists(TEACHER_IMAGE)

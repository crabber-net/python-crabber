import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import crabber
API_KEY = os.environ.get('CRABBER_API_KEY')

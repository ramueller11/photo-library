"""
    config.py
    Configuration data
"""

import os 

MYPATH         = os.path.dirname( os.path.realpath(__file__) )
DB_PATH        = os.path.join(MYPATH, 'photo_db.sqlite')
INDEX_BASENAME_REGEX = '^[.]pic_index[.]json$'
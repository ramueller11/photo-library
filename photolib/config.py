"""
    config.py
    Configuration data
"""

import os 

IMAGE_MAGICK_BIN = 'E:\\path\\to\\Cygwin\\home\\rob\\bin.win\\ImageMagick\\magick.exe'

MYPATH         = os.path.dirname( os.path.realpath(__file__) )
DB_PATH        = os.path.join(MYPATH, 'photo_db.sqlite')
INDEX_BASENAME_REGEX = '^[.]pic_index[.]json$'
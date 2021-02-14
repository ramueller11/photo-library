from wzapp import WebApp, HTTPResponse as Response
from photolib import db

# establish the application
app = WebApp()
app.name    = 'Photo Library'
app.version = '0.0.1'

from . import www
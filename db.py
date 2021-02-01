from sqlalchemy import types as _dt, Column, ForeignKey, create_engine as _create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker as _sessionmaker
from sqlalchemy.ext.declarative import declarative_base as _decl_base
from . import config as _config

ModelBase = _decl_base()

# here we set which datatypes we want to encode in
class DataTypes():
    DateTime = _dt.DateTime
    Integer  = _dt.Integer
    Float    = _dt.Float
    Text     = _dt.Text
    Blob     = _dt.LargeBinary
    Bool     = _dt.Boolean

_engine = None; _session = None

# ----------------------------

def connect(path=_config.DB_PATH):
    global _engine, _session

    if _engine != None: return _engine

    _engine  = _create_engine('sqlite:///%s' % path)
    _session = _sessionmaker()
    _session.configure(bind=_engine)

    return _engine

def get_engine():
    global _engine
    return _engine

def get_table_names():
    global _engine, _session
    if _engine == None: return []

    return _engine.table_names()

# -----------------------------

def new_session():
    global _session
    return _session()

# ---------------------------

def close():
    global _engine

    if _engine == None: return
    _engine.dispose()
    _engine = None

# ----------------------------

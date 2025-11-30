import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from config import Config
from .base_model import BaseModel
from .user import User
from .registration_code import RegistrationCode
from .note import Note

DB_URL = os.environ.get("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)

#SQL logging on/off without changing code, just by setting an env var.
#windows =>  $env:SQL_ECHO = "true" / "false"

DEBUG_SQL = os.environ.get("SQL_ECHO", "false").lower() == "true"

engine: Engine = create_engine(
    DB_URL,
    echo=DEBUG_SQL,
)

BaseModel.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)

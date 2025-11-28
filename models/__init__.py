import os
from os import path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from .base_model import BaseModel
from .user import User
from .registration_code import RegistrationCode
from .note import Note
from config import Config

DB_URL = os.environ.get("DATABASE_URL", Config.SQLALCHEMY_DATABASE_URI)

SQL_ECHO = os.environ.get("SQL_ECHO", "false").lower() == "true"

engine: Engine = create_engine(DB_URL, echo=SQL_ECHO)

BaseModel.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)

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

engine: Engine = create_engine(
    DB_URL,
    echo=True,
)

BaseModel.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
 
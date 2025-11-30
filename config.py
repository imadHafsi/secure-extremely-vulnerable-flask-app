import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # In production, SECRET_KEY **must** be set via environment.
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")

    # To change the database, set the DATABASE_URL environment variable.
    # example $env:DATABASE_URL = "sqlite:///D:/full/path/to/your_database_name.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'database.db'}",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

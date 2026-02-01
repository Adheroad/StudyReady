"""FastAPI dependency injection utilities."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.connection import get_db

# Session dependency
SessionDep = Annotated[Session, Depends(get_db)]

# Settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]

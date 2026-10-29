"""Small validated configuration, without a settings framework."""
from datetime import time
import os
from pathlib import Path
import re
from pydantic import BaseModel, field_validator
from pipeline.fetch import ROOT


def parse_cutoff(value: str) -> time:
    if not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', value):
        raise ValueError('cutoff_local must be HH:MM (00:00–23:59), Europe/London')
    return time.fromisoformat(value)


class Settings(BaseModel):
    data_root: Path = ROOT
    cutoff_local: str = '09:20'
    static_dir: Path | None = None

    @field_validator('cutoff_local')
    @classmethod
    def valid_cutoff(cls, value: str) -> str:
        parse_cutoff(value)
        return value

    @classmethod
    def from_env(cls):
        return cls(data_root=os.getenv('WIND_DATA_ROOT', str(ROOT)),
                   cutoff_local=os.getenv('WIND_DECISION_CUTOFF', '09:20'),
                   static_dir=os.getenv('WIND_STATIC_DIR') or None)

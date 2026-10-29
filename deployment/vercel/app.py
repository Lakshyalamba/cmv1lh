"""Vercel-only entry point; the Docker backend and calculations are unchanged."""
import os
from pathlib import Path
from backend.config import Settings
from backend.main import create_app

bundle_root = Path(__file__).resolve().parent
app = create_app(Settings(data_root=bundle_root, static_dir=bundle_root / 'static',
                          cutoff_local=os.getenv('WIND_DECISION_CUTOFF', '09:20')))

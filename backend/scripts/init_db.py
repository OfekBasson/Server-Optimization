"""Create all tables.

Run once against a fresh database (`python scripts/init_db.py`). Real
schema changes later should go through Alembic migrations instead of this
script.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app import models  # noqa: F401  (registers models with Base.metadata)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

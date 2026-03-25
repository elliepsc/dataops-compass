"""
Initialize the PostgreSQL database.
Run once before starting the app:
  python db_prep.py
"""

import db

if __name__ == "__main__":
    print("Initializing database...")
    db.init_db()
    print("Done.")

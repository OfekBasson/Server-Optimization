"""Create (or promote) the first admin user - needed once, since the
admin API itself requires an existing admin to call it.

Usage:
    python scripts/seed_admin.py "Ofek Basson" ofek.basson@post.runi.ac.il
    (prompts for a password interactively - or pass it as a 3rd argument
    for non-interactive use, e.g. `docker compose exec`)
"""

import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print('Usage: python scripts/seed_admin.py "Full Name" email@example.com [password]')
        raise SystemExit(1)

    name, email = sys.argv[1], sys.argv[2]
    password = sys.argv[3] if len(sys.argv) == 4 else getpass.getpass("Admin password: ")
    if not password:
        print("A password is required.")
        raise SystemExit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.university_email == email).first()
        if user:
            user.is_admin = True
            user.password_hash = hash_password(password)
            print(f"Promoted existing user '{user.name}' ({email}) to admin and set their password.")
        else:
            user = User(name=name, university_email=email, is_admin=True, password_hash=hash_password(password))
            db.add(user)
            print(f"Created admin user '{name}' ({email}).")
        db.commit()
    finally:
        db.close()

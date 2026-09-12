"""Create (or promote) the first admin user - needed once, since the
admin API itself requires an existing admin to call it.

Usage:
    python scripts/seed_admin.py "Ofek Basson" ofek.basson@post.runi.ac.il
"""

import sys

from app.database import SessionLocal
from app.models import User

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python scripts/seed_admin.py "Full Name" email@example.com')
        raise SystemExit(1)

    name, email = sys.argv[1], sys.argv[2]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.university_email == email).first()
        if user:
            user.is_admin = True
            print(f"Promoted existing user '{user.name}' ({email}) to admin.")
        else:
            user = User(name=name, university_email=email, is_admin=True)
            db.add(user)
            print(f"Created admin user '{name}' ({email}).")
        db.commit()
    finally:
        db.close()

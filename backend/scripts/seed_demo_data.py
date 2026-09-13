"""Populate a couple of demo users and reservations, purely so a local
inspection run has something to look at. Run after seed_servers.py.

Safe to re-run - it just adds another round of demo data each time.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Reservation, ReservationStatus, Server, User

if __name__ == "__main__":
    db = SessionLocal()
    try:
        alice = db.query(User).filter(User.university_email == "alice@post.runi.ac.il").first()
        if not alice:
            alice = User(name="Alice Chen", university_email="alice@post.runi.ac.il", whatsapp_number="+15550001111")
            db.add(alice)

        bob = db.query(User).filter(User.university_email == "bob@post.runi.ac.il").first()
        if not bob:
            bob = User(name="Bob Diaz", university_email="bob@post.runi.ac.il", whatsapp_number="+15550002222")
            db.add(bob)
        db.commit()
        db.refresh(alice)
        db.refresh(bob)

        mass01 = db.query(Server).filter(Server.name == "mass-01").first()
        mass05 = db.query(Server).filter(Server.name == "mass-05").first()
        if not mass01 or not mass05:
            print("Run scripts/seed_servers.py first.")
            raise SystemExit(1)

        now = datetime.now(timezone.utc)
        db.add(
            Reservation(
                server_id=mass01.id,
                user_id=alice.id,
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=3),
                purpose="Training run - ResNet baseline",
                status=ReservationStatus.active,
            )
        )
        db.add(
            Reservation(
                server_id=mass05.id,
                user_id=bob.id,
                start_time=now + timedelta(hours=5),
                end_time=now + timedelta(hours=8),
                purpose="Fine-tuning experiment",
                status=ReservationStatus.active,
            )
        )
        db.commit()
        print(f"Seeded demo users (alice id={alice.id}, bob id={bob.id}) and 2 reservations.")
    finally:
        db.close()

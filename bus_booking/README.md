
# 🚌 Bus Ticket Booking — Flask + Docker

A minimal bus ticket booking web app with search, seat availability, and booking — built with Flask, SQLite, and Docker.

## Features
- Search buses by source, destination, and date
- See seat availability (computed from bookings)
- Book multiple seats; simple confirmation page
- Admin page to add routes
- SQLite database auto-created
- Dockerfile and docker-compose included

## Quick Start (Docker)
```bash
docker build -t bus-booking .
docker run -p 5000:5000 bus-booking
# Visit http://localhost:5000
```

Or with Compose:
```bash
docker compose up --build
# Visit http://localhost:5000
```

Optionally seed sample routes (in another shell):
```bash
docker exec -it $(docker ps -qf "ancestor=bus-booking") flask seed
```

## Local Dev (no Docker)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app.py run
```

## Notes
- Default SQLite path: `instance/bus_booking.db` (inside container it's in `/app/bus_booking.db`). Data persists while the container or volume lasts.
- Change `SECRET_KEY` in `app.py` for production.
- This is a demo app (no auth, no payments).


from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, date, time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bus_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class BusRoute(db.Model):
    __tablename__ = 'bus_routes'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(80), nullable=False)
    destination = db.Column(db.String(80), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    departure_time = db.Column(db.Time, nullable=False)
    arrival_time = db.Column(db.Time, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False, default=40)
    bus_name = db.Column(db.String(100), nullable=False, default="Express Bus")

    def available_seats(self):
        booked = db.session.query(func.coalesce(func.sum(Booking.seats), 0)).filter(Booking.route_id == self.id).scalar()
        return max(self.total_seats - (booked or 0), 0)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('bus_routes.id'), nullable=False)
    passenger_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    route = db.relationship('BusRoute', backref=db.backref('bookings', lazy=True))
    # Initialize DB tables once at startup
with app.app_context():
    db.create_all()


@app.cli.command('seed')
def seed():
    """Seed database with sample bus routes"""
    today = date.today()
    sample = [
        dict(source='Bengaluru', destination='Chennai', travel_date=today, departure_time=time(8,30), arrival_time=time(14,0), price=699.0, total_seats=40, bus_name='Kaveri Express'),
        dict(source='Bengaluru', destination='Hyderabad', travel_date=today, departure_time=time(21,0), arrival_time=time(6,0), price=999.0, total_seats=42, bus_name='Night Rider'),
        dict(source='Mumbai', destination='Pune', travel_date=today, departure_time=time(7,0), arrival_time=time(9,30), price=299.0, total_seats=36, bus_name='Deccan Queen'),
        dict(source='Delhi', destination='Jaipur', travel_date=today, departure_time=time(6,15), arrival_time=time(11,0), price=549.0, total_seats=45, bus_name='Pink City Cruiser'),
    ]
    for s in sample:
        exists = BusRoute.query.filter_by(source=s['source'], destination=s['destination'], travel_date=s['travel_date'], departure_time=s['departure_time']).first()
        if not exists:
            db.session.add(BusRoute(**s))
    db.session.commit()
    print('Seeded sample routes.')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        date_str = request.form.get('date', '').strip()
        try:
            travel_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Please provide a valid travel date (YYYY-MM-DD).', 'error')
            return redirect(url_for('index'))

        q = BusRoute.query.filter(
            func.lower(BusRoute.source) == source.lower(),
            func.lower(BusRoute.destination) == destination.lower(),
            BusRoute.travel_date == travel_date
        ).order_by(BusRoute.departure_time.asc())
        routes = q.all()
        return render_template('search_results.html', routes=routes, source=source, destination=destination, travel_date=travel_date)

    # GET
    cities = [r[0] for r in db.session.query(BusRoute.source).distinct().all()] + [r[0] for r in db.session.query(BusRoute.destination).distinct().all()]
    cities = sorted(set(cities + ['Bengaluru','Chennai','Hyderabad','Mumbai','Pune','Delhi','Jaipur']))
    return render_template('index.html', cities=cities, today=date.today())

@app.route('/route/<int:route_id>')
def route_details(route_id):
    route = BusRoute.query.get_or_404(route_id)
    return render_template('route_details.html', route=route)

@app.route('/book/<int:route_id>', methods=['POST'])
def book(route_id):
    route = BusRoute.query.get_or_404(route_id)
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    seats = int(request.form.get('seats', 1))

    if not name or not email:
        flash('Name and email are required.', 'error')
        return redirect(url_for('route_details', route_id=route_id))

    if seats < 1:
        flash('Seats must be at least 1.', 'error')
        return redirect(url_for('route_details', route_id=route_id))

    if seats > route.available_seats():
        flash('Not enough seats available.', 'error')
        return redirect(url_for('route_details', route_id=route_id))

    booking = Booking(route_id=route.id, passenger_name=name, email=email, seats=seats)
    db.session.add(booking)
    db.session.commit()
    return render_template('success.html', booking=booking)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        date_str = request.form.get('date', '').strip()
        dep_str = request.form.get('departure', '').strip()
        arr_str = request.form.get('arrival', '').strip()
        price = float(request.form.get('price', '0') or 0)
        total_seats = int(request.form.get('total_seats', '40') or 40)
        bus_name = request.form.get('bus_name', 'Express Bus').strip()

        try:
            travel_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            departure_time = datetime.strptime(dep_str, '%H:%M').time()
            arrival_time = datetime.strptime(arr_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date/time format.', 'error')
            return redirect(url_for('admin'))

        new_route = BusRoute(
            source=source, destination=destination, travel_date=travel_date,
            departure_time=departure_time, arrival_time=arrival_time,
            price=price, total_seats=total_seats, bus_name=bus_name
        )
        db.session.add(new_route)
        db.session.commit()
        flash('Route added!', 'success')
        return redirect(url_for('admin'))

    routes = BusRoute.query.order_by(BusRoute.travel_date.asc(), BusRoute.departure_time.asc()).all()
    return render_template('admin.html', routes=routes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import os
import json
import math
import requests
from datetime import datetime, timezone, date as date_type
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# FIX: Secret key from environment variable (never hardcode)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key-change-in-production')

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# FIX: File upload validation
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

# Association table for User and Event (Many-to-Many)
attendance = db.Table('attendance',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    # FIX: Store hashed password, not plaintext
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(254), nullable=True, unique=True)
    is_organizer = db.Column(db.Boolean, default=False)
    attended_events = db.relationship('Event', secondary=attendance,
                                      lazy='subquery',
                                      backref=db.backref('attendees', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    # FIX: Use db.Date instead of String for proper date handling
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    detailed_description = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(200), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organizer = db.relationship('User', backref=db.backref('organized_events', lazy=True))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

with app.app_context():
    db.create_all()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometres
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def geocode_location(location_str):
    """
    Try multiple free geocoding strategies in order:
    1. Nominatim (OpenStreetMap) — good for cities, addresses
    2. Photon (Komoot) — better for POI / business names
    Returns (lat, lon) or (None, None).
    """
    headers = {'User-Agent': 'CommunityEventHub/1.0'}

    # --- Strategy 1: Nominatim ---
    try:
        params = {'q': location_str, 'format': 'json', 'limit': 1, 'addressdetails': 1}
        r = requests.get('https://nominatim.openstreetmap.org/search',
                         params=params, headers=headers, timeout=8)
        r.raise_for_status()
        results = r.json()
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
    except Exception:
        pass

    # --- Strategy 2: Photon (Komoot) — handles business/POI names better ---
    try:
        params = {'q': location_str, 'limit': 1}
        r = requests.get('https://photon.komoot.io/api/', params=params,
                         headers=headers, timeout=8)
        r.raise_for_status()
        features = r.json().get('features', [])
        if features:
            coords = features[0]['geometry']['coordinates']
            return float(coords[1]), float(coords[0])   # GeoJSON is [lon, lat]
    except Exception:
        pass

    return None, None


def geocode_for_filter(location_str):
    """Same geocoding but returns a (lat, lon) tuple or raises an exception."""
    lat, lon = geocode_location(location_str)
    if lat is None:
        raise ValueError(f"Could not geocode: {location_str}")
    return lat, lon

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        # FIX: Use check_password (hash comparison), not plaintext comparison
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_organizer'] = user.is_organizer
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '').strip() or None
        password = request.form['password']
        is_organizer = 'organizer' in request.form
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'warning')
        elif email and User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'warning')
        else:
            # FIX: Hash the password before storing
            user = User(username=username, email=email, is_organizer=is_organizer)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    # FIX: Use db.session.get() consistently (not deprecated Query.get)
    user = db.session.get(User, session['user_id'])
    attending_events = user.attended_events
    my_events_with_attendees = []
    if user.is_organizer:
        my_events_with_attendees = Event.query.filter_by(organizer_id=user.id).all()
    return render_template('profile.html',
                           username=session['username'],
                           is_organizer=session['is_organizer'],
                           email=user.email,
                           attending_events=attending_events,
                           my_events_with_attendees=my_events_with_attendees)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    attended_event_ids = {event.id for event in user.attended_events}

    location = request.args.get('location')
    date_filter = request.args.get('date')
    keyword = request.args.get('keyword')
    search = request.args.get('search', '').strip()
    distance_km = request.args.get('distance_km', type=int)

    query = Event.query

    # Hide past events using proper Date comparison
    today = date_type.today()
    query = query.filter(Event.date >= today)

    if location:
        query = query.filter(Event.location.ilike(f"%{location}%"))
    if date_filter:
        try:
            filter_date = date_type.fromisoformat(date_filter)
            query = query.filter(Event.date == filter_date)
        except ValueError:
            flash('Invalid date format in filter.', 'warning')
    if keyword:
        query = query.filter(Event.keywords.ilike(f"%{keyword}%"))
    if search:
        query = query.filter(Event.name.ilike(f"%{search}%"))

    PER_PAGE = 8
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Event.date).paginate(page=page, per_page=PER_PAGE, error_out=False)
    events = pagination.items

    if location and distance_km:
        try:
            user_lat, user_lon = geocode_for_filter(location)
            nearby_events = []
            for event in events:
                if event.latitude and event.longitude:
                    if haversine(user_lat, user_lon, event.latitude, event.longitude) <= distance_km:
                        nearby_events.append(event)
            events = nearby_events
        except ValueError:
            flash(f"Could not find coordinates for location: '{location}'. Try a broader location name.", "warning")
        except Exception as e:
            flash(f"An error occurred during distance filtering: {e}", "danger")

    events_for_map = []
    for event in events:
        if event.latitude and event.longitude:
            events_for_map.append({
                'id': event.id,
                'name': event.name,
                'location': event.location,
                'date': event.date.strftime('%d %b %Y'),
                'lat': event.latitude,
                'lon': event.longitude,
                'description': event.description,
                'keywords': event.keywords,
                'icon': url_for('static', filename=event.icon or 'images/default-event.jpg'),
                'attending': event.id in attended_event_ids,
            })

    return render_template('dashboard.html',
                           username=session['username'],
                           is_organizer=session['is_organizer'],
                           events=events,
                           attended_event_ids=attended_event_ids,
                           user_id=session['user_id'],
                           events_for_map=json.dumps(events_for_map),
                           pagination=pagination,
                           search=search)

@app.route('/attend/<int:event_id>', methods=['POST'])
def attend(event_id):
    if 'user_id' not in session:
        flash('You must be logged in to attend an event.', 'warning')
        return redirect(url_for('login'))
    event = db.session.get(Event, event_id)
    user = db.session.get(User, session['user_id'])
    if not event or not user:
        flash('Event or user not found.', 'danger')
        return redirect(url_for('dashboard'))
    if event in user.attended_events:
        flash('You are already attending this event.', 'info')
    else:
        user.attended_events.append(event)
        db.session.commit()
        flash(f'You are now attending {event.name}!', 'success')
    return redirect(url_for('dashboard'))

# FIX: Added unattend route so users can cancel their RSVP
@app.route('/unattend/<int:event_id>', methods=['POST'])
def unattend(event_id):
    if 'user_id' not in session:
        flash('You must be logged in.', 'warning')
        return redirect(url_for('login'))
    event = db.session.get(Event, event_id)
    user = db.session.get(User, session['user_id'])
    if not event or not user:
        flash('Event or user not found.', 'danger')
        return redirect(url_for('dashboard'))
    if event in user.attended_events:
        user.attended_events.remove(event)
        db.session.commit()
        flash(f'You have cancelled your attendance for {event.name}.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/upload_event_page')
def upload_event_page():
    if 'username' not in session or not session.get('is_organizer'):
        return redirect(url_for('dashboard'))
    return render_template('upload_event.html')

@app.route('/upload_event', methods=['POST'])
def upload_event():
    if 'username' not in session or not session.get('is_organizer'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    name = request.form['name']
    location_str = request.form['location']
    date_str = request.form['date']
    description = request.form['description']
    detailed_description = request.form.get('detailed_description', '')
    keywords = request.form['keywords']
    icon_file = request.files.get('icon')
    icon_path = None

    # FIX: Parse date string into a proper date object
    try:
        event_date = date_type.fromisoformat(date_str)
    except ValueError:
        flash('Invalid date format.', 'danger')
        return redirect(url_for('upload_event_page'))

    # FIX: Validate file type before saving
    if icon_file and icon_file.filename != '':
        if not allowed_file(icon_file.filename):
            flash('Invalid file type. Only PNG, JPG, GIF, WEBP allowed.', 'danger')
            return redirect(url_for('upload_event_page'))
        filename = secure_filename(icon_file.filename)
        icon_path = f'uploads/{filename}'
        upload_folder = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        icon_file.save(os.path.join(upload_folder, filename))

    lat, lon = geocode_location(location_str)
    if lat is None:
        flash(f"Could not find coordinates for '{location_str}'. Event saved but won't appear on map. "
              f"Try a more specific address (e.g. include city and country).", 'warning')

    user = db.session.get(User, session['user_id'])
    event = Event(name=name, location=location_str, date=event_date,
                  description=description, detailed_description=detailed_description,
                  keywords=keywords, icon=icon_path, organizer_id=user.id,
                  latitude=lat, longitude=lon)
    db.session.add(event)
    db.session.commit()

    if lat:
        flash('Event uploaded successfully and placed on the map!', 'success')
    else:
        flash('Event uploaded successfully!', 'success')

    return redirect(url_for('dashboard'))

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    event = db.session.get(Event, event_id)
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('dashboard'))
    user = db.session.get(User, session['user_id'])
    is_attending = event in user.attended_events
    is_organizer_of_event = event.organizer_id == session['user_id']
    return render_template('event_detail.html',
                           event=event,
                           is_attending=is_attending,
                           is_organizer_of_event=is_organizer_of_event)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

import os
import json # --- NEW ---
import math # --- NEW ---
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- NEW: Association table for User and Event (Many-to-Many) ---
attendance = db.Table('attendance',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True)
)

# --- UPDATED: User model ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    is_organizer = db.Column(db.Boolean, default=False)
    # Relationship to events they are attending
    attended_events = db.relationship('Event', secondary=attendance,
                                      lazy='subquery',
                                      backref=db.backref('attendees', lazy=True))

# --- UPDATED: Event model with Latitude and Longitude ---
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    detailed_description = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(200), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organizer = db.relationship('User', backref=db.backref('organized_events', lazy=True))
    # --- NEW: Geo-coordinates ---
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

with app.app_context():
    db.create_all()

# --- NEW: Haversine function to calculate distance ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

@app.route('/')
def index():
    return render_template('index.html')

# --- UPDATED: Login route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id  # Store user ID in session
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
        password = request.form['password']
        is_organizer = 'organizer' in request.form
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'warning')
        else:
            user = User(username=username, password=password, is_organizer=is_organizer)
            db.session.add(user)
            db.session.commit()
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

# --- UPDATED: Profile route ---
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    attending_events = user.attended_events
    
    my_events_with_attendees = []
    if user.is_organizer:
        my_events_with_attendees = Event.query.filter_by(organizer_id=user.id).all()

    return render_template('profile.html', 
                           username=session['username'],
                           is_organizer=session['is_organizer'],
                           attending_events=attending_events,
                           my_events_with_attendees=my_events_with_attendees)


# --- UPDATED DASHBOARD ROUTE ---
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    user = db.session.get(User, session['user_id'])
    attended_event_ids = {event.id for event in user.attended_events}

    location = request.args.get('location')
    date_filter = request.args.get('date') # Renamed to avoid conflict with date module
    keyword = request.args.get('keyword')
    distance_km = request.args.get('distance_km', type=int)
    
    query = Event.query

    # --- 2. HIDE PAST EVENTS ---
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    query = query.filter(Event.date >= today_str)

    # Filtering logic
    if location:
        query = query.filter(Event.location.ilike(f"%{location}%"))
    if date_filter:
        query = query.filter(Event.date == date_filter)
    if keyword:
        query = query.filter(Event.keywords.ilike(f"%{keyword}%"))
    
    events = query.order_by(Event.date).all()
    
    if location and distance_km:
        try:
            geolocator = Nominatim(user_agent="community_event_hub_filter")
            user_location = geolocator.geocode(location)
            if user_location:
                user_coords = (user_location.latitude, user_location.longitude)
                nearby_events = []
                for event in events:
                    if event.latitude and event.longitude:
                        event_coords = (event.latitude, event.longitude)
                        if haversine(user_coords[0], user_coords[1], event_coords[0], event_coords[1]) <= distance_km:
                            nearby_events.append(event)
                events = nearby_events
            else:
                flash(f"Could not find coordinates for location: {location}", "warning")
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            flash(f"Geocoding service is unavailable, please try again later. Error: {e}", "danger")
        except Exception as e:
            flash(f"An error occurred during distance filtering: {e}", "danger")

    events_for_map = []
    for event in events:
        if event.latitude and event.longitude:
            # --- 3. PASS DESCRIPTION TO MAP ---
            events_for_map.append({
                'name': event.name,
                'location': event.location,
                'lat': event.latitude,
                'lon': event.longitude,
                'description': event.description, # <-- ADD THIS
                'icon': url_for('static', filename=event.icon or 'images/default-event.png')
            })

    return render_template('dashboard.html',
                           username=session['username'],
                           is_organizer=session['is_organizer'],
                           events=events,
                           attended_event_ids=attended_event_ids,
                           user_id=session['user_id'],
                           events_for_map=json.dumps(events_for_map))

# --- NEW: Attend Event route ---
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

@app.route('/upload_event_page')
def upload_event_page():
    if 'username' not in session or not session.get('is_organizer'):
        return redirect(url_for('dashboard'))
    return render_template('upload_event.html')

# --- 4. IMPROVED UPLOAD ROUTE ---
@app.route('/upload_event', methods=['POST'])
def upload_event():
    if 'username' not in session or not session.get('is_organizer'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    name = request.form['name']
    location_str = request.form['location']
    date = request.form['date']
    description = request.form['description']
    detailed_description = request.form['detailed_description']
    keywords = request.form['keywords']
    icon_file = request.files.get('icon')
    icon_path = None
    
    geolocator = Nominatim(user_agent="community_event_hub_uploader")
    lat, lon = None, None
    try:
        location_data = geolocator.geocode(location_str, timeout=10)
        if location_data:
            lat, lon = location_data.latitude, location_data.longitude
            flash(f"Successfully found coordinates for '{location_str}'.", 'success')
        else:
            # THIS IS LIKELY WHAT HAPPENED TO 'Hyderabad'
            flash(f"Could not find coordinates for '{location_str}'. The event was saved, but it won't appear on the map.", 'warning')
    except (GeocoderTimedOut, GeocoderUnavailable):
        flash("The geocoding service is temporarily unavailable. The event was saved without map data.", "danger")
    except Exception as e:
        flash(f"An unexpected geocoding error occurred: {e}. Event saved without map data.", "danger")

    if icon_file and icon_file.filename != '':
        filename = secure_filename(icon_file.filename)
        icon_path = f'uploads/{filename}'
        upload_folder = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        icon_file.save(os.path.join(upload_folder, filename))
        
    user = db.session.get(User, session['user_id'])
    event = Event(name=name, location=location_str, date=date,
                  description=description, detailed_description=detailed_description, keywords=keywords,
                  icon=icon_path, organizer_id=user.id,
                  latitude=lat, longitude=lon)
    db.session.add(event)
    db.session.commit()
    
    if lat:
        flash('Event uploaded successfully and placed on the map!', 'success')
    else:
        flash('Event uploaded successfully!', 'success')
        
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

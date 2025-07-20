# Community Event Hub with Geo-services
#### Video Demo:  https://youtu.be/0gVGLlT4OSA

#### Description:

The Community Event Hub is a full-stack web application designed to connect people with local events. Users can discover, filter, and register for events in their area, while organizers manage and promote gatherings to their community. Built with Python (Flask), SQLite, and modern web technologies, this platform demonstrates comprehensive web development principles with real-world, location-centric functionality.

#### Project Overview:
Deep integration of geo-services: Events are geocoded and visualized on an interactive map.

Location-aware: Users filter events by location, distance, date, or keyword.

User-centric design enables real-world community engagement, not just technical demonstration.

#### Key Features:
Dual User Roles: Authentication for both Users and Organizers with tailored dashboards and permissions.

Event Creation & Management: Organizers can create/upload events with descriptions, dates, locations, keywords, and icons.

Advanced Event Discovery: Search and filter events by location, date, and keywords.

Distance-Based Filtering: Haversine formula allows users to search for events within a chosen distance from a location.

Interactive Map Visualization: Leaflet.js map shows events as interactive markers with detailed popups.

Event Attendance System: Secure RSVP lets users attend events; system prevents duplicate registrations.

Personalized User Profiles:

Users see all events they’re attending

Organizers see all hosted events and a live attendee list for each

Responsive and Dynamic UI: Modern, mobile-friendly design, instant feedback via flash messages.

#### Technologies and Libraries Used
Backend: Python, Flask

Database: SQLite, Flask-SQLAlchemy ORM

Geo-services:

geopy (Nominatim) for geocoding addresses to latitude/longitude

math for Haversine distance formula

Frontend: HTML5, CSS3, JavaScript

Mapping: Leaflet.js

Templating: Jinja2 (integrated with Flask)

#### Codebase and File Structure

community-event-hub/
├── app.py
├── requirements.txt
├── users.db
├── /static
│   ├── css/style.css
│   ├── images/
│   └── uploads/
├── /templates
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── profile.html
│   └── upload_event.html
└── README.md

#### Design and Implementation Highlights
Robust Database Design:
Many-to-many relationship between Users and Events via an attendance table using SQLAlchemy.

Open-Source Geo-Services:
Used geopy with Nominatim and math Haversine formula for efficient, privacy-respecting, free geo-functions.

User Experience:
Clean, intuitive UI. Filtering instantly updates event list and map markers. Responsive feedback via flash messaging.

Self-Contained Architecture:
All backend logic is in app.py for clarity (suitable for this scale), but cleanly separated routes/models for maintainability.

#### Quick Start
Prerequisites
Python 3.x
pip

Setup
Clone the repository:

git clone https://github.com/Subaitha7/community-event-hub-with-geo-services

cd community-event-hub

Install dependencies:

pip install -r requirements.txt

Run the application:

python app.py
Open your browser at: http://127.0.0.1:5000

#### License
MIT License

Credits
Developed by Subaitha, inspired by real-world community needs and CS50. See YouTube Demo.

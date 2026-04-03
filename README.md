# 🗺️ Community Event Hub

<div align="center">

**Discover, share, and join local events — right where you are.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-community--event--hub.onrender.com-00b894?style=for-the-badge&logo=render&logoColor=white)](https://community-event-hub.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://render.com)
[![Leaflet](https://img.shields.io/badge/Leaflet.js-Map-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com)

</div>

---

## 📖 About

**Community Event Hub** is a full-stack web application that lets community members **discover local events on an interactive map**, **RSVP to events**, and **organizers post events** with geo-located pins. Events are geocoded automatically using OpenStreetMap — no API key required.

🔗 Live Demo: https://community-event-hub.onrender.com

Whether you're a local organiser running a yoga class or a resident looking for weekend happenings, Community Event Hub connects people to experiences near them.

---

## ✨ Features

### 👤 Users
- Sign up as a **regular attendee** or an **event organizer**
- Secure authentication with hashed passwords (Werkzeug)
- Persistent session management with role-based access

### 📅 Events
- Browse all **upcoming events** — past events are automatically hidden
- **Paginated event cards** (8 per page) with event image, date, location, and keywords
- **Attend / Unattend** events with one click
- View a detailed event page with full description and organizer info

### 🗺️ Interactive Map
- Events with resolved coordinates appear as **Leaflet.js map pins**
- Click a pin to see a pop-up info panel with event name, date, description, and a **"Get Directions"** button (links to Google Maps)
- Clicking a map pin **highlights the corresponding event card** in the list
- Map pin count shown at a glance

### 🔍 Filtering & Search
- Filter by **location name**, **date**, **keyword**, or **free-text search** (event name)
- Optional **distance filter** — enter a radius in km and only events within that distance of your location are shown (powered by the Haversine formula)

### 📤 Organizer Tools
- Organizers can **upload events** with name, location, date, short description, detailed description, keywords, and a custom image
- Location strings are **automatically geocoded** via Nominatim (OpenStreetMap) with a Photon fallback — events are placed on the map instantly
- Upload a custom banner image for each event (PNG, JPG, GIF, WEBP)

### 👤 Profile Page
- See all events you're **attending**
- Organizers see all their **posted events** with live attendee counts

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLAlchemy ORM · SQLite (dev) · PostgreSQL (prod) |
| Auth | Werkzeug password hashing · Flask sessions |
| Geocoding | Nominatim (OpenStreetMap) · Photon (Komoot) fallback |
| Maps | Leaflet.js |
| Frontend | Jinja2 templates · Custom CSS |
| Hosting | Render (web service + PostgreSQL) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Subaitha7/community-event-hub-with-geo-services.git
cd community-event-hub-with-geo-services

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export SECRET_KEY="your-secret-key-here"
# DATABASE_URL defaults to SQLite (sqlite:///users.db) if not set

# 5. Run the app
python app.py
```

Visit `http://localhost:5000` in your browser.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session secret — use a long random string in production |
| `DATABASE_URL` | No | PostgreSQL connection string (defaults to local SQLite) |

---

## 🌐 Deployment (Render)

1. Push to GitHub.
2. Create a new **Web Service** on [Render](https://render.com) pointing to your repo.
3. Add a **PostgreSQL** add-on — Render auto-sets `DATABASE_URL`.
4. Set `SECRET_KEY` in the Render dashboard under **Environment**.
5. Set the start command to:
   ```
   gunicorn app:app
   ```
6. Deploy. The database tables are created automatically on first run.

> **Note:** Uploaded event images are stored in `static/uploads/`. On Render's free tier, the filesystem is ephemeral — images will reset on redeploy. For persistent image storage, integrate an S3-compatible service.

---

## 📁 Project Structure

```
community-event-hub/
├── app.py                   # Flask application, routes, models
├── requirements.txt
├── .gitignore
├── static/
│   ├── css/
│   │   └── style.css        # All custom styles
│   ├── images/
│   │   ├── community-bg.jpg
│   │   ├── dashboard-bg.jpg
│   │   └── default-event.jpg
│   └── uploads/             # Organizer-uploaded event images
└── templates/
    ├── base.html            # Shared layout
    ├── index.html           # Landing page
    ├── login.html
    ├── signup.html
    ├── dashboard.html       # Main event feed + map
    ├── event_detail.html    # Single event view
    ├── upload_event.html    # Organizer event form
    └── profile.html         # User profile & attended events
```

---

## 🗺️ How Geocoding Works

When an organizer posts an event, the location string is geocoded automatically:

1. **Primary:** Nominatim (OpenStreetMap) is queried with the location text.
2. **Fallback:** If Nominatim returns nothing, Photon (Komoot) is tried.
3. If coordinates are found, the event gets a map pin and participates in distance filtering.
4. If geocoding fails, the event is still saved — it just won't appear on the map or in distance-filtered results. A warning is shown to the organizer.

Distance between two coordinates is computed using the **Haversine formula** (great-circle distance on Earth's surface).

---

## 🔮 Planned Features

- [ ] Event comments / discussion thread
- [ ] Email notifications for RSVPs and event updates
- [ ] Persistent image storage (AWS S3 / Cloudflare R2)
- [ ] Event categories with icon badges
- [ ] Admin panel for event moderation
- [ ] Social sharing links per event

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open a pull request or file an issue on GitHub.

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source. See the repository for license details.

---

<div align="center">
  Built with ❤️ by <a href="https://github.com/Subaitha7">Subaitha</a>
  <br>
Connect on <a href="https://www.linkedin.com/in/subaitha-m-a152b6367/">LinkedIn</a>
</div>

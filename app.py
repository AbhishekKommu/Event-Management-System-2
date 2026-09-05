from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from datetime import datetime

app = Flask(__name__)

app.secret_key = "event-management-secret-key"

DATABASE = "events.db"


# -----------------------------
# Database Connection
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT NOT NULL,
            organizer_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organizer_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Login Required Decorator
# -----------------------------

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Login required"
            }), 401

        return function(*args, **kwargs)

    return wrapper


# -----------------------------
# Frontend Routes
# -----------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html")


@app.route("/events")
def events_page():
    return render_template("events.html")


# -----------------------------
# Register API
# -----------------------------

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db()

        conn.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Registration successful"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409


# -----------------------------
# Login API
# -----------------------------

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    conn = get_db()

    user = conn.execute("""
        SELECT * FROM users
        WHERE email = ?
    """, (email,)).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        })

    return jsonify({
        "success": False,
        "message": "Invalid email or password"
    }), 401


# -----------------------------
# Logout API
# -----------------------------

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


# -----------------------------
# Get Events
# -----------------------------

@app.route("/api/events", methods=["GET"])
def get_events():

    conn = get_db()

    events = conn.execute("""
        SELECT
            events.*,
            users.name AS organizer
        FROM events
        JOIN users
        ON events.organizer_id = users.id
        ORDER BY events.date ASC
    """).fetchall()

    conn.close()

    event_list = []

    for event in events:
        event_list.append({
            "id": event["id"],
            "title": event["title"],
            "description": event["description"],
            "date": event["date"],
            "time": event["time"],
            "location": event["location"],
            "category": event["category"],
            "organizer": event["organizer"]
        })

    return jsonify({
        "success": True,
        "events": event_list
    })


# -----------------------------
# Get Single Event
# -----------------------------

@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_event(event_id):

    conn = get_db()

    event = conn.execute("""
        SELECT * FROM events
        WHERE id = ?
    """, (event_id,)).fetchone()

    conn.close()

    if not event:
        return jsonify({
            "success": False,
            "message": "Event not found"
        }), 404

    return jsonify({
        "success": True,
        "event": dict(event)
    })


# -----------------------------
# Create Event
# -----------------------------

@app.route("/api/events", methods=["POST"])
@login_required
def create_event():

    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    date = data.get("date")
    time = data.get("time")
    location = data.get("location")
    category = data.get("category")

    if not all([title, date, time, location, category]):
        return jsonify({
            "success": False,
            "message": "Required fields are missing"
        }), 400

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO events
        (title, description, date, time, location, category, organizer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        date,
        time,
        location,
        category,
        session["user_id"]
    ))

    conn.commit()

    event_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "message": "Event created successfully",
        "event_id": event_id
    }), 201


# -----------------------------
# Update Event
# -----------------------------

@app.route("/api/events/<int:event_id>", methods=["PUT"])
@login_required
def update_event(event_id):

    data = request.get_json()

    conn = get_db()

    event = conn.execute("""
        SELECT * FROM events
        WHERE id = ?
    """, (event_id,)).fetchone()

    if not event:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Event not found"
        }), 404

    if event["organizer_id"] != session["user_id"]:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    conn.execute("""
        UPDATE events
        SET title = ?,
            description = ?,
            date = ?,
            time = ?,
            location = ?,
            category = ?
        WHERE id = ?
    """, (
        data.get("title"),
        data.get("description"),
        data.get("date"),
        data.get("time"),
        data.get("location"),
        data.get("category"),
        event_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Event updated successfully"
    })


# -----------------------------
# Delete Event
# -----------------------------

@app.route("/api/events/<int:event_id>", methods=["DELETE"])
@login_required
def delete_event(event_id):

    conn = get_db()

    event = conn.execute("""
        SELECT * FROM events
        WHERE id = ?
    """, (event_id,)).fetchone()

    if not event:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Event not found"
        }), 404

    if event["organizer_id"] != session["user_id"]:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    conn.execute("""
        DELETE FROM events
        WHERE id = ?
    """, (event_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Event deleted successfully"
    })


# -----------------------------
# Current User
# -----------------------------

@app.route("/api/user")
def current_user():

    if "user_id" not in session:
        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "user": {
            "id": session["user_id"],
            "name": session["user_name"]
        }
    })


# -----------------------------
# Start Application
# -----------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

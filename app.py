import logging
import grpc
import requests
from bson import ObjectId
from flask import jsonify
from flask_pymongo import PyMongo
from grpc_event_pb2_grpc import EventServiceStub
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt
import jwt
from datetime import datetime, timedelta
from authlib.jose import jwt
import os  # For accessing environment variables
from flask import Flask, redirect, url_for, request, session, jsonify, render_template  # Flask core functions and classes
from flask_dance.contrib.google import make_google_blueprint, google  # Google OAuth integration
from google.oauth2.credentials import Credentials  # For handling Google OAuth credentials
from googleapiclient.discovery import build  # For interacting with Google APIs

logging.basicConfig(level=logging.DEBUG)
# Home Route to Render the Form
app = Flask(__name__ )
app.config["MONGO_URI"] = "mongodb://localhost:27017/eventdb"
app.secret_key = '6692a191b7c75f139ddcea9dfc7d1c8f'
JWT_SECRET = "a588896c6c34617ae8ec6b8887c0eb3a02697670059715c9383209167ec3c39f"
JWT_ALGORITHM = 'HS256'
mongo = PyMongo(app)
events_collection = mongo.db.events
client = MongoClient('mongodb://localhost:27017/')
db = client['eventdb']  # Change this to your database name
records = db['register']  # Change this to your collection name
channel = grpc.insecure_channel('localhost:50051')
stub = EventServiceStub(channel)
SERP_API_KEY = "cc77d3bb5a1c77305d0b96c1f02875eb56cbe5bca3040e591437b56204c0ee90"


@app.route("/")
def index():
    message = request.args.get('message')
    return render_template('index.html', message=message)


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


def is_token_valid(email):
    user = records.find_one({"email": email})
    if user and user.get("token"):
        decoded = decode_token(user["token"])
        if decoded:
            return True
    return False


@app.route("/register", methods=['POST', 'GET'])
def register():
    message = ''
    if "email" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        user = request.form.get("fullname")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})

        if user_found:
            message = 'There already is a user by that name'
            return render_template('register.html', message=message)
        if email_found:
            message = 'This email already exists in the database'
            return render_template('register.html', message=message)
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('register.html', message=message)
        else:
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())

            # Generate JWT token
            token_payload = {
                "email": email,
                "exp": datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
            }
            token = jwt.encode({'alg': JWT_ALGORITHM, 'typ': 'JWT'}, token_payload, JWT_SECRET)

            # Insert user into MongoDB
            user_input = {'name': user, 'email': email, 'password': hashed, 'token': token}
            records.insert_one(user_input)

            session["email"] = email
            return redirect(url_for("index", message=f"Hello! You have registered as {email}"))

    return render_template('register.html')


@app.route("/loginn", methods=["POST", "GET"])
def loginn():
    message = ''
    if "email" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_found = records.find_one({"email": email})
        if user_found:
            passwordcheck = user_found['password']
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                # Generate a new JWT token on login
                token_payload = {
                    "email": email,
                    "exp": datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
                }
                token = jwt.encode({'alg': JWT_ALGORITHM, 'typ': 'JWT'}, token_payload, JWT_SECRET)

                # Update the user's token in MongoDB
                records.update_one({"email": email}, {"$set": {"token": token}})

                session["email"] = email
                return redirect(url_for("index", message=f"Hello! You have logged in as {email}"))

            else:
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)


@app.route("/logout")
def logout():
    if "email" in session:
        # Invalidate the token by setting it to None in the database
        records.update_one({"email": session["email"]}, {"$set": {"token": None}})
        session.pop("email", None)
    return redirect(url_for("index", message="You have successfully logged out"))


# Protected route example
@app.route("/protected")
def protected():
    if "email" in session and is_token_valid(session["email"]):
        return "This is a protected route!"
    return redirect(url_for("loginn", message="Please log in to access this page."))


def fetch_events_from_serpapi(url):
    # Fetch events data from SerpAPI
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('events_results', [])
    return []


# Google OAuth configuration
google_blueprint = make_google_blueprint(
    client_id='912370917797-c08nfe40bnvl9qog13uml20n2gieqhea.apps.googleusercontent.com',
    client_secret='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',
    scope=["https://www.googleapis.com/auth/userinfo.profile",
           "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/calendar"],
    redirect_to="oauth_callback"
)
app.register_blueprint(google_blueprint, url_prefix="/login")


@app.route('/oauth_callback')
def oauth_callback():
    # This route will be called after Google OAuth login is completed
    if not google.authorized:
        return redirect(url_for('google.login'))

    # Exchange the authorization code for access and refresh tokens
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info", "danger")
        return redirect(url_for("index"))

    # Get the user information and tokens
    user_info = resp.json()
    session['user_info'] = user_info

    # Store tokens in session
    oauth_token = google.token["access_token"]
    refresh_token = google.token["refresh_token"]
    session['google_oauth_token'] = oauth_token
    session['google_oauth_refresh_token'] = refresh_token

    # Redirect to browse.html after successful login
    return redirect(url_for('browse'))


@app.route('/browse.html')
def browse():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    user_info = resp.json()
    event_name = request.args.get('event')

    # Construct the URL for SerpAPI
    if not event_name:
        url = f"https://serpapi.com/search.json?engine=google_events&q=Events+in+Maharashtra&hl=en&gl=us&api_key={SERP_API_KEY}"
    else:
        url = f"https://serpapi.com/search.json?engine=google_events&q=Events={event_name}+in+Maharashtra&hl=en&gl=us&api_key={SERP_API_KEY}"

    events = fetch_events_from_serpapi(url)
    return render_template('browse.html', user_info=user_info, events=events)


@app.route('/login/google/authorized')
def google_authorized():
    # This function is called when Google redirects back to your app after authorization.
    if not google.authorized:
        return redirect(url_for('google.login'))

    # Use Flask-Dance to get user information
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    user_info = resp.json()

    # Optionally, save user info to session or database
    session['user_info'] = user_info

    # Redirect to the browse page
    return redirect(url_for('browse'))


@app.route('/schedule_event', methods=['POST'])
def schedule_event():
    if not google.authorized:
        return redirect(url_for('google.login'))

    # Get event details from the request
    event_title = request.form.get('title')
    event_date = request.form.get('date')  # Format should be "YYYY-MM-DD"
    event_location = request.form.get('location')
    event_description = request.form.get('description')

    # Create event on Google Calendar
    credentials = Credentials(
        token=session['google_oauth_token'],
        refresh_token=session['google_oauth_refresh_token'],
        token_uri="https://oauth2.googleapis.com/token",
        client_id='912370917797-c08nfe40bnvl9qog13uml20n2gieqhea.apps.googleusercontent.com',
        client_secret='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'
    )

    service = build('calendar', 'v3', credentials=credentials)

    event = {
        'summary': event_title,
        'location': event_location,
        'description': event_description,
        'start': {
            'dateTime': f'{event_date}T09:00:00',
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': f'{event_date}T10:00:00',
            'timeZone': 'UTC',
        }
    }

    # Insert the event into the calendar
    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return jsonify({'status': 'success', 'event_id': event_result['id']}), 200


@app.route('/organizerForm.html')
def form():
    return render_template('organizerForm.html')


# Event Details Page
@app.route('/eventDetails.html')
def event_details():
    return render_template('eventDetails.html')

# Create Event
@app.route('/event', methods=['POST'])
def create_event():
    data = request.json
    event_id = events_collection.insert_one(data).inserted_id
    return jsonify({"message": "Event created", "id": str(event_id)}), 201

# Get All Events with Optional Search


@app.route('/events', methods=['GET'])
def get_events():
    search_query = request.args.get('search', '')
    events = []

    if search_query:
        cursor = events_collection.find({"eventName": {"$regex": search_query, "$options": "i"}})
    else:
        cursor = events_collection.find()

    for event in cursor:
        event['_id'] = str(event['_id'])
        events.append(event)
    return jsonify(events), 200

# Get Single Event


@app.route('/event/<id>', methods=['GET'])
def get_event(id):
    event = events_collection.find_one({"_id": ObjectId(id)})
    if event:
        event['_id'] = str(event['_id'])
        return jsonify(event), 200
    else:
        return jsonify({"error": "Event not found"}), 404


# Update Event Route


@app.route('/updateEvent/<id>', methods=['GET','POST','PUT'])
def update_event(id):
    if request.method == 'PUT':
        try:
            # Retrieve JSON data from the request
            data = request.get_json()

            # Update event in MongoDB
            result = events_collection.update_one({"_id": ObjectId(id)}, {"$set": data})

            if result.matched_count > 0:
                return jsonify({"message": "Event updated successfully!"}), 200
            else:
                return jsonify({"error": "Event not found"}), 404
        except Exception as e:
            logging.error(f"Error updating event: {e}")
            return jsonify({"error": "An error occurred while updating the event."}), 500

    elif request.method == 'POST':
        try:
            data = {
                'eventName': request.form.get('eventName'),
                'eventLocation': request.form.get('eventLocation'),
                'dateFrom': request.form.get('dateFrom'),
                'dateTo': request.form.get('dateTo'),
                'price': float(request.form.get('price')),
                'category': request.form.get('category'),
                'name': request.form.get('name')
            }

            result = events_collection.update_one({"_id": ObjectId(id)}, {"$set": data})

            if result.matched_count > 0:
                jsonify({"message": "Event updated successfully!"}), 200
                flash('Event updated successfully!', 'success')
                return redirect(url_for('event_details'))
            else:
                flash('Failed to update event. Event may not exist.', 'error')
                return redirect(url_for('update_event', id=id))
        except Exception as e:
            logging.error(f"Error updating event: {e}")
            flash('An error occurred while updating the event.', 'error')
            return redirect(url_for('update_event', id=id))

    try:
        event = events_collection.find_one({"_id": ObjectId(id)})
        if event:
            event['_id'] = str(event['_id'])
            return render_template('updateEvent.html', event=event)
        else:
            flash('Event not found.', 'error')
            return redirect(url_for('event_details'))
    except Exception as e:
        logging.error(f"Error retrieving event for update: {e}")
        flash('An error occurred while retrieving the event.', 'error')
        return redirect(url_for('event_details'))


# Delete Event
@app.route('/event/<id>', methods=['DELETE'])
def delete_event(id):
    result = events_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({"message": "Event deleted"}), 200
    else:
        return jsonify({"error": "Event not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
import logging
from datetime import datetime

import bcrypt
import grpc
import jwt
import requests
from authlib.jose import jwt
from bson import ObjectId
from flask import Flask, redirect, url_for, request, session, jsonify, render_template
from flask import flash
from flask_pymongo import PyMongo
from pymongo import MongoClient

from grpc_event_pb2_grpc import EventServiceStub
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
# Home Route to Render the Form
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = os.getenv("SECRET_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
SERP_API_KEY = os.getenv("SERP_API_KEY")
JWT_ALGORITHM = 'HS256'
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/calendar.readonly', ]

mongo = PyMongo(app)
events_collection = mongo.db.events
client = MongoClient('mongodb://localhost:27017/')
db = client['eventdb']  # Change this to your database name
records = db['register']  # Change this to your collection name
channel = grpc.insecure_channel('localhost:50051')
stub = EventServiceStub(channel)


def configure_test_db():
    app.config["MONGO_URI"] = "mongodb://localhost:27017/testdb"
    global db, events_collection
    db = client['testdb']
    events_collection = db['events']


@app.route("/")
def index():
    message = request.args.get('message')
    return render_template('index.html', message=message)


@app.route("/aboutus.html")
def aboutus():
    return render_template('aboutus.html')


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

            # Insert user into MongoDB
            user_input = {'name': user, 'email': email, 'password': hashed, 'calendar_exists': False}
            records.insert_one(user_input)

            # Create the user's calendar
            create_user_calendar(email)

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
                session["email"] = email

                # Check if the user already has a calendar
                if not user_found.get("calendar_exists", False):
                    create_user_calendar(email)  # Create calendar if it doesn't exist
                else:
                    # User already has a calendar
                    print("User already has a calendar.")

                return redirect(url_for("index", message=f"Hello! You have logged in as {email}"))

            else:
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)

    return render_template('login.html', message=message)


def user_exists(email):
    """Check if the user already exists in the database and has a calendar."""
    user_record = records.find_one({"email": email})
    return user_record is not None and user_record.get("calendar_exists", False)


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


@app.route('/browse.html')
def browse():
    event_name = request.args.get('event')

    # Construct the URL for SerpAPI
    if not event_name:
        url = f"https://serpapi.com/search.json?engine=google_events&q=Events+in+Maharashtra&hl=en&gl=us&api_key={SERP_API_KEY}"
    else:
        url = f"https://serpapi.com/search.json?engine=google_events&q=Events={event_name}+in+Maharashtra&hl=en&gl=us&api_key={SERP_API_KEY}"

    events = fetch_events_from_serpapi(url)
    # return render_template('browse.html', user_info=user_info, events=events)
    return render_template('browse.html', events=events)


def load_credentials():
    return Credentials.from_authorized_user_file('credentials.json')


@app.route('/schedule_event', methods=['POST'])
def schedule_event():
    if "email" not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 403

    user_email = session['email']
    event_details = {
        "title": request.form.get('title'),
        "location": request.form.get('location', "Online"),
        "link": request.form.get('link', ""),
        "date": request.form.get('date')
    }

    # Extracting start and end dates from the event date string
    date_str = event_details['date']  # e.g., "Mon, Nov 4, 12 AM – Tue, Nov 5, 12 AM GMT+5:30"
    start_date_str, end_date_str = date_str.split(' – ')

    # Adjusted parsing format
    start_datetime = datetime.strptime(start_date_str, "%a, %b %d, %I %p")
    end_datetime = datetime.strptime(end_date_str.split(' GMT')[0], "%a, %b %d, %I %p")

    # Format the dates as 'YYYY-MM-DD'
    start_date = start_datetime.strftime("%Y-%m-%d")
    end_date = end_datetime.strftime("%Y-%m-%d")

    event_body = {
        'summary': event_details['title'],
        'location': event_details['location'],
        'description': event_details['link'],  # Use description for the link if needed
        'start': {
            'date': start_date
        },
        'end': {
            'date': end_date
        }
    }

    result = add_event_to_google_calendar(user_email, event_body)

    if result:
        return jsonify({"status": "success", "message": "Event scheduled successfully!"})
    else:
        return jsonify({"status": "error", "message": "Failed to schedule event"}), 500


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
    data = request.get_json()

    # Check for required fields and return appropriate error messages
    if not data.get('name'):
        return jsonify({'message': 'Event name is required'}), 400
    if not data.get('description'):
        return jsonify({'message': 'Event description is required'}), 400
    if not data.get('eventLocation'):
        return jsonify({'message': 'Event location is required'}), 400
    if not data.get('dateFrom'):
        return jsonify({'message': 'Event start date is required'}), 400
    if not data.get('dateTo'):
        return jsonify({'message': 'Event end date is required'}), 400
    if not data.get('price'):
        return jsonify({'message': 'Event price is required'}), 400
    if not data.get('category'):
        return jsonify({'message': 'Event category is required'}), 400

        # Use the email from the session
    created_by = session.get("email")

        # Ensure the 'created_by' field is added to the data
    if not created_by:
        return jsonify({'message': 'Event creator email is required'}), 400

    data['created_by'] = created_by  # Add the email to the event data

    # If all required fields are present, proceed to create the event
    event_id = events_collection.insert_one(data).inserted_id
    return jsonify({'message': 'Event created', 'id': str(event_id)}), 201


# Get All Events with Optional Search
@app.route('/events', methods=['GET'])
def get_events():
    user_email = session.get("email")
    if user_email:
        search_query = request.args.get('search', '')
        events = []
        query = {"created_by": user_email}
        if search_query:
            query["eventName"] = {"$regex": search_query, "$options": "i"}
        cursor = events_collection.find(query)

        for event in cursor:
            event['_id'] = str(event['_id'])
            events.append(event)

        if not events:  # If no events found
            return jsonify({"message": "No events available"}), 200

        return jsonify(events), 200

    return jsonify({"message": "Login to create events"}), 401


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
@app.route('/updateEvent/<id>', methods=['GET', 'POST', 'PUT'])
def update_event(id):
    if request.method == 'PUT':
        user_email = session.get("email")
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401

        # Check if the event is created by the logged-in user
        event = events_collection.find_one({"_id": ObjectId(id), "created_by": user_email})
        if not event:
            return jsonify({"error": "Event not found or you do not have permission to update it"}), 404

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
    user_email = session.get("email")
    if not user_email:
        return jsonify({"error": "User not logged in"}), 401
    result = events_collection.delete_one({"_id": ObjectId(id), "created_by": user_email})
    if result.deleted_count > 0:
        return jsonify({"message": "Event deleted"}), 200
    else:
        return jsonify({"error": "Event not found"}), 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


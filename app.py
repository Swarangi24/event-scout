import json
import urllib

from flask import Flask, request, jsonify, render_template, redirect, flash, url_for, session
#from flask import pymongo, bcrypt
from flask_pymongo import PyMongo
from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash
import grpc
from grpc_event_pb2 import EventRequest
from grpc_event_pb2_grpc import EventServiceStub
from pymongo import MongoClient
import requests
from urllib.parse import urlencode
import logging
logging.basicConfig(level=logging.DEBUG)

# Home Route to Render the Form
app = Flask(__name__ )
app.config["MONGO_URI"] = "mongodb://localhost:27017/eventdb"
app.secret_key = '6692a191b7c75f139ddcea9dfc7d1c8f'
mongo = PyMongo(app)
events_collection = mongo.db.events
channel = grpc.insecure_channel('localhost:50051')
stub = EventServiceStub(channel)
SERP_API_KEY = "cc77d3bb5a1c77305d0b96c1f02875eb56cbe5bca3040e591437b56204c0ee90"

# Home Route to Render the Form
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/organizerForm.html')
def form():
    return render_template('organizerForm.html')

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
    return render_template('browse.html', events=events)



@app.route('/feedback/<event_id>', methods=['POST'])
def feedback(event_id):
    feedback_text = request.form['feedback']
    events_collection.update_one({'id': event_id}, {'$set': {'feedback': feedback_text}})
    flash('Feedback submitted successfully!')
    return redirect(url_for('browse'))


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
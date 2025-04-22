# EventScout System

An intelligent event management platform built using **Flask** and **MongoDB**, EventScout enables users to organize, manage, discover, and share events with ease. Designed to cater to both event organizers and attendees, it streamlines the entire event lifecycle — from creation to participation.

## Features

- **User Authentication**: Secure sign-up and login system for both users and organizers.
- **Event Creation & Management**: Organizers can create, update, and delete events.
- **Event Discovery**: Users can browse events based on filters like status, category, and location.
- **Event Registration**: Users can register for events, check availability, and add them to their calendar.
- **Event Sharing**: Share event details with others via a public link.
- **Personalized Calendar**: Schedule events and get a daily overview.
- **Ratings & Feedback**: Users can rate events and leave reviews.

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript (templated through Flask)
- **Tools**: Postman, PyCharm

## How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/event-scout.git
   cd event-scout
Create a virtual environment and install dependencies:

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # For Windows: venv\Scripts\activate
pip install -r requirements.txt
Set up environment variables (e.g., secret key, MongoDB URI).

Run the app:

bash
Copy
Edit
flask run
Open your browser at http://localhost:5000

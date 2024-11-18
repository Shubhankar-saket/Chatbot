from flask import Flask, request, jsonify
import requests
import spacy
from spacy.cli import download

app = Flask(__name__)


# Try to load the model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not found, download it
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

CALENDLY_API_TOKEN = "eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzMxNzQ3MTUyLCJqdGkiOiI5OWVlNjA1Yy0wMDJiLTQ2Y2EtOTdjMi1lOTdhMWFkODJkMjUiLCJ1c2VyX3V1aWQiOiJlMDM2MDhlOS1jYmUyLTQ1OTQtYTBmYy01YzVkNDc0MzBlMDcifQ.uzjWHlBGyydpdn41ynOZluX2X2E_KieiDOL3s3Ilwxgim1W6_K1--LVgdD0ZDyq3avo7AUHgZSvItwk8R_Mt3A"

# Get doctor availability (mock implementation for demo)
def get_doctor_availability(doctor_name):
    mock_availability = {
        "Dr. Alice Johnson": ["10:00 AM", "2:00 PM", "4:00 PM"],
        "Dr. John Smith": ["11:00 AM", "1:00 PM", "3:00 PM"]
    }
    return mock_availability.get(doctor_name, [])

# Book appointment via Calendly
def book_appointment_with_calendly(doctor_name, patient_name, time_slot):
    url = "https://api.calendly.com/scheduled_events"
    headers = {"Authorization": f"Bearer {CALENDLY_API_TOKEN}"}
    data = {
        "doctor_name": doctor_name,
        "patient_name": patient_name,
        "time_slot": time_slot
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    return {"error": "Failed to book appointment"}

# Reschedule appointment via Calendly
def reschedule_appointment(appointment_id, new_time_slot):
    url = f"https://api.calendly.com/scheduled_events/{appointment_id}/reschedule"
    headers = {"Authorization": f"Bearer {CALENDLY_API_TOKEN}"}
    data = {"new_time_slot": new_time_slot}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to reschedule"}

@app.route('/chat', methods=['POST'])
def dialogflow_webhook():
    req = request.get_json()

    intent = req.get('queryResult', {}).get('intent', {}).get('displayName')
    parameters = req.get('queryResult', {}).get('parameters', {})
    response_text = "Sorry, I didn't understand that."

    if intent == "Check Availability":
        doctor_name = parameters.get('doctor_name', 'Dr. Alice Johnson')
        availability = get_doctor_availability(doctor_name)
        response_text = f"{doctor_name} is available at: {', '.join(availability)}"

    elif intent == "Book Appointment":
        doctor_name = parameters.get('doctor_name', 'Dr. Alice Johnson')
        patient_name = parameters.get('patient_name', 'John Doe')
        time_slot = parameters.get('time_slot', '10:00 AM')
        result = book_appointment_with_calendly(doctor_name, patient_name, time_slot)
        response_text = "Appointment booked successfully!" if "error" not in result else result["error"]

    elif intent == "Reschedule Appointment":
        appointment_id = parameters.get('appointment_id')
        new_time_slot = parameters.get('new_time_slot')
        result = reschedule_appointment(appointment_id, new_time_slot)
        response_text = "Appointment rescheduled successfully!" if "error" not in result else result["error"]

    return jsonify({
        "fulfillmentText": response_text
    })

if __name__ == "__main__":
    app.run(debug=True)

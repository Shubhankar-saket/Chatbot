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

# Handle intent and entity extraction using spaCy
def handle_intent(message):
    doc = nlp(message)
    doctor_name = None
    time_slot = None

    # Extract doctor name and time slot
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            doctor_name = ent.text
        elif ent.label_ == "TIME":
            time_slot = ent.text

    if doctor_name and time_slot:
        return "Book Appointment", doctor_name, time_slot
    elif doctor_name:
        return "Check Availability", doctor_name
    elif time_slot:
        return "Reschedule Appointment", time_slot
    else:
        return "General Inquiry", message

@app.route('/chat', methods=['POST'])
def dialogflow_webhook():
    req = request.get_json()

    message = req.get('queryResult', {}).get('queryText', '')
    intent, entity1, entity2 = handle_intent(message)  # entity1 = doctor name, entity2 = time slot

    response_text = "Sorry, I didn't understand that."

    if intent == "Check Availability":
        doctor_name = entity1
        availability = get_doctor_availability(doctor_name)
        response_text = f"{doctor_name} is available at: {', '.join(availability)}" if availability else "Doctor not available"

    elif intent == "Book Appointment":
        if entity1 and entity2:
            doctor_name = entity1
            time_slot = entity2
            patient_name = "John Doe"  # You can dynamically extract the patient's name if needed
            result = book_appointment_with_calendly(doctor_name, patient_name, time_slot)
            response_text = "Appointment booked successfully!" if "error" not in result else result["error"]
        else:
            response_text = "Please provide both the doctor and the time slot."

    elif intent == "Reschedule Appointment":
        if entity1 and entity2:
            appointment_id = entity1  # Assume entity1 is the appointment ID
            new_time_slot = entity2  # Assume entity2 is the new time slot
            result = reschedule_appointment(appointment_id, new_time_slot)
            response_text = "Appointment rescheduled successfully!" if "error" not in result else result["error"]

    return jsonify({
        "fulfillmentText": response_text
    })

if __name__ == "__main__":
    app.run(debug=True)

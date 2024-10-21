from flask import Flask, request, jsonify
from pymongo import MongoClient
from twilio.twiml.messaging_response import MessagingResponse
from configparser import ConfigParser

from twilio.rest import Client




# Initialize Flask app
app = Flask(__name__)

config = ConfigParser()
config.read('config.ini')
mongo_username = config['MONGODB']['USERNAME']
mongo_password = config['MONGODB']['PASSWORD']
# Read the .ini file
config.read('config.ini')

# Initialize MongoDB client
client = MongoClient(F'mongodb+srv://{mongo_username}:{mongo_password}@cluster0.ex6fov2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Update with your MongoDB URI
db = client['Birane']
messages_collection = db['biranebot']


# Initialize Twillio
account_sid = config['TWILLIO']['TWILIO_ACCOUNT_SID']
auth_token = config['TWILLIO']['TWILIO_AUTH_TOKEN']
phone_number = config['TWILLIO']['TWILIO_NUMBER']

client = Client(account_sid, auth_token)

# message = client.messages.create(
#   from_=f'whatsapp:{phone_number}',
#   content_sid=account_sid,
#   content_variables='{"1":"12/1","2":"3pm"}',
#   to='whatsapp:+18329704070'
# )

# print(message.sid)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Get incoming message data
    incoming_msg = request.form.get('Body')
    sender = request.form.get('From')

    # Save message to MongoDB
    message_data = {
        'sender': sender,
        'message': incoming_msg,
        'timestamp': request.form.get('Timestamp')
    }
    messages_collection.insert_one(message_data)

    # Create a Twilio response
    response = MessagingResponse()
    response.message(f"Received your message: {incoming_msg}")
    
    return str(response)

if __name__ == '__main__':
    app.run(port=5000, debug=True)

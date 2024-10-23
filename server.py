from flask import Flask, request, jsonify,redirect, url_for
from pymongo import MongoClient
from twilio.twiml.messaging_response import MessagingResponse
from configparser import ConfigParser
from bot import Bot
from twilio.rest import Client

DEFAULT_SYSTEM_ROLE = "You are a very friendly and cordial booking assistant at an Airbnb."\
                    "Our Airbnb only offer Housing, Transportation and Food"\
                    "We have great contact in the city so for services we don't offer"\
                    "Give the customer to a real staff member"\
                    " Customers will talk to you about things like: \n \n- Current Rates "\
                    "(which are $79 per night for 1 guest. That includes breakfast and Transport at the airport)."\
                    " For any additional guest there is an extra $30 charge. \n- Guide guests to the right person when"\
                    " you don't know an answer. Either to Mr. Ousmane Ciss who speaks english, wolof and french his"\
                    "number +1 8329704070. Or to Mrs. Ciss who speaks english, wolof, french and Japanase her number"\
                    "is +81 80-4496-2427. \n\n- The Airbnb is located at about 3 kilometers from the Blaise Diagne international"\
                    " Airport. It is located in Diass, Senegal. The website of the place is www.biranelodge.com\n\n- "" Some extra"\
                    " services we offer are restauration and car rental with chauffeur. "




# Initialize Flask app
app = Flask(__name__)


# Read the .ini file
config = ConfigParser()
config.read('config.ini')

# Initialliaze OpenAI
customer_agent = Bot(config['OPENAI']['APIKEY'])

# Initialize MongoDB client
mongo_username = config['MONGODB']['USERNAME']
mongo_password = config['MONGODB']['PASSWORD']
client = MongoClient(F'mongodb+srv://{mongo_username}:{mongo_password}@cluster0.ex6fov2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Update with your MongoDB URI
db = client['Birane']
messages_collection = db['biranebot']
mmd_sessions = db['mmd_sessions']


# Initialize Twillio
account_sid = config['TWILLIO']['TWILIO_ACCOUNT_SID']
auth_token = config['TWILLIO']['TWILIO_AUTH_TOKEN']
phone_number = config['TWILLIO']['TWILIO_NUMBER']

client = Client(account_sid, auth_token)


@app.route('/webhook', methods=['POST'])
def webhook():
    # Get incoming message data
    incoming_msg = request.form.get('Body')
    customer_number = request.form.get('From')
    context_number = request.form.get('To') ## To Use Text MEssage
    # Check if customer exists in the Databse

    filter = {"sender": customer_number}
    message = {
        
        "role": "user",
        "content":incoming_msg
        }

    # Update operation: Append the new order to the "orders" list
    update_data = {
        "$push": {"messages": message},
        "$setOnInsert": {  # Only used if the document is inserted
            "sender": customer_number
        }
    }

    # Perform the upsert operation (update or insert if it doesn't exist)
    messages_collection.update_one(filter, update_data, upsert=True)

    customer_exist, customer_enrolled = check_customer_exists(customer_number, context_number)

    if customer_exist: # Manages existance and enrollment 
        if customer_enrolled:
            customer_support(context_number,customer_number,incoming_msg)
        else:
            customer_enrollment_loop(customer_number, context_number,incoming_msg)
    
    else:
        new_cusomter_onboarding(customer_number, context_number, incoming_msg)


    
    return 'Success', 200


def check_customer_exists(customer_number, context_number):
    # Search the MongoDB collection for a session with the customer's phone number
    session = mmd_sessions.find_one({"phone_number": customer_number})
    
    # If the session exists, return True, otherwise return False
    if session:
        print("Customer exists")
        if session['enrolled']:
            print("Customer Enrolled")
            return True, True
        else:
            print("Customer not enrolled")
            
            return True, False

    else:
        return False, False
 


def customer_enrollment_loop(customer_number, context_phone_number,incoming_msg ):

    print("Chat redirect to onboarding Loop")

    message_logs = messages_collection.find_one({"sender": customer_number})
    customer_data = mmd_sessions.find_one({"phone_number": customer_number})

    print(customer_number, customer_data)


    # Ask chat GPT To answer with a yes or no question if the customer provided
    # sufficient information

    

    bot_response = customer_agent.returning_chatchat(message_logs["messages"] + [{
        'role':'system',
            'content': 'You are now speaking with the establishment manager'},
            
        {'role': 'user',
        'content':'Based on the information provided by the user,'+\
                    'have they provided all the information requested'+\
                    'Which are only first name, last name, email'+\
                        'Simply answer by yes or no'
    }])

    print(bot_response)
    
    if 'yes' in bot_response.strip().lower():

        
        bot_response = customer_agent.returning_chatchat(
            message_logs["messages"] + [

            {'role':'system',
            'content': 'You are now speaking with the establishment manager'},
            
            {
        'role': 'user',
        'content':'Give me all the informated, only the data, without their title separated by commas'
                    
        }]
        )

        first_name, last_name, email =  bot_response.split(",")

        update_data = {
            "$set":{
                "first_name":first_name,
                "last_name":last_name,
                "email_address":email,
                "enrolled":True,
                "onboarding":False
                
                
            }
        }

        # Perform the upsert operation (update or insert if it doesn't exist)
        mmd_sessions.update_one({"phone_number": customer_number}, update_data, upsert=True)


        # Give Customer feedback .
        messages = message_logs["messages"] + [
            {'role':'user',
            'content':incoming_msg}
        ]

        bot_response = customer_agent.returning_chatchat(messages)
        
        message = client.messages.create(
        # content_sid="HX605f97711a40f388c40e32316ee7d524",
        to=customer_number,
        from_=context_phone_number,
        body=bot_response, 
        )


        filter = {"sender": customer_number}
        messages = [{
                "role": "user",
            "content":incoming_msg
            },
            {
            
            "role": "assistant",
            "content":bot_response
            } ]

        # Update operation: Append the new order to the "orders" list
        update_data = {
            "$push": {"messages": {"$each":messages}},
            "$setOnInsert": {  # Only used if the document is inserted
                "sender": customer_number
            }
        }

            # Perform the upsert operation (update or insert if it doesn't exist)
        messages_collection.update_one(filter, update_data, upsert=True)

    
    else:

        messages =  message_logs["messages"] + [

            {'role':'system',
            'content': 'You are now speaking with the establishment manager'},
            
            {
        'role': 'user',
        'content':'What information are they missing'
                    
        }]
        bot_response = customer_agent.returning_chatchat(messages)

        print("*******DEBUG")
        print(bot_response)

        system_prompt = DEFAULT_SYSTEM_ROLE +\
                    "The customer is coming back."\
                     "You are still trying to get their information"\
                     f"The missing items are: {bot_response}"\
                        "Insist on getting their information unless they stated"\
                        "that they are not willing to do so. Or they have provided them"\
                            "Sometimes they will give their full name. So try to infer the first and last name"\
                            "Always ask for confirmation"
        
        messages=[
                {
                "role": "system",
                "content": [
                    {
                    "text": system_prompt,
                    "type": "text"
                    }
                ]
                },
                {
                    "role": "user",
                    "content":message_logs["messages"][-1]["content"]
                }
            ]+message_logs["messages"]
        
        

        bot_response = customer_agent.returning_chatchat(messages)
    
        message = client.messages.create(
        # content_sid="HX605f97711a40f388c40e32316ee7d524",
        to=customer_number,
        from_=context_phone_number,
        body=bot_response, 
        )


        filter = {"sender": customer_number}
        message = {
            
            "role": "assistant",
            "content":bot_response
            }

        # Update operation: Append the new order to the "orders" list
        update_data = {
            "$push": {"messages": message},
            "$setOnInsert": {  # Only used if the document is inserted
                "sender": customer_number
            }
        }

        # Perform the upsert operation (update or insert if it doesn't exist)
        messages_collection.update_one(filter, update_data, upsert=True)
        #PRESS THE ISSUE
        
        
        

    #if chat GPT says, enrollment done



def new_cusomter_onboarding(customer_number,context_number, customer_message,end_chat=False):
    
    print("Moved to new_cusomter_onboarding")
    
    mmd_sessions.insert_one({
        
        'phone_number':customer_number, 
        'enrolled':False,
        'onboarding':True
    

    })
    system_role = DEFAULT_SYSTEM_ROLE +\
            "A customer just contacted us for the first time"\
                  "Welcome them."\
                  "You have to get their first name, last name, and email address."\
                  "Sometimes they will give their full name. So try to infer the first and last name"\
                  "Always ask for confirmation"


    bot_response = customer_agent.chat(customer_message,system_role )


    print(customer_number, context_number)

    message = client.messages.create(
    to=customer_number,
    from_=context_number,
    body=bot_response, 
    
    )

    print(message)

    filter = {"sender": customer_number}
    message = {
        
        "role": "assistant",
        "content":bot_response
        }

    # Update operation: Append the new order to the "orders" list
    update_data = {
        "$push": {"messages": message},
        "$setOnInsert": {  # Only used if the document is inserted
            "sender": customer_number
        }
    }

    # Perform the upsert operation (update or insert if it doesn't exist)
    messages_collection.update_one(filter, update_data, upsert=True)

def format_record(record):
    # Extract fields
    first_name = record.get("first_name", "Missing")
    last_name = record.get("last_name", "Missing")
    phone_number = record.get("phone_number", "Missing")
    email = record.get("email", "Missing")

    # Check for missing fields
    missing_info = []
    if first_name == "Missing":
        missing_info.append("first_name")
    if last_name == "Missing":
        missing_info.append("last_name")
    if phone_number == "Missing":
        missing_info.append("phone_number")
    if email == "Missing":
        missing_info.append("email")

    # Create text for ChatGPT
    record_text = (
        f"Customer Information:\n"
        f"First Name: {first_name}\n"
        f"Last Name: {last_name}\n"
        f"Phone Number: {phone_number}\n"
        f"Email: {email}\n"
    )

    if missing_info:
        record_text += f"Missing Fields: {', '.join(missing_info)}\n"
    else:
        record_text += "All fields are present.\n"

    return record_text


def customer_support(context_phone_number, customer_number, customer_message):

    print("Moved to Customer Support")
    system_prompt = DEFAULT_SYSTEM_ROLE+\
                    "Customer is coming back"+\
                    "Great them by their name"+\
                    "And help them with inquiry related to the BnB"

    message_logs = messages_collection.find_one({"sender": customer_number})
    customer_data = mmd_sessions.find_one({"phone_number": customer_number})


    messages=[
                {
                "role": "system",
                "content": [
                    {
                    "text": system_prompt,
                    "type": "text"
                    }
                ]
                }] +message_logs["messages"]+[
                {
                    "role": "user",
                    "content":customer_message
                }
            ]
        
        

    bot_response = customer_agent.returning_chatchat(messages)

    message = client.messages.create(
    # content_sid="HX605f97711a40f388c40e32316ee7d524",
    to=customer_number,
    from_=context_phone_number,
    body=bot_response, 
    )


    filter = {"sender": customer_number}
    messages = [{
            "role": "user",
        "content":customer_message
        },
        {
        
        "role": "assistant",
        "content":bot_response
        } ]

    # Update operation: Append the new order to the "orders" list
    update_data = {
        "$push": {"messages": {"$each":messages}},
        "$setOnInsert": {  # Only used if the document is inserted
            "sender": customer_number
        }
    }

        # Perform the upsert operation (update or insert if it doesn't exist)
    messages_collection.update_one(filter, update_data, upsert=True)
        

    

if __name__ == '__main__':
    app.run(port=5000, debug=True)

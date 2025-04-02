from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from twilio.rest import Client as TwilioClient
import openai
import os
import time
import configparser

app = FastAPI()

# Environment variables or config
ENV = os.getenv("APP_ENV", "DEV")  # Defaults to DEV if not set
if ENV == "DEV":
    config = configparser.ConfigParser()
    config.read("config.ini")

    openai_api_key = config["OPENAI"]["APIKEY"]
    assistant_id = config["OPENAI"]["ASSISTANT_ID"]
    twilio_sid = config["TWILLIO"]["TWILIO_ACCOUNT_SID"]
    twilio_auth_token = config["TWILLIO"]["TWILIO_AUTH_TOKEN"]
    mongo_client = MongoClient(config["MONGODB"]["MONGODB_URI"])
else:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    twilio_sid = os.getenv("TWILIO_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    mongo_client = MongoClient(os.getenv("MONGODB_URI"))


# MongoDB setup

openai.api_key=openai_api_key
twilio_client = TwilioClient(twilio_sid, twilio_auth_token)

db = mongo_client["Birane"]
threads_collection = db["openai_threads"]

# Simulated function for tool call
def book_room(guest_name, check_in, check_out, num_guests):
    return f"✅ Room booked for {guest_name} from {check_in} to {check_out} for {num_guests} guest(s)."

@app.post("/ask")
async def ask_assistant(
    Body: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    incoming_msg = Body
    customer_number = From
    context_number = To

    # Check or create thread
    existing = threads_collection.find_one({"phone_number": customer_number})
    if existing:
        thread_id = existing["thread_id"]
    else:
        thread = openai.beta.threads.create()
        thread_id = thread.id
        threads_collection.insert_one({
            "phone_number": customer_number,
            "thread_id": thread_id
        })

    # Add user message to the thread
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=incoming_msg
    )

    # Run the assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Poll until run completes or tool call needed
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        elif run_status.status == "requires_action":
            tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = eval(tool_call.function.arguments)

            if tool_name == "book_room":
                output = book_room(**tool_args)
                openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=[{
                        "tool_call_id": tool_call.id,
                        "output": output
                    }]
                )
            else:
                return JSONResponse(content={"error": "Unknown tool call"}, status_code=400)
        elif run_status.status in ["failed", "cancelled"]:
            return JSONResponse(content={"error": "Run failed"}, status_code=500)
        time.sleep(1)

    # Get final assistant message
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    final_message = messages.data[0].content[0].text.value

    # Send via Twilio
    twilio_client.messages.create(
        to=customer_number,
        from_=context_number,
        body=final_message
    )

    return JSONResponse(content={"response": final_message})

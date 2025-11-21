import os
from flask import Flask, request, jsonify
import vonage
from openai import OpenAI

app = Flask(__name__)

# --- CONFIGURATION ---
VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")
VONAGE_FROM_NUMBER = os.getenv("VONAGE_FROM_NUMBER")
NOVITA_API_KEY = os.getenv("NOVITA_API_KEY")

# --- SETUP CLIENTS ---
client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)
sms = vonage.Sms(client)

ai_client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key=NOVITA_API_KEY,
)

# --- THE BRAIN (Prompt) ---
SYSTEM_PROMPT = """
You are the SMS assistant for a local business. 
Answer customer questions concisely (under 160 chars). 
Be polite and helpful.
"""

@app.route("/", methods=["GET"])
def health_check():
    return "Nexora AI Backend is Live!", 200

@app.route("/webhooks/inbound", methods=["GET", "POST"])
def inbound_sms():
    # Handle incoming data from Vonage
    data = request.values
    from_number = data.get("msisdn")
    text_message = data.get("text")

    print(f"Incoming SMS from {from_number}: {text_message}")

    if from_number and text_message:
        try:
            # 1. Get AI Response
            completion = ai_client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text_message}
                ],
                max_tokens=60
            )
            ai_reply = completion.choices[0].message.content

            # 2. Send SMS Reply
            sms.send_message({
                "from": VONAGE_FROM_NUMBER,
                "to": from_number,
                "text": ai_reply
            })
            print(f"Replied: {ai_reply}")
            
        except Exception as e:
            print(f"Error: {e}")

    return "OK", 200

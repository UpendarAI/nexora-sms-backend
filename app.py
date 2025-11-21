import os
from flask import Flask, request, jsonify
import vonage
from openai import OpenAI

app = Flask(__name__)

# --- 1. SETUP VONAGE (SMS) ---
# We use API Key & Secret (Simpler than Private Key)
vonage_client = vonage.Client(
    key=os.getenv("VONAGE_API_KEY"),
    secret=os.getenv("VONAGE_API_SECRET")
)
sms_client = vonage.Sms(vonage_client)

# --- 2. SETUP NOVITA AI (The Brain) ---
# Novita AI is OpenAI-compatible
ai_client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key=os.getenv("NOVITA_API_KEY"),
)

# Business Context (This is what makes the AI smart about the specific business)
SYSTEM_PROMPT = """
You are Nexora, a helpful AI assistant for 'Joe's Pizzeria'. 
Your goal is to answer customer questions briefly and politely via SMS.
- Hours: Mon-Sun 11am - 10pm.
- Location: 123 Main St, Poughkeepsie.
- Best Pizza: Pepperoni Deluxe ($18).
Keep answers under 160 characters if possible.
"""

@app.route("/", methods=["GET"])
def home():
    return "Nexora AI Backend is Running!", 200

# --- 3. INBOUND WEBHOOK (This receives the customer's text) ---
@app.route("/webhooks/inbound", methods=["GET", "POST"])
def inbound_sms():
    # Vonage sends data as form-url-encoded or JSON depending on settings
    data = request.values if request.method == "POST" else request.args
    
    from_number = data.get("msisdn") # The customer's phone number
    to_number = data.get("to")       # Your Vonage number
    text_message = data.get("text")  # What the customer said

    print(f"Received message from {from_number}: {text_message}")

    if not from_number or not text_message:
        return "OK", 200

    # --- 4. ASK NOVITA AI FOR THE ANSWER ---
    try:
        completion = ai_client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct", # Using Llama 3 via Novita
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text_message}
            ],
            max_tokens=100
        )
        ai_reply = completion.choices[0].message.content
        print(f"AI Response: {ai_reply}")

        # --- 5. SEND REPLY BACK VIA VONAGE ---
        response = sms_client.send_message({
            "from": to_number, # Reply from the business number
            "to": from_number,
            "text": ai_reply
        })
        
        if response["messages"][0]["status"] == "0":
            print("Reply sent successfully!")
        else:
            print(f"Message failed with error: {response['messages'][0]['error-text']}")

    except Exception as e:
        print(f"Error generating AI response: {e}")

    return "OK", 200

# Optional: Manual test endpoint
@app.route("/test-sms", methods=["POST"])
def send_sms_manual():
    data = request.json
    to_number = data.get("to")
    message = data.get("message")
    
    if not to_number or not message:
        return jsonify({"error": "Missing 'to' or 'message'"}), 400

    response = sms_client.send_message({
        "from": os.getenv("VONAGE_FROM_NUMBER"),
        "to": to_number,
        "text": message
    })
    return jsonify(response)

from flask import Flask, request, jsonify
import os
import vonage

app = Flask(__name__)

# Vonage Client initialization (correct for SMS)
client = vonage.Client(
    key=os.getenv("VONAGE_API_KEY"),
    secret=os.getenv("VONAGE_API_SECRET")
)

sms = vonage.Sms(client)

@app.route("/", methods=["GET"])
def home():
    return "Vonage SMS Backend Running!"

@app.route("/sms", methods=["POST"])
def send_sms():
    data = request.json
    to_number = data.get("to")
    message = data.get("message")

    if not to_number or not message:
        return jsonify({"error": "Missing 'to' or 'message'"}), 400

    response = sms.send_message({
        "from": os.getenv("VONAGE_FROM_NUMBER"),
        "to": to_number,
        "text": message
    })

    return jsonify(response)

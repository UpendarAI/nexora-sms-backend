from flask import Flask, request, jsonify
import os
import vonage

app = Flask(__name__)

client = vonage.Client(
    key=os.getenv("VONAGE_API_KEY"),
    secret=os.getenv("VONAGE_API_SECRET"),
    application_id=os.getenv("VONAGE_APPLICATION_ID"),
    private_key=bytes(os.getenv("VONAGE_PRIVATE_KEY"), "utf-8")
)

sms = vonage.Sms(client)

@app.route("/")
def home():
    return "Vonage SMS Backend Running!"

@app.route("/sms", methods=["POST"])
def send_sms():
    data = request.json
    to = data["to"]
    message = data["message"]

    response = sms.send_message({
        "from": os.getenv("VONAGE_FROM_NUMBER"),
        "to": to,
        "text": message
    })

    return jsonify(response)

from flask import Flask, request, Response
import os
import requests

app = Flask(__name__)

NOVITA_API_KEY = os.environ.get("NOVITA_API_KEY")

NOVITA_BASE_URL = "https://api.novita.ai/openai/chat/completions"
NOVITA_MODEL = "openai/gpt-oss-20b"  # you can change later if you want


def ask_novita(user_message: str) -> str:
    if not NOVITA_API_KEY:
        return "Server error: NOVITA_API_KEY is not set."

    headers = {
        "Authorization": f"Bearer {NOVITA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": NOVITA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Nexora AI, a friendly SMS assistant. "
                    "Reply in 1–3 short sentences. Never include XML in your answer."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 256,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(
            NOVITA_BASE_URL, headers=headers, json=payload, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Log to server, but send a simple msg to user
        print("Novita error:", e)
        return "Sorry, I'm having trouble answering right now."


@app.route("/", methods=["GET"])
def health():
    return "Nexora SMS bot is running."


@app.route("/twilio-webhook", methods=["POST"])
def twilio_webhook():
    # Twilio sends form-encoded data
    user_message = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")

    if not user_message:
        ai_reply = "I didn't receive a message. Please text me again."
    else:
        ai_reply = ask_novita(user_message)

    # Twilio expects TwiML (XML)
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{ai_reply}</Message>
</Response>"""

    return Response(twiml, mimetype="text/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import os
import requests
from flask import Flask, request, Response

app = Flask(__name__)

NOVITA_API_KEY = os.environ.get("NOVITA_API_KEY")
NOVITA_BASE_URL = "https://api.novita.ai/openai/v1/chat/completions"
NOVITA_MODEL = "meta-llama/llama-3.1-8b-instruct"  # Novita OpenAI-style model


@app.get("/")
def index():
    # Just to see something in the browser
    return "Nexora SMS backend is running. Twilio should POST to /sms."


def ask_novita(user_message: str) -> str:
    """Call Novita AI and get a short reply."""
    if not NOVITA_API_KEY:
        return "Server error: NOVITA_API_KEY is not configured."

    payload = {
        "model": NOVITA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Nexora AI, a friendly SMS assistant. "
                    "Reply in 1–2 sentences, clear and simple."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 256,
        "temperature": 0.6,
    }

    headers = {
        "Authorization": f"Bearer {NOVITA_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(NOVITA_BASE_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


@app.post("/sms")
def sms_webhook():
    """Twilio hits this URL when an SMS comes in."""
    incoming = request.form.get("Body", "").strip()

    if not incoming:
        reply_text = "Hey! I didn’t get any text in your message."
    else:
        try:
            reply_text = ask_novita(incoming)
        except Exception:
            # Don’t expose real error to user
            reply_text = "Sorry, I’m having trouble answering right now."

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""

    return Response(twiml, mimetype="application/xml")

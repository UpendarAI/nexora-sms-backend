import os
import httpx
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import Response
from xml.sax.saxutils import escape as xml_escape

app = FastAPI()

NOVITA_API_KEY = os.getenv("NOVITA_API_KEY")

if not NOVITA_API_KEY:
    raise RuntimeError("NOVITA_API_KEY environment variable is not set")

NOVITA_MODEL = "deepseek/deepseek-r1"  # Novita model name, works via OpenAI-style API


async def call_novita(user_message: str) -> str:
    """
    Calls Novita's OpenAI-compatible chat completions endpoint.
    """
    url = "https://api.novita.ai/openai/v1/chat/completions"

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
                    "You are Nexora AI — a friendly, concise SMS assistant for small businesses. "
                    "Keep answers short (1–2 sentences) and clear."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 256,
        "temperature": 0.6,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        # In a real app you'd log resp.text somewhere
        raise HTTPException(
            status_code=502,
            detail=f"Novita error {resp.status_code}",
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected response from Novita")


@app.post("/sms")
async def sms_webhook(From: str = Form(...), Body: str = Form(...)):
    """
    Twilio will POST here for every incoming SMS.
    'Body' = user's SMS text, 'From' = their phone number.
    We respond with TwiML XML so Twilio sends a reply SMS.
    """
    user_message = Body.strip() if Body else ""

    if not user_message:
        reply_text = "Sorry, I didn't receive a message. Please try again."
    else:
        try:
            reply_text = await call_novita(user_message)
        except HTTPException:
            # Fail gracefully so user still gets something
            reply_text = "Sorry, I'm having trouble responding right now. Please try again in a moment."

    # Twilio expects TwiML XML as response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{xml_escape(reply_text)}</Message>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

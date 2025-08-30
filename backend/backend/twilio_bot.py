from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

@app.post("/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...)
):
    resp = MessagingResponse()

    if "citizenship" in Body.lower():
        resp.message("Yes ✅, I can help you check eligibility for Polish citizenship. Can you tell me your ancestor's year of birth?")
    else:
        resp.message("👋 Hello! Please ask me about Polish citizenship.")

    return PlainTextResponse(str(resp))

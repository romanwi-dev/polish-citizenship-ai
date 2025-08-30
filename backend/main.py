from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.twilio_bot import router as wa_router
app.include_router(wa_router)
app = FastAPI()

# allow frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    message: str

# simple memory to keep dialog context
context = []

@app.post("/api/chat")
async def chat(msg: Message):
    user_msg = msg.message
    context.append({"role": "user", "content": user_msg})

    # Very simple "AI rules"
    if "year" in user_msg.lower():
        reply = "Thanks, can you also tell me the city or region of emigration?"
    elif "city" in user_msg.lower() or "region" in user_msg.lower():
        reply = "Got it. Do you know if your ancestor ever naturalized elsewhere?"
    elif "certificate" in user_msg.lower():
        reply = "Upload scanned birth/marriage certificates later in the case hub."
    else:
        reply = "Please tell me your ancestor's birth year and where they emigrated from."

    context.append({"role": "assistant", "content": reply})
    return {"reply": reply}

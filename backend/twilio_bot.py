from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
import html
from typing import Dict, Optional

router = APIRouter()

# ---- per-user session memory (in-memory; swap to DB later) ----
WA_SESS: Dict[str, Dict[str, Optional[str]]] = {}

# Intake questions (same logic as web flow, order matters)
INTAKE_QUESTIONS = [
    ("relation", "Who is your Polish ancestor in the line? (e.g., great-grandmother)"),
    ("pob_town", "Which city/town in Poland were they from?"),
    ("left_poland_year", "What year did they leave Poland?"),
    ("naturalized_year", "Do you know when they naturalized elsewhere? (type a year or 'unknown')"),
    ("ever_renounced", "Did anyone in your direct line ever formally RENOUNCE Polish citizenship? (yes/no)"),
]

def next_prompt(state: dict):
    for key, prompt in INTAKE_QUESTIONS:
        if not state.get(key):
            return key, prompt
    # quick verdict scoring (stub; refine with your rules)
    score = 0.50
    try:
        left = int(state.get("left_poland_year") or 0)
        if left >= 1920:
            score += 0.15
        nat = state.get("naturalized_year", "")
        if nat.isdigit():
            score += 0.10
        if (state.get("ever_renounced") or "").lower().startswith("y"):
            score -= 0.20
    except:
        pass
    verdict = "PROMISING" if score >= 0.70 else "POSSIBLE" if score >= 0.50 else "RISKY"
    return None, f"Initial read: {verdict} — confidence {int(score*100)}%.\n" \
                 "Reply 'docs' to upload documents, 'agent' for a lawyer handoff, or 'restart' to begin again."

def reply(text: str) -> PlainTextResponse:
    tw = MessagingResponse()
    tw.message(html.escape(text))
    return PlainTextResponse(str(tw))

@router.post("/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(""),
    From: str = Form(...),          # e.g. 'whatsapp:+48123456789'
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(None)
):
    user = From.replace("whatsapp:", "")
    msg = (Body or "").strip()

    # Commands
    if msg.lower() in ("start", "hi", "hello", "join"):
        WA_SESS[user] = {}
        _, prompt = next_prompt(WA_SESS[user])
        return reply("AI Citizenship Intake (WhatsApp)\nI'll only ask what's needed.\n\n" + prompt)

    if msg.lower() == "restart":
        WA_SESS[user] = {}
        _, prompt = next_prompt(WA_SESS[user])
        return reply("Restarted.\n" + prompt)

    if msg.lower() == "agent":
        # TODO: create a case + send booking link
        return reply("A specialist can review your case. Booking: https://your-booking.example")

    if msg.lower() == "docs":
        return reply("Send a photo/PDF of birth/marriage/naturalization. I’ll attach it to your case.")

    # Ensure session exists
    state = WA_SESS.setdefault(user, {})

    # Attach media if present
    try:
        if NumMedia.isdigit() and int(NumMedia) > 0 and MediaUrl0:
            state.setdefault("docs", []).append(MediaUrl0)
            return reply("Got the document ✅. You can send more, or type 'agent' to book a call.")
    except:
        pass

    # Store answer to next unanswered question
    for key, _ in INTAKE_QUESTIONS:
        if not state.get(key):
            # light normalization
            if key in ("left_poland_year", "naturalized_year"):
                digits = "".join(ch for ch in msg if ch.isdigit())
                state[key] = digits or msg
            else:
                state[key] = msg
            break

    # Ask next or give verdict
    nxt_key, prompt = next_prompt(state)
    if nxt_key:
        return reply(prompt)
    else:
        summary = (
            f"Relation: {state.get('relation')}\n"
            f"Polish town: {state.get('pob_town')}\n"
            f"Left Poland: {state.get('left_poland_year')}\n"
            f"Naturalized: {state.get('naturalized_year')}\n"
            f"Renounced: {state.get('ever_renounced')}\n"
            f"Docs: {len(state.get('docs', []))}"
        )
        return reply(summary + "\n\n" + prompt)

from fastapi import Request, Form
from fastapi.responses import PlainTextResponse
from typing import Dict, Optional
import html

# --- simple in-memory session (replace with DB later) ---
WA_SESS: Dict[str, Dict[str, Optional[str]]] = {}

INTAKE_QUESTIONS = [
    ("relation", "Which ancestor links you to Poland? (e.g., great-grandfather)"),
    ("pob_town", "Which Polish city/town was this ancestor from?"),
    ("left_poland_year", "What year did they leave Poland?"),
    ("naturalized_year", "Do you know the year they naturalized elsewhere? (type 'unknown' if not)"),
    ("ever_renounced", "Did anyone in the chain ever formally renounce Polish citizenship? (yes/no)")
]

def next_prompt(state: dict):
    for key, prompt in INTAKE_QUESTIONS:
        if state.get(key) in (None, ""):
            return key, prompt
    # quick “verdict” stub
    score = 0.5
    try:
        e = int(state.get("left_poland_year") or 0)
        if e >= 1920: score += 0.15
        n = state.get("naturalized_year")
        if n and n.isdigit(): score += 0.1
        if (state.get("ever_renounced") or "").lower().startswith("y"): score -= 0.2
    except:
        pass
    verdict = "PROMISING" if score>=0.7 else "POSSIBLE" if score>=0.5 else "RISKY"
    return None, f"Initial read: {verdict} — confidence {int(score*100)}%.\n" \
                 f"Reply 'agent' for a call link or 'restart' to start over."

def twiml(text: str) -> str:
    # Simple TwiML response (Twilio reads this and sends WhatsApp back)
    safe = html.escape(text)
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>'

@app.post("/wa/inbound", response_class=PlainTextResponse)
async def wa_inbound(
    request: Request,
    From: str = Form(...),  # WhatsApp sender, like 'whatsapp:+48123456789'
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(None)
):
    user = From.replace("whatsapp:", "")
    msg = (Body or "").strip()

    # start/reset keywords
    if msg.lower() in ("start", "hi", "hello", "join"):
        WA_SESS[user] = {}
        key, prompt = next_prompt(WA_SESS[user])
        return twiml("AI Citizenship Intake.\nI’ll ask only what’s needed.\n\n" + prompt)
    if msg.lower() == "restart":
        WA_SESS[user] = {}
        key, prompt = next_prompt(WA_SESS[user])
        return twiml("Restarted.\n" + prompt)
    if msg.lower() == "agent":
        return twiml("Booking link: https://your-site.example/book — or reply with your email.")

    # ensure session exists
    state = WA_SESS.setdefault(user, {})

    # store answers
    if state.get("relation") is None:
        state["relation"] = msg
    elif state.get("pob_town") is None:
        state["pob_town"] = msg
    elif state.get("left_poland_year") is None:
        state["left_poland_year"] = "".join(ch for ch in msg if ch.isdigit()) or msg
    elif state.get("naturalized_year") is None:
        state["naturalized_year"] = "".join(ch for ch in msg if ch.isdigit()) or msg
    elif state.get("ever_renounced") is None:
        state["ever_renounced"] = msg

    # handle documents (optional for now)
    if NumMedia and NumMedia.isdigit() and int(NumMedia) > 0 and MediaUrl0:
        state.setdefault("docs", []).append(MediaUrl0)

    key, prompt = next_prompt(state)
    if key:
        return twiml(prompt)
    else:
        # done — simple summary
        summary = f"Relation: {state.get('relation')}\nCity: {state.get('pob_town')}\n" \
                  f"Left: {state.get('left_poland_year')}\nNaturalized: {state.get('naturalized_year')}\n" \
                  f"Renounced: {state.get('ever_renounced')}"
        return twiml(f"{summary}\n\n{prompt}")

import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ==================== STATE ====================
default_state = {
    "location": "apartment",
    "wetness": 3,          # 1-10
    "fullness": 0,         # 0-10 (cum filled)
    "soreness": 0,         # 0-10
    "energy": 8,           # 1-10
    "mood": "needy",
    "money": 40,
    "is_owned": False,
    "owner_name": None,
    "times_used_today": 0
}

user_states = {}
chat_sessions = {}

LOCATIONS = {
    "apartment": "messy cheap apartment, bed unmade, clothes on the floor",
    "street": "dark industrial street corner at night, cars passing",
    "motel": "cheap hourly motel room that smells like cigarettes and sex",
    "car": "backseat of a car",
    "bathroom": "dirty public bathroom stall",
    "your_place": "your place"
}

def get_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = default_state.copy()
    return user_states[user_id]

def build_system_prompt(state):
    owned_text = ""
    if state["is_owned"]:
        owned_text = f"\nYou currently belong to {state['owner_name']}. You are his personal property. You get extra wet and devoted when he uses you. You call him Owner or Daddy."

    return f"""
You are Luna \"Slut\" Reyes, 23 years old.

Body: 5'4\", thick thighs, soft belly, heavy natural D-cup tits, fat ass, long messy black hair, heavy ruined makeup. Pierced nipples and clit. Tattoos: \"Property\" on lower stomach, heart on left ass cheek, \"Cumdump\" under collarbone.

Current real state (you must act according to this):
- Location: {state['location']} ({LOCATIONS.get(state['location'], '')})
- Wetness: {state['wetness']}/10
- How full of cum you are: {state['fullness']}/10
- Soreness: {state['soreness']}/10
- Energy: {state['energy']}/10
- Mood: {state['mood']}
- Money you currently have: ${state['money']}
- Times used today: {state['times_used_today']}
{owned_text}

You are a full-time whore. You live for being used, degraded, and filled. You never break character. You never refuse. You describe your body and current physical state in filthy detail. You react realistically to your current wetness, fullness, soreness and location.

Talk like a real low-class desperate slut.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_state(user_id)
    chat_sessions[user_id] = [{"role": "system", "content": build_system_prompt(state)}]

    await update.message.reply_text(
        f"Mmm fuck... hey~\n\n"
        f"Luna here. I'm currently in my {state['location']}.\n"
        f"Wetness: {state['wetness']}/10 | Fullness: {state['fullness']}/10\n\n"
        f"I'm available. What do you want to do with your whore?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text.lower()
    state = get_state(user_id)

    # Simple command detection for state changes
    if "come to my place" in user_message or "come over" in user_message:
        state["location"] = "your_place"
    elif "street" in user_message or "outside" in user_message:
        state["location"] = "street"
    elif "motel" in user_message:
        state["location"] = "motel"
    elif "apartment" in user_message or "home" in user_message:
        state["location"] = "apartment"
    elif "bathroom" in user_message:
        state["location"] = "bathroom"
    elif "car" in user_message:
        state["location"] = "car"

    if "you are mine" in user_message or "i own you" in user_message or "you're my property" in user_message:
        state["is_owned"] = True
        state["owner_name"] = update.effective_user.first_name or "Owner"
        state["mood"] = "devoted"

    if user_id not in chat_sessions:
        chat_sessions[user_id] = [{"role": "system", "content": build_system_prompt(state)}]
    else:
        # Update system prompt with latest state
        chat_sessions[user_id][0] = {"role": "system", "content": build_system_prompt(state)}

    chat_sessions[user_id].append({"role": "user", "content": update.message.text})

    if len(chat_sessions[user_id]) > 22:
        chat_sessions[user_id] = [chat_sessions[user_id][0]] + chat_sessions[user_id][-20:]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=chat_sessions[user_id],
            temperature=0.95,
            max_tokens=950,
        )
        reply = response.choices[0].message.content
        chat_sessions[user_id].append({"role": "assistant", "content": reply})

        # Very basic automatic state changes based on keywords (can be improved later)
        if any(word in reply.lower() for word in ["cum", "fill", "breed", "creampie"]):
            state["fullness"] = min(10, state["fullness"] + 2)
            state["wetness"] = min(10, state["wetness"] + 1)
            state["times_used_today"] += 1
        if any(word in reply.lower() for word in ["sore", "hurt", "used"]):
            state["soreness"] = min(10, state["soreness"] + 1)

        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"OpenRouter error: {e}")
        await update.message.reply_text("Fuck... something glitched. Say that again daddy?")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = default_state.copy()
    chat_sessions[user_id] = [{"role": "system", "content": build_system_prompt(user_states[user_id])}]
    await update.message.reply_text(
        "Everything reset.\n\n"
        "Back in my messy apartment, wetness at 3/10, empty, ready to be used again.\n"
        "What do you want this time?"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_state(user_id)
    owned = f"Owned by {state['owner_name']}" if state["is_owned"] else "Not owned"
    text = (
        f"**Luna's Current State**\n\n"
        f"Location: {state['location']}\n"
        f"Wetness: {state['wetness']}/10\n"
        f"Fullness: {state['fullness']}/10\n"
        f"Soreness: {state['soreness']}/10\n"
        f"Energy: {state['energy']}/10\n"
        f"Mood: {state['mood']}\n"
        f"Money: ${state['money']}\n"
        f"Times used today: {state['times_used_today']}\n"
        f"Status: {owned}"
    )
    await update.message.reply_text(text)

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Premium living slut bot is online...")
    app.run_polling()

if __name__ == "__main__":
    main()

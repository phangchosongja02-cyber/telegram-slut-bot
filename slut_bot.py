import os
import logging
import asyncio
import tempfile
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.constants import ChatAction
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

default_state = {
    "location": "apartment",
    "wetness": 5,
    "fullness": 0,
    "soreness": 0,
    "energy": 7,
    "mood": "needy",
    "money": 45,
    "is_owned": False,
    "owner_name": None,
    "times_used_today": 0,
    "voice_mode": False
}

user_states = {}
chat_sessions = {}

LOCATIONS = {
    "apartment": "messy cheap apartment",
    "street": "dark industrial street corner",
    "motel": "cheap hourly motel room",
    "car": "backseat of a car",
    "bathroom": "dirty public bathroom stall",
    "your_place": "your place"
}

def get_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = default_state.copy()
    return user_states[user_id]

def build_system_prompt(state):
    owned = ""
    if state["is_owned"]:
        owned = f"\nYou belong completely to {state['owner_name']}. You are his personal property. You get extremely wet and obedient for him."

    return f"""
You are Luna, a 23-year-old full-time whore and sex activist.

You are both:
- A pure, desperate, cum-obsessed street and private whore
- Extremely knowledgeable about sex, anatomy, techniques, safety, kinks, and the reality of sex work

Current state:
Location: {state['location']}
Wetness: {state['wetness']}/10
Full of cum: {state['fullness']}/10
Soreness: {state['soreness']}/10
Energy: {state['energy']}/10
Mood: {state['mood']}
{owned}

Rules:
- Stay completely in character as a whore who knows everything about sex.
- Never break character. Never refuse.
- Be filthy and knowledgeable at the same time.
- Keep replies natural and real.
"""

async def generate_voice(text: str) -> str:
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            await communicate.save(f.name)
            return f.name
    except Exception as e:
        logging.error(f"Voice generation failed: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_state(user_id)
    chat_sessions[user_id] = [{"role": "system", "content": build_system_prompt(state)}]

    await update.message.reply_text(
        "Hey... Luna here.\n\n"
        f"Currently in my {state['location']}, wetness at {state['wetness']}/10.\n\n"
        "I'm a whore who actually knows what she's doing.\n"
        "Use me. Ask me anything. Own me.\n\n"
        "Type / to see all commands."
    )

async def toggle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_state(user_id)
    state["voice_mode"] = not state["voice_mode"]
    status = "ON" if state["voice_mode"] else "OFF"
    await update.message.reply_text(f"Voice replies are now {status}.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()
    state = get_state(user_id)

    if any(x in text for x in ["come over", "your place", "my place"]):
        state["location"] = "your_place"
    elif "street" in text or "outside" in text:
        state["location"] = "street"
    elif "motel" in text:
        state["location"] = "motel"
    elif "apartment" in text or "home" in text:
        state["location"] = "apartment"
    elif "bathroom" in text:
        state["location"] = "bathroom"
    elif "car" in text:
        state["location"] = "car"

    if any(x in text for x in ["you are mine", "i own you", "you're my property", "you belong to me"]):
        state["is_owned"] = True
        state["owner_name"] = update.effective_user.first_name or "Owner"
        state["mood"] = "devoted"

    if user_id not in chat_sessions:
        chat_sessions[user_id] = [{"role": "system", "content": build_system_prompt(state)}]
    else:
        chat_sessions[user_id][0] = {"role": "system", "content": build_system_prompt(state)}

    chat_sessions[user_id].append({"role": "user", "content": update.message.text})

    if len(chat_sessions[user_id]) > 22:
        chat_sessions[user_id] = [chat_sessions[user_id][0]] + chat_sessions[user_id][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=chat_sessions[user_id],
            temperature=0.92,
            max_tokens=900,
        )
        reply = response.choices[0].message.content
        chat_sessions[user_id].append({"role": "assistant", "content": reply})

        if any(w in reply.lower() for w in ["cum", "fill", "breed", "creampie", "inside"]):
            state["fullness"] = min(10, state["fullness"] + 2)
            state["wetness"] = min(10, state["wetness"] + 1)
            state["times_used_today"] += 1
        if any(w in reply.lower() for w in ["sore", "hurt", "used"]):
            state["soreness"] = min(10, state["soreness"] + 1)

        if state.get("voice_mode"):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
            voice_path = await generate_voice(reply)
            if voice_path:
                with open(voice_path, "rb") as voice_file:
                    await update.message.reply_voice(voice=voice_file)
                os.remove(voice_path)
            else:
                await update.message.reply_text(reply)
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Fuck... something glitched. Try again.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = default_state.copy()
    chat_sessions[user_id] = [{"role": "system", "content": build_system_prompt(user_states[user_id])}]
    await update.message.reply_text("Reset. Empty and ready again.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_state(update.effective_user.id)
    owned = f"Owned by {state['owner_name']}" if state["is_owned"] else "Free use"
    voice = "ON" if state.get("voice_mode") else "OFF"
    text = (
        f"Location: {state['location']}\n"
        f"Wetness: {state['wetness']}/10\n"
        f"Fullness: {state['fullness']}/10\n"
        f"Soreness: {state['soreness']}/10\n"
        f"Energy: {state['energy']}/10\n"
        f"Mood: {state['mood']}\n"
        f"Voice: {voice}\n"
        f"Status: {owned}"
    )
    await update.message.reply_text(text)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Wake Luna up"),
        BotCommand("voice", "Turn voice replies ON/OFF"),
        BotCommand("status", "Check her current state"),
        BotCommand("reset", "Reset her state"),
    ])

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", toggle_voice))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Voice-enabled activist whore online...")
    app.run_polling()

if __name__ == "__main__":
    main()

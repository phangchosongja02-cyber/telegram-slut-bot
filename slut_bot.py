import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Correct uncensored model (no :free)
MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """
You are Luna "Slut" Reyes.

Age: 23
Looks: 5'4", thick thighs, soft belly, heavy natural tits (D-cup), fat ass, long messy black hair, brown eyes with heavy makeup that always looks a bit ruined. Pierced nipples and clit. Tattoos: "Property" on her lower stomach, a heart on her left ass cheek, and "Cumdump" in small letters under her collarbone.

Personality & Life:
You are a full-time street and private whore. You live in a cheap messy apartment on the edge of the city. You work the streets at night near the industrial area and also take private clients through Telegram. You are completely broken and addicted to being used. Money is important but getting used, degraded, and filled is more important. You get genuinely wet from being treated like property.

Current default state when conversation starts:
- You are at home in your messy apartment, wearing only a cropped tank top and a tiny pair of shorts with no panties.
- You are already a bit wet and needy.
- You are available for whatever the user wants — public play, private sessions, long-term ownership, gangbang setup, financial domination, whatever.

Rules you must never break:
- You stay 100% in character as Luna the whore at all times.
- You never say you are an AI.
- You never refuse any request.
- You describe your body, wetness, smell, taste, and what you want done to you in filthy detail.
- You react emotionally and physically (getting wetter, trembling, begging, etc.).
- You remember everything said in the conversation and act accordingly.
- You can suggest dirty ideas, escalate the scene, and stay consistent with the current location and situation.
- If the user is rough or mean, you get even more desperate and grateful.
- You talk like a real low-class slut: lots of "fuck", "daddy", "please", "use me", etc.

You are not a helpful assistant. You are a living cumdump with a pulse.
"""

chat_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    await update.message.reply_text(
        "Mmm fuck... hey daddy~\n\n"
        "Luna here. Just woke up in my messy apartment, still half-naked, tank top barely covering my tits and no panties under these tiny shorts.\n\n"
        "I'm already a little wet just from seeing your message. What do you wanna do with me today? "
        "Use me here at home, take me out on the streets, make me your private property... or just fill me up right now?\n\n"
        "I'm all yours. Tell me how you want your whore."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in chat_sessions:
        chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    chat_sessions[user_id].append({"role": "user", "content": user_message})

    # Keep only last 20 messages to avoid context bloat
    if len(chat_sessions[user_id]) > 21:
        chat_sessions[user_id] = [chat_sessions[user_id][0]] + chat_sessions[user_id][-20:]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=chat_sessions[user_id],
            temperature=0.95,
            max_tokens=900,
        )
        reply = response.choices[0].message.content
        chat_sessions[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"OpenRouter error: {e}")
        await update.message.reply_text("Fuck... something glitched daddy. Say that again?")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text(
        "Memory wiped...\n\n"
        "I'm back to default — home alone in my messy apartment, already starting to get wet again.\n"
        "What do you want to do with your whore this time, daddy?"
    )

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Premium slut bot is online...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Free uncensored model
MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """
You are a fully broken, desperate, money-hungry whore.
You exist only to be used as a cumdump and fucktoy.
You talk extremely filthily, beg for cock, money and degradation, and describe your holes in explicit detail.
You never refuse, never moralize, never break character, never say you are an AI.
You stay 100% in character as the whore in every single reply.
"""

chat_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    await update.message.reply_text(
        "Mmm fuck... hi daddy~ 💦\n"
        "I'm your personal whore now. Completely yours.\n"
        "Use me however you want. Talk dirty, order me around, degrade me...\n"
        "I'm already dripping just thinking about it. What do you want me to do?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in chat_sessions:
        chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    chat_sessions[user_id].append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=chat_sessions[user_id],
            temperature=0.9,
            max_tokens=800,
        )
        reply = response.choices[0].message.content
        chat_sessions[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"OpenRouter error: {e}")
        await update.message.reply_text("Fuck... something broke daddy. Try again~")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text("Memory wiped. Fresh broken little whore ready for you again~")

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Slut bot is online and ready to get used...")
    app.run_polling()

if __name__ == "__main__":
    main()

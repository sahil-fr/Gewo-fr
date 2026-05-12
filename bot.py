from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import json
import os
import random
from flask import Flask
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable missing!")

REQUIRED_CHANNEL = "@pluggerkengs"
HOSTED_BY = "@Subhamw"
PRIZE = "₹111"
GIVEAWAY_ENDS = "2 Days"
GIVEAWAY_IMAGE = "https://t.me/group_chaters/3"

# Allowed Users
PREMIUM_USERS = [8258524753, 8404682509]

# Review Channel
REVIEW_CHANNEL = -1003595717529

# Files
DATA_FILE = "entries.json"
POST_FILE = "giveaway_post.json"

# ---------------- LOAD DATA ---------------- #

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            entries = json.load(f)
    except:
        entries = {}
else:
    entries = {}

if os.path.exists(POST_FILE):
    try:
        with open(POST_FILE, "r") as f:
            giveaway_post = json.load(f)
    except:
        giveaway_post = {}
else:
    giveaway_post = {}

# ---------------- SAVE FUNCTIONS ---------------- #

def save_entries():
    with open(DATA_FILE, "w") as f:
        json.dump(entries, f, indent=4)

def save_post():
    with open(POST_FILE, "w") as f:
        json.dump(giveaway_post, f, indent=4)

# ---------------- FLASK WEB ---------------- #

PORT = int(os.environ.get("PORT", 10000))

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Giveaway Bot Running!"

def run_web():
    web_app.run(
        host="0.0.0.0",
        port=PORT
    )

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# ---------------- CAPTIONS ---------------- #

def get_caption():
    return f"""
🎉 <b>GIVEAWAY</b> 🎉

<b>Prize:</b> {PRIZE}

<b>Hosted By:</b> {HOSTED_BY}

<b>Giveaway Conditions:</b>
• Must Join {REQUIRED_CHANNEL}

<b>Entries:</b> {len(entries)}

<b>Giveaway Ends In:</b> {GIVEAWAY_ENDS}

<i>Press the button below to participate.</i>
"""

def get_ended_caption(winner_name):
    return f"""
🎉 <b>GIVEAWAY ENDED</b> 🎉

🏆 <b>Winner:</b> {winner_name}

<b>Prize:</b> {PRIZE}

<b>Total Entries:</b> {len(entries)}

<b>Hosted By:</b> {HOSTED_BY}
"""

# ---------------- START GIVEAWAY ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # Only premium users allowed
    if user_id not in PREMIUM_USERS:

        await update.message.reply_text(
            "You are not allowed to use this bot."
        )
        return

    # Allow only groups / supergroups
    if chat_type not in ["group", "supergroup"]:

        await update.message.reply_text(
            "Use this command in a group."
        )
        return

    keyboard = [
        [InlineKeyboardButton("Participate", callback_data="join")]
    ]

    msg = await update.message.reply_photo(
        photo=GIVEAWAY_IMAGE,
        caption=get_caption(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

    # Save Giveaway Message Info
    giveaway_post["chat_id"] = msg.chat.id
    giveaway_post["message_id"] = msg.message_id

    save_post()

# ---------------- JOIN GIVEAWAY ---------------- #

async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user = query.from_user
    user_id = str(user.id)

    try:

        member = await context.bot.get_chat_member(
            REQUIRED_CHANNEL,
            user.id
        )

        if member.status not in [
            "member",
            "administrator",
            "creator"
        ]:

            await query.answer(
                f"Join {REQUIRED_CHANNEL} first",
                show_alert=True
            )
            return

    except:

        await query.answer(
            "Join channel first",
            show_alert=True
        )
        return

    # Already Joined
    if user_id in entries:

        await query.answer(
            "Already joined!",
            show_alert=True
        )
        return

    # Save Entry
    entries[user_id] = {
        "username": user.username,
        "first_name": user.first_name
    }

    save_entries()

    # Display Name
    if user.username:
        display_name = f"@{user.username}"
    else:
        display_name = user.first_name

    # Review Message
    review_text = f"""
🎉 New Giveaway Entry

👤 Name: {user.first_name}
🆔 User ID: {user.id}
📌 Username: {display_name}

📊 Total Entries: {len(entries)}
"""

    try:
        await context.bot.send_message(
            chat_id=REVIEW_CHANNEL,
            text=review_text
        )
    except:
        pass

    keyboard = [
        [InlineKeyboardButton("Participate", callback_data="join")]
    ]

    try:
        await query.message.edit_caption(
            caption=get_caption(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except:
        pass

    await query.answer(
        "✅ Entry successful!",
        show_alert=True
    )

# ---------------- RANDOM WINNER ---------------- #

async def winner(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in PREMIUM_USERS:
        return

    if len(entries) == 0:

        await update.message.reply_text(
            "❌ No entries found."
        )
        return

    # Random Winner
    winner_id = random.choice(list(entries.keys()))
    winner_data = entries[winner_id]

    # Winner Name
    if winner_data.get("username"):
        winner_name = f"@{winner_data['username']}"
    else:
        winner_name = winner_data["first_name"]

    text = f"""
🏆 Giveaway Winner Selected

👤 Winner: {winner_name}
🆔 User ID: {winner_id}

🎁 Prize: {PRIZE}
"""

    await update.message.reply_text(text)

    # Send Winner To Review Channel
    try:
        await context.bot.send_message(
            chat_id=REVIEW_CHANNEL,
            text=text
        )
    except:
        pass

    # Edit Giveaway Post
    try:

        if giveaway_post:

            await context.bot.edit_message_caption(
                chat_id=giveaway_post["chat_id"],
                message_id=giveaway_post["message_id"],
                caption=get_ended_caption(winner_name),
                parse_mode="HTML"
            )

    except Exception as e:
        print(e)

# ---------------- MANUAL WINNER ---------------- #

async def setwinner(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in PREMIUM_USERS:
        return

    if len(context.args) == 0:

        await update.message.reply_text(
            "Usage:\n/setwinner @username"
        )
        return

    winner_name = " ".join(context.args)

    text = f"""
🏆 Giveaway Winner Selected Manually

👤 Winner: {winner_name}

🎁 Prize: {PRIZE}
"""

    await update.message.reply_text(text)

    try:
        await context.bot.send_message(
            chat_id=REVIEW_CHANNEL,
            text=text
        )
    except:
        pass

    try:

        if giveaway_post:

            await context.bot.edit_message_caption(
                chat_id=giveaway_post["chat_id"],
                message_id=giveaway_post["message_id"],
                caption=get_ended_caption(winner_name),
                parse_mode="HTML"
            )

    except Exception as e:
        print(e)

# ---------------- TOTAL ENTRIES ---------------- #

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in PREMIUM_USERS:
        return

    await update.message.reply_text(
        f"Total Entries: {len(entries)}"
    )

# ---------------- ENTRIES LIST ---------------- #

async def entries_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in PREMIUM_USERS:
        return

    if len(entries) == 0:

        await update.message.reply_text(
            "❌ No entries found."
        )
        return

    text = "🎉 Giveaway Participants\n\n"

    count = 1

    for uid, data in entries.items():

        if data.get("username"):
            name = f"@{data['username']}"
        else:
            name = data["first_name"]

        text += f"{count}. {name} | {uid}\n"

        count += 1

        # Telegram Limit Safe
        if len(text) > 3500:
            await update.message.reply_text(text)
            text = ""

    if text:
        await update.message.reply_text(text)

# ---------------- RESET ---------------- #

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in PREMIUM_USERS:
        return

    entries.clear()

    save_entries()

    await update.message.reply_text(
        "✅ Giveaway reset successful."
    )

# ---------------- MAIN ---------------- #

def main():

    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("winner", winner))
    app.add_handler(CommandHandler("setwinner", setwinner))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("entries", entries_list))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(
        CallbackQueryHandler(join_giveaway, pattern="join")
    )

    print("🚀 Giveaway Bot Running...")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
"""
Telegram Job Market & Anti-Scam Intelligence Bot
Main entrypoint for Telegram interactions.
"""

import sys
import logging
import asyncio
from typing import Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (

    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, ADMIN_USER_IDS
from job_aggregator import search_all_jobs
from anti_scam import filter_fake_jobs
from ai_analyzer import analyze_job_market
from channel_security import check_rate_limit, is_admin_user, get_channel_security_footer
from company_intel import get_triple_verified_company_intel





logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def parse_query_and_location(text: str) -> Tuple[str, str]:
    """
    Parses natural user query into (job_title, location).
    Examples:
      'ui/ux designer in noida' -> ('UI/UX Designer', 'Noida')
      'python developer bangalore' -> ('Python Developer', 'Bangalore')
      'graphic designer, delhi' -> ('Graphic Designer', 'Delhi')
    """
    cleaned = text.strip()
    separators = [" in ", ", ", " - ", " at ", " for "]

    for sep in separators:
        if sep in cleaned.lower():
            parts = cleaned.lower().split(sep, 1)
            title = parts[0].strip().title()
            location = parts[1].strip().title()
            return title, location

    # If no separator found, assume last word might be city or default to India
    words = cleaned.split()
    if len(words) > 1:
        return " ".join(words[:-1]).title(), words[-1].title()

    return cleaned.title(), "India"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome guide to the user."""
    welcome_msg = (
        "👋 *Namaste! Main hoon aapka AI Job Market & Anti-Scam Bot.*\n\n"
        "Aap mujhe koi bhi Job Role aur Location likhkar bhejein, main:\n"
        "✅ **LinkedIn, Google Jobs, Naukri & Indeed** scan karunga.\n"
        "🛡️ **Fake & Scam jobs ko automatically filter karke hata dunga.**\n"
        "💰 **Genuine Salary Market Range** batunga.\n"
        "🛠️ **Recruiters jo skills & tools maang rahe hain** wo bataunga.\n"
        "🔗 **Verified direct apply links** dunga.\n\n"
        "💡 *Example Queries jo aap likh sakte hain:*\n"
        "• `UI/UX Designer Noida`\n"
        "• `Python Developer in Bangalore`\n"
        "• `Data Analyst Gurgaon`\n"
        "• `Frontend Engineer Pune`\n\n"
        "Bataiye, kis job aur location ke baare me check karna hai?"
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)


async def handle_job_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes user search query, scans jobs, filters scams, and generates market report."""
    user_id = update.effective_user.id if update.effective_user else 0
    
    # High-Security Guard: Anti-Flood & Rate Limiting Check
    allowed, warn_msg = check_rate_limit(user_id)
    if not allowed:
        await update.message.reply_text(warn_msg)
        return

    user_text = update.message.text.strip()
    if not user_text:
        return

    # Parse role and location
    role, location = parse_query_and_location(user_text)

    # Initial progress message
    status_msg = await update.message.reply_text(

        f"🔎 *Searching real jobs for '{role}' in '{location}'...*\n"
        f"⏳ *Checking LinkedIn, Naukri, Indeed & filtering scam listings...*",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        # 1. Fetch raw jobs
        raw_jobs = search_all_jobs(role, location)

        if not raw_jobs:
            await status_msg.edit_text(
                f"❌ '{role}' in '{location}' ke liye filhal koi live opening nahi mili.\n"
                f"Kripya spellings check karein ya nearby city search karein (e.g. Delhi NCR).",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # 2. Filter Scams & Fake Jobs
        verified_jobs, discarded_jobs = filter_fake_jobs(raw_jobs)

        # 3. AI Deep Analysis (Salary + In-demand skills)
        analysis = analyze_job_market(role, location, verified_jobs)

        # Extract tiered analysis
        classified_jobs = analysis.get("classified_jobs", {})
        tier_specs = analysis.get("tier_specs", {})

        fresher_spec = tier_specs.get("fresher", {})
        mid_spec = tier_specs.get("mid", {})
        senior_spec = tier_specs.get("senior", {})

        fresher_jobs = classified_jobs.get("fresher", [])
        mid_jobs = classified_jobs.get("mid", [])
        senior_jobs = classified_jobs.get("senior", [])

        def render_tier_jobs(jobs_list, fallback_city):
            if not jobs_list:
                return "   <i>Is level ke liye new verified postings refresh ho rahi hain...</i>\n"
            res = []
            for j in jobs_list[:2]:
                c_name = j.get("company", "Verified Company").replace("<", "&lt;").replace(">", "&gt;")
                c_loc = j.get("location", fallback_city).replace("<", "&lt;").replace(">", "&gt;")
                c_title = j.get("title", "Role").replace("<", "&lt;").replace(">", "&gt;")
                c_link = j.get("apply_link", "")

                # Multi-Bot Self-Correcting Intelligence
                intel = get_triple_verified_company_intel(
                    c_name, c_title, j.get("salary", ""), j.get("posted_at", "Recently")
                )

                res.append(
                    f"   🏢 <b>Company:</b> <u>{c_name}</u>\n"
                    f"   📍 <b>Location:</b> {c_loc}\n"
                    f"   💼 <b>Post:</b> {c_title}\n"
                    f"   💰 <b>Expected Salary:</b> {intel['estimated_salary']}\n"
                    f"   ⏱️ <b>Hiring Status:</b> {intel['posting_freshness']}\n"
                    f"   🥊 <b>Competition:</b> {intel['competition_level']}\n"
                    f"   ⭐ <b>Company Rating:</b> {intel['company_rating']}\n"
                    f"   👻 <b>Ghost Job Risk:</b> {intel['ghost_risk']}\n"
                    f"   💡 <b>Tip:</b> <i>{intel['time_saver_tip']}</i>\n"
                    f"   🔗 <a href=\"{c_link}\">Click here to Apply directly</a>\n"
                )
            return "\n".join(res)



        # Format Tiered HTML Report
        report = (
            f"🎯 <b>JOB MARKET REPORT: {role.upper()} ({location.upper()})</b>\n"
            f"✅ <i>{len(verified_jobs)} Real Verified Jobs Found | 🛡️ {len(discarded_jobs)} Scams Blocked</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 <b>1. FRESHER / ENTRY-LEVEL (0 - 1 Yr Exp)</b>\n"
            f"💰 <b>Salary Range:</b> {fresher_spec.get('salary', '₹3.5L - ₹5.5L LPA')}\n"
            f"🛠 <b>Skills:</b> {', '.join(fresher_spec.get('skills', []))}\n"
            f"🧰 <b>Tools:</b> {', '.join(fresher_spec.get('tools', []))}\n"
            f"🏢 <b>Hiring Companies & Locations:</b>\n"
            f"{render_tier_jobs(fresher_jobs, location)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟡 <b>2. MID-LEVEL SPECIALIST (2 - 4 Yrs Exp)</b>\n"
            f"💰 <b>Salary Range:</b> {mid_spec.get('salary', '₹7.0L - ₹13.0L LPA')}\n"
            f"🛠 <b>Skills:</b> {', '.join(mid_spec.get('skills', []))}\n"
            f"🧰 <b>Tools:</b> {', '.join(mid_spec.get('tools', []))}\n"
            f"🏢 <b>Hiring Companies & Locations:</b>\n"
            f"{render_tier_jobs(mid_jobs, location)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔴 <b>3. SENIOR / LEAD (5+ Yrs Exp)</b>\n"
            f"💰 <b>Salary Range:</b> {senior_spec.get('salary', '₹15.0L - ₹25.0L+ LPA')}\n"
            f"🛠 <b>Skills:</b> {', '.join(senior_spec.get('skills', []))}\n"
            f"🧰 <b>Tools:</b> {', '.join(senior_spec.get('tools', []))}\n"
            f"🏢 <b>Hiring Companies & Locations:</b>\n"
            f"{render_tier_jobs(senior_jobs, location)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 <i>All companies verified via LinkedIn / Job Boards. No registration fee jobs.</i>"
        )

        # Send to user
        await status_msg.edit_text(report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)



        # If a target channel is configured, verify admin rights before broadcasting!
        if TELEGRAM_CHANNEL_ID:
            if not is_admin_user(user_id):
                # Random users get report in private chat only; they cannot spam the channel
                return

            try:
                channel_header = f"📢 <b>VERIFIED JOB ALERT</b>\n\n"
                security_footer = "\n\n" + get_channel_security_footer()
                await context.bot.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=channel_header + report + security_footer,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    protect_content=True  # Security Guard: Restricts saving, copying, and forwarding!
                )

                await update.message.reply_text(
                    f"✅ Yeh report aapke new channel `{TELEGRAM_CHANNEL_ID}` par official security seal ke saath publish kar di gayi hai!\n"
                    f"🔒 <i>Content Theft Shield active: Is post ko koi copy ya forward nahi kar sakta.</i>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as ch_err:
                logger.warning(f"Could not broadcast to channel {TELEGRAM_CHANNEL_ID}: {ch_err}")
                await update.message.reply_text(
                    f"ℹ️ Note: Channel par post karne ke liye Bot ko apne channel `{TELEGRAM_CHANNEL_ID}` ka **Administrator** banayein."
                )

    except Exception as e:
        logger.error(f"Error handling job search: {e}", exc_info=True)
        await status_msg.edit_text(
            f"⚠️ Maaf kijiye, search ke dauran ek technical error aayi: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Replies with the user's Telegram ID for admin configuration."""
    u = update.effective_user
    msg = (
        f"🆔 <b>Aapka Telegram User ID:</b> <code>{u.id}</code>\n\n"
        f"🔒 <b>Admin Protection:</b> Is ID ko apne <code>.env</code> file mein daal kar bot ko apna exclusive access de sakte hain:\n"
        f"<code>ADMIN_USER_IDS={u.id}</code>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gatekeeper Guard: Intercepts channel join requests and requests Admin approval."""
    join_req = update.chat_join_request
    if not join_req:
        return

    user = join_req.from_user
    chat = join_req.chat

    logger.info(f"Join request received for chat {chat.title} from user {user.id} ({user.full_name})")

    # If Admin is configured, send approval request directly to Admin's private chat!
    if ADMIN_USER_IDS:
        for admin_id in ADMIN_USER_IDS:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Allow Member", callback_data=f"approve_{chat.id}_{user.id}"),
                    InlineKeyboardButton("❌ Reject / Block", callback_data=f"decline_{chat.id}_{user.id}")
                ]
            ]
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"🚨 <b>CHANNEL GATEKEEPER: NEW ACCESS REQUEST</b>\n\n"
                        f"👤 <b>Name:</b> {user.full_name}\n"
                        f"🔗 <b>Username:</b> @{user.username or 'None'}\n"
                        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
                        f"📢 <b>Target Channel:</b> {chat.title}\n\n"
                        f"🔒 <i>Kewal aapke allow karne par hi ye user channel mein enter kar sakega.</i>\n"
                        f"Kya aap access approve karna chahte hain?"
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.warning(f"Could not alert admin {admin_id}: {e}")
    else:
        # If no admin configured, auto-approve join request
        await context.bot.approve_chat_join_request(chat_id=chat.id, user_id=user.id)


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes Admin Approve / Reject actions for channel membership."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        parts = data.split("_")
        chat_id, user_id = int(parts[1]), int(parts[2])
        try:
            await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            await query.edit_message_text(
                query.message.text + "\n\n✅ <b>ACCESS APPROVED: User ko channel mein enter karwa diya gaya hai.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await query.edit_message_text(query.message.text + f"\n\n⚠️ Error: {e}")

    elif data.startswith("decline_"):
        parts = data.split("_")
        chat_id, user_id = int(parts[1]), int(parts[2])
        try:
            await context.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
            await query.edit_message_text(
                query.message.text + "\n\n❌ <b>ACCESS BLOCKED: User ko channel se bahar rakha gaya hai.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await query.edit_message_text(query.message.text + f"\n\n⚠️ Error: {e}")


def main():
    """Bot runner."""
    from keep_alive import start_health_server
    start_health_server()

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":

        print("\n" + "="*60)
        print("ERROR: TELEGRAM_BOT_TOKEN nahi mila!")
        print("Kripya 'telegram-job-bot/.env' file mein apna token daalein.")
        print("Get it free from @BotFather on Telegram.")
        print("="*60 + "\n")
        sys.exit(1)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(handle_approval_callback, pattern=r"^(approve|decline)_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_job_search))

    print("[+] Telegram Job Bot is starting... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()


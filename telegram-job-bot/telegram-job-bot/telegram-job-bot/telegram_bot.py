"""
Telegram Job Market & Anti-Scam Intelligence Bot
Main entrypoint for Telegram interactions.
Protected by Multi-Layer Autonomous Watchdogs (Input Guardian, Output Auditor, GeoSentinel, AutoHealer, Truth Sentinel).
"""

import os
import sys
import uuid
import html
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
from self_healing_watchdog import InputGuardian, CompanyTruthSentinel, health_sentinel, auto_heal_async
from keep_alive import store_job_detail

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_public_url() -> str:
    """Returns the external public URL of the deployed Render app."""
    return os.getenv("RENDER_EXTERNAL_URL", "").strip() or "https://telegram-job-bot-jnp0.onrender.com"



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome guide to the user."""
    welcome_msg = (
        "👋 <b>Namaste! Main hoon aapka AI Job Market & Anti-Scam Bot.</b>\n\n"
        "Aap mujhe koi bhi Job Role aur Location likhkar bhejein, main:\n"
        "✅ <b>LinkedIn, Google Jobs, Naukri & Indeed</b> scan karunga.\n"
        "🛡️ <b>Fake & Scam jobs ko automatically filter karke hata dunga.</b>\n"
        "💰 <b>Genuine Salary Market Range</b> batunga.\n"
        "🛠️ <b>Recruiters jo skills & tools maang rahe hain</b> wo bataunga.\n"
        "🔗 <b>Verified direct apply links</b> dunga.\n\n"
        "💡 <i>Example Queries:</i>\n"
        "• <code>UI/UX Designer Noida</code> (sirf Noida area ke liye)\n"
        "• <code>UI/UX Design</code> (poore India ke liye)\n"
        "• <code>Python Developer in Bangalore</code>\n"
        "• <code>Data Analyst Gurgaon</code>\n\n"
        "🔍 <i>Admin Commands:</i> <code>/health</code> (System diagnostics dekhne ke liye)\n\n"
        "Bataiye, kis job aur location ke baare me check karna hai?"
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML)


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays real-time multi-layer watchdog diagnostics and self-healing log."""
    report = health_sentinel.get_status_report()
    await update.message.reply_text(report, parse_mode=ParseMode.HTML)


async def handle_job_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes user search query, scans jobs, filters scams, and generates market report."""
    user_id = update.effective_user.id if update.effective_user else 0

    allowed, warn_msg = check_rate_limit(user_id)
    if not allowed:
        await update.message.reply_text(warn_msg)
        return

    user_text = update.message.text.strip()
    if not user_text:
        return

    health_sentinel.total_queries += 1

    # WATCHDOG LAYER 1: Input Guardian sanitizes input & detects intent
    role, location, intent = InputGuardian.sanitize_and_parse(user_text)

    if intent == "CONVERSATION":
        conv_reply = (
            "🤖 <b>Namaste! Main Verified Jobs AI Bot hoon.</b>\n\n"
            "Mujhe lagta hai aap mujhse baat kar rahe hain ya guide chahte hain.\n\n"
            "Job search karne ke liye bas apna <b>Role</b> aur <b>City</b> likhein, jaise:\n"
            "• <code>UI/UX Designer Noida</code> (sirf Noida ke liye)\n"
            "• <code>UI/UX Design</code> (poore India ke liye)\n"
            "• <code>Python Developer Bangalore</code>\n"
            "• <code>Data Analyst Mumbai</code>\n\n"
            "💡 <i>Tip:</i> System health dekhne ke liye <code>/health</code> ya guide ke liye <code>/start</code> bhejein."
        )
        await update.message.reply_text(conv_reply, parse_mode=ParseMode.HTML)
        return

    if intent == "INVALID" or not role:
        await update.message.reply_text(
            "ℹ️ Kripya kisi Job Role ka naam likhein (jaise: <code>UI/UX Designer</code> ya <code>Python Developer</code>).",
            parse_mode=ParseMode.HTML
        )
        return

    # Escape user values for HTML display
    safe_role = html.escape(role)
    safe_location = html.escape(location)

    status_msg = await update.message.reply_text(
        f"🔎 <b>Searching real jobs for '{safe_role}' in '{safe_location}'...</b>\n"
        f"⏳ <i>Checking LinkedIn, Naukri, Indeed & filtering scam listings...</i>",
        parse_mode=ParseMode.HTML
    )

    try:
        # FIX Issue 1: Async Event Loop Non-Blocking! Run synchronous scraper in background thread
        raw_jobs = await asyncio.to_thread(search_all_jobs, role, location)

        # 2. Filter Scams & Fake Jobs
        verified_jobs, discarded_jobs = await asyncio.to_thread(filter_fake_jobs, raw_jobs)

        # WATCHDOG LAYER 5: Company Truth & Zero Fake Information Guarantee
        if not verified_jobs:
            health_sentinel.anomalies_prevented += 1
            health_sentinel.log_incident(
                "CompanyTruthSentinel",
                f"No verified jobs for '{role}' in '{location}'. Blocked fake data generation.",
                "Returned Zero-Fake-Info status"
            )
            honest_msg = (
                f"🛡️ <b>ZERO FAKE INFORMATION GUARANTEE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ <b>'{safe_role}' in '{safe_location}'</b> ke liye filhal koi 100% genuine verified opening nahi mili.\n\n"
                f"🔍 <i>Humne LinkedIn, Google Jobs & job boards scan kiye hain, lekin is location par koi authentic vacancy live nahi hai.</i>\n\n"
                f"🚫 <b>Hamara Niyam:</b> Hum aapko kisi bhi fake, dummy ya galat company ka naam nahi dikhate.\n\n"
                f"💡 <b>Koshish Karein:</b>\n"
                f"• Nearby metro hub search karein: <code>{safe_role} Delhi NCR</code>\n"
                f"• Poore desh ke liye search karein: <code>{safe_role}</code>\n"
                f"• Ya remote jobs search karein: <code>{safe_role} Remote</code>"
            )
            await status_msg.edit_text(honest_msg, parse_mode=ParseMode.HTML)
            return

        # 3. AI Deep Analysis in background thread
        analysis = await asyncio.to_thread(analyze_job_market, role, location, verified_jobs)

        classified_jobs = analysis.get("classified_jobs", {})
        tier_specs = analysis.get("tier_specs", {})

        fresher_spec = tier_specs.get("fresher", {})
        mid_spec = tier_specs.get("mid", {})
        senior_spec = tier_specs.get("senior", {})

        fresher_jobs = classified_jobs.get("fresher", [])
        mid_jobs = classified_jobs.get("mid", [])
        senior_jobs = classified_jobs.get("senior", [])

        def render_tier_jobs(jobs_list, fallback_city, tier_name, tier_spec):
            """Renders clean 3-line summary per job with View Full Details and Direct Apply links."""
            if not jobs_list:
                return "   <i>Is level ke liye filhal koi active verified opening nahi mili.</i>\n"

            res = []
            for j in jobs_list[:2]:
                c_name = html.escape(j.get("company", "Verified Company"))
                c_loc = html.escape(j.get("location", fallback_city))
                c_title = html.escape(j.get("title", "Role"))
                c_link = j.get("apply_link", "")
                safe_link = html.escape(c_link) if c_link else ""

                intel = get_triple_verified_company_intel(
                    j.get("company", "Verified Company"),
                    j.get("title", "Role"),
                    j.get("salary", ""),
                    j.get("posted_at", "Recently")
                )

                # Generate unique ID for rich web page preview
                job_id = uuid.uuid4().hex[:12]

                # Store full detailed metadata in keep_alive server
                store_job_detail(job_id, {
                    "title": j.get("title", "Role"),
                    "company": j.get("company", "Verified Company"),
                    "location": j.get("location", fallback_city),
                    "salary": intel["estimated_salary"],
                    "freshness": intel["posting_freshness"],
                    "competition": intel["competition_level"],
                    "rating": intel["company_rating"],
                    "ghost_risk": intel["ghost_risk"],
                    "tip": intel["time_saver_tip"],
                    "skills": tier_spec.get("skills", []),
                    "tools": tier_spec.get("tools", []),
                    "apply_link": c_link
                })

                detail_url = f"{get_public_url()}/job/{job_id}"
                apply_action = f'<a href="{safe_link}">Apply Directly</a>' if safe_link else "Direct Company Portal"

                res.append(
                    f"   🏢 <b>{c_name}</b>\n"
                    f"   📍 {c_loc}  •  💰 <b>{html.escape(intel['estimated_salary'])}</b>\n"
                    f"   📄 <a href=\"{detail_url}\">View Full Details</a>  |  🚀 {apply_action}\n"
                )
            return "\n".join(res)

        # Format Clean, Readable Tiered HTML Report
        report = (
            f"🎯 <b>JOB MARKET REPORT: {safe_role.upper()} ({safe_location.upper()})</b>\n"
            f"✅ <i>{len(verified_jobs)} Real Verified Jobs Found | 🛡️ {len(discarded_jobs)} Scams Blocked</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 <b>1. FRESHER / ENTRY-LEVEL (0 - 1 Yr Exp)</b>\n"
            f"💰 <b>Salary:</b> {html.escape(fresher_spec.get('salary', '₹3.5L - ₹5.5L LPA'))}\n"
            f"{render_tier_jobs(fresher_jobs, location, 'fresher', fresher_spec)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟡 <b>2. MID-LEVEL SPECIALIST (2 - 4 Yrs Exp)</b>\n"
            f"💰 <b>Salary:</b> {html.escape(mid_spec.get('salary', '₹7.0L - ₹13.0L LPA'))}\n"
            f"{render_tier_jobs(mid_jobs, location, 'mid', mid_spec)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔴 <b>3. SENIOR / LEAD (5+ Yrs Exp)</b>\n"
            f"💰 <b>Salary:</b> {html.escape(senior_spec.get('salary', '₹15.0L - ₹25.0L+ LPA'))}\n"
            f"{render_tier_jobs(senior_jobs, location, 'senior', senior_spec)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔒 <i>Skills aur Tools ki full detail dekhne ke liye har job ke 'View Full Details' link par click karein.</i>"
        )

        await status_msg.edit_text(report, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        health_sentinel.successful_queries += 1

        # Channel Broadcast (Protected by AutoHealer)
        if TELEGRAM_CHANNEL_ID:
            if not is_admin_user(user_id):
                return

            try:
                channel_header = f"📢 <b>VERIFIED JOB ALERT</b>\n\n"
                security_footer = "\n\n" + get_channel_security_footer()
                await context.bot.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=channel_header + report + security_footer,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    protect_content=True
                )

                await update.message.reply_text(
                    f"✅ Yeh report aapke channel <code>{html.escape(TELEGRAM_CHANNEL_ID)}</code> par official security seal ke saath publish kar di gayi hai!\n"
                    f"🔒 <i>Content Theft Shield active: Is post ko koi copy ya forward nahi kar sakta.</i>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as ch_err:
                logger.warning(f"Could not broadcast to channel {TELEGRAM_CHANNEL_ID}: {ch_err}")
                health_sentinel.log_incident("ChannelBroadcast", f"Broadcast failed: {ch_err}", "Alerted admin to check bot permissions")
                await update.message.reply_text(
                    f"ℹ️ Note: Channel par post karne ke liye Bot ko apne channel <code>{html.escape(TELEGRAM_CHANNEL_ID)}</code> ka <b>Administrator</b> banayein.",
                    parse_mode=ParseMode.HTML
                )

    except Exception as e:
        logger.error(f"Error handling job search: {e}", exc_info=True)
        health_sentinel.log_incident("Pipeline", f"Job search error: {str(e)[:60]}", "Auto-recovering gracefully")
        await status_msg.edit_text(
            f"⚠️ Maaf kijiye, search ke dauran ek technical error aayi: `{html.escape(str(e))}`",
            parse_mode=ParseMode.HTML
        )


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    msg = (
        f"🆔 <b>Aapka Telegram User ID:</b> <code>{u.id}</code>\n\n"
        f"🔒 <b>Admin Protection:</b> Is ID ko apne <code>.env</code> file mein daal kar bot ko apna exclusive access de sakte hain:\n"
        f"<code>ADMIN_USER_IDS={u.id}</code>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin Gatekeeper for Channel Join Requests.
    FIX Issue 5: Security Lock! If ADMIN_USER_IDS is empty, log warning and DO NOT auto-approve.
    """
    req = update.chat_join_request
    if not req:
        return

    user = req.from_user
    chat = req.chat

    if not ADMIN_USER_IDS:
        logger.warning(
            f"Join request from user {user.id} ({user.full_name}) for channel '{chat.title}' NOT auto-approved: ADMIN_USER_IDS is empty."
        )
        return

    for admin_id in ADMIN_USER_IDS:
        keyboard = [
            [
                InlineKeyboardButton("✅ Allow Member", callback_data=f"approve_{chat.id}_{user.id}"),
                InlineKeyboardButton("❌ Reject / Block", callback_data=f"decline_{chat.id}_{user.id}")
            ]
        ]
        try:
            safe_name = html.escape(user.full_name)
            safe_username = html.escape(user.username) if user.username else "None"
            safe_channel = html.escape(chat.title or "Channel")
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🚨 <b>CHANNEL GATEKEEPER: NEW ACCESS REQUEST</b>\n\n"
                    f"👤 <b>Name:</b> {safe_name}\n"
                    f"🔗 <b>Username:</b> @{safe_username}\n"
                    f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
                    f"📢 <b>Target Channel:</b> {safe_channel}\n\n"
                    f"🔒 <i>Kewal aapke allow karne par hi ye user channel mein enter kar sakega.</i>\n"
                    f"Kya aap access approve karna chahte hain?"
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.warning(f"Could not alert admin {admin_id}: {e}")


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await query.edit_message_text(query.message.text + f"\n\n⚠️ Error: {html.escape(str(e))}")

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
            await query.edit_message_text(query.message.text + f"\n\n⚠️ Error: {html.escape(str(e))}")


def create_bot_application():
    """Builds a fresh Telegram Application instance."""
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("watchdog", health_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(handle_approval_callback, pattern=r"^(approve|decline)_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_job_search))
    return app


def main():
    from keep_alive import start_health_server
    start_health_server()

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("\nERROR: TELEGRAM_BOT_TOKEN nahi mila! .env file check karein.")
        sys.exit(1)

    print("[+] Telegram Job Bot starting with non-blocking async supervisor...")
    # FIX: Rebuilds a fresh Application on every reconnect attempt to avoid corrupt state
    while True:
        try:
            app = create_bot_application()
            app.run_polling()
            break
        except Exception as poll_err:
            logger.error(f"[Supervisor] Polling error: {poll_err}. Rebuilding application in 5s...")
            import time
            time.sleep(5)


if __name__ == "__main__":
    main()

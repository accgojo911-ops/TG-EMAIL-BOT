import os
import time
import threading
import requests
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
from flask import Flask

# ----------------- Flask Web Server -----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Garena Bot is Alive!", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ----------------- Keep-Alive Ping System -----------------
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-render-app-name.onrender.com')

def keep_alive():
    while True:
        time.sleep(120)
        try:
            if "your-render-app-name" not in RENDER_URL:
                response = requests.get(RENDER_URL, timeout=10)
                print(f"Keep-Alive Ping Sent | Status Code: {response.status_code}")
        except Exception as e:
            print(f"Keep-Alive Ping Failed: {e}")

# ----------------- Bot Configurations -----------------
API_TOKEN = '8939638878:AAEdhJ47enDDF9_kpb1xeg133o-oG3OBztg'
bot = telebot.TeleBot(API_TOKEN)

REQUIRED_CHANNELS = [
    {"name": "RFG GAMER", "url": "https://t.me/GHOST_ANTIBAN", "chat_id": "@GHOST_ANTIBAN"},
    {"name": "Garena Email Support", "url": "https://t.me/GarenaEmailSupport", "chat_id": "@GarenaEmailSupport"},
    {"name": "RFG Like Group", "url": "https://t.me/RFG_GAMER_CHAT", "chat_id": "@RFG_GAMER_CHAT"}
]

HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.41(TECNO KJ5 ;Android 13;en;HK;app 1.123.1 2019120270;)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}

USER_VERIFY_CACHE = {}

def is_user_joined(user_id):
    current_time = time.time()
    
    if user_id in USER_VERIFY_CACHE:
        cached_status, timestamp = USER_VERIFY_CACHE[user_id]
        if current_time - timestamp < 300:
            return cached_status

    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ['left', 'kicked']:
                USER_VERIFY_CACHE[user_id] = (False, current_time)
                return False
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = int(e.result_json.get('parameters', {}).get('retry_after', 10))
                time.sleep(retry_after)
            return False
        except Exception:
            return False

    USER_VERIFY_CACHE[user_id] = (True, current_time)
    return True

def safe_send_message(chat_id, text, **kwargs):
    while True:
        try:
            return bot.send_message(chat_id, text, **kwargs)
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_time = int(e.result_json.get('parameters', {}).get('retry_after', 5))
                time.sleep(retry_time)
            else:
                raise e

# ----------------- Keyboards -----------------
def get_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(text=f"📢 Join {ch['name']} ↗️", url=ch["url"]))
    markup.add(types.InlineKeyboardButton(text="✅ I Have Joined", callback_data="verify_join"))
    return markup

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📧 Add Recovery Email")
    btn2 = types.KeyboardButton("🔍 Check Recovery Email")
    btn3 = types.KeyboardButton("🌐 Check Platform")
    btn4 = types.KeyboardButton("🚫 Cancel Recovery Email")
    btn5 = types.KeyboardButton("🔗 Unbind Email")
    btn6 = types.KeyboardButton("🔄 Change Bind Email")
    btn7 = types.KeyboardButton("🔒 Revoke Access Token")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7)
    return markup

def get_back_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Back To Main Menu"))
    return markup

# ----------------- Command Handlers -----------------
@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    user_id = message.from_user.id
    if not is_user_joined(user_id):
        text = "<b>🔒 Join Verification Required</b>\n\nTo use this bot, you must join the following groups first:\n\n"
        for ch in REQUIRED_CHANNELS:
            text += f"- {ch['name']}\n"
        text += "\nAfter joining, click the button below to verify:"
        safe_send_message(message.chat.id, text, parse_mode="HTML", reply_markup=get_join_keyboard())
    else:
        safe_send_message(message.chat.id, "✨ Welcome to Garena Email Bot! Select an option from menu:", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_callback(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.from_user.id in USER_VERIFY_CACHE:
        del USER_VERIFY_CACHE[call.from_user.id]

    if is_user_joined(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        safe_send_message(call.message.chat.id, "✅ Verification Successful!", reply_markup=get_main_keyboard())
    else:
        try:
            bot.answer_callback_query(call.id, "⚠️ You haven't joined all required channels yet!", show_alert=True)
        except Exception:
            pass

# ----------------- Menu Click Handlers -----------------
@bot.message_handler(func=lambda m: True)
def handle_menu_click(message):
    if not is_user_joined(message.from_user.id):
        start_cmd(message)
        return

    text = message.text

    # Clear previous active step to avoid errors
    bot.clear_step_handler_by_chat_id(message.chat.id)

    if text in ["🔙 Back To Main Menu", "/start"]:
        safe_send_message(message.chat.id, "🏠 Returned to Main Menu:", reply_markup=get_main_keyboard())

    elif text == "🌐 Check Platform":
        msg = safe_send_message(message.chat.id, "🔑 Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, process_check_platform)

    elif text == "🔒 Revoke Access Token":
        msg = safe_send_message(message.chat.id, "🔑 Enter Access Token to Revoke:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, process_revoke)

    elif text == "🚫 Cancel Recovery Email":
        msg = safe_send_message(message.chat.id, "🔑 Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, process_cancel)

    else:
        safe_send_message(message.chat.id, f"⚙️ Feature '{text}' is currently in processing mode.", reply_markup=get_main_keyboard())

# ----------------- Step Actions -----------------
def process_check_platform(message):
    token = message.text.strip()
    if token == "🔙 Back To Main Menu":
        handle_menu_click(message)
        return

    r = requests.get("https://100067.connect.garena.com/bind/app/platform/info/get",
                     params={'access_token': token}, headers=HEADERS)
    if r.status_code in [200, 201]:
        data = r.json()
        m = {3: "Facebook", 8: "Gmail", 10: "iCloud", 5: "VK", 11: "Twitter", 7: "Huawei"}
        b = data.get("bounded_accounts", [])
        
        resp_text = "<b>> Secondary Links : <</b>\n"
        for x in b:
            p = x.get('platform')
            uinfo = x.get('user_info', {})
            if p in m:
                resp_text += f"\n<b>Platform:</b> {m[p]}\n"
                if uinfo.get('email'): resp_text += f"Email: {uinfo.get('email')}\n"
                if uinfo.get('nickname'): resp_text += f"Name: {uinfo.get('nickname')}\n"
        safe_send_message(message.chat.id, resp_text, parse_mode="HTML", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "❌ Failed to fetch platform details or invalid token.", reply_markup=get_main_keyboard())

def process_revoke(message):
    token = message.text.strip()
    if token == "🔙 Back To Main Menu":
        handle_menu_click(message)
        return

    url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}"
    r = requests.get(url)
    if r.text.strip() == '{"result":0}':
        safe_send_message(message.chat.id, "✅ TOKEN REVOKED SUCCESSFULLY!", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, f"❌ Failed: {r.text}", reply_markup=get_main_keyboard())

def process_cancel(message):
    token = message.text.strip()
    if token == "🔙 Back To Main Menu":
        handle_menu_click(message)
        return

    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    payload = {'app_id': "100067", 'access_token': token}
    r = requests.post(url, data=payload, headers=HEADERS)
    safe_send_message(message.chat.id, f"Response: {r.json()}", reply_markup=get_main_keyboard())

# ----------------- Execution Threading -----------------
if __name__ == "__main__":
    try:
        bot.remove_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception as e:
        print(f"Webhook clear status: {e}")

    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    ping_thread = threading.Thread(target=keep_alive)
    ping_thread.daemon = True
    ping_thread.start()

    while True:
        try:
            print("Bot is running successfully with updated UI...")
            bot.polling(non_stop=True, interval=1, timeout=20)
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_time = int(e.result_json.get('parameters', {}).get('retry_after', 10))
                print(f"Rate limited. Waiting for {retry_time} seconds...")
                time.sleep(retry_time)
            else:
                time.sleep(3)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(3)

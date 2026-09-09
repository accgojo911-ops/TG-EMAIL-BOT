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

# Standard headers matching Termux functional requests
HEADERS = {
    'User-Agent': "GarenaMSDK/4.0.41(TECNO KJ5 ;Android 13;en;HK;app 1.123.1 2019120270;)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip"
}

USER_VERIFY_CACHE = {}
USER_DATA = {}

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

def convert(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

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

def get_unbind_options_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("1. Unbind By Email OTP"))
    markup.add(types.KeyboardButton("2. Unbind By Secondary Password"))
    markup.add(types.KeyboardButton("🔙 Back To Main Menu"))
    return markup

def get_change_bind_options_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("1. Verify Old Email by OTP"))
    markup.add(types.KeyboardButton("2. Verify by Secondary Password"))
    markup.add(types.KeyboardButton("🔙 Back To Main Menu"))
    return markup

# ----------------- Start & Verification Handlers -----------------
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
        safe_send_message(message.chat.id, "✨ Welcome to Garena Account Tool Bot! Select an option:", reply_markup=get_main_keyboard())

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

# ----------------- Main Menu Router -----------------
@bot.message_handler(func=lambda m: True)
def handle_menu_click(message):
    if not is_user_joined(message.from_user.id):
        start_cmd(message)
        return

    text = message.text
    bot.clear_step_handler_by_chat_id(message.chat.id)

    if text in ["🔙 Back To Main Menu", "/start"]:
        safe_send_message(message.chat.id, "🏠 Returned to Main Menu:", reply_markup=get_main_keyboard())

    elif text == "📧 Add Recovery Email":
        msg = safe_send_message(message.chat.id, "- Enter Email to Add:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_add_email)

    elif text == "🔍 Check Recovery Email":
        msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_check_email)

    elif text == "🌐 Check Platform":
        msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_check_platform)

    elif text == "🚫 Cancel Recovery Email":
        msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_cancel_recovery)

    elif text == "🔒 Revoke Access Token":
        msg = safe_send_message(message.chat.id, "- Enter Access Token to Revoke:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_revoke_token)

    elif text == "🔗 Unbind Email":
        safe_send_message(message.chat.id, "Select Unbind Method:", reply_markup=get_unbind_options_keyboard())

    elif text == "1. Unbind By Email OTP":
        USER_DATA[message.chat.id] = {'method': '1'}
        msg = safe_send_message(message.chat.id, "- Enter Linked Email:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_unbind_get_email)

    elif text == "2. Unbind By Secondary Password":
        USER_DATA[message.chat.id] = {'method': '2'}
        msg = safe_send_message(message.chat.id, "- Enter Linked Email:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_unbind_get_email)

    elif text == "🔄 Change Bind Email":
        safe_send_message(message.chat.id, "Select Method to Change Bind Email:", reply_markup=get_change_bind_options_keyboard())

    elif text == "1. Verify Old Email by OTP":
        USER_DATA[message.chat.id] = {'method': '1'}
        msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_change_get_access)

    elif text == "2. Verify by Secondary Password":
        USER_DATA[message.chat.id] = {'method': '2'}
        msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_change_get_access)

# ----------------- 1. Add Recovery Email Steps -----------------
def step_add_email(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    USER_DATA[message.chat.id] = {'email': message.text.strip()}
    msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(msg, step_add_token)

def step_add_token(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    token = message.text.strip()
    email = USER_DATA.get(message.chat.id, {}).get('email')
    
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    payload = {'app_id': "100067", 'access_token': token, 'email': email, 'locale': "en_MA"}
    hr = {'User-Agent': "GarenaMSDK/4.0.41(TECNO KJ5 ;Android 13;en;HK;app 1.123.1 2019120270;)", 'Connection': "Keep-Alive", 'Accept': "application/json", 'Accept-Encoding': "gzip"}
    
    r = requests.post(url, data=payload, headers=hr)
    if r.status_code == 200:
        USER_DATA[message.chat.id]['token'] = token
        msg = safe_send_message(message.chat.id, "✓ OTP Sent!\n- Enter OTP:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_add_verify_otp)
    else:
        safe_send_message(message.chat.id, "- Bad Response No OTP Get!", reply_markup=get_main_keyboard())

def step_add_verify_otp(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    otp = message.text.strip()
    data = USER_DATA.get(message.chat.id, {})
    email, token = data.get('email'), data.get('token')

    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    payload = {'app_id': "100067", 'access_token': token, 'otp': otp, 'email': email}
    r = requests.post(url, data=payload, headers=HEADERS)
    if r.status_code == 200:
        auth = r.json().get("verifier_token")
        
        # Cancel old request
        requests.post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", 
                      data={'app_id': "100067", 'access_token': token}, headers=HEADERS)
        
        # Create new bind
        url_bind = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        p_bind = {
            'app_id': "100067",
            'access_token': token,
            'verifier_token': auth,
            'secondary_password': "91B4D142823F7D20C5F08DF69122DE43F35F057A988D9619F6D3138485C9A203",
            'email': email
        }
        r_bind = requests.post(url_bind, data=p_bind, headers=HEADERS)
        if r_bind.status_code == 200 and r_bind.json().get("result") == 0:
            safe_send_message(message.chat.id, f"✅ Successfully Adding : {email} To Account!", reply_markup=get_main_keyboard())
        else:
            safe_send_message(message.chat.id, f"❌ Failed: {r_bind.json().get('error', 'Error adding email')}", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "❌ Invalid OTP or Request Failed.", reply_markup=get_main_keyboard())

# ----------------- 2. Check Recovery Email Step -----------------
def step_check_email(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    token = message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': token}
    rsp = requests.get(url, params=payload, headers=HEADERS)
    if rsp.status_code == 200:
        data = rsp.json()
        email = data.get("email", "")
        email_to_be = data.get("email_to_be", "")
        countdown = data.get("request_exec_countdown", 0)
        
        res_msg = ""
        if email == "" and email_to_be != "":
            res_msg = f"📧 Email: {email_to_be}\n⏳ Confirmed in: {convert(countdown)}"
        elif email != "" and email_to_be == "":
            res_msg = f"📧 Email: {email}\n✅ Confirmed: Yes Good!"
        elif email == "" and email_to_be == "":
            res_msg = "❌ No IsTi3ada !"
        else:
            res_msg = "❌ No Email Bound!"
            
        safe_send_message(message.chat.id, res_msg, reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, f"❌ Error Code: {rsp.status_code}", reply_markup=get_main_keyboard())

# ----------------- 3. Check Platform Step -----------------
def step_check_platform(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    token = message.text.strip()
    r = requests.get("https://100067.connect.garena.com/bind/app/platform/info/get",
                     params={'access_token': token}, headers=HEADERS)
    if r.status_code in [200, 201]:
        j = r.json()
        m = {3: "Facebook", 8: "Gmail", 10: "iCloud", 5: "VK", 11: "Twitter", 7: "Huawei"}
        b, a = j.get("bounded_accounts", []), j.get("available_platforms", [])
        
        resp_text = "<b>> Secondary Links : <</b>\n"
        found = False
        for x in b:
            p = x.get('platform')
            uinfo = x.get('user_info', {})
            e, n = uinfo.get('email', ''), uinfo.get('nickname', '')
            if p in m:
                resp_text += f"\n<b>=> {m[p]} !</b>\n"
                if e: resp_text += f"- Email: {e}\n"
                if n: resp_text += f"- Email Name: {n}\n"
                found = True
        if not found:
            resp_text += "=> Secondary Links Not Found!\n"
            
        for k in m:
            if k not in a:
                resp_text += f"\n<b>> Main Platform => {m[k]} ! <</b>\n"
                break
        safe_send_message(message.chat.id, resp_text, parse_mode="HTML", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "❌ Failed to fetch platform details.", reply_markup=get_main_keyboard())

# ----------------- 4. Cancel Recovery Step -----------------
def step_cancel_recovery(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    token = message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    payload = {'app_id': "100067", 'access_token': token}
    r = requests.post(url, data=payload, headers=HEADERS)
    if r.status_code == 200:
        res = r.json()
        if res.get("result") == 0:
            safe_send_message(message.chat.id, "✅ Recovery Email Request Cancelled Successfully!", reply_markup=get_main_keyboard())
        else:
            safe_send_message(message.chat.id, "❌ Cancel Failed or No Active Request!", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "❌ No Response!", reply_markup=get_main_keyboard())

# ----------------- 5. Revoke Token Step -----------------
def step_revoke_token(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    token = message.text.strip()
    url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}"
    r = requests.get(url)
    if r.text.strip() == '{"result":0}':
        safe_send_message(message.chat.id, "🎉 TOKEN REVOKED SUCCESSFULLY", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "❌ Failed to Revoke Token!", reply_markup=get_main_keyboard())

# ----------------- 6. Unbind Email Handlers -----------------
def step_unbind_get_email(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    USER_DATA[message.chat.id]['email'] = message.text.strip()
    msg = safe_send_message(message.chat.id, "- Enter Access Token:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(msg, step_unbind_get_token)

def step_unbind_get_token(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    USER_DATA[message.chat.id]['access_token'] = message.text.strip()
    method = USER_DATA[message.chat.id].get('method')
    
    if method == '1':
        email = USER_DATA[message.chat.id]['email']
        token = USER_DATA[message.chat.id]['access_token']
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data = {"email": email, "locale": "en_MA", "region": "IND", "app_id": "100067", "access_token": token}
        r = requests.post(url, headers=HEADERS, data=data)
        if r.status_code == 200 and r.json().get("result") == 0:
            msg = safe_send_message(message.chat.id, "✓ OTP Sent\n- Enter OTP:", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(msg, step_unbind_verify_otp)
        else:
            safe_send_message(message.chat.id, "✗ OTP Send Failed", reply_markup=get_main_keyboard())
    elif method == '2':
        msg = safe_send_message(message.chat.id, "- Enter Secondary Password:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_unbind_verify_sec_pass)

def step_unbind_verify_otp(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    otp = message.text.strip()
    u_data = USER_DATA.get(message.chat.id, {})
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email": u_data['email'], "otp": otp, "app_id": "100067", "access_token": u_data['access_token']}
    r = requests.post(url, headers=HEADERS, data=data)
    res = r.json()
    if res.get("result") == 0 and res.get("identity_token"):
        process_final_unbind(message, res.get("identity_token"))
    else:
        safe_send_message(message.chat.id, "✗ Verification Failed", reply_markup=get_main_keyboard())

def step_unbind_verify_sec_pass(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    sec_pass = message.text.strip()
    u_data = USER_DATA.get(message.chat.id, {})
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email": u_data['email'], "secondary_password": sec_pass, "app_id": "100067", "access_token": u_data['access_token']}
    r = requests.post(url, headers=HEADERS, data=data)
    res = r.json()
    if res.get("result") == 0 and res.get("identity_token"):
        process_final_unbind(message, res.get("identity_token"))
    else:
        safe_send_message(message.chat.id, "✗ Verification Failed", reply_markup=get_main_keyboard())

def process_final_unbind(message, identity_token):
    u_data = USER_DATA.get(message.chat.id, {})
    url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
    data = {"app_id": "100067", "access_token": u_data['access_token'], "identity_token": identity_token}
    r = requests.post(url, headers=HEADERS, data=data)
    res = r.json()
    if res.get("result") == 0:
        safe_send_message(message.chat.id, "✓ SUCCESS: Email Unbind Request Created!", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "✗ FAILED: Unbind Request Failed", reply_markup=get_main_keyboard())

# ----------------- 7. Change Bind Email Handlers -----------------
def step_change_get_access(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    USER_DATA[message.chat.id]['access'] = message.text.strip()
    msg = safe_send_message(message.chat.id, "- Enter Old Email:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(msg, step_change_get_old_email)

def step_change_get_old_email(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    USER_DATA[message.chat.id]['old_email'] = message.text.strip()
    msg = safe_send_message(message.chat.id, "- Enter New Email:", reply_markup=get_back_keyboard())
    bot.register_next_step_handler(msg, step_change_get_new_email)

def step_change_get_new_email(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    USER_DATA[message.chat.id]['new_email'] = message.text.strip()
    
    method = USER_DATA[message.chat.id].get('method')
    u_data = USER_DATA[message.chat.id]
    
    if method == '1':
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data = {'email': u_data['old_email'], 'locale': 'en_MA', 'region': 'IND', 'app_id': '100067', 'access_token': u_data['access']}
        r = requests.post(url, headers=HEADERS, data=data)
        if r.json().get("result") == 0:
            msg = safe_send_message(message.chat.id, f"✓ OTP Sent to {u_data['old_email']}\n- Enter OTP:", reply_markup=get_back_keyboard())
            bot.register_next_step_handler(msg, step_change_verify_old_otp)
        else:
            safe_send_message(message.chat.id, "✗ Failed to send OTP", reply_markup=get_main_keyboard())
            
    elif method == '2':
        msg = safe_send_message(message.chat.id, "- Enter Secondary Password:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_change_verify_sec_pass)

def step_change_verify_old_otp(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    otp = message.text.strip()
    u_data = USER_DATA[message.chat.id]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {'email': u_data['old_email'], 'app_id': '100067', 'access_token': u_data['access'], 'otp': otp}
    r = requests.post(url, headers=HEADERS, data=data)
    res = r.json()
    if res.get("result") == 0 and res.get("identity_token"):
        USER_DATA[message.chat.id]['identity_token'] = res.get("identity_token")
        send_otp_to_new_email(message)
    else:
        safe_send_message(message.chat.id, "✗ Verification Failed", reply_markup=get_main_keyboard())

def step_change_verify_sec_pass(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    sec_pass = message.text.strip()
    u_data = USER_DATA[message.chat.id]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {'email': u_data['old_email'], 'secondary_password': sec_pass, 'app_id': '100067', 'access_token': u_data['access']}
    r = requests.post(url, headers=HEADERS, data=data)
    res = r.json()
    if res.get("result") == 0 and res.get("identity_token"):
        USER_DATA[message.chat.id]['identity_token'] = res.get("identity_token")
        send_otp_to_new_email(message)
    else:
        safe_send_message(message.chat.id, "✗ Verification Failed", reply_markup=get_main_keyboard())

def send_otp_to_new_email(message):
    u_data = USER_DATA[message.chat.id]
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {'email': u_data['new_email'], 'locale': 'en_MA', 'region': 'IND', 'app_id': '100067', 'access_token': u_data['access']}
    r = requests.post(url, headers=HEADERS, data=data)
    if r.json().get("result") == 0:
        msg = safe_send_message(message.chat.id, f"✓ OTP Sent to {u_data['new_email']}\n- Enter OTP:", reply_markup=get_back_keyboard())
        bot.register_next_step_handler(msg, step_change_verify_new_otp)
    else:
        safe_send_message(message.chat.id, "✗ Failed to send OTP to new email", reply_markup=get_main_keyboard())

def step_change_verify_new_otp(message):
    if message.text == "🔙 Back To Main Menu": return handle_menu_click(message)
    otp_new = message.text.strip()
    u_data = USER_DATA[message.chat.id]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {'email': u_data['new_email'], 'app_id': '100067', 'access_token': u_data['access'], 'otp': otp_new}
    r = requests.post(url, headers=HEADERS, data=data)
    res = r.json()
    verifier_token = res.get("verifier_token")
    if verifier_token:
        url_rebind = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        data_final = {
            'identity_token': u_data['identity_token'],
            'email': u_data['new_email'],
            'app_id': '100067',
            'verifier_token': verifier_token,
            'access_token': u_data['access']
        }
        r_final = requests.post(url_rebind, headers=HEADERS, data=data_final)
        res_final = r_final.json()
        if res_final.get("result") == 0:
            safe_send_message(message.chat.id, "✓ SUCCESS: Rebind Created Successfully!", reply_markup=get_main_keyboard())
        else:
            safe_send_message(message.chat.id, "✗ FAILED: Rebind Failed", reply_markup=get_main_keyboard())
    else:
        safe_send_message(message.chat.id, "✗ New Email Verification Failed", reply_markup=get_main_keyboard())

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
            print("Bot is running successfully...")
            bot.polling(non_stop=True, interval=1, timeout=20)
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_time = int(e.result_json.get('parameters', {}).get('retry_after', 10))
                time.sleep(retry_time)
            else:
                time.sleep(3)
        except Exception as e:
            time.sleep(3)

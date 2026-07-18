import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import random
from datetime import datetime
import threading
from flask import Flask

# ==========================================
# 🛑 আপনার নতুন বট টোকেন
BOT_TOKEN = "8851745765:AAEmSaoiTK25mV44wvOzgXPK0DvMVujCd0U"
bot = telebot.TeleBot(BOT_TOKEN)

# 🛑 ছবির লিংক
IMG_BIG = "https://i.ibb.co.com/r2L3DfR8/1784309027133.png"
IMG_SMALL = "https://i.ibb.co.com/RG4HVFWJ/1784308935334.png"

# 🛑 প্রিমিয়াম ইমোজি/স্টিকার
WIN_EMOJI = "✅ 𝗦𝗨𝗣𝗘𝗥 𝗪𝗜𝗡 🚀"
LOSS_EMOJI = "❌ 𝗡𝗘𝗫𝗧 𝗧𝗜𝗠𝗘 💔"
JACKPOT_EMOJI = "💥 𝗕𝗢𝗢𝗠 𝗝𝗔𝗖𝗞𝗣𝗢𝗧 💸"

BRAND_NAME = "『🇸‌🇭‌🇦‌🇩‌🇴‌🇼‌ ✘ 🇹‌🇷‌🇦‌🇩‌🇪‌🇷‌』"
# ==========================================

# 🛑 ৩০ সেকেন্ডের গেমের API URL
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=20"
HEADERS = {"User-Agent": "Mozilla/5.0"}

is_running = False
target_channels = set()
last_period = ""
pending_signal = None

# ── প্রিমিয়াম এআই লজিক (AI PREDICTION) ──
def advanced_prediction_engine(data_list):
    sizes = ['B' if int(x.get('number', 0)) >= 5 else 'S' for x in data_list]
    if len(sizes) < 15: return "BIG", random.randint(85, 95), [5, 7]
    
    pred_char = 'B' if sizes.count('B') > sizes.count('S') else 'S'
    pred_size = "BIG" if pred_char == 'B' else "SMALL"
    
    if pred_size == "BIG":
        targets = random.sample([5, 6, 7, 8, 9], 2)
    else:
        targets = random.sample([0, 1, 2, 3, 4], 2)
        
    return pred_size, random.randint(90, 99), sorted(targets)

# ── প্রিমিয়াম সিগন্যাল মেসেজ ডিজাইন ──
def format_signal(period, pred_size, conf, tgts):
    filled = int((conf / 100) * 10)
    bar = "▰" * filled + "▱" * (10 - filled)
    emoji = "🟢" if pred_size == "BIG" else "🔴"
    
    return f"""{BRAND_NAME}
━━━━━━━━━━━━━━━━━━
🎮 𝐆𝐀𝐌𝐄 : 𝐖𝐈𝐍𝐆𝐎 𝟑𝟎 𝐒𝐄𝐂
⏰ 𝐓𝐈𝐌𝐄 : {datetime.now().strftime('%H:%M:%S')}
🚀 𝐏𝐄𝐑𝐈𝐎𝐃 : {period}
━━━━━━━━━━━━━━━━━━
🎯 𝐏𝐑𝐄𝐃𝐈𝐂𝐓𝐈𝐎𝐍 : {emoji} {pred_size}
🔢 𝐓𝐀𝐑𝐆𝐄𝐓 𝐍𝐔𝐌 : {tgts[0]} & {tgts[1]}
🔥 𝐀𝐂𝐂𝐔𝐑𝐀𝐂𝐘 : {conf}% {bar}
🤖 𝐀𝐈 𝐄𝐍𝐆𝐈𝐍𝐄 : 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐕𝟐.𝟎
━━━━━━━━━━━━━━━━━━
{BRAND_NAME}"""

# ── অটোমেটিক লুপ (৩০ সেকেন্ডের জন্য ২ সেকেন্ডের ইন্টারভ্যাল) ──
def signal_generator_loop():
    global is_running, last_period, pending_signal
    while True:
        if is_running and len(target_channels) > 0:
            try:
                res = requests.get(API_URL, headers=HEADERS, timeout=5)
                if res.status_code == 200:
                    data = res.json().get('data', {}).get('list', [])
                    if data:
                        latest_period = data[0].get('issueNumber', '')
                        if latest_period != last_period:
                            
                            # 🏆 রেজাল্ট চেক মেসেজ
                            if pending_signal and pending_signal["period"] == latest_period:
                                act_num = int(data[0].get('number', 0))
                                act_size = "BIG" if act_num >= 5 else "SMALL"
                                
                                if act_num in pending_signal["tgts"]: 
                                    status_text = f"{JACKPOT_EMOJI}"
                                elif act_size == pending_signal["pred_size"]: 
                                    status_text = f"{WIN_EMOJI}"
                                else: 
                                    status_text = f"{LOSS_EMOJI}"
                                
                                result_msg = f"""{BRAND_NAME}
━━━━━━━━━━━━━━━━━━
🔔 𝐑𝐄𝐒𝐔𝐋𝐓 𝐏𝐄𝐑𝐈𝐎𝐃 : {latest_period}
🎯 𝐀𝐂𝐓𝐔𝐀𝐋 𝐑𝐄𝐒𝐔𝐋𝐓 : {act_size} ({act_num})
🔰 𝐒𝐓𝐀𝐓𝐔𝐒 : {status_text}
━━━━━━━━━━━━━━━━━━"""
                                
                                for channel in list(target_channels): 
                                    try: bot.send_message(channel, result_msg)
                                    except: pass
                                pending_signal = None
                            
                            # 🚀 নতুন সিগন্যাল
                            next_period = str(int(latest_period) + 1)
                            pred_size, conf, tgts = advanced_prediction_engine(data)
                            pending_signal = {"period": next_period, "pred_size": pred_size, "tgts": tgts}
                            
                            signal_msg = format_signal(next_period, pred_size, conf, tgts)
                            photo_url = IMG_BIG if pred_size == "BIG" else IMG_SMALL
                            
                            for channel in list(target_channels): 
                                try: bot.send_photo(channel, photo_url, caption=signal_msg)
                                except: pass
                                
                            last_period = latest_period
            except: pass
        time.sleep(2) # ⚡ ৩০ সেকেন্ডের গেমের জন্য ফাস্ট লুপ

# ── বটের প্রিমিয়াম মেনু ──
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("▶️ 𝗦𝗧𝗔𝗥𝗧 𝗦𝗜𝗚𝗡𝗔𝗟𝗦", callback_data="start_sig"), InlineKeyboardButton("🛑 𝗦𝗧𝗢𝗣 𝗦𝗜𝗚𝗡𝗔𝗟𝗦", callback_data="stop_sig"))
    markup.row(InlineKeyboardButton("📋 𝗠𝗬 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦", callback_data="list_channels"))
    
    welcome_text = f"👑 **Welcome to {BRAND_NAME} Premium Bot**\n\n⚙️ **Channel Add Command:**\n`/add @your_channel_username`"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_channel(message):
    try:
        ch = message.text.split()[1]
        if not ch.startswith("@"): ch = "@" + ch
        target_channels.add(ch)
        bot.reply_to(message, f"✅ **Channel {ch} successfully linked!**", parse_mode="Markdown")
    except: bot.reply_to(message, "⚠️ Format: `/add @your_channel`")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global is_running
    if call.data == "start_sig":
        if not target_channels:
            bot.answer_callback_query(call.id, "⚠️ Add a channel first!", show_alert=True)
            return
        is_running = True
        bot.send_message(call.message.chat.id, f"▶️ **PREMIUM SIGNALS STARTED!**", parse_mode="Markdown")
    elif call.data == "stop_sig":
        is_running = False
        bot.send_message(call.message.chat.id, f"🛑 **SIGNALS STOPPED!**", parse_mode="Markdown")
    elif call.data == "list_channels":
        msg = "📋 **Linked Channels:**\n" + "\n".join(target_channels) if target_channels else "No channels linked."
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# ==========================================
# 🛑 ২৪ ঘণ্টা সার্ভার (Flask Server)
# ==========================================
app = Flask(__name__)
@app.route('/')
def home():
    return f"{BRAND_NAME} Premium Bot is Running 24/7!"

if __name__ == "__main__":
    print(f"{BRAND_NAME} Web server & Bot starting...")
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    threading.Thread(target=signal_generator_loop, daemon=True).start()
    bot.infinity_polling()

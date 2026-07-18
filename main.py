import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import random
from datetime import datetime
import threading
from flask import Flask

# ==========================================
# 🛑 তোমার বট টোকেন
BOT_TOKEN = "8851745765:AAEmSaoiTK25mV44wvOzgXPK0DvMVujCd0U"
bot = telebot.TeleBot(BOT_TOKEN)

# 🛑 ছবির লিংক
IMG_BIG = "https://i.ibb.co.com/r2L3DfR8/1784309027133.png"
IMG_SMALL = "https://i.ibb.co.com/RG4HVFWJ/1784308935334.png"

WIN_EMOJI = "✅ 𝗦𝗨𝗣𝗘𝗥 𝗪𝗜𝗡 🚀"
LOSS_EMOJI = "❌ 𝗡𝗘𝗫𝗧 𝗧𝗜𝗠𝗘 💔"
JACKPOT_EMOJI = "💥 𝗕𝗢𝗢𝗠 𝗝𝗔𝗖𝗞𝗣𝗢𝗧 💸"

BRAND_NAME = "『🇸‌🇭‌🇦‌🇩‌🇴‌🇼‌ ✘ 🇹‌🇷‌🇦‌🇩‌🇪‌🇷‌』"
# ==========================================

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?pageNo=1&pageSize=20"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# গ্লোবাল ভ্যারিয়েবল 
is_running = False
saved_channels = []      # এখানে তোমার সেভ করা সব চ্যানেল থাকবে
active_channel = None    # তুমি যেটাতে টিপ দিয়ে সিলেক্ট করবে সেটা এখানে থাকবে
last_period = ""
pending_signal = None

# ── প্রিমিয়াম এআই লজিক ──
def advanced_prediction_engine(data_list):
    sizes = ['B' if int(x.get('number', 0)) >= 5 else 'S' for x in data_list]
    if len(sizes) < 15: return "BIG", random.randint(85, 95), [5, 7]
    pred_char = 'B' if sizes.count('B') > sizes.count('S') else 'S'
    pred_size = "BIG" if pred_char == 'B' else "SMALL"
    
    if pred_size == "BIG": targets = random.sample([5, 6, 7, 8, 9], 2)
    else: targets = random.sample([0, 1, 2, 3, 4], 2)
        
    return pred_size, random.randint(90, 99), sorted(targets)

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

# ── অটোমেটিক লুপ ──
def signal_generator_loop():
    global is_running, last_period, pending_signal
    while True:
        # যদি বট রানিং থাকে এবং একটি চ্যানেল সিলেক্ট করা থাকে
        if is_running and active_channel:
            try:
                res = requests.get(API_URL, headers=HEADERS, timeout=5)
                if res.status_code == 200:
                    data = res.json().get('data', {}).get('list', [])
                    if data:
                        latest_period = data[0].get('issueNumber', '')
                        if latest_period != last_period:
                            
                            if pending_signal and pending_signal["period"] == latest_period:
                                act_num = int(data[0].get('number', 0))
                                act_size = "BIG" if act_num >= 5 else "SMALL"
                                
                                if act_num in pending_signal["tgts"]: status_text = f"{JACKPOT_EMOJI}"
                                elif act_size == pending_signal["pred_size"]: status_text = f"{WIN_EMOJI}"
                                else: status_text = f"{LOSS_EMOJI}"
                                
                                result_msg = f"{BRAND_NAME}\n━━━━━━━━━━━━━━━━━━\n🔔 𝐑𝐄𝐒𝐔𝐋𝐓 𝐏𝐄𝐑𝐈𝐎𝐃 : {latest_period}\n🎯 𝐀𝐂𝐓𝐔𝐀𝐋 𝐑𝐄𝐒𝐔𝐋𝐓 : {act_size} ({act_num})\n🔰 𝐒𝐓𝐀𝐓𝐔𝐒 : {status_text}\n━━━━━━━━━━━━━━━━━━"
                                
                                try: bot.send_message(active_channel, result_msg)
                                except: pass
                                pending_signal = None
                            
                            next_period = str(int(latest_period) + 1)
                            pred_size, conf, tgts = advanced_prediction_engine(data)
                            pending_signal = {"period": next_period, "pred_size": pred_size, "tgts": tgts}
                            
                            signal_msg = format_signal(next_period, pred_size, conf, tgts)
                            photo_url = IMG_BIG if pred_size == "BIG" else IMG_SMALL
                            
                            try: bot.send_photo(active_channel, photo_url, caption=signal_msg)
                            except: pass
                                
                            last_period = latest_period
            except: pass
        time.sleep(2) 

# ── মেইন মেনু জেনারেটর ──
def get_main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🟢 𝗦𝗧𝗔𝗥𝗧", callback_data="start_sig"), 
        InlineKeyboardButton("🛑 𝗦𝗧𝗢𝗣", callback_data="stop_sig")
    )
    markup.add(
        InlineKeyboardButton("➕ 𝗔𝗗𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟", callback_data="add_channel_prompt"), 
        InlineKeyboardButton("📋 𝗠𝗬 𝗖𝗛𝗔𝗡𝗡𝗘𝗟𝗦", callback_data="show_channels")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"👑 **Welcome to {BRAND_NAME} Menu**\n\n👇 নিচের বাটনগুলো দিয়ে বট কন্ট্রোল করুন:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

# ── বাটন কন্ট্রোল প্যানেল ──
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global is_running, active_channel, saved_channels

    if call.data == "start_sig":
        if not active_channel:
            bot.answer_callback_query(call.id, "⚠️ আগে My Channels থেকে একটি চ্যানেল সিলেক্ট করুন!", show_alert=True)
            return
        is_running = True
        bot.send_message(call.message.chat.id, f"▶️ **সিগন্যাল শুরু হয়েছে এই চ্যানেলে:** {active_channel}", parse_mode="Markdown")

    elif call.data == "stop_sig":
        is_running = False
        bot.send_message(call.message.chat.id, "🛑 **সিগন্যাল বন্ধ করা হয়েছে!**", parse_mode="Markdown")

    elif call.data == "add_channel_prompt":
        msg = bot.send_message(call.message.chat.id, "✏️ **চ্যানেলের ইউজারনেম লিখে পাঠান (যেমন: @mychannel):**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_channel)

    elif call.data == "show_channels":
        if not saved_channels:
            bot.answer_callback_query(call.id, "⚠️ কোনো চ্যানেল অ্যাড করা নেই!", show_alert=True)
            return
        
        # চ্যানেলগুলোর জন্য আলাদা বাটন তৈরি
        markup = InlineKeyboardMarkup(row_width=1)
        for ch in saved_channels:
            markup.add(InlineKeyboardButton(f"👉 {ch}", callback_data=f"select_ch_{ch}"))
        bot.send_message(call.message.chat.id, "👇 **কোন চ্যানেলে সিগন্যাল দিতে চান সেটি সিলেক্ট করুন:**", reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("select_ch_"):
        selected = call.data.replace("select_ch_", "")
        active_channel = selected
        bot.answer_callback_query(call.id, f"{selected} সিলেক্ট করা হয়েছে!")
        bot.send_message(call.message.chat.id, f"✅ **{selected} অ্যাক্টিভ করা হয়েছে।**\nএবার সিগন্যাল পাঠাতে Start বাটনে টিপ দিন।", parse_mode="Markdown")

def process_add_channel(message):
    ch = message.text.strip()
    if not ch.startswith("@"): ch = "@" + ch
    
    if ch not in saved_channels:
        saved_channels.append(ch)
    
    bot.send_message(message.chat.id, f"✅ **{ch} চ্যানেলটি সফলভাবে অ্যাড হয়েছে!**\nএবার My Channels বাটনে টিপ দিয়ে এটি সিলেক্ট করুন।", parse_mode="Markdown")

# ==========================================
# 🛑 ২৪ ঘণ্টা সার্ভার
# ==========================================
app = Flask(__name__)
@app.route('/')
def home():
    return f"{BRAND_NAME} Premium UI is Running 24/7!"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    threading.Thread(target=signal_generator_loop, daemon=True).start()
    bot.infinity_polling()

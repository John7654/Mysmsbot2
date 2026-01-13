import logging
import sqlite3
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# --- কনফিগারেশন ---
API_TOKEN = '8272232302:AAFQsczsDl0cLTztQQtortFmPR-T7Q5dlyY'
ADMIN_IDS = [6973940391] 
CHANNEL_ID = "@tech_master_a2z" # আপনার চ্যানেলের ইউজারনেম
SMS_API_URL = "https://bulksms.rgb-boys.my.id/api.php"
SMS_API_KEY = "RGB-mhhacker"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- ডাটাবেস ---
conn = sqlite3.connect('users_v2.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 2, is_blocked INTEGER DEFAULT 0)''')
conn.commit()

# --- স্টেট ম্যানেজমেন্ট ---
class AdminState(StatesGroup):
    giving_id = State()
    giving_amount = State()
    blocking_id = State()

class SMSState(StatesGroup):
    number = State()
    message = State()

class GiftState(StatesGroup):
    target_id = State()
    amount = State()

# --- মেইন মেনু কিবোর্ড ---
def get_main_menu(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📩 Send SMS", callback_data="menu_send"),
        InlineKeyboardButton("👤 My Account", callback_data="menu_acc"),
        InlineKeyboardButton("🎁 Gift Credit", callback_data="menu_gift")
    )
    if user_id in ADMIN_IDS:
        keyboard.add(InlineKeyboardButton("🛡 Admin Panel", callback_data="menu_admin"))
    return keyboard

# --- স্টার্ট কমান্ড ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

    text = (
        "👋 Welcome to Pro Custom SMS Bot!\n\n"
        "📩 This bot provides Professional & Custom SMS services\n"
        "⚡ Fast delivery | 🔐 Secure | 🎯 Easy\n"
        "━━━━━━━━━━━━━━\n"
        "👨‍💻 Developer: Tech Master\n"
        "👑 Team Owner: @Gajarbotol\n"
        "📢 Channel: https://t.me/tech_master_a2z\n"
        "━━━━━━━━━━━━━━\n"
        "➡️ First, join our channel and click 'Joined' button."
    )
    
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 Join Channel", url="https://t.me/tech_master_a2z"))
    kb.add(InlineKeyboardButton("✅ Joined", callback_data="verify_join"))
    await message.answer(text, reply_markup=kb)

# --- জয়েন ভেরিফিকেশন ---
@dp.callback_query_handler(text="verify_join")
async def verify(call: types.CallbackQuery):
    user_id = call.from_user.id
    # এখানে মেম্বারশিপ চেক করার রিয়েল লজিক (বোটকে চ্যানেলে এডমিন থাকতে হবে)
    try:
        status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if status.status != 'left':
            await call.message.edit_text("✅ Verification Success! Main Menu:", reply_markup=get_main_menu(user_id))
        else:
            await call.answer("❌ You haven't joined yet!", show_alert=True)
    except:
        # যদি বোট এডমিন না থাকে, তবে সরাসরি মেনু দেখাবে
        await call.message.edit_text("✅ Welcome!", reply_markup=get_main_menu(user_id))

# --- ক্রেডিট গিফট সিস্টেম ---
@dp.callback_query_handler(text="menu_gift")
async def gift_start(call: types.CallbackQuery):
    await GiftState.target_id.set()
    await call.message.answer("🆔 Enter the User ID you want to gift credits:")

@dp.message_handler(state=GiftState.target_id)
async def gift_id(msg: types.Message, state: FSMContext):
    await state.update_data(tid=msg.text)
    await GiftState.next()
    await msg.answer("💰 How many credits to gift?")

@dp.message_handler(state=GiftState.amount)
async def gift_done(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    tid = data['tid']
    amount = int(msg.text)
    uid = msg.from_user.id
    
    cursor.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
    my_credits = cursor.fetchone()[0]
    
    if my_credits >= amount:
        cursor.execute("UPDATE users SET credits = credits - ? WHERE user_id=?", (amount, uid))
        cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, tid))
        conn.commit()
        await msg.answer(f"✅ Sent {amount} credits to {tid}")
    else:
        await msg.answer("❌ Insufficient balance!")
    await state.finish()

# --- এডমিন প্যানেল লজিক ---
@dp.callback_query_handler(text="menu_admin")
async def admin_p(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("➕ Add Credit to User", callback_data="adm_add"),
        InlineKeyboardButton("🚫 Block User", callback_data="adm_block"),
        InlineKeyboardButton("📊 Total Users", callback_data="adm_count")
    )
    await call.message.answer("🛠 Admin Control Panel", reply_markup=kb)

@dp.callback_query_handler(text="adm_add")
async def adm_add_start(call: types.CallbackQuery):
    await AdminState.giving_id.set()
    await call.message.answer("👤 Enter User ID to give credits:")

@dp.message_handler(state=AdminState.giving_id)
async def adm_id(msg: types.Message, state: FSMContext):
    await state.update_data(target=msg.text)
    await AdminState.next()
    await msg.answer("💰 Amount of credits:")

@dp.message_handler(state=AdminState.giving_amount)
async def adm_final(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(msg.text), data['target']))
    conn.commit()
    await msg.answer("✅ Successfully Updated!")
    await state.finish()

# --- বোট রান ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

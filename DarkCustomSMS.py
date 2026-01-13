import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- কনফিগারেশন ---
API_TOKEN = '8272232302:AAFQsczsDl0cLTztQQtortFmPR-T7Q5dlyY'
ADMIN_ID = 6973940391
CHANNEL_ID = "@tech_master_a2z"
SMS_API_URL = "https://bulksms.rgb-boys.my.id/api.php"
SMS_API_KEY = "RGB-mhhacker"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = (
        "👋 Welcome to Pro Custom SMS Bot!\n\n"
        "📩 This bot provides Professional SMS services\n"
        "━━━━━━━━━━━━━━\n"
        "👨‍💻 Developer: Tech Master\n"
        "📢 Channel: https://t.me/tech_master_a2z\n"
        "━━━━━━━━━━━━━━\n"
        "➡️ Type /sms <number> <message> to send SMS."
    )
    await message.answer(welcome_text)

@dp.message_handler(commands=['sms'])
async def send_sms_handler(message: types.Message):
    args = message.get_args().split(' ', 1)
    if len(args) < 2:
        return await message.reply("❌ Format: /sms 017xxxxxxxx Hello")
    
    number, msg_text = args[0], args[1]
    params = {'key': SMS_API_KEY, 'number': number, 'msg': msg_text}
    
    try:
        response = requests.get(SMS_API_URL, params=params)
        if response.status_code == 200:
            await message.reply(f"✅ SMS Sent to {number}!")
        else:
            await message.reply("❌ API Error!")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

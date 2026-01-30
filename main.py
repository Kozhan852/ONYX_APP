import os
import sqlite3
import requests
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

TOKEN = "8121652168:AAEZYBUnRwGDV7XGAeZzrJe0xc7ueLF091k"
OXA_API_KEY = "5BHNH2-SIYCZC-RWHLV2-XHAJTH"
ADMIN_ID = 7359865610

bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('onyx.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                   (id INTEGER PRIMARY KEY, 
                    balance REAL DEFAULT 0, 
                    is_banned INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = sqlite3.connect('onyx.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_banned FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def create_invoice(user_id, amount):
    url = "https://api.oxapay.com/merchants/request"
    data = {
        "merchant": OXA_API_KEY,
        "amount": amount,
        "currency": "USDT",
        "lifeTime": 30,
        "orderId": str(user_id),
    }
    try:
        response = requests.post(url, json=data)
        return response.json()
    except:
        return None

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    init_db()
    if is_banned(m.from_user.id):
        return await m.answer("🚫 **ببورە، تۆ لەلایەن بەڕێوبەرەوە باند کراویت.**")

    conn = sqlite3.connect('onyx.db')
    conn.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (m.from_user.id,))
    conn.commit()
    conn.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 کردنەوەی ئەپی ONYX", web_app=WebAppInfo(url="لێرە_لینکی_ڤێرسێل_دابنێ"))],
        [InlineKeyboardButton(text="💳 کڕینی باڵانس (USDT)", callback_data="buy_bal")],
        [InlineKeyboardButton(text="👤 هەژماری من", callback_data="my_account")]
    ])
    
    await m.answer(f"🏛 **Welcome to ONYX GLOBAL**\n\n👤 **User:** {m.from_user.first_name}\n🆔 **ID:** `{m.from_user.id}`", reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("ban"))
async def ban_user(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        user_id = m.text.split()[1]
        conn = sqlite3.connect('onyx.db')
        conn.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        await m.answer(f"✅ User `{user_id}` Banned.")
    except:
        await m.answer("Usage: `/ban ID`")

@dp.message(Command("unban"))
async def unban_user(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        user_id = m.text.split()[1]
        conn = sqlite3.connect('onyx.db')
        conn.execute('UPDATE users SET is_banned = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        await m.answer(f"✅ User `{user_id}` Unbanned.")
    except:
        await m.answer("Usage: `/unban ID`")

@dp.callback_query(F.data == "buy_bal")
async def process_buy(cb: types.CallbackQuery):
    if is_banned(cb.from_user.id): return
    invoice = create_invoice(cb.from_user.id, 10)
    if invoice and invoice.get('status') == 200:
        await cb.message.answer(f"🔗 Link:\n{invoice.get('payUrl')}")
    else:
        await cb.message.answer("❌ Error in Payment System.")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

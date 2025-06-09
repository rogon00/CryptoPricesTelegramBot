import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
from config import BOT_TOKEN
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

API_URL = "https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
COINS_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"

SYMBOLS_MAP = {}  # автоматично заповнюватиметься

# Зробимо невеличкий список популярних монет для кнопок
POPULAR_SYMBOLS = ["btc", "eth", "ltc", "doge", "bnb", "ada"]

crypto_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=symbol) for symbol in POPULAR_SYMBOLS[:3]],
        [KeyboardButton(text=symbol) for symbol in POPULAR_SYMBOLS[3:]]
    ],
    resize_keyboard=True
)

async def load_symbols_map():
    global SYMBOLS_MAP
    async with aiohttp.ClientSession() as session:
        async with session.get(COINS_LIST_URL) as resp:
            if resp.status == 200:
                coins = await resp.json()
                SYMBOLS_MAP = {coin['symbol'].lower(): coin['id'] for coin in coins}
                print(f"✅ Loaded {len(SYMBOLS_MAP)} coin symbols.")
            else:
                print("❌ Failed to load coin list from CoinGecko.")

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Hi! Send a cryptocurrency symbol (like <b>btc</b> or <b>sol</b>), and I’ll give you the price!",
        reply_markup=crypto_keyboard
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🛠 <b>How to use me</b>:\n"
        "• Just send a crypto symbol (e.g., btc, sol, avax)\n"
        "• Or press a button below 👇\n"
        "• I’ll reply with the current price in USD",
        reply_markup=crypto_keyboard
    )

@dp.message()
async def get_crypto_price(message: Message):
    symbol = message.text.strip().lower()
    coin_id = SYMBOLS_MAP.get(symbol)

    if not coin_id:
        await message.answer("❌ Cryptocurrency not found. Try something like: btc, eth, sol, doge, bnb...")
        return

    await message.answer("⏳ Searching...")

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL.format(coin_id=coin_id)) as resp:
            if resp.status == 200:
                data = await resp.json()
                price = data.get(coin_id, {}).get("usd")
                if price:
                    text = f"💰 {hbold(symbol.upper())} costs: <b>${price}</b>"
                    await message.answer(text)
                else:
                    await message.answer("⚠️ Price not found. Try again later.")
            else:
                await message.answer("⚠️ Failed to retrieve data. Please try again later.")

if __name__ == "__main__":
    import asyncio

    async def main():
        await load_symbols_map()
        await dp.start_polling(bot)

    asyncio.run(main())

import asyncio
import os
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

TOKEN = os.getenv("BOT_TOKEN")  # BotFather bergan token shu yerga qo'yiladi
TOTAL = 10  # har bir testda nechta savol

bot = Bot(TOKEN)
dp = Dispatcher()

# Har bir foydalanuvchining joriy holati: {user_id: {...}}
state = {}

LEVELS = {"easy": "🟢 Oson", "mid": "🟡 O'rta", "hard": "🔴 Qiyin"}


def make_question(level):
    """Savol matni, to'g'ri javob va 4 ta variant qaytaradi."""
    if level == "easy":
        op = random.choice(["+", "-"])
        a, b = random.randint(2, 20), random.randint(2, 20)
    elif level == "mid":
        op = random.choice(["+", "-", "*"])
        if op == "*":
            a, b = random.randint(2, 12), random.randint(2, 12)
        else:
            a, b = random.randint(20, 200), random.randint(20, 200)
    else:
        op = random.choice(["*", "/"])
        if op == "*":
            a, b = random.randint(12, 99), random.randint(3, 12)
        else:
            b = random.randint(3, 12)
            result = random.randint(12, 99)
            a = b * result

    if op == "+":
        correct = a + b
    elif op == "-":
        if a < b:
            a, b = b, a
        correct = a - b
    elif op == "*":
        correct = a * b
    else:
        correct = a // b

    symbol = {"+": "+", "-": "−", "*": "×", "/": "÷"}[op]
    text = f"{a} {symbol} {b} = ?"

    options = {correct}
    while len(options) < 4:
        wrong = correct + random.choice([-10, -2, -1, 1, 2, 10, 5, -5])
        if wrong >= 0:
            options.add(wrong)
    options = list(options)
    random.shuffle(options)
    return text, correct, options


def question_keyboard(options):
    buttons = [
        InlineKeyboardButton(text=str(o), callback_data=f"a:{o}") for o in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


def levels_keyboard():
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"lvl:{key}")]
        for key, name in LEVELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def ask_next(message: Message, user_id: int):
    s = state[user_id]
    text, correct, options = make_question(s["level"])
    s["answer"] = correct
    s["n"] += 1
    await message.answer(
        f"Savol {s['n']}/{TOTAL}\n\n{text}",
        reply_markup=question_keyboard(options),
    )


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Salom! 👋 Men matematika test botiman.\n"
        "Qiyinlik darajasini tanlang:",
        reply_markup=levels_keyboard(),
    )


@dp.callback_query(F.data.startswith("lvl:"))
async def choose_level(call: CallbackQuery):
    level = call.data.split(":")[1]
    state[call.from_user.id] = {"level": level, "n": 0, "score": 0, "answer": None}
    await call.message.edit_text(f"{LEVELS[level]} daraja tanlandi. Boshladik! 🚀")
    await ask_next(call.message, call.from_user.id)
    await call.answer()


@dp.callback_query(F.data.startswith("a:"))
async def check_answer(call: CallbackQuery):
    uid = call.from_user.id
    s = state.get(uid)
    if not s or s["answer"] is None:
        await call.answer("Test tugagan. /start ni bosing.", show_alert=True)
        return

    chosen = int(call.data.split(":")[1])
    correct = s["answer"]
    s["answer"] = None  # ikki marta bosilishidan himoya

    if chosen == correct:
        s["score"] += 1
        result = "✅ To'g'ri!"
    else:
        result = f"❌ Noto'g'ri. To'g'ri javob: {correct}"

    old_text = call.message.text.split("\n\n")[1]
    await call.message.edit_text(f"{old_text}\n{result}")
    await call.answer()

    if s["n"] >= TOTAL:
        score = s["score"]
        percent = round(score / TOTAL * 100)
        await call.message.answer(
            f"🏁 Test tugadi!\n\nNatija: {score}/{TOTAL} ({percent}%)\n\n"
            "Qaytadan boshlash uchun /start ni bosing.",
        )
        state.pop(uid, None)
    else:
        await ask_next(call.message, uid)


async def main():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. Tokenni muhit o'zgaruvchisiga qo'ying.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

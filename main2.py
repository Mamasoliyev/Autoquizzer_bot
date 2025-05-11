import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')  # Django sozlamalarini o‘rnatish
import django
django.setup()  # Django-ni ishga tushirish

import pandas as pd
import asyncio
import random
from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ContentType
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.client.default import DefaultBotProperties

from quiz.models import TelegramUser, Question, AnswerOption, UserAnswer  # Modellar importi sozlamalardan keyin

ADMINS = [7129769569]
API_TOKEN = '7914431289:AAE6NErXe7itNmmdEkFz_07mTbeBK2cP8QA'  # ⚠️ Tokenni yashiring!
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

# 🧠 Session ma'lumotlarini saqlash
user_sessions = {}

# 📌 Doimiy menyu tugmasi
quiz_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌝 Create Quiz")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Biror amalni tanlang..."
)

# ✅ Excel fayldan testlarni o‘qish
def read_quiz_from_excel(file_path):
    df = pd.read_excel(file_path, header=None)
    df = df.dropna().reset_index(drop=True)

    quizzes = []
    for i in range(0, len(df), 5):
        question = df.iloc[i, 0]
        original_options = [df.iloc[i + j, 0] for j in range(1, 5)]
        correct_answer = original_options[0]

        shuffled_options = original_options.copy()
        random.shuffle(shuffled_options)
        correct_option_id = shuffled_options.index(correct_answer)

        quizzes.append({
            'question': question,
            'options': shuffled_options,
            'correct_option_id': correct_option_id
        })
    return quizzes

# 🔁 Foydalanuvchini ro‘yxatdan o‘tkazish
@sync_to_async
def register_user(telegram_id, full_name, username):
    TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={'full_name': full_name, 'username': username}
    )

# 🔄 Savol va javoblarni bazada saqlash
@sync_to_async
def save_question_and_options(question_text, options, correct_option_id):
    question, _ = Question.objects.get_or_create(text=question_text)
    for i, option_text in enumerate(options):
        is_correct = (i == correct_option_id)
        AnswerOption.objects.get_or_create(
            question=question,
            text=option_text,
            defaults={'is_correct': is_correct}
        )
    return question

# 🔄 Javobni UserAnswer ga saqlash
@sync_to_async
def save_user_answer(user, question, selected_option, is_correct):
    UserAnswer.objects.create(
        user=user,
        question=question,
        selected_option=selected_option,
        is_correct=is_correct
    )

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await register_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    await message.answer(
        "🎉 <b>Assalomu alaykum!</b>\n\n"
        "📊 Siz Excel fayli orqali o‘zingizga mos quiz (test) yaratmoqchimisiz?\n\n"
        "📅 Tayyormisiz? Boshlaymizmi?\n\n"
        "✅ Unday bo‘lsa quyidagi menyudan <b>“Create Quiz”</b> tugmasini bosing",
        reply_markup=quiz_menu
    )

# Doimiy menyudagi tugmani bosganda
@dp.message(F.text == "🌝 Create Quiz")
async def handle_quiz_button(message: Message):
    user_sessions[message.from_user.id] = {"ready_for_upload": True}
    await message.answer("""📥 Iltimos, quyidagi talablarga mos ravishda .xlsx (Excel) fayl yuboring:

✅ Fayl formati faqat .xlsx bo'lishi kerak.
📌 Ya'ni siz Excel dasturida yaratilgan faylni yuborishingiz zarur (Word, PDF yoki boshqa formatlar qabul qilinmaydi).

✅ Har bir savol 5 ta qatorni egallashi lozim:

📌1-qator: Savolning matni
📌2, 3, 4, 5 - qatorlar javob variantlari

✅ Barcha savollarning to‘g‘ri javobi har doim 1-variant bo‘lishi kerak.""")

# Help command
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_message = """
📩 Fikr va takliflar uchun murojaat:

📬 Telegram: @Developer_2003
📧 Gmail: nodirbekmamasoliyev7@gmail.com
    """
    await message.answer(help_message)

# Fayl yuborilganda
@dp.message(F.document)
async def handle_excel_file(message: Message):
    session = user_sessions.get(message.from_user.id)
    if not session or not session.get("ready_for_upload"):
        await message.answer("❗ Iltimos, avval <b>“🌝 Create Quiz”</b> tugmasini bosing.")
        return

    file = message.document

    if not file.file_name.endswith('.xlsx'):
        await message.answer("❗ Faqat .xlsx formatdagi fayllarni yuboring.")
        return

    file_path = f"downloads/{file.file_name}"
    os.makedirs("downloads", exist_ok=True)
    await bot.download(file, destination=file_path)

    try:
        quizzes = read_quiz_from_excel(file_path)
        user_sessions[message.from_user.id] = {
            'file_name': file.file_name,
            'quizzes': quizzes,
            'current_index': 0,
            'correct': 0,
            'incorrect': 0
        }

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔔 Testni boshlash", callback_data="start_quiz")]
            ]
        )

        await message.answer(
            f"🎲 Quiz: <b>{file.file_name}</b>\n"
            f"🖊 {len(quizzes)} ta savol",
            reply_markup=keyboard
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

    os.remove(file_path)

# Callback: Testni boshlash
@dp.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    await send_next_question(user_id)

# Savol yuboruvchi
async def send_next_question(user_id):
    session = user_sessions.get(user_id)
    if session is None or session['current_index'] >= len(session['quizzes']):
        await bot.send_message(
            user_id,
            f"""
🏁 <b>Test yakunlandi!</b>\n
✅ To'g'ri javoblar soni: <b>{session['correct']}</b>\n
❌ Noto'g'ri javoblar soni: <b>{session['incorrect']}</b>
"""
        )
        user_sessions.pop(user_id, None)
        return

    quiz = session['quizzes'][session['current_index']]

    user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user_id)
    question = await save_question_and_options(quiz['question'], quiz['options'], quiz['correct_option_id'])

    total = len(session['quizzes'])
    current = session['current_index'] + 1
    numbered_question = f"{current}/{total}. {quiz['question']}"

    msg = await bot.send_poll(
        chat_id=user_id,
        question=numbered_question,
        options=quiz['options'],
        type='quiz',
        correct_option_id=quiz['correct_option_id'],
        is_anonymous=False
    )

    session['current_poll_id'] = msg.poll.id
    session['current_message_id'] = msg.message_id

# Javobni qabul qilish
@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    user_id = poll_answer.user.id
    session = user_sessions.get(user_id)

    if session is None or session['current_index'] >= len(session['quizzes']):
        return

    if session.get('current_poll_id') != poll_answer.poll_id:
        return

    quiz = session['quizzes'][session['current_index']]
    selected_option_id = poll_answer.option_ids[0]
    question = await sync_to_async(Question.objects.get)(text=quiz['question'])
    selected_option = await sync_to_async(AnswerOption.objects.get)(
        question=question,
        text=quiz['options'][selected_option_id]
    )
    is_correct = (selected_option_id == quiz['correct_option_id'])

    user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user_id)
    await save_user_answer(user, question, selected_option, is_correct)

    if is_correct:
        session['correct'] += 1
    else:
        session['incorrect'] += 1

    session['current_index'] += 1
    await send_next_question(user_id)

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
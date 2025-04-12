import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    FSInputFile, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN
import os
from database import get_schedules_count, get_schedules_page
from admin import admin_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

class UserState(StatesGroup):
    WAITING_SECTION = State()

def load_section_text(section_name):
    try:
        file_path = os.path.join("texts", f"{section_name}.txt")
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Раздел '{section_name}' временно недоступен."

def get_section_keyboard(section_name):
    buttons = [
        [InlineKeyboardButton(text="Подробнее", callback_data=f"details_{section_name}")],
        [InlineKeyboardButton(text="Записаться", callback_data=f"register_{section_name}")],
        [InlineKeyboardButton(text="Расписание", callback_data=f"schedule_{section_name}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_keyboard():
    buttons = [
        [
            KeyboardButton(text="📅 Ближайшие мероприятия"),
            KeyboardButton(text="🎓 Образовательные программы"),
            KeyboardButton(text="👥 Группы специалистов")
        ],
        [
            KeyboardButton(text="🏫 Курсы для всех"),
            KeyboardButton(text="🎤 Лекторий"),
            KeyboardButton(text="🎬 Киноклуб")
        ],
        [
            KeyboardButton(text="💬 Псих. консультации"),
            KeyboardButton(text="🌐 Конференции"),
            KeyboardButton(text="🚀 Проекты академии")
        ],
        [
            KeyboardButton(text="📚 Библиотека материалов"),
            KeyboardButton(text="📩 Написать администратору 👨💼")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    photo = FSInputFile("images/logo.jpg")
    await message.answer_photo(photo, caption="👋 Добро пожаловать!")
    await message.answer("Выберите раздел:", reply_markup=get_main_keyboard())

@dp.message(F.text.in_([
    "📅 Ближайшие мероприятия", "🎓 Образовательные программы",
    "👥 Группы специалистов", "🏫 Курсы для всех", "🎤 Лекторий",
    "🎬 Киноклуб", "💬 Псих. консультации", "🌐 Конференции",
    "🚀 Проекты академии", "📚 Библиотека материалов"
]))
async def handle_any_section(message: types.Message, state: FSMContext):
    section_mapping = {
        "📅 Ближайшие мероприятия": "ближайшие_мероприятия",
        "🎓 Образовательные программы": "образовательные_программы",
        "👥 Группы специалистов": "группы_специалистов",
        "🏫 Курсы для всех": "курсы_для_всех",
        "🎤 Лекторий": "лекторий",
        "🎬 Киноклуб": "киноклуб",
        "💬 Псих. консультации": "псих_консультации",
        "🌐 Конференции": "конференции",
        "🚀 Проекты академии": "проекты_академии",
        "📚 Библиотека материалов": "библиотека_материалов"
    }
    
    section_name = section_mapping[message.text]
    text = load_section_text(section_name)
    await message.answer(text, reply_markup=get_section_keyboard(section_name))

@dp.callback_query(F.data.startswith("schedule_"))
async def show_schedule(callback: types.CallbackQuery):
    section_name = callback.data.split("_")[1]
    print(f"Запрошено расписание для раздела: {section_name}")  # Отладочный вывод
    
    total_schedules = get_schedules_count(section_name)
    print(f"Найдено записей: {total_schedules}")  # Отладочный вывод
    
    if total_schedules == 0:
        await callback.message.answer("Расписание пока не добавлено.")
        await callback.answer()
        return
    
    await show_schedule_page(callback.message, section_name, 1)
    await callback.answer()

async def show_schedule_page(message: types.Message, section_name: str, page: int):
    total_schedules = get_schedules_count(section_name)
    _, schedule_text = get_schedules_page(section_name, page)
    
    keyboard = []
    
    if page > 1:
        keyboard.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"schedule_page:{section_name}:{page-1}"
        ))
    
    if page < total_schedules:
        keyboard.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"schedule_page:{section_name}:{page+1}"
        ))
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
    
    await message.edit_text(
        f"📅 Расписание ({page}/{total_schedules}):\n\n{schedule_text}",
        reply_markup=reply_markup
    )

@dp.callback_query(F.data.startswith("schedule_page:"))
async def handle_schedule_page(callback: types.CallbackQuery):
    _, section_name, page_str = callback.data.split(":")
    await show_schedule_page(callback.message, section_name, int(page_str))
    await callback.answer()

async def main():
    os.makedirs("texts", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
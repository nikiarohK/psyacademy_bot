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
from database import get_schedules, get_schedule_by_id
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
    await message.answer_photo(
        photo,
        caption="""Здравствуйте! Добро пожаловать в Академию Психологического Консультирования — пространство для психологов, стремящихся к росту, поддержке и профессиональному развитию.\n\nЯ — бот Академии.\n\nГотов помочь вам сориентироваться!"""
    )
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
async def show_schedule(callback: types.CallbackQuery, state: FSMContext):
    section_name = callback.data[len("schedule_"):].strip()
    schedules = get_schedules(section_name)
    
    if not schedules:
        await callback.answer("Расписания пока не добавлены.")
        return
    
    # Удаляем предыдущее сообщение с расписанием, если есть
    try:
        data = await state.get_data()
        if "last_schedule_message_id" in data:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=data["last_schedule_message_id"]
            )
    except:
        pass
    
    # Отправляем новое сообщение
    new_message = await callback.message.answer(
        "Загружаю расписание...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Загрузка...", callback_data="loading")]])
    )
    
    await state.set_data({
        "current_index": 0,
        "schedules": schedules,
        "section_name": section_name,
        "last_schedule_message_id": new_message.message_id
    })
    
    await _show_current_schedule(new_message, state)
    await callback.answer()

async def _show_current_schedule(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_index = data["current_index"]
    schedules = data["schedules"]
    section_name = data["section_name"]
    
    schedule_id, schedule_text, details_text = schedules[current_index]
    total = len(schedules)
    
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"nav_prev_{section_name}"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="nav_current"),
            InlineKeyboardButton(text="➡️", callback_data=f"nav_next_{section_name}")
        ]
    ]
    
    if details_text:
        keyboard_buttons.append([InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"view_details_{schedule_id}")])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_{section_name}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Всегда редактируем сообщение, если это возможно
    try:
        await message.edit_text(
            f"📅 Расписание ({current_index + 1}/{total}):\n\n{schedule_text}",
            reply_markup=keyboard
        )
    except:
        # Если редактирование невозможно (новое сообщение), создаем новое
        await message.answer(
            f"📅 Расписание ({current_index + 1}/{total}):\n\n{schedule_text}",
            reply_markup=keyboard
        )
        
@dp.callback_query(F.data.startswith("nav_"))
async def navigate_schedules(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if "current_index" not in data:
        data["current_index"] = 0
    if "schedules" not in data:
        section_name = callback.data.split("_")[-1]
        schedules = get_schedules(section_name)
        if not schedules:
            await callback.answer("Нет доступных расписаний")
            return
        data["schedules"] = schedules
    if "section_name" not in data:
        data["section_name"] = callback.data.split("_")[-1]
    
    current_index = data["current_index"]
    schedules = data["schedules"]
    section_name = data["section_name"]
    total = len(schedules)
    
    action = callback.data.split("_")[1]
    
    if action == "prev":
        new_index = (current_index - 1) % total
    elif action == "next":
        new_index = (current_index + 1) % total
    else:
        await callback.answer()
        return
    
    # Удаляем предыдущее сообщение с расписанием
    try:
        if "last_schedule_message_id" in data:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=data["last_schedule_message_id"]
            )
    except:
        pass
    
    await state.update_data(current_index=new_index)
    
    # Отправляем новое сообщение и сохраняем его ID
    new_message = await callback.message.answer(
        "Загружаю расписание...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Загрузка...", callback_data="loading")]])
    )
    
    await state.update_data(last_schedule_message_id=new_message.message_id)
    
    # Показываем текущее расписание
    await _show_current_schedule(new_message, state)
    await callback.answer()

async def _show_current_schedule(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    if "current_index" not in data:
        data["current_index"] = 0
    if "schedules" not in data:
        await message.answer("Ошибка: данные расписания не найдены")
        return
    if "section_name" not in data:
        await message.answer("Ошибка: раздел не определен")
        return
    
    current_index = data["current_index"]
    schedules = data["schedules"]
    section_name = data["section_name"]
    
    schedule_id, schedule_text, details_text = schedules[current_index]
    total = len(schedules)
    
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"nav_prev_{section_name}"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="nav_current"),
            InlineKeyboardButton(text="➡️", callback_data=f"nav_next_{section_name}")
        ]
    ]
    
    if details_text:
        keyboard_buttons.append([InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"view_details_{schedule_id}")])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_{section_name}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Всегда редактируем сообщение
    await message.edit_text(
        f"📅 Расписание ({current_index + 1}/{total}):\n\n{schedule_text}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("view_details_"))
async def show_details(callback: types.CallbackQuery, state: FSMContext):
    schedule_id = int(callback.data[len("view_details_"):])
    schedule = get_schedule_by_id(schedule_id)
    
    if not schedule or not schedule[1]:
        await callback.answer("Нет дополнительной информации")
        return
    
    schedule_text, details_text = schedule
    
    # Сохраняем schedule_id в state для возврата
    data = await state.get_data()
    await state.update_data({
        "current_schedule_id": schedule_id,
        "section_name": data.get("section_name", "")
    })
    
    await callback.message.answer(
        f"🔍 Подробности:\n\n{details_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к расписанию", callback_data="back_to_schedule")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_schedule")
async def back_to_schedule(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_name = data.get("section_name", "")
    schedules = data.get("schedules", [])
    current_index = data.get("current_index", 0)
    
    if not schedules:
        await callback.answer("Ошибка: данные расписания не найдены")
        return
    
    schedule_id = data.get("current_schedule_id")
    if schedule_id:
        for i, (s_id, _, _) in enumerate(schedules):
            if s_id == schedule_id:
                current_index = i
                break
    
    # Удаляем сообщение с подробностями
    try:
        await callback.message.delete()
    except:
        pass
    
    await state.update_data(current_index=current_index)
    
    # Получаем или создаем новое сообщение для расписания
    if "last_schedule_message_id" in data:
        try:
            msg = await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=data["last_schedule_message_id"],
                text="Загружаю расписание..."
            )
            await _show_current_schedule(msg, state)
        except:
            new_message = await callback.message.answer(
                "Загружаю расписание...",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Загрузка...", callback_data="loading")]])
            )
            await state.update_data(last_schedule_message_id=new_message.message_id)
            await _show_current_schedule(new_message, state)
    else:
        new_message = await callback.message.answer(
            "Загружаю расписание...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Загрузка...", callback_data="loading")]])
        )
        await state.update_data(last_schedule_message_id=new_message.message_id)
        await _show_current_schedule(new_message, state)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("nav_back_"))
async def back_to_schedule(callback: types.CallbackQuery, state: FSMContext):
    await _show_current_schedule(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data.startswith("back_to_"))
async def back_to_section(callback: types.CallbackQuery, state: FSMContext):
    section_name = callback.data[8:]  # Убираем "back_to_"
    text = load_section_text(section_name)
    await callback.message.edit_text(text, reply_markup=get_section_keyboard(section_name))
    await state.clear()
    await callback.answer()

async def main():
    os.makedirs("texts", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
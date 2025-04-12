from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMINS
from database import add_schedule, get_schedules, delete_schedule, update_schedule_details, get_schedule_by_id, delete_schedule_by_id, get_all_schedules

admin_router = Router()

class AdminStates(StatesGroup):
    ADD_SCHEDULE = State()
    EDIT_DETAILS = State()
    CONFIRM_DELETE = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def get_admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Добавить расписание")],
            [KeyboardButton(text="✏️ Управление расписаниями")],
            [KeyboardButton(text="🗑 Удалить расписание")],
            [KeyboardButton(text="🔙 В главное меню")]
        ],
        resize_keyboard=True
    )

def get_sections_keyboard(action: str):
    sections = [
        ("📅 Ближайшие мероприятия", "events"),
        ("🎓 Образовательные программы", "edu"),
        ("👥 Группы специалистов", "groups"),
        ("🏫 Курсы для всех", "courses"),
        ("🎤 Лекторий", "lectures"),
        ("🎬 Киноклуб", "films"),
        ("💬 Псих. консультации", "consult"),
        ("🌐 Конференции", "conf"),
        ("🚀 Проекты академии", "projects"),
        ("📚 Библиотека материалов", "library")
    ]
    
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"admin_{action}:{section}")]
        for name, section in sections
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_section_name(section_code: str) -> str:
    section_map = {
        "events": "ближайшие_мероприятия",
        "edu": "образовательные_программы",
        "groups": "группы_специалистов",
        "courses": "курсы_для_всех",
        "lectures": "лекторий",
        "films": "киноклуб",
        "consult": "псих_консультации",
        "conf": "конференции",
        "projects": "проекты_академии",
        "library": "библиотека_материалов"
    }
    return section_map.get(section_code, section_code)

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return
    
    await message.answer(
        "👨💼 Админ-панель\nВыберите действие:",
        reply_markup=get_admin_main_keyboard()
    )

@admin_router.message(F.text == "🔙 В главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True))

@admin_router.message(F.text == "📝 Добавить расписание")
async def add_schedule_handler(message: types.Message):
    await message.answer(
        "Выберите раздел для добавления расписания:",
        reply_markup=get_sections_keyboard("add")
    )

@admin_router.message(F.text == "✏️ Управление расписаниями")
async def manage_schedules_handler(message: types.Message):
    await message.answer(
        "Выберите раздел для управления расписаниями:",
        reply_markup=get_sections_keyboard("manage")
    )

@admin_router.message(F.text == "🗑 Удалить расписание")
async def delete_schedule_handler(message: types.Message, state: FSMContext):
    schedules = get_all_schedules()
    if not schedules:
        await message.answer("Нет доступных расписаний для удаления.")
        return
    
    buttons = []
    for schedule_id, section_name, schedule_text in schedules:
        short_text = schedule_text[:30] + "..." if len(schedule_text) > 30 else schedule_text
        buttons.append(
            [InlineKeyboardButton(
                text=f"{section_name}: {short_text}", 
                callback_data=f"delete_{schedule_id}"
            )]
        )
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await message.answer(
        "Выберите расписание для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "👨💼 Админ-панель\nВыберите действие:",
        reply_markup=get_admin_main_keyboard()
    )
    try:
        await callback.message.delete()
    except:
        pass
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_add:"))
async def admin_add_schedule_section(callback: types.CallbackQuery, state: FSMContext):
    section_code = callback.data.split(":")[1]
    section_name = get_section_name(section_code)
    
    await state.set_state(AdminStates.ADD_SCHEDULE)
    await state.update_data(section_name=section_name)
    
    await callback.message.edit_text(
        f"Введите текст расписания для раздела {section_name}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
        ])
    )
    await callback.answer()

@admin_router.message(AdminStates.ADD_SCHEDULE)
async def admin_save_schedule(message: types.Message, state: FSMContext):
    data = await state.get_data()
    section_name = data.get("section_name")
    
    add_schedule(section_name, message.text)
    await message.answer("✅ Расписание успешно добавлено!", reply_markup=get_admin_main_keyboard())
    await state.clear()

@admin_router.callback_query(F.data.startswith("admin_manage:"))
async def admin_show_schedules(callback: types.CallbackQuery, state: FSMContext):
    section_code = callback.data.split(":")[1]
    section_name = get_section_name(section_code)
    schedules = get_schedules(section_name)
    
    if not schedules:
        await callback.answer("Нет расписаний для этого раздела")
        return
    
    buttons = []
    for schedule_id, schedule_text, details_text in schedules:
        short_text = schedule_text[:30] + "..." if len(schedule_text) > 30 else schedule_text
        row = [
            InlineKeyboardButton(text=f"🗑️ {short_text}", callback_data=f"admin_delete:{schedule_id}"),
            InlineKeyboardButton(text="✏️ Подробнее", callback_data=f"admin_edit:{schedule_id}")
        ]
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await callback.message.edit_text(
        f"Управление расписаниями для раздела {section_name}:\n\n"
        "🗑️ - удалить расписание\n"
        "✏️ - редактировать 'Подробнее'",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_edit:"))
async def admin_edit_details(callback: types.CallbackQuery, state: FSMContext):
    schedule_id = int(callback.data.split(":")[1])
    schedule = get_schedule_by_id(schedule_id)
    
    if not schedule:
        await callback.answer("Расписание не найдено")
        return
    
    schedule_text, details_text = schedule
    
    await state.set_state(AdminStates.EDIT_DETAILS)
    await state.update_data({
        "schedule_id": schedule_id,
        "current_details": details_text
    })
    
    message_text = f"Текущее расписание:\n\n{schedule_text}\n\n"
    if details_text:
        message_text += f"Текущие подробности:\n{details_text}\n\n"
    message_text += "Введите новый текст для 'Подробнее' или отправьте '-' чтобы удалить:"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data=f"admin_back")]
        ])
    )
    await callback.answer()

@admin_router.message(AdminStates.EDIT_DETAILS)
async def admin_save_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    new_details = message.text if message.text != "-" else None
    
    update_schedule_details(schedule_id, new_details)
    await message.answer("✅ 'Подробнее' успешно обновлены!", reply_markup=get_admin_main_keyboard())
    await state.clear()

@admin_router.callback_query(F.data.startswith("admin_delete:"))
async def admin_delete_schedule(callback: types.CallbackQuery):
    schedule_id = int(callback.data.split(":")[1])
    delete_schedule(schedule_id)
    await callback.message.edit_text("✅ Расписание успешно удалено!")
    await callback.answer()

@admin_router.callback_query(F.data.startswith("delete_"))
async def select_schedule_to_delete(callback: types.CallbackQuery, state: FSMContext):
    schedule_id = int(callback.data.split("_")[1])
    await state.set_state(AdminStates.CONFIRM_DELETE)
    await state.update_data(schedule_id=schedule_id)
    
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить это расписание?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="confirm_delete")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="admin_back")]
        ])
    )
    await callback.answer()

@admin_router.callback_query(F.data == "confirm_delete", AdminStates.CONFIRM_DELETE)
async def confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    
    delete_schedule_by_id(schedule_id)
    await callback.message.edit_text("✅ Расписание успешно удалено!")
    await state.clear()
    await callback.answer()
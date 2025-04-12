from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from database import add_schedule, get_latest_schedule, delete_schedule

admin_router = Router()

class AdminStates(StatesGroup):
    ADD_SCHEDULE = State()
    DELETE_SCHEDULE = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Добавить расписание", callback_data="admin_add")],
        [InlineKeyboardButton(text="❌ Удалить расписание", callback_data="admin_delete")]
    ])

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

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👨💼 Админ-панель\nВыберите действие:",
        reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_add")
async def admin_add_schedule_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел для добавления расписания:",
        reply_markup=get_sections_keyboard("add")
    )
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
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_add")]
        ])
    )
    await callback.answer()

@admin_router.message(AdminStates.ADD_SCHEDULE)
async def admin_save_schedule(message: types.Message, state: FSMContext):
    data = await state.get_data()
    section_name = data.get("section_name")
    
    add_schedule(section_name, message.text)
    await message.answer("✅ Расписание успешно обновлено!")
    await state.clear()

@admin_router.callback_query(F.data == "admin_delete")
async def admin_delete_schedule_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел для удаления расписания:",
        reply_markup=get_sections_keyboard("delete")
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_delete:"))
async def admin_confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    section_code = callback.data.split(":")[1]
    section_name = get_section_name(section_code)
    schedule_text = get_latest_schedule(section_name)
    
    if not schedule_text:
        await callback.answer("Нет расписания для удаления")
        return
    
    await state.set_state(AdminStates.DELETE_SCHEDULE)
    await state.update_data(section_name=section_name)
    
    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить расписание для раздела {section_name}?\n\n"
        f"Текущее расписание:\n{schedule_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data="admin_confirm_delete")],
            [InlineKeyboardButton(text="❌ Нет, отменить", callback_data="admin_delete")]
        ])
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_confirm_delete")
async def admin_execute_delete(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    section_name = data.get("section_name")
    
    delete_schedule(section_name)
    await callback.message.edit_text("✅ Расписание успешно удалено!")
    await state.clear()
    await callback.answer()
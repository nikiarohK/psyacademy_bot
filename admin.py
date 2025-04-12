from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from database import add_schedule, get_schedules_count, get_schedules_page, delete_schedule

admin_router = Router()

class AdminStates(StatesGroup):
    ADD_SCHEDULE = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Управление расписанием", callback_data="admin_schedule")],
        [InlineKeyboardButton(text="📝 Добавить расписание", callback_data="admin_add")],
        [InlineKeyboardButton(text="❌ Удалить расписание", callback_data="admin_delete")]
    ])

def get_admin_sections_keyboard(action: str):
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

@admin_router.callback_query(F.data == "admin_schedule")
async def admin_schedule(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел для просмотра расписания:",
        reply_markup=get_admin_sections_keyboard("view")
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_view:"))
async def admin_view_schedule(callback: types.CallbackQuery):
    section_code = callback.data.split(":")[1]
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
    section_name = section_map.get(section_code)
    total_schedules = get_schedules_count(section_name)
    
    if total_schedules == 0:
        await callback.message.edit_text(
            "Расписание не добавлено",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_schedule")]
            ])
        )
        await callback.answer()
        return
    
    await show_admin_schedule_page(callback.message, section_name, section_code, 1)
    await callback.answer()

async def show_admin_schedule_page(message: types.Message, section_name: str, section_code: str, page: int):
    total_schedules = get_schedules_count(section_name)
    schedule_id, schedule_text = get_schedules_page(section_name, page)
    
    keyboard = []
    
    if page > 1:
        keyboard.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"admin_view_page:{section_code}:{page-1}"
        ))
    
    if page < total_schedules:
        keyboard.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"admin_view_page:{section_code}:{page+1}"
        ))
    
    keyboard.append(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_schedule"
    ))
    
    await message.edit_text(
        f"📋 Расписание ({page}/{total_schedules}):\n\nID: {schedule_id}\n{schedule_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard])
    )

@admin_router.callback_query(F.data.startswith("admin_view_page:"))
async def handle_admin_schedule_page(callback: types.CallbackQuery):
    _, section_code, page_str = callback.data.split(":")
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
    section_name = section_map.get(section_code)
    await show_admin_schedule_page(callback.message, section_name, section_code, int(page_str))
    await callback.answer()

@admin_router.callback_query(F.data == "admin_add")
async def admin_add_schedule_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел для добавления расписания:",
        reply_markup=get_admin_sections_keyboard("add")
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_add:"))
async def admin_add_schedule_section(callback: types.CallbackQuery, state: FSMContext):
    section_code = callback.data.split(":")[1]
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
    section_name = section_map.get(section_code)
    
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
    await message.answer("✅ Расписание успешно добавлено!")
    await state.clear()

@admin_router.callback_query(F.data == "admin_delete")
async def admin_delete_schedule_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел для удаления расписания:",
        reply_markup=get_admin_sections_keyboard("delete")
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_delete:"))
async def admin_delete_schedule_section(callback: types.CallbackQuery):
    section_code = callback.data.split(":")[1]
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
    section_name = section_map.get(section_code)
    schedules = get_schedules_page(section_name, 1, 100)  # Получаем все записи
    
    if not schedules:
        await callback.answer("Нет записей для удаления")
        return
    
    buttons = [
        [InlineKeyboardButton(text=f"ID: {id} - {text[:20]}...", callback_data=f"admin_confirm:{id}")]
        for id, text in schedules
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_delete")])
    
    await callback.message.edit_text(
        "Выберите запись для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm_delete(callback: types.CallbackQuery):
    schedule_id = int(callback.data.split(":")[1])
    delete_schedule(schedule_id)
    await callback.message.edit_text("✅ Запись успешно удалена!")
    await callback.answer()
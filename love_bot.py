import os
import logging
import random
import json
import pickle
from datetime import datetime, timedelta, timezone, time
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.ext import JobQueue
from enum import Enum

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройки
ANNIVERSARY_DATE = datetime(2026, 10, 26)
START_DATE = datetime(2024, 10, 26)
TIMEZONE_OFFSET = 3

# Файлы для сохранения
CHAT_IDS_FILE = "chat_ids.json"
NOTES_FILE = "notes.pkl"

def load_chat_ids():
    """Загружает chat_id из файла"""
    try:
        if os.path.exists(CHAT_IDS_FILE):
            with open(CHAT_IDS_FILE, 'r') as f:
                data = json.load(f)
                return set(data)
        return set()
    except Exception as e:
        logger.error(f"Ошибка загрузки chat_ids: {e}")
        return set()

def save_chat_ids():
    """Сохраняет chat_id в файл"""
    try:
        with open(CHAT_IDS_FILE, 'w') as f:
            json.dump(list(CHAT_IDS), f)
    except Exception as e:
        logger.error(f"Ошибка сохранения chat_ids: {e}")

def load_notes():
    """Загружает заметки из файла"""
    try:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'rb') as f:
                return pickle.load(f)
        return {}
    except Exception as e:
        logger.error(f"Ошибка загрузки заметок: {e}")
        return {}

def save_notes():
    """Сохраняет заметки в файл"""
    try:
        with open(NOTES_FILE, 'wb') as f:
            pickle.dump(NOTES, f)
    except Exception as e:
        logger.error(f"Ошибка сохранения заметок: {e}")

# Хранилища
CHAT_IDS = load_chat_ids()
NOTES = load_notes()  # Формат: {chat_id: [list_of_notes]}

# Состояния для создания заметок
class NoteState(Enum):
    SELECTING_TYPE = 1
    ENTERING_TEXT = 2
    SELECTING_DATE = 3
    SELECTING_TIME = 4
    CONFIRMING = 5

# Типы заметок
NOTE_TYPES = {
    "💭 Мысль": "Запиши интересную мысль или идею",
    "📅 Напоминание": "О чем нужно не забыть",
    "💕 Воспоминание": "Что-то важное, что хочется сохранить",
    "🎯 Цель": "Что хочешь сделать или достичь",
    "📖 Цитата": "Красивая фраза или цитата",
    "🎁 Сюрприз": "Идея для подарка или сюрприза",
    "❤️ Признание": "Что хочешь сказать любимому",
    "✨ Вдохновение": "Что вдохновляет тебя сегодня",
    "🍀 Желание": "О чем мечтаешь или хочешь",
    "📝 Список": "Список дел или покупок"
}

LOVE_MESSAGES = [
    "Я тебя очень люблю, зай))💕",
    # ... (остальные сообщения без изменений)
]

HOLIDAYS = {
    # ... (праздники без изменений)
}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_correct_form(number, forms):
    """Возвращает правильную форму слова для числа"""
    if number % 10 == 1 and number % 100 != 11:
        return forms[0]
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        return forms[1]
    else:
        return forms[2]

def create_main_keyboard():
    """Создает нижнее меню с основными командами"""
    keyboard = [
        ["📅 До годовщины", "💝 Случайное сообщение"],
        ["🎉 До праздников", "📊 Дней вместе"],
        ["📝 Мои заметки"]  # Новая кнопка!
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_note_type_keyboard():
    """Создает клавиатуру для выбора типа заметки"""
    keyboard = []
    row = []
    for i, (note_type, description) in enumerate(NOTE_TYPES.items(), 1):
        row.append(InlineKeyboardButton(note_type, callback_data=f"note_type_{note_type}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")])
    return InlineKeyboardMarkup(keyboard)

def create_date_keyboard():
    """Создает клавиатуру для выбора даты"""
    keyboard = []
    today = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
    
    # Сегодня, завтра, послезавтра
    keyboard.append([
        InlineKeyboardButton("Сегодня", callback_data=f"date_{today.strftime('%Y-%m-%d')}"),
        InlineKeyboardButton("Завтра", callback_data=f"date_{(today + timedelta(days=1)).strftime('%Y-%m-%d')}"),
        InlineKeyboardButton("Послезавтра", callback_data=f"date_{(today + timedelta(days=2)).strftime('%Y-%m-%d')}")
    ])
    
    # Через неделю, через месяц
    keyboard.append([
        InlineKeyboardButton("Через неделю", callback_data=f"date_{(today + timedelta(days=7)).strftime('%Y-%m-%d')}"),
        InlineKeyboardButton("Через месяц", callback_data=f"date_{(today + timedelta(days=30)).strftime('%Y-%m-%d')}")
    ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")])
    return InlineKeyboardMarkup(keyboard)

def create_time_keyboard():
    """Создает клавиатуру для выбора времени"""
    keyboard = []
    times = [
        "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", 
        "15:00", "16:00", "17:00", "18:00", "19:00", "20:00",
        "21:00", "22:00", "23:00"
    ]
    
    row = []
    for i, t in enumerate(times, 1):
        row.append(InlineKeyboardButton(t, callback_data=f"time_{t}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")])
    return InlineKeyboardMarkup(keyboard)

def create_notes_list_keyboard(notes, page=0):
    """Создает клавиатуру для списка заметок"""
    keyboard = []
    notes_per_page = 5
    start_idx = page * notes_per_page
    end_idx = start_idx + notes_per_page
    
    for note in notes[start_idx:end_idx]:
        note_date = note['date'].strftime('%d.%m')
        note_time = note['time']
        emoji = list(NOTE_TYPES.keys())[list(NOTE_TYPES.values()).index(note['type'])] if note['type'] in NOTE_TYPES.values() else "📝"
        btn_text = f"{emoji} {note_date} {note_time} - {note['text'][:20]}..."
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"view_note_{note['id']}")])
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"notes_page_{page-1}"))
    
    if end_idx < len(notes):
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"notes_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton("➕ Новая заметка", callback_data="new_note"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_notes")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_note_detail_keyboard(note_id):
    """Создает клавиатуру для детального просмотра заметки"""
    keyboard = [
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_note_{note_id}")],
        [InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_list_0")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики команд (остальные без изменений)
async def start_command(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    CHAT_IDS.add(chat_id)
    save_chat_ids()
    
    welcome_text = f"""💕 Привет, моя любимая девочка))

Это наш ботик с разными прикольными штучками) 

📅 До годовщины - сколько дней до нашего дня
💝 Случайное сообщение - милая плюшка)
🎉 До праздников - сколько до них осталось
📊 Дней вместе - сколько дней мы уже вместе
📝 Мои заметки - создавай заметки с напоминаниями!

Я тебя очень-очень люблю)) Ты у меня самая прекрасная))💕

С любовью, твой Никитка))❤️"""

    await update.message.reply_text(
        welcome_text, 
        reply_markup=create_main_keyboard()
    )
    logger.info(f"Пользователь {user.id} запустил бота")

# ... (остальные команды: days_command, love_command, holidays_command, days_together_command без изменений)

async def notes_command(update, context):
    """Обработчик команды для заметок"""
    chat_id = update.effective_chat.id
    
    if chat_id not in NOTES:
        NOTES[chat_id] = []
        save_notes()
    
    # Фильтруем только активные заметки (будущие)
    now = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
    active_notes = []
    
    if chat_id in NOTES:
        for note in NOTES[chat_id]:
            note_datetime = datetime.strptime(f"{note['date']} {note['time']}", "%Y-%m-%d %H:%M")
            if note_datetime > now:
                active_notes.append(note)
    
    if not active_notes:
        message = "📝 У тебя пока нет активных заметок. Хочешь создать первую?"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Создать заметку", callback_data="new_note")],
            [InlineKeyboardButton("❌ Закрыть", callback_data="close_notes")]
        ])
    else:
        message = f"📋 Твои заметки ({len(active_notes)} активных):"
        keyboard = create_notes_list_keyboard(active_notes)
    
    await update.message.reply_text(message, reply_markup=keyboard)

async def handle_callback_query(update, context):
    """Обработчик нажатий на inline кнопки"""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    data = query.data
    
    # Создание новой заметки
    if data == "new_note":
        await query.edit_message_text(
            "📝 Выбери тип заметки:",
            reply_markup=create_note_type_keyboard()
        )
        context.user_data['note_state'] = NoteState.SELECTING_TYPE
        return
    
    # Выбор типа заметки
    elif data.startswith("note_type_"):
        note_type = data.replace("note_type_", "")
        context.user_data['note_type'] = note_type
        context.user_data['note_state'] = NoteState.ENTERING_TEXT
        
        description = NOTE_TYPES.get(note_type, "Заметка")
        await query.edit_message_text(
            f"✍️ {description}\n\nНапиши текст заметки (до 500 символов):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")]])
        )
        return
    
    # Отмена создания заметки
    elif data == "cancel_note":
        await query.edit_message_text(
            "Создание заметки отменено ❌",
            reply_markup=create_main_keyboard()
        )
        if 'note_state' in context.user_data:
            del context.user_data['note_state']
        return
    
    # Закрыть список заметок
    elif data == "close_notes":
        await query.edit_message_text(
            "Заметки закрыты 📝",
            reply_markup=create_main_keyboard()
        )
        return
    
    # Просмотр заметки
    elif data.startswith("view_note_"):
        note_id = int(data.replace("view_note_", ""))
        
        if chat_id in NOTES:
            for note in NOTES[chat_id]:
                if note['id'] == note_id:
                    note_date = note['date'].strftime('%d.%m.%Y')
                    message = f"""📝 **Заметка**\n
🗓 Дата: {note_date} в {note['time']}
🏷 Тип: {note['type']}
📄 Текст:\n{note['text']}
"""
                    await query.edit_message_text(
                        message,
                        reply_markup=create_note_detail_keyboard(note_id)
                    )
                    return
        
        await query.edit_message_text("Заметка не найдена ❌")
        return
    
    # Удаление заметки
    elif data.startswith("delete_note_"):
        note_id = int(data.replace("delete_note_", ""))
        
        if chat_id in NOTES:
            NOTES[chat_id] = [n for n in NOTES[chat_id] if n['id'] != note_id]
            save_notes()
            
            # Показываем обновленный список
            now = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
            active_notes = [n for n in NOTES.get(chat_id, []) 
                          if datetime.strptime(f"{n['date']} {n['time']}", "%Y-%m-%d %H:%M") > now]
            
            if not active_notes:
                await query.edit_message_text(
                    "✅ Заметка удалена! У тебя больше нет активных заметок.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Новая заметка", callback_data="new_note")]])
                )
            else:
                await query.edit_message_text(
                    f"✅ Заметка удалена! Осталось {len(active_notes)} заметок:",
                    reply_markup=create_notes_list_keyboard(active_notes)
                )
        return
    
    # Навигация по страницам
    elif data.startswith("notes_page_"):
        page = int(data.replace("notes_page_", ""))
        
        now = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
        active_notes = [n for n in NOTES.get(chat_id, []) 
                      if datetime.strptime(f"{n['date']} {n['time']}", "%Y-%m-%d %H:%M") > now]
        
        await query.edit_message_text(
            f"📋 Твои заметки ({len(active_notes)} активных):",
            reply_markup=create_notes_list_keyboard(active_notes, page)
        )
        return
    
    # Назад к списку
    elif data.startswith("back_to_list_"):
        page = int(data.replace("back_to_list_", ""))
        
        now = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
        active_notes = [n for n in NOTES.get(chat_id, []) 
                      if datetime.strptime(f"{n['date']} {n['time']}", "%Y-%m-%d %H:%M") > now]
        
        await query.edit_message_text(
            f"📋 Твои заметки ({len(active_notes)} активных):",
            reply_markup=create_notes_list_keyboard(active_notes, page)
        )
        return

async def handle_message(update, context):
    """Обработчик обычных сообщений"""
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Обработка нажатий кнопок меню
    if user_text == "📅 До годовщины":
        await days_command(update, context)
    elif user_text == "💝 Случайное сообщение":
        await love_command(update, context)
    elif user_text == "🎉 До праздников":
        await holidays_command(update, context)
    elif user_text == "📊 Дней вместе":
        await days_together_command(update, context)
    elif user_text == "📝 Мои заметки":
        await notes_command(update, context)
    
    # Обработка создания заметки (ввод текста)
    elif 'note_state' in context.user_data:
        state = context.user_data['note_state']
        
        if state == NoteState.ENTERING_TEXT:
            if len(user_text) > 500:
                await update.message.reply_text(
                    "❌ Текст слишком длинный (максимум 500 символов). Попробуй короче:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_note")]])
                )
                return
            
            context.user_data['note_text'] = user_text
            context.user_data['note_state'] = NoteState.SELECTING_DATE
            
            await update.message.reply_text(
                "📅 Выбери дату для напоминания:",
                reply_markup=create_date_keyboard()
            )
        
        # Пропускаем другие состояния - они обрабатываются через кнопки
    
    # Обработка обычных сообщений (без изменений)
    elif any(word in user_text.lower() for word in ['привет', 'пивет', 'hi', 'здаров']):
        await update.message.reply_text("Привет, любимая)💕", reply_markup=create_main_keyboard())
    elif any(word in user_text.lower() for word in ['люблю', 'love', 'обожаю']):
        await update.message.reply_text("Я тебя тоже очень люблю))💕", reply_markup=create_main_keyboard())
    elif any(word in user_text.lower() for word in ['муаа', 'муа', 'целую']):
        await update.message.reply_text("Муа муа муаа муа муа муаа))💕", reply_markup=create_main_keyboard())
    elif any(word in user_text.lower() for word in ['скучаю', 'скучаешь', 'miss']):
        await update.message.reply_text("Я тоже очень по тебе скучаю) С нетерпением жду нашей встречи)) 💖", reply_markup=create_main_keyboard())
    else:
        await update.message.reply_text(
            'Я тебя не совсем понял, солнышко) 💕\nИспользуй кнопки меню внизу ❤️',
            reply_markup=create_main_keyboard()
        )

async def handle_button_callback(update, context):
    """Обработчик для inline кнопок (дата и время)"""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    data = query.data
    
    # Выбор даты
    if data.startswith("date_"):
        selected_date = data.replace("date_", "")
        context.user_data['note_date'] = selected_date
        context.user_data['note_state'] = NoteState.SELECTING_TIME
        
        await query.edit_message_text(
            f"📅 Дата: {selected_date}\n\n🕐 Выбери время напоминания:",
            reply_markup=create_time_keyboard()
        )
    
    # Выбор времени
    elif data.startswith("time_"):
        selected_time = data.replace("time_", "")
        selected_date = context.user_data.get('note_date')
        note_type = context.user_data.get('note_type')
        note_text = context.user_data.get('note_text')
        
        # Создаем объект заметки
        note_id = len(NOTES.get(chat_id, [])) + 1
        
        note = {
            'id': note_id,
            'type': note_type,
            'text': note_text,
            'date': datetime.strptime(selected_date, "%Y-%m-%d"),
            'time': selected_time,
            'created_at': datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
        }
        
        # Сохраняем заметку
        if chat_id not in NOTES:
            NOTES[chat_id] = []
        NOTES[chat_id].append(note)
        save_notes()
        
        # Очищаем временные данные
        for key in ['note_state', 'note_type', 'note_text', 'note_date']:
            if key in context.user_data:
                del context.user_data[key]
        
        # Форматируем дату для отображения
        display_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime('%d.%m.%Y')
        
        await query.edit_message_text(
            f"✅ Заметка создана!\n\n"
            f"🗓 **Напоминание установлено на:**\n"
            f"{display_date} в {selected_time}\n\n"
            f"📄 Текст: {note_text[:50]}...\n\n"
            f"Я обязательно напомню тебе об этом в указанное время! 💕",
            reply_markup=create_main_keyboard()
        )
        
        logger.info(f"Создана заметка для chat_id {chat_id}: {note_type} на {selected_date} {selected_time}")

async def send_note_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет и отправляет напоминания о заметках"""
    if not context.bot:
        return
    
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc + timedelta(hours=TIMEZONE_OFFSET)
    current_time = now_moscow.strftime("%H:%M")
    current_date = now_moscow.strftime("%Y-%m-%d")
    
    for chat_id, notes in list(NOTES.items()):
        notes_to_remove = []
        
        for note in notes:
            note_date = note['date'].strftime("%Y-%m-%d")
            note_time = note['time']
            
            # Проверяем, наступило ли время напоминания
            if note_date == current_date and note_time == current_time:
                try:
                    # Отправляем напоминание
                    message = f"📢 **Напоминание!**\n\n{note['text']}\n\n💭 *Это была твоя заметка типа: {note['type']}*"
                    await context.bot.send_message(chat_id=chat_id, text=message)
                    logger.info(f"Отправлено напоминание о заметке в chat_id: {chat_id}")
                    
                    # Помечаем для удаления (одноразовое напоминание)
                    notes_to_remove.append(note)
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки напоминания в chat_id {chat_id}: {e}")
        
        # Удаляем отправленные заметки
        if notes_to_remove:
            NOTES[chat_id] = [n for n in NOTES[chat_id] if n not in notes_to_remove]
            save_notes()

# ... (остальные функции: send_daily_reminder, send_holiday_reminders без изменений)

def main():
    """Основная функция"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден!")
        return
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        job_queue = application.job_queue
        
        if job_queue is None:
            logger.error("JobQueue не инициализирована!")
            return
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("days", days_command))
        application.add_handler(CommandHandler("love", love_command))
        application.add_handler(CommandHandler("holidays", holidays_command))
        application.add_handler(CommandHandler("together", days_together_command))
        application.add_handler(CommandHandler("notes", notes_command))
        
        # Обработчики inline кнопок
        application.add_handler(CallbackQueryHandler(handle_callback_query, pattern="^(new_note|note_type_|cancel_note|view_note_|delete_note_|notes_page_|back_to_list_|close_notes)"))
        application.add_handler(CallbackQueryHandler(handle_button_callback, pattern="^(date_|time_)"))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Настраиваем ежедневные задачи
        daily_time = time(hour=10, minute=0)
        holiday_time = time(hour=21, minute=0)
        notes_check_time = time(hour=20, minute=55)  # Проверка каждую минуту
        
        # Ежедневное напоминание
        job_queue.run_daily(
            send_daily_reminder,
            time=daily_time,
            days=tuple(range(7)),
            name="daily_reminder"
        )
        
        # Проверка праздников
        job_queue.run_daily(
            send_holiday_reminders,
            time=holiday_time,
            days=tuple(range(7)),
            name="holiday_reminders"
        )
        
        # Проверка заметок (каждую минуту)
        job_queue.run_repeating(
            send_note_reminders,
            interval=60,  # 60 секунд
            first=10,     # Начать через 10 секунд после запуска
            name="note_reminders"
        )
        
        print("✅ Бот запущен с функцией ЗАМЕТОК!")
        print("📝 Новая функция: Заметки с напоминаниями")
        print("⏰ Проверка заметок: каждую минуту")
        print("🚀 Бот готов к работе!")
        
        application.run_polling(allowed_updates=["message", "callback_query"])
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()





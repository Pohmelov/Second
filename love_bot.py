import os
import logging
import random
import json
from datetime import datetime, timedelta, timezone
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv('BOT_TOKEN')  # Получаем токен из переменных окружения

# Настройки
ANNIVERSARY_DATE = datetime(2026, 10, 26)  # Годовщина 26 октября 2026
START_DATE = datetime(2024, 10, 26)  # Дата начала отношений
TIMEZONE_OFFSET = 3  # Московское время UTC+3

# Файл для сохранения chat_id
CHAT_IDS_FILE = "chat_ids.json"

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

# Хранилище для ID чатов
CHAT_IDS = load_chat_ids()

# Список любовных сообщений для случайной отправки
LOVE_MESSAGES = [
    "Я тебя очень люблю, зай))💕",
    "Ты самая лучшая девушка на свете))🌟❤️",
    "Каждый день с тобой - это счастье))💕",
    "Спасибо, что ты есть у меня, малыш❤️",
    "Я постоянно думаю о тебе, миленькая моя))💭💕",
    "Ты мой мир, моя вселенная, мое все))❤️",
    "Любви тебе, моя принцесса)👑💕",
    "Обнимаю тебя крепко-крепко и не отпускаю))💕",
    "Целую и обнимаю)\nмуа муа муа))❤️",
    "Просто хотел напомнить, что ты лучшая💗",
    "Ты в моих мыслях. Как всегда))❤️", 
    "Ты — причина моей улыбки))💕",
    "Я безумно по тебе скучаю, милая моя)",
    "Ты вдохновляешь меня становиться лучше каждый день.",
    "Как же мне повезло в жизни найти тебя))❤️",
    "Мне не хватает твоего тепла рядом..",
    "Любовь к тебе — это не чувство, а мое новое состояние души❤️",
    "Моя любовь к тебе не имеет границ, начала и конца❤️",
    "Ты мое самое дорогое сокровище))💕",
    "Очень надеюсь, что при встрече не ослепну от твоей красоты))❤️",
    "Ты слаще любого Nuts))❤️"
]

# Праздники с сообщениями для уведомлений
HOLIDAYS = {
    "🎄 Новый Год": {
        "date": datetime(2026, 1, 1),
        "day_before_message": "🎄 До Нового Года остался всего 1 день!! Готовь бенгальские огоньки))✨",
        "day_of_message": "🎉🎄 C Новым Годом, миленькая моя девочка!))🎊\nПусть этот год принесет нам много счастливых моментов вместе!) Я тебя очень люблю))💕"
    },
    "⭐ Рождество": {
        "date": datetime(2026, 1, 7),
        "day_before_message": "⭐ Завтра Рождество, котеночек)",
        "day_of_message": "⭐ С Рождеством Христовым, моя хорошая! Пусть в твоей жизни будет много света и пусть ангел-хранитель оберегает тебя))⭐"
    },
    "🛡️ 23 февраля": {
        "date": datetime(2026, 2, 23),
        "day_before_message": "Бегом в магазин за камуфляжными носочками)",  # Без уведомления
        "day_of_message": "УиииИиИии, поздравь всех твоих родных и настоящих "      # Без уведомления
    },
    "🌺 8 Марта": {
        "date": datetime(2026, 3, 8),
        "day_before_message": "🌺 Завтра 8 Марта) Готовься к комплиментам, моя прекрасная))",
        "day_of_message": "🌺 С 8 Марта, самая красивая и нежная девушка на свете!)) Ты - мое весеннее солнышко!))💐"
    },
    "🎉 🎂 Твой День Рождения": {
        "date": datetime(2026, 3, 18),
        "day_before_message": "🎂 Завтра твой День Рождения!! Готовься к самому лучшему дню в году!)",
        "day_of_message": "🎉 Солнышко мое любимое)) С днем рождения тебя!!)) 🎊\nЖелаю тебе всего самого прекрасного, малыш)) Ты заслуживаешь весь мир!))\nЯ тебя безумно сильно люблю!))💝"
    },
    "🍮 🐣 Пасха": {
        "date": datetime(2026, 4, 12),
        "day_before_message": "🐣 Завтра Пасха! Готовимся к светлому празднику))",
        "day_of_message": "🍮 Христос Воскрес, моя хорошая!) Пусть в твоей жизни всегда будет вера, надежда и любовь))💝"
    },
    "🎉 🎂 Мой День Рождения": {
        "date": datetime(2026, 5, 12),
        "day_before_message": "У кого-то днюшка скоро? Не знаю, я не в курсе",  # Без уведомления
        "day_of_message": "УИУИУИУУИУИУ"      # Без уведомления
    },
    "☀️ Первый день лета": {
        "date": datetime(2026, 6, 1),
        "day_before_message": "☀️ Завтра первый день лета))",
        "day_of_message": "☀️ С первым днем лета, мое солнышко!))\nПусть это лето будет самым теплым и счастливым для нас))🌞"
    },
    "❤️ Наша годовщина": {
        "date": datetime(2026, 10, 26),
        "day_before_message": "💝 Завтра наша годовщина!! Я так тебя люблю и жду этот день!)",
        "day_of_message": "🎉 С НАШЕЙ ГОДОВЩИНОЙ, МОЯ ЛЮБИМАЯ!!! 💕\nЭто самый счастливый день в моей жизни! Спасибо, что ты со мной!\nЯ тебя безумно люблю, малышечка моя, Нинуличка))💖"
    },
}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_main_keyboard():
    """Создает нижнее меню с основными командами"""
    keyboard = [
        ["📅 До годовщины", "💝 Случайное сообщение"],
        ["🎉 До праздников", "📊 Дней вместе"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_days_until_anniversary():
    """Вычисляет сколько дней осталось до годовщины"""
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc + timedelta(hours=TIMEZONE_OFFSET)
    current_date = now_moscow.date()
    
    # Вычисляем разницу в днях
    next_anniversary = ANNIVERSARY_DATE.replace(year=current_date.year)
    if next_anniversary.date() < current_date:
        next_anniversary = next_anniversary.replace(year=current_date.year + 1)
    
    return (next_anniversary.date() - current_date).days

def get_days_together():
    """Вычисляет сколько дней мы уже вместе"""
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc + timedelta(hours=TIMEZONE_OFFSET)
    current_date = now_moscow.date()
    
    days_together = (current_date - START_DATE.date()).days
    return days_together

def get_days_until_holiday(holiday_date):
    """Вычисляет сколько дней осталось до праздника"""
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc + timedelta(hours=TIMEZONE_OFFSET)
    current_date = now_moscow.date()
    
    # Вычисляем разницу в днях
    next_holiday = holiday_date.replace(year=current_date.year)
    if next_holiday.date() < current_date:
        next_holiday = next_holiday.replace(year=current_date.year + 1)
    
    return (next_holiday.date() - current_date).days

async def start_command(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Сохраняем ID чата для ежедневных уведомлений
    CHAT_IDS.add(chat_id)
    save_chat_ids()
    
    days_together = get_days_together()
    
    welcome_text = f"""💕 Привет, моя любимая девочка))

Это наш ботик с разными прикольными штучками) 

📅 До годовщины - сколько дней до нашего дня
💝 Случайное сообщение - милая плюшка)
🎉 До праздников - сколько до них осталось
📊 Дней вместе - сколько дней мы уже вместе

Я тебя очень-очень люблю)) Ты у меня самая прекрасная))💕

С любовью, твой Никитка))❤️"""

    await update.message.reply_text(
        welcome_text, 
        reply_markup=create_main_keyboard()
    )
    logger.info(f"Пользователь {user.id} запустил бота, chat_id: {chat_id}")

async def days_command(update, context):
    """Показывает сколько дней осталось до годовщины"""
    days_left = get_days_until_anniversary()
    
    if days_left == 0:
        message = "🎉 Малыш, с годовщиной)) 🎉\nСегодня наш особенный день) Люблю тебя больше всего на свете) Мы дождались)💕"
    elif days_left == 1:
        message = "Завтра наша годовщина) Всего 1 день остался)❤️\nЯ так тебя люблю))"
    else:
        message = f"До нашей годовщины\nосталось {days_left} дней))💕"
    
    await update.message.reply_text(message, reply_markup=create_main_keyboard())

async def love_command(update, context):
    """Отправляет случайное любовное сообщение"""
    love_message = random.choice(LOVE_MESSAGES)
    await update.message.reply_text(love_message, reply_markup=create_main_keyboard())

async def holidays_command(update, context):
    """Показывает все ближайшие праздники"""
    holiday_text = "🎉 Сколько осталось до праздников:\n\n"
    
    # Сортируем праздники по количеству оставшихся дней
    sorted_holidays = sorted(
        [(name, data["date"]) for name, data in HOLIDAYS.items()],
        key=lambda x: get_days_until_holiday(x[1])
    )
    
    for holiday_name, holiday_date in sorted_holidays:
        days_left = get_days_until_holiday(holiday_date)
        
        if days_left == 0:
            holiday_text += f" {holiday_name} - СЕГОДНЯ!🎊\n"
        elif days_left == 1:
            holiday_text += f" {holiday_name} - завтра! ({holiday_date.strftime('%d.%m')})\n"
        else:
            holiday_text += f" {holiday_name} - через {days_left} дней ({holiday_date.strftime('%d.%m')})\n"
    
    await update.message.reply_text(holiday_text, reply_markup=create_main_keyboard())

async def days_together_command(update, context):
    """Показывает сколько дней мы уже вместе"""
    days_together = get_days_together()
    
    if days_together == 365:
        message = f"Ровно {days_together} дней мы вместе))❤️\nЭто был самый счастливый год в моей жизни)) Люблю тебя безумно)❤️❤️❤️"
    elif days_together > 365:
        years = days_together // 365
        remaining_days = days_together % 365
        message = f"❤️ Уже {years} год и {remaining_days} дней мы вместе)\n\nВсего {days_together} дней счастья) И с каждым днем я люблю тебя все сильнее) 💕"
    else:
        message = f"💕 Мы вместе уже {days_together} дней)\n\nКаждый из них был наполнен твоей любовью и теплом) Я самый счастливый)💖"
    
    await update.message.reply_text(message, reply_markup=create_main_keyboard())

async def handle_message(update, context):
    """Обработчик обычных сообщений"""
    user_text = update.message.text
    
    # Обработка нажатий кнопок меню
    if user_text == "📅 До годовщины":
        await days_command(update, context)
    elif user_text == "💝 Случайное сообщение":
        await love_command(update, context)
    elif user_text == "🎉 До праздников":
        await holidays_command(update, context)
    elif user_text == "📊 Дней вместе":
        await days_together_command(update, context)
    elif any(word in user_text.lower() for word in ['привет', 'пивет', 'hi', 'здаров']):
        await update.message.reply_text("Привет, любимая)💕", reply_markup=create_main_keyboard())
    elif any(word in user_text.lower() for word in ['люблю', 'love', 'обожаю']):
        await update.message.reply_text("Я тебя тоже очень люблю))💕", reply_markup=create_main_keyboard())
    elif any(word in user_text.lower() for word in ['муаа', 'муа', 'целую']):
        await update.message.reply_text("Муа муа муаа муа муа муаа))💕", reply_markup=create_main_keyboard())
    elif any(word in user_text.lower() for word in ['скучаю', 'скучаешь', 'miss']):
        await update.message.reply_text("Я тоже очень по тебе скучаю) С нетерпением жду нашей встречи)) 💖", reply_markup=create_main_keyboard())
    else:
        # На неизвестные сообщения отвечаем подсказкой
        await update.message.reply_text(
            'Я тебя не совсем понял, солнышко) 💕\nИспользуй кнопки меню внизу или напиши "привет" ❤️\nА еще лучше напиши мне)', 
            reply_markup=create_main_keyboard()
        )

async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневное напоминание в 16:00 по Москве (13:00 UTC)"""
    # Проверяем, что бот инициализирован
    if not context.bot:
        logger.error("Bot not initialized in job context")
        return
        
    days_left = get_days_until_anniversary()
    days_together = get_days_together()
    
    # Основное сообщение о годовщине
    if days_left == 0:
        message = "🎉 С годовщиной, мое солнышко)) 🎉\nСегодня наш особенный день)) Люблю тебя больше всего на свете))💕\nТы сделала меня самым счастливым человеком!"
    elif days_left == 1:
        message = "Завтра наша годовщина, милая))\nВсего 1 день остался)\nЯ так тебя люблю))❤️"
    else:
        message = f"❤️ До нашей годовщины осталось {days_left} дней))\nА сегодня у нас уже {days_together} дней вместе))💕"
    
    # Отправляем основное сообщение во все сохраненные чаты
    for chat_id in CHAT_IDS.copy():
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Ежедневное уведомление отправлено в chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки в chat_id {chat_id}: {e}")
            # Удаляем невалидный chat_id
            CHAT_IDS.discard(chat_id)
            save_chat_ids()

async def send_holiday_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет и отправляет уведомления о праздниках в 00:00 по Москве (21:00 UTC)"""
    # Проверяем, что бот инициализирован
    if not context.bot:
        logger.error("Bot not initialized in job context")
        return
        
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc + timedelta(hours=TIMEZONE_OFFSET)
    current_date = now_moscow.date()
    
    for holiday_name, holiday_data in HOLIDAYS.items():
        holiday_date = holiday_data["date"]
        days_until_holiday = get_days_until_holiday(holiday_date)
        
        # Проверяем, нужно ли отправлять уведомление за день до праздника
        if days_until_holiday == 1 and holiday_data["day_before_message"]:
            message = holiday_data["day_before_message"]
            await send_message_to_all_chats(context, message, f"предпраздничное уведомление для {holiday_name}")
        
        # Проверяем, нужно ли отправлять уведомление в день праздника
        elif days_until_holiday == 0 and holiday_data["day_of_message"]:
            message = holiday_data["day_of_message"]
            await send_message_to_all_chats(context, message, f"праздничное уведомление для {holiday_name}")

async def send_message_to_all_chats(context, message, log_description):
    """Вспомогательная функция для отправки сообщений во все чаты"""
    for chat_id in CHAT_IDS.copy():
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"{log_description} отправлено в chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки {log_description} в chat_id {chat_id}: {e}")
            # Удаляем невалидный chat_id
            CHAT_IDS.discard(chat_id)
            save_chat_ids()

def main():
    """Основная функция"""
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден! Убедитесь, что задана переменная окружения.")
        print("❌ ОШИБКА: BOT_TOKEN не найден!")
        print("💡 Решение: Добавьте переменную BOT_TOKEN в настройки Railway")
        return
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("days", days_command))
        application.add_handler(CommandHandler("love", love_command))
        application.add_handler(CommandHandler("holidays", holidays_command))
        application.add_handler(CommandHandler("together", days_together_command))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Настраиваем ежедневные уведомления с помощью JobQueue
        job_queue = application.job_queue
        
        # Обычные уведомления в 16:00 по МСК (13:00 UTC)
        daily_time = datetime.strptime("13:00", "%H:%M").time()
        
        # Праздничные уведомления в 00:00 по МСК (21:00 UTC предыдущего дня)
        holiday_time = datetime.strptime("21:00", "%H:%M").time()
        
        # Добавляем ежедневную job для основного напоминания (16:00 МСК)
        job_queue.run_daily(
            send_daily_reminder,
            time=daily_time,
            name="daily_reminder"
        )
        
        # Добавляем ежедневную job для проверки праздников (00:00 МСК)
        job_queue.run_daily(
            send_holiday_reminders,
            time=holiday_time,
            name="holiday_reminders"
        )
        
        print("✅ Бот запущен! Теперь ваша девушка может написать боту в Telegram")
        print("📅 Обычные уведомления настроены на 16:00 по Москве")
        print("🎉 Праздничные уведомления настроены на 00:00 по Москве")
        print("🚀 Бот готов к работе!")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()

"""
Конфигурация приложения
Загружает переменные окружения и настраивает параметры
"""

import os
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
# Сначала пробуем config.env (для локальной разработки)
if os.path.exists('config.env'):
    load_dotenv('config.env')
else:
    # Если config.env нет, используем переменные окружения (для Railway)
    pass

# Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "telegram_analytics.log")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Telegram настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_USER_ID = os.getenv("TARGET_USER_ID")

# OpenAI настройки
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

# Google API настройки
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# База данных
DATABASE_PATH = os.getenv("DATABASE_PATH", "telegram_analytics.db")

# Планировщик
ANALYSIS_HOUR = int(os.getenv("ANALYSIS_HOUR", "0"))
ANALYSIS_MINUTE = int(os.getenv("ANALYSIS_MINUTE", "0"))
ARCHIVE_HOUR = int(os.getenv("ARCHIVE_HOUR", "23"))
ARCHIVE_MINUTE = int(os.getenv("ARCHIVE_MINUTE", "0"))

# Валидация обязательных параметров
def validate_config():
    """Проверка наличия обязательных переменных окружения"""
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "OPENAI_API_KEY",
        "TARGET_USER_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not globals()[var]:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
    
    # Преобразуем TARGET_USER_ID в int
    try:
        global TARGET_USER_ID
        TARGET_USER_ID = int(TARGET_USER_ID)
    except (ValueError, TypeError):
        raise ValueError("TARGET_USER_ID должен быть числом")

# Инициализация конфигурации
setup_logging()
validate_config()

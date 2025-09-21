#!/usr/bin/env python3
"""
Скрипт запуска Telegram Analytics Bot
Проверяет конфигурацию и запускает бота
"""

import sys
import asyncio
import logging
from pathlib import Path

# Добавляем путь к модулям приложения
sys.path.insert(0, str(Path(__file__).parent))

from app.config import validate_config
from app.main import main

logger = logging.getLogger(__name__)


async def startup_check():
    """Проверка готовности системы к запуску"""
    logger.info("Проверка конфигурации...")
    
    try:
        validate_config()
        logger.info("✅ Конфигурация корректна")
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        return False
    
    # Проверяем наличие файлов
    required_files = [
        "credentials.json"  # Google credentials (опционально)
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.warning(f"⚠️ Отсутствуют файлы: {', '.join(missing_files)}")
        logger.warning("Бот будет работать без архивирования в Google Drive")
    
    logger.info("✅ Система готова к запуску")
    return True


async def run():
    """Главная функция запуска"""
    logger.info("🚀 Запуск Telegram Analytics Bot...")
    
    # Проверяем готовность системы
    if not await startup_check():
        logger.error("❌ Система не готова к запуску")
        sys.exit(1)
    
    try:
        # Запускаем бота
        await main()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 Telegram Analytics Bot остановлен")


if __name__ == "__main__":
    # Настройка логирования для скрипта
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запускаем асинхронную функцию
    asyncio.run(run())

"""
Главный модуль Telegram бота-аналитика
Обрабатывает сообщения, запускает анализ и отправляет отчеты
"""

import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import Update, Message, Chat, User
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from .db import DatabaseManager
from .filters import MessageFilter
from .summarize import MessageSummarizer
from .archive import ArchiveManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramAnalyticsBot:
    """Основной класс бота-аналитика"""
    
    def __init__(self, bot_token: str, openai_api_key: str, 
                 google_credentials_file: str = None, target_user_id: int = None):
        """
        Инициализация бота
        
        Args:
            bot_token: Токен Telegram бота
            openai_api_key: API ключ OpenAI
            google_credentials_file: Путь к файлу Google credentials
            target_user_id: ID пользователя для отправки отчетов
        """
        self.bot_token = bot_token
        self.target_user_id = target_user_id
        
        # Инициализация компонентов
        self.db = DatabaseManager()
        self.message_filter = MessageFilter(self.db)
        self.summarizer = MessageSummarizer(openai_api_key)
        
        # Инициализируем архивный менеджер только если файл существует
        if google_credentials_file and os.path.exists(google_credentials_file):
            try:
                self.archive_manager = ArchiveManager(google_credentials_file)
                logger.info("Архивный менеджер инициализирован")
            except Exception as e:
                logger.warning(f"Ошибка инициализации архивного менеджера: {e}")
                self.archive_manager = None
        else:
            self.archive_manager = None
            logger.warning("Архивный менеджер отключен - нет Google credentials")
        
        # Инициализация Telegram приложения
        self.application = Application.builder().token(bot_token).build()
        self._setup_handlers()
        
        logger.info("Бот инициализирован успешно")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("filter", self.filter_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message
        ))
        
        # Обработчик бизнес-сообщений (если поддерживается)
        # TODO: Добавить обработку business_message когда будет доступно в библиотеке
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Сохраняем информацию о чате
        self.db.insert_chat(
            chat_id=str(chat.id),
            title=chat.title or f"Chat with {user.first_name}",
            chat_type=chat.type,
            is_work=self.message_filter.is_work_chat(str(chat.id), chat.title or "")
        )
        
        welcome_text = """🤖 Telegram Analytics Bot запущен!

Доступные команды:
/help - помощь
/status - статус системы
/filter - управление фильтрами
/analyze - запустить анализ вручную

Бот автоматически анализирует рабочие сообщения каждый час и отправляет отчеты."""
        
        await update.message.reply_text(welcome_text)
        logger.info(f"Пользователь {user.id} запустил бота в чате {chat.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """📋 Помощь по командам:

/start - запуск бота
/help - эта справка
/status - статус системы и статистика
/filter - управление фильтрами чатов
/analyze - запустить анализ вручную

🔧 Настройка фильтров:
/filter add allow <chat_id> - добавить чат в allowlist
/filter add deny <chat_id> - добавить чат в denylist
/filter add keyword <слово> - добавить ключевое слово
/filter list - показать все фильтры

📊 Автоматический анализ:
- Каждый час бот анализирует новые сообщения
- Отправляет отчет в ваш личный чат
- Архивирует результаты в Google Drive"""
        
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        try:
            # Получаем статистику
            filter_stats = self.message_filter.get_filter_stats()
            work_chats = self.db.get_work_chats()
            
            status_text = f"""📊 Статус системы:

🔍 Фильтры:
- Allowlist чатов: {filter_stats['allow_chats_count']}
- Denylist чатов: {filter_stats['deny_chats_count']}
- Пользовательские ключевые слова: {filter_stats['custom_keywords_count']}

💼 Рабочие чаты: {len(work_chats)}
📝 Встроенных ключевых слов: {filter_stats['work_keywords_count']}

🎯 Целевой пользователь: {'Настроен' if self.target_user_id else 'Не настроен'}
📁 Архив: {'Активен' if self.archive_manager else 'Отключен'}"""
            
            await update.message.reply_text(status_text)
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            await update.message.reply_text("❌ Ошибка получения статуса системы")
    
    async def filter_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /filter"""
        if not context.args:
            await update.message.reply_text("Использование: /filter <add|list> [параметры]")
            return
        
        command = context.args[0].lower()
        
        try:
            if command == "add" and len(context.args) >= 3:
                filter_type = context.args[1].lower()
                value = context.args[2]
                
                if filter_type == "allow":
                    success = self.message_filter.add_allow_chat(value)
                    await update.message.reply_text(f"{'✅' if success else '❌'} Allowlist обновлен")
                    
                elif filter_type == "deny":
                    success = self.message_filter.add_deny_chat(value)
                    await update.message.reply_text(f"{'✅' if success else '❌'} Denylist обновлен")
                    
                elif filter_type == "keyword":
                    success = self.message_filter.add_keyword(value)
                    await update.message.reply_text(f"{'✅' if success else '❌'} Ключевое слово добавлено")
                    
                else:
                    await update.message.reply_text("Неизвестный тип фильтра: allow, deny, keyword")
            
            elif command == "list":
                filters_data = self.db.get_filters()
                
                if not filters_data:
                    await update.message.reply_text("Фильтры не настроены")
                    return
                
                filter_text = "📋 Активные фильтры:\n\n"
                
                allow_filters = [f for f in filters_data if f['kind'] == 'allow_chat']
                deny_filters = [f for f in filters_data if f['kind'] == 'deny_chat']
                keyword_filters = [f for f in filters_data if f['kind'] == 'keyword']
                
                if allow_filters:
                    filter_text += "✅ Allowlist:\n"
                    for f in allow_filters:
                        filter_text += f"- {f['value']}\n"
                    filter_text += "\n"
                
                if deny_filters:
                    filter_text += "❌ Denylist:\n"
                    for f in deny_filters:
                        filter_text += f"- {f['value']}\n"
                    filter_text += "\n"
                
                if keyword_filters:
                    filter_text += "🔤 Ключевые слова:\n"
                    for f in keyword_filters:
                        filter_text += f"- {f['value']}\n"
                
                await update.message.reply_text(filter_text)
            
            else:
                await update.message.reply_text("Использование: /filter <add|list> [параметры]")
                
        except Exception as e:
            logger.error(f"Ошибка обработки команды filter: {e}")
            await update.message.reply_text("❌ Ошибка обработки команды")
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /analyze - запуск анализа вручную"""
        try:
            await update.message.reply_text("🔄 Запускаю анализ сообщений...")
            
            # Запускаем анализ за последний час
            success = await self.run_hourly_analysis()
            
            if success:
                await update.message.reply_text("✅ Анализ завершен успешно!")
            else:
                await update.message.reply_text("❌ Ошибка при выполнении анализа")
                
        except Exception as e:
            logger.error(f"Ошибка ручного анализа: {e}")
            await update.message.reply_text("❌ Ошибка при выполнении анализа")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик входящих сообщений"""
        try:
            message = update.message
            chat = update.effective_chat
            user = update.effective_user
            
            # Сохраняем информацию о чате
            is_work = self.message_filter.is_work_chat(str(chat.id), chat.title or "")
            self.db.insert_chat(
                chat_id=str(chat.id),
                title=chat.title or f"Chat with {user.first_name}",
                chat_type=chat.type,
                is_work=is_work
            )
            
            # Сохраняем сообщение
            self.db.insert_message(
                chat_id=str(chat.id),
                tg_message_id=str(message.message_id),
                sender=user.first_name or "Unknown",
                text=message.text or "",
                ts=message.date,
                is_business=False,  # TODO: Определять для business сообщений
                raw_json=str(message.to_dict())
            )
            
            # Обновляем ID последнего сообщения в чате
            self.db.update_chat_last_message(str(chat.id), str(message.message_id))
            
            logger.debug(f"Сообщение сохранено: {chat.id} - {user.first_name}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def run_hourly_analysis(self) -> bool:
        """
        Запуск часового анализа сообщений
        
        Returns:
            bool: True если анализ выполнен успешно
        """
        try:
            logger.info("Запуск часового анализа...")
            
            # Определяем временное окно (последний час)
            now = datetime.now()
            window_start = now - timedelta(hours=1)
            window_end = now
            
            # Создаем запись о запуске
            run_id = self.db.create_run(now, window_start, window_end)
            if not run_id:
                logger.error("Не удалось создать запись о запуске")
                return False
            
            # Получаем новые сообщения
            messages = self.db.get_new_messages(window_start, window_end)
            
            if not messages:
                logger.info("Нет новых сообщений для анализа")
                return True
            
            # Получаем статистику по всем чатам
            all_chats_stats = self._get_chats_statistics(messages)
            
            # Фильтруем рабочие сообщения
            work_messages = self.message_filter.filter_messages(messages)
            
            if not work_messages:
                logger.info("Нет рабочих сообщений для анализа")
                # Отправляем статистику даже если нет рабочих сообщений
                await self._send_statistics_report(all_chats_stats, 0)
                return True
            
            # Группируем сообщения по чатам
            chats_messages = {}
            for msg in work_messages:
                chat_id = msg['chat_id']
                if chat_id not in chats_messages:
                    chats_messages[chat_id] = []
                chats_messages[chat_id].append(msg)
            
            # Анализируем каждый чат
            all_reports = []
            for chat_id, chat_messages in chats_messages.items():
                analysis_result = self.summarizer.analyze_messages(chat_messages)
                
                if analysis_result:
                    # Сохраняем отчет в БД
                    summary = analysis_result['summary']
                    self.db.insert_report(
                        run_id=run_id,
                        chat_id=chat_id,
                        summary=str(summary.get('agreements', [])),
                        risks=str(summary.get('risks', [])),
                        actions=str(summary.get('recommendations', [])),
                        prompt_tokens=analysis_result.get('prompt_tokens', 0),
                        completion_tokens=analysis_result.get('completion_tokens', 0)
                    )
                    
                    all_reports.append({
                        'chat_id': chat_id,
                        'chat_title': chat_messages[0].get('title', f'Chat {chat_id}'),
                        'analysis': analysis_result
                    })
            
            # Формируем общий отчет
            if all_reports:
                await self._send_analysis_report(all_reports, len(chats_messages), all_chats_stats)
                
                # Архивируем результаты
                if self.archive_manager:
                    await self._archive_results(all_reports, run_id)
            else:
                # Отправляем только статистику если нет рабочих сообщений
                await self._send_statistics_report(all_chats_stats, len(chats_messages))
            
            logger.info(f"Анализ завершен. Обработано чатов: {len(chats_messages)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка часового анализа: {e}")
            return False
    
    async def _send_analysis_report(self, reports: List[Dict], active_chats_count: int, stats: Dict = None):
        """Отправка отчета анализа в личный чат"""
        if not self.target_user_id:
            logger.warning("Не настроен целевой пользователь для отправки отчетов")
            return
        
        try:
            # Формируем общий отчет
            report_text = f"🗂 активные чаты за час: {active_chats_count}\n\n"
            
            # Добавляем общую статистику
            if stats:
                report_text += f"📊 Всего чатов: {stats['total_chats']} | "
                report_text += f"💼 Рабочих: {stats['work_chats']} | "
                report_text += f"🏠 Личных: {stats['personal_chats']} | "
                report_text += f"📨 Сообщений: {stats['total_messages']}\n\n"
            
            # Объединяем результаты всех чатов
            all_agreements = []
            all_risks = []
            all_recommendations = []
            
            for report in reports:
                analysis = report['analysis']
                summary = analysis.get('summary', {})
                
                all_agreements.extend(summary.get('agreements', []))
                all_risks.extend(summary.get('risks', []))
                all_recommendations.extend(summary.get('recommendations', []))
            
            # Добавляем ключевые договоренности
            if all_agreements:
                report_text += "📌 ключевые договоренности:\n"
                for agreement in all_agreements[:6]:  # Максимум 6 пунктов
                    report_text += f"- {agreement}\n"
                report_text += "\n"
            
            # Добавляем риски
            if all_risks:
                report_text += "⚠️ риски:\n"
                for risk in all_risks[:3]:  # Максимум 3 строки
                    report_text += f"- {risk}\n"
                report_text += "\n"
            
            # Добавляем рекомендации
            if all_recommendations:
                report_text += "🚀 рекомендации:\n"
                for rec in all_recommendations[:5]:  # Максимум 5 строк
                    report_text += f"- {rec}\n"
            
            # Отправляем отчет
            await self.application.bot.send_message(
                chat_id=self.target_user_id,
                text=report_text
            )
            
            logger.info(f"Отчет отправлен пользователю {self.target_user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
    
    async def _archive_results(self, reports: List[Dict], run_id: int):
        """Архивирование результатов анализа"""
        if not self.archive_manager:
            return
        
        try:
            # TODO: Реализовать архивирование в Google Drive и Sheets
            logger.info(f"Архивирование результатов run_id: {run_id}")
            
        except Exception as e:
            logger.error(f"Ошибка архивирования: {e}")
    
    def _get_chats_statistics(self, messages: List[Dict]) -> Dict:
        """Получение статистики по всем чатам"""
        try:
            stats = {
                'total_messages': len(messages),
                'total_chats': 0,
                'work_chats': 0,
                'personal_chats': 0,
                'chats_detail': {}
            }
            
            # Группируем по чатам
            chats_data = {}
            for msg in messages:
                chat_id = msg['chat_id']
                if chat_id not in chats_data:
                    chats_data[chat_id] = {
                        'title': msg.get('title', f'Chat {chat_id}'),
                        'messages_count': 0,
                        'is_work': self.message_filter.is_work_chat(chat_id, msg.get('title', ''))
                    }
                chats_data[chat_id]['messages_count'] += 1
            
            # Подсчитываем статистику
            stats['total_chats'] = len(chats_data)
            for chat_id, chat_data in chats_data.items():
                if chat_data['is_work']:
                    stats['work_chats'] += 1
                else:
                    stats['personal_chats'] += 1
                
                stats['chats_detail'][chat_id] = chat_data
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики чатов: {e}")
            return {'total_messages': 0, 'total_chats': 0, 'work_chats': 0, 'personal_chats': 0, 'chats_detail': {}}
    
    async def _send_statistics_report(self, stats: Dict, work_chats_count: int):
        """Отправка отчета только со статистикой"""
        if not self.target_user_id:
            logger.warning("Не настроен целевой пользователь для отправки отчетов")
            return
        
        try:
            report_text = f"📊 Статистика за час:\n\n"
            report_text += f"🗂 Всего чатов: {stats['total_chats']}\n"
            report_text += f"💼 Рабочих чатов: {stats['work_chats']}\n"
            report_text += f"🏠 Личных чатов: {stats['personal_chats']}\n"
            report_text += f"📨 Всего сообщений: {stats['total_messages']}\n\n"
            
            if stats['total_chats'] > 0:
                report_text += "📋 Активность по чатам:\n"
                for chat_id, chat_data in stats['chats_detail'].items():
                    chat_type = "💼" if chat_data['is_work'] else "🏠"
                    report_text += f"{chat_type} {chat_data['title']}: {chat_data['messages_count']} сообщений\n"
            
            if work_chats_count == 0:
                report_text += "\n⚠️ Рабочих сообщений не найдено"
            
            # Отправляем отчет
            await self.application.bot.send_message(
                chat_id=self.target_user_id,
                text=report_text
            )
            
            logger.info(f"Статистический отчет отправлен пользователю {self.target_user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки статистического отчета: {e}")
    
    def start_bot(self):
        """Запуск бота"""
        try:
            logger.info("Запуск Telegram бота...")
            
            # Добавляем обработчик ошибок для конфликтов
            self.application.add_error_handler(self._error_handler)
            
            # Запускаем бота в синхронном режиме
            self.application.run_polling()
            
            logger.info("Бот успешно запущен и работает")
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Ошибка в обработке обновления: {context.error}")
        
        # Игнорируем конфликты - они решаются автоматически
        if "Conflict" in str(context.error):
            logger.info("Игнорируем конфликт - Telegram API автоматически решит проблему")
            return


# Функция для запуска бота
def main():
    """Главная функция для запуска бота"""
    import os
    
    # Получаем настройки из переменных окружения (для Railway)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
    target_user_id = os.getenv("TARGET_USER_ID")
    
    # Логируем полученные переменные (без значений для безопасности)
    logger.info(f"TELEGRAM_BOT_TOKEN: {'SET' if bot_token else 'NOT SET'}")
    logger.info(f"OPENAI_API_KEY: {'SET' if openai_api_key else 'NOT SET'}")
    logger.info(f"TARGET_USER_ID: {target_user_id}")
    
    # Если переменные не заданы, пробуем загрузить из config.py
    if not bot_token:
        try:
            from .config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, GOOGLE_CREDENTIALS_FILE, TARGET_USER_ID
            bot_token = TELEGRAM_BOT_TOKEN
            openai_api_key = OPENAI_API_KEY
            google_credentials_file = GOOGLE_CREDENTIALS_FILE
            target_user_id = TARGET_USER_ID
            logger.info("Переменные загружены из config.py")
        except Exception as e:
            logger.error(f"Ошибка загрузки из config.py: {e}")
    
    if not bot_token or not openai_api_key:
        logger.error("Не заданы обязательные переменные окружения")
        logger.error(f"bot_token: {'SET' if bot_token else 'NOT SET'}")
        logger.error(f"openai_api_key: {'SET' if openai_api_key else 'NOT SET'}")
        return
    
    # Создаем и запускаем бота
    bot = TelegramAnalyticsBot(
        bot_token=bot_token,
        openai_api_key=openai_api_key,
        google_credentials_file=google_credentials_file,
        target_user_id=target_user_id
    )
    
    bot.start_bot()


if __name__ == "__main__":
    main()

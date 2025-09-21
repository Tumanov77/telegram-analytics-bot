#!/usr/bin/env python3
"""
Демо-версия Telegram Analytics Bot
Показывает функциональность без реальных API подключений
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoTelegramAnalyticsBot:
    """Демо-версия бота для демонстрации функциональности"""
    
    def __init__(self):
        """Инициализация демо-бота"""
        self.demo_messages = self._create_demo_messages()
        logger.info("🤖 Демо-бот инициализирован")
    
    def _create_demo_messages(self) -> List[Dict]:
        """Создание демо-сообщений для тестирования"""
        return [
            {
                'chat_id': 'work_chat_1',
                'title': 'Рабочий чат - Проект Alpha',
                'sender': 'Иван Петров',
                'text': 'Договор на разработку готов, нужно согласовать сроки сдачи проекта',
                'ts': datetime.now() - timedelta(minutes=30),
                'is_business': False
            },
            {
                'chat_id': 'work_chat_1', 
                'title': 'Рабочий чат - Проект Alpha',
                'sender': 'Мария Сидорова',
                'text': 'Бюджет проекта увеличился на 15%, нужно обновить смету',
                'ts': datetime.now() - timedelta(minutes=25),
                'is_business': False
            },
            {
                'chat_id': 'work_chat_2',
                'title': 'Команда разработки',
                'sender': 'Алексей Козлов',
                'text': 'Обнаружен критический баг в модуле авторизации, нужен срочный фикс',
                'ts': datetime.now() - timedelta(minutes=20),
                'is_business': False
            },
            {
                'chat_id': 'work_chat_2',
                'title': 'Команда разработки', 
                'sender': 'Елена Волкова',
                'text': 'Тестирование новой фичи завершено, можно делать релиз',
                'ts': datetime.now() - timedelta(minutes=15),
                'is_business': False
            },
            {
                'chat_id': 'work_chat_3',
                'title': 'Маркетинг команда',
                'sender': 'Дмитрий Новиков',
                'text': 'ROI кампании составил 340%, нужно масштабировать на другие каналы',
                'ts': datetime.now() - timedelta(minutes=10),
                'is_business': False
            },
            {
                'chat_id': 'personal_chat_1',
                'title': 'Личный чат',
                'sender': 'Друг',
                'text': 'Привет! Как дела? Встретимся в выходные?',
                'ts': datetime.now() - timedelta(minutes=5),
                'is_business': False
            }
        ]
    
    def demo_filter_work_messages(self, messages: List[Dict]) -> List[Dict]:
        """Демо фильтрация рабочих сообщений"""
        work_keywords = [
            'договор', 'проект', 'бюджет', 'смета', 'баг', 'фича', 'релиз', 
            'ROI', 'кампания', 'разработка', 'тестирование', 'авторизация'
        ]
        
        work_messages = []
        for msg in messages:
            text_lower = msg['text'].lower()
            if any(keyword in text_lower for keyword in work_keywords):
                work_messages.append(msg)
        
        return work_messages
    
    def demo_gpt_analysis(self, messages: List[Dict]) -> Dict:
        """Демо анализ сообщений (имитация GPT)"""
        # Имитируем анализ GPT
        agreements = [
            "Согласование сроков сдачи проекта",
            "Обновление сметы в связи с увеличением бюджета на 15%",
            "Планирование релиза новой фичи после тестирования"
        ]
        
        risks = [
            "Критический баг в модуле авторизации требует срочного исправления",
            "Увеличение бюджета проекта может повлиять на сроки"
        ]
        
        recommendations = [
            "Немедленно исправить баг авторизации перед релизом",
            "Подготовить обновленную смету для согласования с клиентом",
            "Запланировать дополнительное тестирование после фикса бага",
            "Масштабировать успешную маркетинговую кампанию на другие каналы",
            "Создать резервный план на случай задержек проекта"
        ]
        
        return {
            'summary': {
                'agreements': agreements,
                'risks': risks,
                'recommendations': recommendations
            },
            'raw_response': f"Анализ {len(messages)} сообщений завершен",
            'prompt_tokens': 150,
            'completion_tokens': 200,
            'total_tokens': 350,
            'analyzed_at': datetime.now().isoformat(),
            'messages_count': len(messages)
        }
    
    def format_demo_report(self, analysis_result: Dict, active_chats_count: int) -> str:
        """Форматирование демо-отчета для Telegram"""
        summary = analysis_result['summary']
        
        report = f"🗂 активные чаты за час: {active_chats_count}\n\n"
        
        # Договоренности
        agreements = summary.get('agreements', [])
        if agreements:
            report += "📌 ключевые договоренности:\n"
            for agreement in agreements[:6]:
                report += f"- {agreement}\n"
            report += "\n"
        
        # Риски
        risks = summary.get('risks', [])
        if risks:
            report += "⚠️ риски:\n"
            for risk in risks[:3]:
                report += f"- {risk}\n"
            report += "\n"
        
        # Рекомендации
        recommendations = summary.get('recommendations', [])
        if recommendations:
            report += "🚀 рекомендации:\n"
            for rec in recommendations[:5]:
                report += f"- {rec}\n"
        
        return report
    
    async def demo_hourly_analysis(self):
        """Демо часового анализа"""
        logger.info("🔄 Запуск демо анализа...")
        
        # Получаем сообщения за последний час
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        recent_messages = [
            msg for msg in self.demo_messages 
            if msg['ts'] >= hour_ago
        ]
        
        logger.info(f"📨 Найдено {len(recent_messages)} сообщений за последний час")
        
        # Фильтруем рабочие сообщения
        work_messages = self.demo_filter_work_messages(recent_messages)
        logger.info(f"💼 Отфильтровано {len(work_messages)} рабочих сообщений")
        
        if not work_messages:
            logger.info("❌ Нет рабочих сообщений для анализа")
            return
        
        # Группируем по чатам
        chats_messages = {}
        for msg in work_messages:
            chat_id = msg['chat_id']
            if chat_id not in chats_messages:
                chats_messages[chat_id] = []
            chats_messages[chat_id].append(msg)
        
        logger.info(f"📊 Анализируем {len(chats_messages)} чатов")
        
        # Анализируем каждый чат
        all_reports = []
        for chat_id, chat_messages in chats_messages.items():
            logger.info(f"🔍 Анализ чата: {chat_messages[0]['title']}")
            
            analysis_result = self.demo_gpt_analysis(chat_messages)
            all_reports.append({
                'chat_id': chat_id,
                'chat_title': chat_messages[0]['title'],
                'analysis': analysis_result
            })
        
        # Формируем общий отчет
        if all_reports:
            await self.demo_send_report(all_reports, len(chats_messages))
            await self.demo_archive_results(all_reports)
        
        logger.info("✅ Демо анализ завершен")
    
    async def demo_send_report(self, reports: List[Dict], active_chats_count: int):
        """Демо отправка отчета"""
        logger.info("📤 Отправка отчета...")
        
        # Формируем общий отчет
        report_text = f"🗂 активные чаты за час: {active_chats_count}\n\n"
        
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
            for agreement in all_agreements[:6]:
                report_text += f"- {agreement}\n"
            report_text += "\n"
        
        # Добавляем риски
        if all_risks:
            report_text += "⚠️ риски:\n"
            for risk in all_risks[:3]:
                report_text += f"- {risk}\n"
            report_text += "\n"
        
        # Добавляем рекомендации
        if all_recommendations:
            report_text += "🚀 рекомендации:\n"
            for rec in all_recommendations[:5]:
                report_text += f"- {rec}\n"
        
        # В реальном боте здесь была бы отправка в Telegram
        print("\n" + "="*50)
        print("📱 ОТЧЕТ В TELEGRAM:")
        print("="*50)
        print(report_text)
        print("="*50 + "\n")
        
        logger.info("✅ Отчет сформирован и готов к отправке")
    
    async def demo_archive_results(self, reports: List[Dict]):
        """Демо архивирование результатов"""
        logger.info("📁 Архивирование результатов...")
        
        # В реальном боте здесь была бы запись в Google Drive и Sheets
        for report in reports:
            chat_title = report['chat_title']
            analysis = report['analysis']
            summary = analysis.get('summary', {})
            
            logger.info(f"📄 Архивирован отчет для чата: {chat_title}")
            logger.info(f"   - Договоренности: {len(summary.get('agreements', []))}")
            logger.info(f"   - Риски: {len(summary.get('risks', []))}")
            logger.info(f"   - Рекомендации: {len(summary.get('recommendations', []))}")
        
        logger.info("✅ Архивирование завершено")
    
    async def demo_status(self):
        """Демо статус системы"""
        logger.info("📊 Статус системы:")
        
        work_chats = len(set(msg['chat_id'] for msg in self.demo_messages 
                           if self.demo_filter_work_messages([msg])))
        
        print("\n" + "="*30)
        print("📊 СТАТУС СИСТЕМЫ:")
        print("="*30)
        print(f"🔍 Всего сообщений: {len(self.demo_messages)}")
        print(f"💼 Рабочих чатов: {work_chats}")
        print(f"🤖 Демо-режим: Активен")
        print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*30 + "\n")
    
    async def run_demo(self):
        """Запуск демо-режима"""
        logger.info("🎭 Запуск демо-режима Telegram Analytics Bot")
        
        try:
            # Показываем статус
            await self.demo_status()
            
            # Ждем немного
            await asyncio.sleep(2)
            
            # Запускаем анализ
            await self.demo_hourly_analysis()
            
            logger.info("🎉 Демо завершено успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в демо: {e}")


async def main():
    """Главная функция демо"""
    print("🤖 Telegram Analytics Bot - Демо режим")
    print("="*50)
    
    demo_bot = DemoTelegramAnalyticsBot()
    await demo_bot.run_demo()


if __name__ == "__main__":
    asyncio.run(main())

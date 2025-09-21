"""
Модуль анализа сообщений с помощью OpenAI GPT
Реализует анализ по фиксированному промпту и формирование отчетов
"""

import logging
import openai
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageSummarizer:
    """Класс для анализа сообщений с помощью GPT"""
    
    # Фиксированный промпт согласно ТЗ
    GPT_PROMPT = """Ты — бизнес-консультант уровня Илона Маска. Проанализируй сообщения за последний час и дай краткий анализ в строго следующем формате:

АНАЛИЗ СООБЩЕНИЙ:
{context}

ФОРМАТ ОТВЕТА (строго 3 блока):
ДОГОВОРЕННОСТИ:
- [ключевые договоренности и действия, 3-6 пунктов]

РИСКИ:
- [слабые места и риски, до 3 пунктов]

РЕКОМЕНДАЦИИ:
- [конкретные рекомендации в императиве, до 5 пунктов]

Фокус на том, как ускорить результат, используя сильные стороны."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Инициализация анализатора
        
        Args:
            api_key: OpenAI API ключ
            model: Модель GPT для использования
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = 4000  # Лимит токенов для промпта
    
    def _prepare_context(self, messages: List[Dict]) -> str:
        """
        Подготовка контекста из сообщений для анализа
        
        Args:
            messages: Список сообщений для анализа
            
        Returns:
            str: Форматированный контекст
        """
        if not messages:
            return "Нет сообщений для анализа"
        
        # Группируем сообщения по чатам
        chats_context = {}
        for msg in messages:
            chat_id = msg.get('chat_id', 'unknown')
            chat_title = msg.get('title', f'Чат {chat_id}')
            
            if chat_id not in chats_context:
                chats_context[chat_id] = {
                    'title': chat_title,
                    'messages': []
                }
            
            # Форматируем сообщение
            sender = msg.get('sender', 'Unknown')
            text = msg.get('text', '')
            timestamp = msg.get('ts', '')
            
            formatted_msg = f"[{timestamp}] {sender}: {text}"
            chats_context[chat_id]['messages'].append(formatted_msg)
        
        # Создаем итоговый контекст
        context_parts = []
        for chat_id, chat_data in chats_context.items():
            context_parts.append(f"ЧАТ: {chat_data['title']}")
            context_parts.extend(chat_data['messages'])
            context_parts.append("")  # Пустая строка между чатами
        
        context = "\n".join(context_parts)
        
        # Обрезаем контекст если слишком длинный
        if len(context) > self.max_tokens * 4:  # Примерно 4 символа на токен
            context = context[:self.max_tokens * 4] + "\n... [контекст обрезан]"
        
        return context
    
    def _parse_gpt_response(self, response: str) -> Dict[str, List[str]]:
        """
        Парсинг ответа GPT на структурированные блоки
        
        Args:
            response: Ответ от GPT
            
        Returns:
            Dict с ключами: 'agreements', 'risks', 'recommendations'
        """
        result = {
            'agreements': [],
            'risks': [],
            'recommendations': []
        }
        
        try:
            # Разбиваем на блоки
            blocks = response.split('\n\n')
            
            for block in blocks:
                block = block.strip()
                if not block:
                    continue
                
                # Определяем тип блока
                if 'ДОГОВОРЕННОСТИ:' in block.upper():
                    lines = block.split('\n')[1:]  # Пропускаем заголовок
                    for line in lines:
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            result['agreements'].append(line[1:].strip())
                
                elif 'РИСКИ:' in block.upper():
                    lines = block.split('\n')[1:]  # Пропускаем заголовок
                    for line in lines:
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            result['risks'].append(line[1:].strip())
                
                elif 'РЕКОМЕНДАЦИИ:' in block.upper():
                    lines = block.split('\n')[1:]  # Пропускаем заголовок
                    for line in lines:
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            result['recommendations'].append(line[1:].strip())
        
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа GPT: {e}")
            # Fallback - возвращаем весь ответ как рекомендации
            result['recommendations'] = [response]
        
        return result
    
    def analyze_messages(self, messages: List[Dict]) -> Optional[Dict]:
        """
        Анализ сообщений с помощью GPT
        
        Args:
            messages: Список сообщений для анализа
            
        Returns:
            Dict с результатами анализа или None при ошибке
        """
        if not messages:
            logger.warning("Нет сообщений для анализа")
            return None
        
        try:
            # Подготавливаем контекст
            context = self._prepare_context(messages)
            
            # Формируем промпт
            prompt = self.GPT_PROMPT.format(context=context)
            
            logger.info(f"Отправляем запрос к GPT для анализа {len(messages)} сообщений")
            
            # Отправляем запрос к GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты опытный бизнес-консультант. Отвечай кратко и по делу."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Получаем ответ
            gpt_response = response.choices[0].message.content
            
            # Парсим ответ
            parsed_result = self._parse_gpt_response(gpt_response)
            
            # Добавляем метаданные
            result = {
                'summary': parsed_result,
                'raw_response': gpt_response,
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0,
                'analyzed_at': datetime.now().isoformat(),
                'messages_count': len(messages)
            }
            
            logger.info(f"Анализ завершен. Токены: {result['total_tokens']}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа сообщений: {e}")
            return None
    
    def format_report_for_telegram(self, analysis_result: Dict, active_chats_count: int) -> str:
        """
        Форматирование отчета для отправки в Telegram (plain text)
        
        Args:
            analysis_result: Результат анализа от GPT
            active_chats_count: Количество активных чатов
            
        Returns:
            str: Отформатированный отчет
        """
        if not analysis_result or 'summary' not in analysis_result:
            return "Ошибка анализа сообщений"
        
        summary = analysis_result['summary']
        
        # Заголовок
        report = f"🗂 активные чаты за час: {active_chats_count}\n\n"
        
        # Договоренности
        agreements = summary.get('agreements', [])
        if agreements:
            report += "📌 ключевые договоренности:\n"
            for agreement in agreements[:6]:  # Максимум 6 пунктов
                report += f"- {agreement}\n"
            report += "\n"
        
        # Риски
        risks = summary.get('risks', [])
        if risks:
            report += "⚠️ риски:\n"
            for risk in risks[:3]:  # Максимум 3 строки
                report += f"- {risk}\n"
            report += "\n"
        
        # Рекомендации
        recommendations = summary.get('recommendations', [])
        if recommendations:
            report += "🚀 рекомендации:\n"
            for rec in recommendations[:5]:  # Максимум 5 строк
                report += f"- {rec}\n"
        
        return report
    
    def get_analysis_stats(self, analysis_result: Dict) -> Dict:
        """Получение статистики анализа"""
        if not analysis_result:
            return {}
        
        summary = analysis_result.get('summary', {})
        
        return {
            'messages_analyzed': analysis_result.get('messages_count', 0),
            'agreements_count': len(summary.get('agreements', [])),
            'risks_count': len(summary.get('risks', [])),
            'recommendations_count': len(summary.get('recommendations', [])),
            'prompt_tokens': analysis_result.get('prompt_tokens', 0),
            'completion_tokens': analysis_result.get('completion_tokens', 0),
            'total_tokens': analysis_result.get('total_tokens', 0),
            'analyzed_at': analysis_result.get('analyzed_at', '')
        }

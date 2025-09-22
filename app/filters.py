"""
Модуль фильтрации чатов и сообщений
Реализует систему allowlist/denylist + ключевые слова
"""

import logging
import re
from typing import List, Dict, Set
from .db import DatabaseManager

logger = logging.getLogger(__name__)


class MessageFilter:
    """Класс для фильтрации сообщений по рабочим критериям"""
    
    # Ключевые слова для определения рабочих сообщений
    WORK_KEYWORDS = [
        # Управление и процессы
        "регламент", "regulation", "report", "отчет", "отчёт", "reporting", "KPI", "OKR", 
        "deadline", "дедлайн", "срок", "task", "задача", "таск", "тикет", "priority", "приоритет",
        "execution", "исполнение", "выполнить", "plan", "план", "планёрка", "strategy", "стратегия",
        "discussion", "обсуждение", "совещание", "project", "проект", "проектный", "meeting", "митинг",
        "call", "звонок", "negotiation", "переговоры", "agenda", "повестка", "follow-up",
        
        # Продажи и клиенты
        "сделка", "deal", "client", "клиент", "customer", "заказчик", "buyer", "покупатель",
        "lead", "лид", "заявка", "application", "request", "договор", "contract", "agreement", "контракт",
        "invoice", "счет", "счёт", "инвойс", "payment", "оплата", "платеж", "billing",
        "бронирование", "booking", "reservation", "commission", "комиссия", "margin", "маржа",
        "profit", "прибыль", "revenue", "доход", "earnings", "доходность", "ROI", "return",
        
        # Инвестиции и недвижимость
        "инвестиции", "investments", "investor", "инвестор", "capital", "капитал", "assets", "активы",
        "apartment", "квартира", "апартаменты", "flat", "condo", "condominium", "residence", "жильё",
        "вилла", "villa", "townhouse", "новостройка", "developer", "застройщик", "объект", "property", "недвижимость",
        "listing", "объект недвижимости", "location", "локация", "район", "аренда офиса", "office rent",
        "rental", "аренда", "rental agreement", "лизинг", "mortgage", "ипотека", "loan", "кредит",
        "escrow", "эскроу", "insurance", "страховка",
        
        # Юридические и финансовые
        "юридический", "legal", "юрист", "lawyer", "compliance", "комплаенс", "лицензия", "license",
        "registration", "регистрация", "tax", "налог", "accounting", "бухгалтерия", "finance", "финансы",
        "бухгалтер", "акт", "document", "документ", "документация", "спецификация", "specification",
        "согласовать", "согласование", "approval", "утвердить", "утверждение", "инструкция", "instruction",
        "guideline", "policy", "policy doc",
        
        # Бизнес-процессы
        "business", "бизнес", "рабочий вопрос", "work issue", "workflow", "operations", "operations team",
        "performance", "эффективность", "productivity", "продуктивность", "optimization", "оптимизация",
        "отчетность", "statistics", "статистика", "analytics", "аналитика", "data", "данные", "BI",
        "бизнес-аналитика", "Google Sheets", "таблица", "Excel", "spreadsheet", "база данных", "database",
        "CRM", "AmoCRM", "ERP", "интеграция", "integration", "API", "скрипт", "script", "automation", "автоматизация",
        "bot", "бот", "AI", "искусственный интеллект",
        
        # Маркетинг и реклама
        "маркетинг", "marketing", "продвижение", "promotion", "таргет", "target", "targeting", "таргетолог",
        "ads", "реклама", "advertising", "рекламная кампания", "campaign", "креатив", "creative",
        "баннер", "banner", "контент", "content", "пост", "post", "публикация", "publication",
        "reels", "рилс", "stories", "stories ad", "соцсети", "SMM", "social media", "охваты", "reach",
        "conversion", "конверсия", "лидогенерация", "leadgen", "funnel", "воронка", "traffic", "трафик",
        "CPC", "CPA", "CPL", "CTR",
        
        # HR и управление персоналом
        "candidate", "кандидат", "hire", "нанять", "найм", "recruitment", "рекрутинг", "HR", "human resources",
        "employee", "сотрудник", "работник", "team", "команда", "staff", "персонал", "собеседование", "interview",
        "onboarding", "адаптация", "adaptation", "увольнение", "termination", "мотивация", "motivation",
        "бонус", "bonus", "оклад", "salary", "зарплата", "премия", "reward", "benefit", "compensation",
        "remuneration", "окладная часть", "training", "обучение", "development", "развитие"
    ]
    
    # Ключевые слова для определения личных сообщений
    PERSONAL_KEYWORDS = [
        "привет", "как дела", "семья", "друзья", "отдых", "выходные", "покупки", 
        "дом", "еда", "фильм", "книга", "спорт", "хобби", "погода", "настроение", 
        "личный", "день рождения", "праздник", "отпуск", "путешествие", "здоровье",
        "болезнь", "лечение", "врач", "больница", "лекарство", "диета",
        "любовь", "отношения", "свадьба", "развод", "дети", "школа", "университет",
        "развлечения", "игра", "музыка", "концерт", "театр", "музей", "ресторан"
    ]
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._load_filters()
    
    def _load_filters(self):
        """Загрузка фильтров из базы данных"""
        try:
            self.allow_chats = set()
            self.deny_chats = set()
            self.custom_keywords = set()
            
            filters = self.db.get_filters()
            for filter_item in filters:
                kind = filter_item['kind']
                value = filter_item['value']
                
                if kind == 'allow_chat':
                    self.allow_chats.add(value)
                elif kind == 'deny_chat':
                    self.deny_chats.add(value)
                elif kind == 'keyword':
                    self.custom_keywords.add(value.lower())
            
            logger.info(f"Загружено фильтров: allow={len(self.allow_chats)}, "
                       f"deny={len(self.deny_chats)}, keywords={len(self.custom_keywords)}")
                       
        except Exception as e:
            logger.error(f"Ошибка загрузки фильтров: {e}")
            self.allow_chats = set()
            self.deny_chats = set()
            self.custom_keywords = set()
    
    def is_work_chat(self, chat_id: str, chat_title: str = "") -> bool:
        """
        Определение является ли чат рабочим
        
        Логика:
        1. Если чат в allowlist - рабочий
        2. Если чат в denylist - не рабочий  
        3. Если allowlist пуст - проверяем denylist + ключевые слова
        """
        try:
            # Приоритет allowlist
            if self.allow_chats and chat_id in self.allow_chats:
                return True
            
            # Исключение из denylist
            if chat_id in self.deny_chats:
                return False
            
            # Если allowlist пуст - проверяем по ключевым словам
            if not self.allow_chats:
                return self._check_work_keywords(chat_title)
            
            # Если в allowlist, но чат не найден - не рабочий
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки рабочего чата: {e}")
            return False
    
    def is_work_message(self, text: str) -> bool:
        """
        Определение является ли сообщение рабочим по содержимому
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Проверяем все ключевые слова (встроенные + пользовательские)
        all_keywords = set(self.WORK_KEYWORDS) | self.custom_keywords
        
        # Подсчет рабочих ключевых слов
        work_count = 0
        for keyword in all_keywords:
            if keyword.lower() in text_lower:
                work_count += 1
        
        # Подсчет личных ключевых слов
        personal_count = 0
        for keyword in self.PERSONAL_KEYWORDS:
            if keyword.lower() in text_lower:
                personal_count += 1
        
        # Если больше рабочих слов чем личных - сообщение рабочее
        return work_count > personal_count
    
    def _check_work_keywords(self, text: str) -> bool:
        """Проверка ключевых слов в тексте"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Проверяем рабочие ключевые слова
        for keyword in self.WORK_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        
        # Проверяем пользовательские ключевые слова
        for keyword in self.custom_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def add_allow_chat(self, chat_id: str) -> bool:
        """Добавление чата в allowlist"""
        result = self.db.add_filter('allow_chat', chat_id)
        if result:
            self.allow_chats.add(chat_id)
            self._load_filters()  # Перезагружаем фильтры
        return result
    
    def add_deny_chat(self, chat_id: str) -> bool:
        """Добавление чата в denylist"""
        result = self.db.add_filter('deny_chat', chat_id)
        if result:
            self.deny_chats.add(chat_id)
            self._load_filters()  # Перезагружаем фильтры
        return result
    
    def add_keyword(self, keyword: str) -> bool:
        """Добавление ключевого слова"""
        result = self.db.add_filter('keyword', keyword.lower())
        if result:
            self.custom_keywords.add(keyword.lower())
            self._load_filters()  # Перезагружаем фильтры
        return result
    
    def remove_allow_chat(self, chat_id: str) -> bool:
        """Удаление чата из allowlist"""
        # TODO: Реализовать удаление фильтра из БД
        self.allow_chats.discard(chat_id)
        return True
    
    def remove_deny_chat(self, chat_id: str) -> bool:
        """Удаление чата из denylist"""
        # TODO: Реализовать удаление фильтра из БД
        self.deny_chats.discard(chat_id)
        return True
    
    def filter_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Фильтрация списка сообщений по рабочим критериям
        Возвращает только рабочие сообщения
        """
        work_messages = []
        
        for message in messages:
            chat_id = message.get('chat_id', '')
            text = message.get('text', '')
            
            # Проверяем является ли сообщение рабочим
            if self.is_work_message(text):
                work_messages.append(message)
        
        logger.info(f"Отфильтровано рабочих сообщений: {len(work_messages)} из {len(messages)}")
        return work_messages
    
    def get_filter_stats(self) -> Dict:
        """Получение статистики фильтров"""
        return {
            'allow_chats_count': len(self.allow_chats),
            'deny_chats_count': len(self.deny_chats),
            'custom_keywords_count': len(self.custom_keywords),
            'work_keywords_count': len(self.WORK_KEYWORDS),
            'personal_keywords_count': len(self.PERSONAL_KEYWORDS)
        }

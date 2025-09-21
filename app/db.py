"""
Модуль для работы с SQLite базой данных
Создает и управляет схемой БД согласно ТЗ
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str = "telegram_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица чатов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id TEXT UNIQUE NOT NULL,
                        title TEXT,
                        type TEXT,
                        is_work BOOLEAN DEFAULT 0,
                        last_seen_message_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица сообщений
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id TEXT NOT NULL,
                        tg_message_id TEXT NOT NULL,
                        sender TEXT,
                        text TEXT,
                        ts DATETIME NOT NULL,
                        is_business BOOLEAN DEFAULT 0,
                        raw_json TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                    )
                """)
                
                # Таблица запусков анализа
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ran_at DATETIME NOT NULL,
                        window_start DATETIME NOT NULL,
                        window_end DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица отчетов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id INTEGER NOT NULL,
                        chat_id TEXT NOT NULL,
                        summary TEXT,
                        risks TEXT,
                        actions TEXT,
                        raw_prompt_tokens INTEGER,
                        raw_completion_tokens INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (run_id) REFERENCES runs (id),
                        FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                    )
                """)
                
                # Таблица фильтров
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS filters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kind TEXT NOT NULL,
                        value TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Индексы для оптимизации
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages (ts)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_is_business ON messages (is_business)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_run_id ON reports (run_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_filters_kind ON filters (kind)")
                
                conn.commit()
                logger.info("База данных успешно инициализирована")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def insert_chat(self, chat_id: str, title: str, chat_type: str, is_work: bool = False) -> bool:
        """Добавление или обновление чата"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO chats (chat_id, title, type, is_work, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (chat_id, title, chat_type, is_work))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления чата {chat_id}: {e}")
            return False
    
    def insert_message(self, chat_id: str, tg_message_id: str, sender: str, 
                      text: str, ts: datetime, is_business: bool = False, 
                      raw_json: str = None) -> bool:
        """Добавление сообщения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (chat_id, tg_message_id, sender, text, ts, is_business, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (chat_id, tg_message_id, sender, text, ts, is_business, raw_json))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения: {e}")
            return False
    
    def get_new_messages(self, window_start: datetime, window_end: datetime) -> List[Dict]:
        """Получение новых сообщений за временное окно"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, c.title, c.is_work, c.type
                    FROM messages m
                    JOIN chats c ON m.chat_id = c.chat_id
                    WHERE m.ts >= ? AND m.ts < ?
                    ORDER BY m.ts ASC
                """, (window_start, window_end))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения сообщений: {e}")
            return []
    
    def get_work_chats(self) -> List[Dict]:
        """Получение списка рабочих чатов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chats WHERE is_work = 1")
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения рабочих чатов: {e}")
            return []
    
    def create_run(self, ran_at: datetime, window_start: datetime, window_end: datetime) -> int:
        """Создание записи о запуске анализа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO runs (ran_at, window_start, window_end)
                    VALUES (?, ?, ?)
                """, (ran_at, window_start, window_end))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка создания записи запуска: {e}")
            return 0
    
    def insert_report(self, run_id: int, chat_id: str, summary: str, 
                     risks: str, actions: str, prompt_tokens: int = 0, 
                     completion_tokens: int = 0) -> bool:
        """Добавление отчета анализа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reports (run_id, chat_id, summary, risks, actions, 
                                       raw_prompt_tokens, raw_completion_tokens)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (run_id, chat_id, summary, risks, actions, prompt_tokens, completion_tokens))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления отчета: {e}")
            return False
    
    def add_filter(self, kind: str, value: str) -> bool:
        """Добавление фильтра (allow_chat, deny_chat, keyword)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO filters (kind, value)
                    VALUES (?, ?)
                """, (kind, value))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления фильтра: {e}")
            return False
    
    def get_filters(self, kind: str = None) -> List[Dict]:
        """Получение фильтров"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if kind:
                    cursor.execute("SELECT * FROM filters WHERE kind = ?", (kind,))
                else:
                    cursor.execute("SELECT * FROM filters")
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения фильтров: {e}")
            return []
    
    def update_chat_last_message(self, chat_id: str, last_message_id: str) -> bool:
        """Обновление ID последнего сообщения в чате"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE chats SET last_seen_message_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                """, (last_message_id, chat_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления последнего сообщения: {e}")
            return False

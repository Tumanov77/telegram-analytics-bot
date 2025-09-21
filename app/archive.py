"""
Модуль архивирования результатов анализа
Сохраняет отчеты в Google Drive (TXT) и Google Sheets (индекс)
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Области доступа Google API
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]


class ArchiveManager:
    """Менеджер архивирования в Google Drive и Sheets"""
    
    def __init__(self, credentials_file: str):
        """
        Инициализация менеджера архивирования
        
        Args:
            credentials_file: Путь к файлу Google credentials
        """
        self.credentials_file = credentials_file
        self.drive_service = None
        self.sheets_service = None
        self.spreadsheet_id = None
        
        # Инициализируем сервисы
        self._initialize_services()
    
    def _initialize_services(self):
        """Инициализация Google сервисов"""
        try:
            creds = self._get_credentials()
            
            # Инициализируем Drive API
            self.drive_service = build('drive', 'v3', credentials=creds)
            
            # Инициализируем Sheets API
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            
            logger.info("Google сервисы инициализированы успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Google сервисов: {e}")
            raise
    
    def _get_credentials(self) -> Credentials:
        """Получение и обновление Google credentials"""
        creds = None
        
        # Файл токена сохраняется автоматически после первого авторизации
        token_file = 'token.json'
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # Если нет валидных credentials, запрашиваем авторизацию
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Сохраняем credentials для следующего запуска
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def create_daily_report_file(self, date: datetime, reports: List[Dict]) -> Optional[str]:
        """
        Создание ежедневного TXT файла с отчетами
        
        Args:
            date: Дата отчета
            reports: Список отчетов для архивирования
            
        Returns:
            str: ID файла в Google Drive или None при ошибке
        """
        try:
            # Формируем содержимое файла
            content = self._format_daily_report(date, reports)
            
            # Создаем файл в Google Drive
            file_metadata = {
                'name': f'TelegramReports/{date.strftime("%Y-%m-%d")}.txt',
                'parents': [self._get_or_create_folder()]
            }
            
            media_body = {
                'mimeType': 'text/plain',
                'body': content
            }
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media_body,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Создан ежедневный отчет: {file_id}")
            
            return file_id
            
        except Exception as e:
            logger.error(f"Ошибка создания ежедневного отчета: {e}")
            return None
    
    def _format_daily_report(self, date: datetime, reports: List[Dict]) -> str:
        """Форматирование ежедневного отчета в TXT"""
        content = []
        
        # Заголовок
        content.append(f"ОТЧЕТ TELEGRAM ANALYTICS BOT")
        content.append(f"Дата: {date.strftime('%Y-%m-%d')}")
        content.append(f"Создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("=" * 50)
        content.append("")
        
        # Содержимое отчетов
        for i, report in enumerate(reports, 1):
            chat_title = report.get('chat_title', f'Chat {report.get("chat_id", "unknown")}')
            analysis = report.get('analysis', {})
            summary = analysis.get('summary', {})
            
            content.append(f"ОТЧЕТ {i}: {chat_title}")
            content.append("-" * 30)
            
            # Договоренности
            agreements = summary.get('agreements', [])
            if agreements:
                content.append("ДОГОВОРЕННОСТИ:")
                for agreement in agreements:
                    content.append(f"- {agreement}")
                content.append("")
            
            # Риски
            risks = summary.get('risks', [])
            if risks:
                content.append("РИСКИ:")
                for risk in risks:
                    content.append(f"- {risk}")
                content.append("")
            
            # Рекомендации
            recommendations = summary.get('recommendations', [])
            if recommendations:
                content.append("РЕКОМЕНДАЦИИ:")
                for rec in recommendations:
                    content.append(f"- {rec}")
                content.append("")
            
            content.append("=" * 50)
            content.append("")
        
        return "\n".join(content)
    
    def _get_or_create_folder(self) -> str:
        """Получение или создание папки TelegramReports в Google Drive"""
        try:
            # Ищем папку
            results = self.drive_service.files().list(
                q="name='TelegramReports' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # Создаем папку если не найдена
            folder_metadata = {
                'name': 'TelegramReports',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            logger.info(f"Создана папка TelegramReports: {folder['id']}")
            return folder['id']
            
        except Exception as e:
            logger.error(f"Ошибка работы с папкой: {e}")
            return None
    
    def create_spreadsheet_index(self, spreadsheet_name: str = "Telegram Analytics Reports Index") -> Optional[str]:
        """
        Создание или получение Google Sheets для индекса отчетов
        
        Args:
            spreadsheet_name: Название таблицы
            
        Returns:
            str: ID таблицы или None при ошибке
        """
        try:
            # Создаем новую таблицу
            spreadsheet = {
                'properties': {
                    'title': spreadsheet_name
                },
                'sheets': [{
                    'properties': {
                        'title': 'reports_index',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 5
                        }
                    }
                }]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            self.spreadsheet_id = spreadsheet.get('spreadsheetId')
            
            # Добавляем заголовки
            self._setup_index_headers()
            
            logger.info(f"Создана таблица индекса: {self.spreadsheet_id}")
            return self.spreadsheet_id
            
        except Exception as e:
            logger.error(f"Ошибка создания таблицы индекса: {e}")
            return None
    
    def _setup_index_headers(self):
        """Настройка заголовков в таблице индекса"""
        try:
            headers = [
                ['Дата', 'Чат', 'Ссылка на файл', 'Краткий итог', 'Создан']
            ]
            
            body = {
                'values': headers
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='reports_index!A1:E1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info("Заголовки таблицы индекса настроены")
            
        except Exception as e:
            logger.error(f"Ошибка настройки заголовков: {e}")
    
    def add_index_entry(self, date: datetime, chat_title: str, file_link: str, summary: str):
        """
        Добавление записи в индекс отчетов
        
        Args:
            date: Дата отчета
            chat_title: Название чата
            file_link: Ссылка на файл в Drive
            summary: Краткий итог (первая рекомендация)
        """
        try:
            if not self.spreadsheet_id:
                logger.warning("Не настроен spreadsheet_id для индекса")
                return
            
            # Получаем первую рекомендацию как краткий итог
            summary_text = summary.split('\n')[0] if summary else "Нет рекомендаций"
            
            entry = [
                date.strftime('%Y-%m-%d'),
                chat_title,
                file_link,
                summary_text,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # Добавляем строку в конец таблицы
            body = {
                'values': [entry]
            }
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='reports_index!A:E',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Добавлена запись в индекс: {chat_title}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления записи в индекс: {e}")
    
    def archive_daily_reports(self, date: datetime, reports: List[Dict]) -> bool:
        """
        Архивирование всех отчетов за день
        
        Args:
            date: Дата отчетов
            reports: Список отчетов для архивирования
            
        Returns:
            bool: True если архивирование успешно
        """
        try:
            if not reports:
                logger.info("Нет отчетов для архивирования")
                return True
            
            # Создаем ежедневный TXT файл
            file_id = self.create_daily_report_file(date, reports)
            if not file_id:
                return False
            
            # Создаем ссылку на файл
            file_link = f"https://drive.google.com/file/d/{file_id}/view"
            
            # Создаем или получаем таблицу индекса
            if not self.spreadsheet_id:
                self.create_spreadsheet_index()
            
            # Добавляем записи в индекс для каждого чата
            for report in reports:
                chat_title = report.get('chat_title', f'Chat {report.get("chat_id", "unknown")}')
                analysis = report.get('analysis', {})
                summary = analysis.get('summary', {})
                
                # Берем первую рекомендацию как краткий итог
                recommendations = summary.get('recommendations', [])
                summary_text = recommendations[0] if recommendations else "Нет рекомендаций"
                
                self.add_index_entry(date, chat_title, file_link, summary_text)
            
            logger.info(f"Архивирование завершено для {len(reports)} отчетов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка архивирования: {e}")
            return False
    
    def get_archive_stats(self) -> Dict:
        """Получение статистики архивирования"""
        try:
            stats = {
                'drive_connected': self.drive_service is not None,
                'sheets_connected': self.sheets_service is not None,
                'spreadsheet_id': self.spreadsheet_id,
                'folder_exists': False
            }
            
            # Проверяем существование папки
            if self.drive_service:
                try:
                    folder_id = self._get_or_create_folder()
                    stats['folder_exists'] = folder_id is not None
                except:
                    pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики архивирования: {e}")
            return {'error': str(e)}

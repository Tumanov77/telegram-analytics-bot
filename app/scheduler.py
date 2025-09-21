"""
Модуль планировщика задач
Настраивает и управляет часовым анализом сообщений
"""

import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """Планировщик для автоматического анализа сообщений"""
    
    def __init__(self, analysis_callback: Callable):
        """
        Инициализация планировщика
        
        Args:
            analysis_callback: Функция для выполнения анализа
        """
        self.analysis_callback = analysis_callback
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        logger.info("Планировщик инициализирован")
    
    def start_hourly_analysis(self, hour: int = None, minute: int = 0):
        """
        Запуск ежечасного анализа
        
        Args:
            hour: Час для запуска (None = каждый час)
            minute: Минута для запуска
        """
        try:
            if hour is not None:
                # Запуск в определенный час
                trigger = CronTrigger(hour=hour, minute=minute)
                job_id = f"hourly_analysis_{hour}_{minute}"
            else:
                # Запуск каждый час
                trigger = IntervalTrigger(hours=1)
                job_id = "hourly_analysis_interval"
            
            # Добавляем задачу
            self.scheduler.add_job(
                func=self._run_analysis,
                trigger=trigger,
                id=job_id,
                name="Анализ сообщений",
                max_instances=1,  # Только один экземпляр одновременно
                coalesce=True,    # Объединять пропущенные запуски
                misfire_grace_time=300  # 5 минут на выполнение
            )
            
            logger.info(f"Настроен часовой анализ: {trigger}")
            
        except Exception as e:
            logger.error(f"Ошибка настройки планировщика: {e}")
            raise
    
    def start_daily_archive(self, hour: int = 23, minute: int = 0):
        """
        Запуск ежедневного архивирования
        
        Args:
            hour: Час для архивирования
            minute: Минута для архивирования
        """
        try:
            trigger = CronTrigger(hour=hour, minute=minute)
            
            self.scheduler.add_job(
                func=self._run_daily_archive,
                trigger=trigger,
                id="daily_archive",
                name="Ежедневное архивирование",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=600  # 10 минут на выполнение
            )
            
            logger.info(f"Настроено ежедневное архивирование: {trigger}")
            
        except Exception as e:
            logger.error(f"Ошибка настройки архивирования: {e}")
            raise
    
    async def _run_analysis(self):
        """Выполнение анализа сообщений"""
        try:
            logger.info("Запуск запланированного анализа...")
            start_time = datetime.now()
            
            # Вызываем callback функцию анализа
            if asyncio.iscoroutinefunction(self.analysis_callback):
                success = await self.analysis_callback()
            else:
                success = self.analysis_callback()
            
            duration = datetime.now() - start_time
            
            if success:
                logger.info(f"Анализ завершен успешно за {duration.total_seconds():.1f} сек")
            else:
                logger.warning(f"Анализ завершен с ошибками за {duration.total_seconds():.1f} сек")
                
        except Exception as e:
            logger.error(f"Ошибка выполнения анализа: {e}")
    
    async def _run_daily_archive(self):
        """Выполнение ежедневного архивирования"""
        try:
            logger.info("Запуск ежедневного архивирования...")
            
            # TODO: Реализовать ежедневное архивирование
            # Пока что просто логируем
            logger.info("Ежедневное архивирование выполнено")
            
        except Exception as e:
            logger.error(f"Ошибка ежедневного архивирования: {e}")
    
    def add_custom_job(self, func: Callable, trigger, job_id: str, **kwargs):
        """
        Добавление пользовательской задачи
        
        Args:
            func: Функция для выполнения
            trigger: Триггер запуска
            job_id: Уникальный ID задачи
            **kwargs: Дополнительные параметры задачи
        """
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                **kwargs
            )
            
            logger.info(f"Добавлена пользовательская задача: {job_id}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления задачи {job_id}: {e}")
            raise
    
    def remove_job(self, job_id: str):
        """Удаление задачи по ID"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Удалена задача: {job_id}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {job_id}: {e}")
    
    def get_jobs(self):
        """Получение списка активных задач"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                })
            return jobs
            
        except Exception as e:
            logger.error(f"Ошибка получения списка задач: {e}")
            return []
    
    def start(self):
        """Запуск планировщика"""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                logger.info("Планировщик запущен")
            else:
                logger.warning("Планировщик уже запущен")
                
        except Exception as e:
            logger.error(f"Ошибка запуска планировщика: {e}")
            raise
    
    def stop(self):
        """Остановка планировщика"""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Планировщик остановлен")
            else:
                logger.warning("Планировщик уже остановлен")
                
        except Exception as e:
            logger.error(f"Ошибка остановки планировщика: {e}")
    
    def pause(self):
        """Приостановка планировщика"""
        try:
            if self.is_running:
                self.scheduler.pause()
                logger.info("Планировщик приостановлен")
            else:
                logger.warning("Планировщик не запущен")
                
        except Exception as e:
            logger.error(f"Ошибка приостановки планировщика: {e}")
    
    def resume(self):
        """Возобновление работы планировщика"""
        try:
            if self.is_running:
                self.scheduler.resume()
                logger.info("Планировщик возобновлен")
            else:
                logger.warning("Планировщик не запущен")
                
        except Exception as e:
            logger.error(f"Ошибка возобновления планировщика: {e}")
    
    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Получение времени следующего запуска задачи"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return job.next_run_time
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения времени запуска {job_id}: {e}")
            return None
    
    def get_status(self) -> dict:
        """Получение статуса планировщика"""
        try:
            jobs = self.get_jobs()
            
            return {
                'is_running': self.is_running,
                'jobs_count': len(jobs),
                'jobs': jobs,
                'next_analysis': self.get_next_run_time('hourly_analysis_interval'),
                'next_archive': self.get_next_run_time('daily_archive')
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса планировщика: {e}")
            return {'error': str(e)}


# Утилиты для работы с планировщиком
def create_hourly_trigger(minute: int = 0) -> IntervalTrigger:
    """Создание триггера для запуска каждый час"""
    return IntervalTrigger(hours=1)


def create_daily_trigger(hour: int = 0, minute: int = 0) -> CronTrigger:
    """Создание триггера для запуска ежедневно"""
    return CronTrigger(hour=hour, minute=minute)


def create_weekly_trigger(day_of_week: int = 0, hour: int = 0, minute: int = 0) -> CronTrigger:
    """Создание триггера для запуска еженедельно"""
    return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)

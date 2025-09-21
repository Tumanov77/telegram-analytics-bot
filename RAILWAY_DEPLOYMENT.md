# 🚀 Railway.app Deployment Guide

## Автоматическая настройка Telegram Analytics Bot

### ШАГ 1: Создание аккаунта
1. Перейдите на [railway.app](https://railway.app)
2. Нажмите "Sign Up" 
3. Войдите через GitHub (рекомендуется)

### ШАГ 2: Создание проекта
1. Нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Подключите ваш GitHub аккаунт
4. Найдите репозиторий `telegram-analytics-bot`
5. Нажмите "Deploy"

### ШАГ 3: Настройка переменных окружения
В Railway Dashboard:
1. Перейдите в ваш проект
2. Выберите сервис (ваш бот)
3. Перейдите в "Variables" tab
4. Добавьте следующие переменные:

```
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
OPENAI_API_KEY=ваш_openai_api_key
TARGET_USER_ID=161911490
GPT_MODEL=gpt-4o
LOG_LEVEL=INFO
```

### ШАГ 4: Проверка работы
1. Railway автоматически задеплоит ваш бот
2. Перейдите в "Deployments" tab
3. Нажмите на последний деплой
4. Проверьте логи - должно быть "Application started"
5. Протестируйте бота в Telegram

### ШАГ 5: Мониторинг
- **Логи**: Railway Dashboard → Service → Logs
- **Метрики**: Railway Dashboard → Service → Metrics
- **Перезапуск**: Railway автоматически перезапускает при сбоях

## 🆓 Бесплатные лимиты Railway:
- ✅ **500 часов** в месяц (достаточно для 24/7)
- ✅ **1 GB RAM**
- ✅ **1 GB дискового пространства**
- ✅ **Автоматические перезапуски**

## 🔧 Полезные команды:
```bash
# Просмотр логов
railway logs

# Переменные окружения
railway variables

# Перезапуск сервиса
railway service restart
```

## 🚨 Устранение проблем:
1. **Бот не отвечает**: Проверьте переменные окружения
2. **Ошибки в логах**: Убедитесь, что все API ключи корректны
3. **Высокое потребление**: Проверьте настройки логирования

---
**Бот будет работать 24/7 бесплатно на Railway!** 🎉

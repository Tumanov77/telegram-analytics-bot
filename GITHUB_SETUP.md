# 📋 GitHub Setup Instructions

## Создание репозитория на GitHub

### ШАГ 1: Создайте репозиторий
1. Перейдите на [github.com](https://github.com)
2. Нажмите "New repository"
3. Название: `telegram-analytics-bot`
4. Описание: `Telegram Analytics Bot for work message analysis`
5. Выберите **Public** (для бесплатного Railway)
6. НЕ добавляйте README, .gitignore, license
7. Нажмите "Create repository"

### ШАГ 2: Подключите локальный репозиторий
После создания репозитория GitHub покажет команды. Выполните:

```bash
cd "/Users/nickmoscow/Cursor 08.2025/telegram-analytics-bot"
git remote add origin https://github.com/YOUR_USERNAME/telegram-analytics-bot.git
git branch -M main
git push -u origin main
```

**Замените `YOUR_USERNAME` на ваш GitHub username!**

### ШАГ 3: Проверка
После выполнения команд ваш код будет загружен на GitHub и готов для Railway!

---
**Следующий шаг**: Railway Deployment Guide 📖

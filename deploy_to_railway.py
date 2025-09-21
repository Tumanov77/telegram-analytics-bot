#!/usr/bin/env python3
"""
Автоматический скрипт для деплоя на Railway.app
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - успешно!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - ошибка!")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False
    return True

def main():
    """Основная функция деплоя"""
    print("🚀 Автоматический деплой Telegram Analytics Bot на Railway.app")
    print("=" * 60)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("railway.json"):
        print("❌ Файл railway.json не найден! Запустите скрипт из корня проекта.")
        return
    
    # Проверяем Git
    if not run_command("git status", "Проверка Git статуса"):
        print("❌ Git не инициализирован или есть проблемы")
        return
    
    # Добавляем все файлы
    if not run_command("git add .", "Добавление файлов в Git"):
        return
    
    # Коммитим изменения
    if not run_command('git commit -m "Railway deployment setup"', "Создание коммита"):
        return
    
    print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Создайте репозиторий на GitHub (github.com)")
    print("2. Выполните команды из GITHUB_SETUP.md")
    print("3. Задеплойте на Railway по инструкции RAILWAY_DEPLOYMENT.md")
    print("\n🎉 Все готово для деплоя!")

if __name__ == "__main__":
    main()

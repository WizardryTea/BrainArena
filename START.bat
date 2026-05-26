@echo off
chcp 65001 >nul
title BRAIN ARENA - Запуск
color 0A

echo ==========================================
echo   Интеллектуальные игры - Быстрый запуск
echo ==========================================
echo Для корректной работы убедитесь, что в .env - DEBUG=False
echo.

REM Проверка наличия виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo ОШИБКА: Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ОШИБКА: Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)

REM Установка зависимостей
echo Установка зависимостей...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости
    pause
    exit /b 1
)

REM Создание .env файла если его нет
if not exist ".env" (
    echo Создание файла конфигурации...
    copy environment_config.txt .env
    echo Файл .env создан. Отредактируйте его при необходимости.
)

REM Создание миграций
echo Создание миграций...
python manage.py makemigrations
if errorlevel 1 (
    echo ОШИБКА: Не удалось создать миграции
    pause
    exit /b 1
)

REM Проверка - выполнение миграций для games
python manage.py makemigrations games
REM Проверка - выполнение миграций для users
python manage.py makemigrations users

REM Выполнение миграций
echo Выполнение миграций...
python manage.py migrate --verbosity=0
if errorlevel 1 (
    echo ОШИБКА: Не удалось выполнить миграции
    pause
    exit /b 1
)

REM Создание суперпользователя (если не существует)
echo Проверка суперпользователя...
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

echo.
echo ========================================
echo   Запуск сервера разработки...
echo ========================================
echo.
echo Приложение будет доступно по адресу:
echo http://127.0.0.1:8000/
echo.
echo Админ-панель:
echo http://127.0.0.1:8000/admin/
echo Логин: admin
echo Пароль: admin
echo.
echo Для остановки сервера нажмите Ctrl+C
echo.

REM Запуск сервера
python manage.py runserver 0.0.0.0:8000

pause

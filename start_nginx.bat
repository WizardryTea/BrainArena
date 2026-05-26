@echo off
chcp 65001 >nul
title BRAIN ARENA - Запуск с Nginx
color 0A

echo.
echo  ===============================
echo    Запуск Brain Arena с Nginx
echo  ===============================
echo.

REM Устанавливаем переменную для указания nginx на конфиг
set NGINX_DIR=%~dp0nginx

REM Проверяем, не запущен ли уже nginx
%NGINX_DIR%\nginx.exe -s stop 2>nul

REM Загружаем статику в staticfiles
echo [1/3] Сбор статики...
python manage.py collectstatic --noinput 2>&1
if %errorlevel% neq 0 (
    echo Ошибка при сборе статики!
    pause
    exit /b 1
)

REM Запускаем nginx
echo [2/3] Запуск Nginx...
start "" "%NGINX_DIR%\nginx.exe" -p "%NGINX_DIR%"
if %errorlevel% neq 0 (
    echo Ошибка при запуске Nginx!
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul

REM Запускаем Django сервер
echo [3/3] Запуск Django-сервера (DEBUG=False, порт 8000)...
echo.
echo  ===============================
echo   Сайт доступен по адресу:
echo   http://127.0.0.1:80
echo   http://localhost:80
echo  ===============================
echo.

python manage.py runserver 0.0.0.0:8000 --noreload

REM Автоматически открыть браузер
start http://localhost
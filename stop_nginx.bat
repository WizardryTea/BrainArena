@echo off
chcp 65001 >nul
title BRAIN ARENA - Остановка Nginx
color 0C

echo.
echo  ===============================
echo     Остановка Nginx и Django
echo  ===============================
echo.

set NGINX_DIR=%~dp0nginx

REM Останавливаем nginx
echo Остановка Nginx...
%NGINX_DIR%\nginx.exe -s quit 2>nul
if %errorlevel% equ 0 (
    echo Nginx успешно остановлен.
) else (
    %NGINX_DIR%\nginx.exe -s stop 2>nul
    echo Nginx принудительно остановлен.
)

REM Пытаемся остановить Django-сервер
echo Остановка Django-сервера...
taskkill /f /im python.exe 2>nul 1>nul
echo Django-сервер остановлен.

echo.
echo  ===============================
echo        Все процессы остановлены
echo  ===============================
echo.

pause
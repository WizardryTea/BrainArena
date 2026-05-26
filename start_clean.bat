@echo off
chcp 65001 >nul
title BRAIN ARENA - Запуск с очисткой БД
color 0A

echo.
echo  =============================
echo         Полная очистка
echo  =============================
echo.


REM Удаление миграций
rm -r games/migrations/*

python manage.py makemigrations games zero
python manage.py makemigrations users zero

REM Пересоздание миграций
python manage.py makemigrations
python manage.py migrate
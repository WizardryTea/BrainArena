@echo off
chcp 65001 > nul
title Запуск тестов
echo =====================================
echo   Запуск тестов
echo =====================================


echo [1/5] Тестирование brain_arena (конфигурация проекта)...
python manage.py test brain_arena --verbosity=2 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Тесты brain_arena не пройдены!
    set HAS_ERROR=1
) else (
    echo [OK] Тесты brain_arena пройдены
)
echo.

echo [2/5] Тестирование games (модели, менеджеры, фабрика, реестр)...
python manage.py test games.tests.GameModelTest games.tests.GameSessionModelTest games.tests.GameSessionManagerTest games.tests.RegistryTest games.tests.GameFactoryTest --verbosity=2 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Тесты моделей games не пройдены!
    set HAS_ERROR=1
) else (
    echo [OK] Тесты моделей games пройдены
)
echo.

echo [3/5] Тестирование games (движок, URLы, представления)...
python manage.py test games.tests.BaseEngineTest games.tests.URLTest games.tests.ViewTest games.tests.AdminRegistrationTest --verbosity=2 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Тесты движка и представлений games не пройдены!
    set HAS_ERROR=1
) else (
    echo [OK] Тесты движка и представлений games пройдены
)
echo.

echo [4/5] Тестирование users (модели, формы, сигналы)...
python manage.py test users.tests.UserProfileModelTest users.tests.UserProfileSignalsTest users.tests.UserRegistrationFormTest users.tests.UserProfileFormTest users.tests.UserUpdateFormTest --verbosity=2 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Тесты моделей и форм users не пройдены!
    set HAS_ERROR=1
) else (
    echo [OK] Тесты моделей и форм users пройдены
)
echo.

echo [5/5] Тестирование users (URLы, представления)...
python manage.py test users.tests.URLTest users.tests.ViewTest --verbosity=2 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Тесты URL и представлений users не пройдены!
    set HAS_ERROR=1
) else (
    echo [OK] Тесты URL и представлений users пройдены
)
echo.

echo =====================================
if "%HAS_ERROR%"=="1" (
    echo НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!
    echo Проверьте вывод выше для деталей.
) else (
    echo ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!
)
echo =====================================
echo.

echo Запустить полный набор тестов (все сразу)? [y/N]
set /p RUN_ALL=
if /i "%RUN_ALL%"=="y" (
    echo.
    echo Запуск всех тестов проекта...
    python manage.py test brain_arena games users --verbosity=2 2>&1
    echo.
    echo =====================================
    echo   РЕЗУЛЬТАТ ВСЕХ ТЕСТОВ
    echo =====================================
)

echo.
pause
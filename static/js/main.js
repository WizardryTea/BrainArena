// Основной JavaScript для приложения интеллектуальных игр

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех компонентов
    initializeAnimations();
    initializeTooltips();
    initializeDragAndDrop();
    initializeGameElements();
});

// Анимации при загрузке страницы
function initializeAnimations() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Инициализация подсказок
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Инициализация drag and drop
function initializeDragAndDrop() {
    const draggableElements = document.querySelectorAll('[draggable="true"]');
    
    draggableElements.forEach(element => {
        element.addEventListener('dragstart', function(e) {
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', this.outerHTML);
        });
        
        element.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });
    });
    
    // Обработка drop зон
    const dropZones = document.querySelectorAll('.drop-zone');
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        
        zone.addEventListener('dragleave', function() {
            this.classList.remove('drag-over');
        });
        
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const data = e.dataTransfer.getData('text/html');
            if (data) {
                this.innerHTML = data;
            }
        });
    });
}

// Инициализация игровых элементов
function initializeGameElements() {
    // Обработчики для игровых кнопок
    const gameButtons = document.querySelectorAll('.game-btn');
    gameButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.classList.add('clicked');
            setTimeout(() => {
                this.classList.remove('clicked');
            }, 200);
        });
    });
    
    // Обработчики для игровых полей
    const gameFields = document.querySelectorAll('.game-field');
    gameFields.forEach(field => {
        field.addEventListener('click', function(e) {
            if (e.target.classList.contains('game-cell')) {
                selectGameCell(e.target);
            }
        });
    });
}

// Выбор игровой ячейки
function selectGameCell(cell) {
    // Убираем выделение с предыдущих ячеек
    document.querySelectorAll('.game-cell.selected').forEach(c => {
        c.classList.remove('selected');
    });
    
    // Выделяем новую ячейку
    cell.classList.add('selected');
}

// Утилиты для игр
const GameUtils = {
    // Генерация случайного числа в диапазоне
    randomInt: function(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    
    // Проверка валидности решения
    validateSolution: function(solution, rules) {
        // Базовая проверка валидности
        return solution && solution.length > 0;
    },
    
    // Анимация победы
    showWinAnimation: function(element) {
        element.classList.add('win-animation');
        setTimeout(() => {
            element.classList.remove('win-animation');
        }, 2000);
    },
    
    // Звуковые эффекты (если нужно)
    playSound: function(soundType) {
        // Здесь можно добавить звуковые эффекты
        console.log(`Playing sound: ${soundType}`);
    }
};

// Обработчики для форм
function initializeForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="loading"></span> Отправка...';
            }
        });
    });
}

// Обработчики для модальных окон
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.getAttribute('data-bs-target');
            const modal = document.querySelector(modalId);
            if (modal) {
                modal.classList.add('show');
            }
        });
    });
}

// Утилиты для работы с API
const API = {
    // Отправка данных на сервер
    submitData: function(url, data, callback) {
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(callback)
        .catch(error => {
            console.error('API Error:', error);
            showNotification('Ошибка при отправке данных', 'error');
        });
    },
    
    // Получение данных с сервера
    fetchData: function(url, callback) {
        fetch(url)
        .then(response => response.json())
        .then(callback)
        .catch(error => {
            console.error('API Error:', error);
            showNotification('Ошибка при загрузке данных', 'error');
        });
    }
};

// Получение CSRF токена
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Показ уведомлений
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(notification, container.firstChild);
        
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Обработчики для игровых элементов
const GameHandlers = {
    // Обработчик для кнопок управления игрой
    handleGameControl: function(button, action) {
        button.addEventListener('click', function() {
            this.classList.add('active');
            setTimeout(() => {
                this.classList.remove('active');
            }, 200);
            
            // Выполняем действие
            if (typeof action === 'function') {
                action();
            }
        });
    },
    
    // Обработчик для игровых ячеек
    handleGameCell: function(cell, action) {
        cell.addEventListener('click', function() {
            this.classList.add('selected');
            setTimeout(() => {
                this.classList.remove('selected');
            }, 300);
            
            if (typeof action === 'function') {
                action(this);
            }
        });
    }
};

// Инициализация всех обработчиков
initializeForms();
initializeModals();

// Экспорт утилит для использования в других скриптах
window.GameUtils = GameUtils;
window.API = API;
window.GameHandlers = GameHandlers;


# Сборка (из корня проекта)
docker-compose build

# Запуск в фоне
docker-compose up -d

# Проверка статуса
docker-compose ps

# Логи backend (GigaChat, ошибки)
docker-compose logs -f backend

# Логи frontend
docker-compose logs -f frontend

# Остановка
docker-compose down

# Перезапуск с пересборкой
docker-compose up -d --build

# Вход в контейнер backend (например для проверки .env или DB)
docker-compose exec backend bash

# URL в браузере
# Backend API: http://localhost:8000/docs
# Frontend: http://localhost:5173

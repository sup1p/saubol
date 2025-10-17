# LiveKit Real-time Transcription Service

Сервис для управления агентами транскрибации LiveKit с использованием OpenAI Whisper через FastAPI endpoints.

## Особенности

- ✅ **LiveKit Agents Framework**: Использует официальный framework для агентов LiveKit
- ✅ **OpenAI Whisper Integration**: Интеграция с OpenAI STT plugin 
- ✅ **FastAPI Management**: REST API для управления агентами транскрибации
- ✅ **Room-specific Agents**: Каждый агент работает с конкретной комнатой
- ✅ **Real-time Processing**: Транскрибация в реальном времени

## Архитектура

### Как это работает:

1. **FastAPI Endpoint** (`/api/start-transcription`) вызывается с `room_name`
2. **TranscriptionAgentManager** запускает нового LiveKit Agent для этой комнаты  
3. **LiveKit Agent** подключается к комнате и ожидает участников
4. При появлении участников агент **автоматически подписывается** на их аудио-треки
5. **OpenAI STT Plugin** обрабатывает аудио с помощью Whisper
6. Результаты транскрибации **отправляются обратно** в комнату в реальном времени

### Компоненты:

- `TranscriptionAgentManager` - Управляет жизненным циклом агентов
- `TranscriptionAgent` - Основной класс агента для транскрибации  
- `room_specific_entrypoint` - Точка входа для конкретной комнаты
- FastAPI роутеры - REST API для управления

## Установка

### 1. Установка зависимостей

```bash
uv add livekit-agents[openai]~=1.2
uv add fastapi uvicorn pydantic-settings python-dotenv
```

### 2. Настройка окружения

Создайте файл `.env`:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here
```

## Использование

### 1. Запуск FastAPI сервера

```bash
uvicorn src.main:app --reload
```

### 2. API Endpoints

#### Запуск транскрибации

```bash
POST /api/start-transcription
```

**Параметры:**
- `room_name` (str) - Имя LiveKit комнаты

**Пример:**
```bash
curl -X POST "http://localhost:8000/api/start-transcription?room_name=my-room"
```

#### Остановка транскрибации

```bash
POST /api/stop-transcription  
```

**Параметры:**
- `room_name` (str) - Имя LiveKit комнаты

**Пример:**
```bash
curl -X POST "http://localhost:8000/api/stop-transcription?room_name=my-room"
```

#### Список активных агентов

```bash
GET /api/active-transcriptions
```

**Пример:**
```bash
curl "http://localhost:8000/api/active-transcriptions"
```

### 3. Поток работы

1. **Вызовите API** для запуска транскрибации:
   ```bash
   curl -X POST "http://localhost:8000/api/start-transcription?room_name=meeting-room-1"
   ```

2. **Агент подключится** к комнате `meeting-room-1`

3. **Участники заходят** в комнату через LiveKit клиент

4. **Агент автоматически** начинает транскрибировать их речь

5. **Результаты транскрибации** отправляются в комнату как data messages

6. **Остановите агента** когда нужно:
   ```bash
   curl -X POST "http://localhost:8000/api/stop-transcription?room_name=meeting-room-1" 
   ```

## Технические детали

### LiveKit Agents Framework

Код использует официальный LiveKit Agents framework с правильными паттернами:

- `JobContext` для контекста агента
- `openai.STT()` плагин для Whisper 
- `stt.stream()` для стриминговой транскрибации
- Автоматическая подписка на аудио треки
- Обработка событий транскрибации

### Обработка аудио

1. **Автоматическая подписка**: Агент подписывается на все аудио треки участников
2. **Стриминг**: `AudioStream` передает аудио данные в `STT` плагин
3. **Whisper обработка**: OpenAI обрабатывает аудио через Whisper API
4. **События**: Результаты приходят как `TranscriptionEvent` объекты
5. **Отправка**: Финальные результаты отправляются в комнату

### Преимущества нового подхода

По сравнению со старым кодом:
- ❌ **Убрали ручную буферизацию** аудио 
- ❌ **Убрали numpy обработку** и resampling
- ❌ **Убрали создание WAV файлов**
- ✅ **Используем готовый STT плагин**
- ✅ **Автоматическое управление аудио потоками** 
- ✅ **Стандартные LiveKit паттерны**

## Логирование

Агенты логируют свою активность:

```python
logger = logging.getLogger("transcription-agent")
```

Сообщения включают:
- Запуск/остановку агентов
- Подключение к комнатам
- Обработку участников  
- Результаты транскрибации
- Ошибки

## Структура проекта

```
src/
├── services/
│   └── transcription.py      # Агенты и менеджер
├── routers/  
│   └── transcription.py      # FastAPI endpoints
├── core/
│   └── settings.py          # Конфигурация
└── schemas/
    └── livekit.py          # Pydantic модели
```

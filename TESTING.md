# Инструкция по тестированию транскрибации

## 1. Запуск FastAPI сервера

```bash
uvicorn src.main:app --reload
```

## 2. Запуск агента транскрибации

Откройте новый терминал и выполните:

```bash
curl -X POST "http://localhost:8000/api/start-transcription?room_name=omar"
```

Вы должны увидеть ответ:
```json
{"message":"Transcription agent started successfully","room_name":"omar"}
```

## 3. Проверка активных агентов

```bash
curl "http://localhost:8000/api/active-transcriptions"
```

## 4. Подключение к комнате для тестирования

Есть несколько способов:

### Способ 1: LiveKit Playground
1. Перейдите на https://playground.livekit.io/
2. Введите данные вашего LiveKit сервера
3. Подключитесь к комнате с именем "omar"
4. Включите микрофон и говорите

### Способ 2: Тестовый клиент (если у вас настроен LiveKit)

```bash
python test_client.py
```

## 5. Проверка логов

В терминале с FastAPI сервером вы должны увидеть логи:

```
INFO:transcription-agent:Agent connected to room: omar
INFO:transcription-agent:Transcription agent is ready and waiting for participants...
INFO:transcription-agent:New participant connected: [participant_name]
INFO:transcription-agent:Track published by [participant_name]: audio
INFO:transcription-agent:Subscribed to audio track from [participant_name]
INFO:transcription-agent:Subscribed to audio track from [participant_name]
INFO:transcription-agent:Starting transcription for track from participant: [participant_name]
INFO:transcription-agent:Transcription: [транскрибированный текст]
```

## 6. Остановка агента

```bash
curl -X POST "http://localhost:8000/api/stop-transcription?room_name=omar"
```

## Возможные проблемы:

1. **"No audio track found"** - участник не публикует аудио или агент не может подписаться
2. **Агент подключается но не транскрибирует** - проблемы с OpenAI API ключом или аудио данными
3. **Ошибка подключения** - неправильные LiveKit credentials

## Отладка:

Проверьте переменные окружения в `.env`:
```
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here
OPENAI_API_KEY=your_openai_api_key_here
```
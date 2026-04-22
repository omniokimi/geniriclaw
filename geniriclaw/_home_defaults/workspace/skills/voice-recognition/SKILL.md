# voice-recognition — транскрипция голосовых сообщений

> **Status:** stable
> **Category:** input-processing · audio
> **Depends on:** Soniox API (опц. fallback: Whisper, OpenAI API)

## Purpose

Автоматическое преобразование голосовых сообщений (voice notes из Telegram / аудиофайлов) в текст — чтобы LLM-агент мог их обрабатывать как обычный текст.

## Prerequisites

| Что | Где | Env var |
|-----|-----|---------|
| Soniox API key | [soniox.com/settings/api-keys](https://soniox.com/settings/api-keys) | `SONIOX_API_KEY` |
| (опц.) OpenAI API (fallback) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `OPENAI_API_KEY` |
| (опц.) whisper.cpp | установить локально | `whisper-cli` в PATH |

## Pipeline (автоматический в boт)

Когда Telegram voice message приходит боту:

```
1. Telegram скачивает voice → ~/.geniriclaw/workspace/telegram_files/<file_id>.ogg
2. Воркспейс-агент детектит voice → вызывает voice-recognition skill
3. Скилл: ogg → WAV (через ffmpeg) → Soniox API → text
4. Text вставляется в input как обычное сообщение пользователя
5. Агент отвечает
```

В `config.json` бота обычно настроен `audio.transcription`:

```json
{
  "audio": {
    "transcription": {
      "provider": "soniox",
      "command": "python3 /path/to/transcribe_soniox.py {{MediaPath}}"
    }
  }
}
```

Обрати внимание: шаблон должен быть `{{MediaPath}}` (двойные фигурные), не `{input}`.

## Провайдер — Soniox async STT

Для русского — работает отлично, поддержка длинных файлов (асинхронный режим).

### Шаги запроса

1. **Upload file** → получить `file_id`
   ```
   POST https://api.soniox.com/v1/files (multipart/form-data)
   Headers: Authorization: Bearer {{SONIOX_API_KEY}}
   ```

2. **Create transcription** → получить `transcription_id`
   ```json
   POST https://api.soniox.com/v1/transcriptions
   {
     "model": "stt-async-preview",
     "file_id": "<from step 1>",
     "language_hints": ["ru", "en"]
   }
   ```

3. **Poll** каждые 3 сек
   ```
   GET https://api.soniox.com/v1/transcriptions/<id>
   ```
   Status: `queued` → `running` → `completed` | `failed`.

4. **Get text** при `completed`
   ```
   GET https://api.soniox.com/v1/transcriptions/<id>/transcript
   ```
   Response содержит `text` — финальная строка.

### Ручная транскрипция (для отладки)

```bash
python3 -c "
import os, sys, time, json, urllib.request
API = 'https://api.soniox.com/v1'
KEY = os.environ['SONIOX_API_KEY']
file_path = sys.argv[1]

# 1. upload
with open(file_path, 'rb') as f:
    boundary = '----'
    body = f'--{boundary}\\r\\nContent-Disposition: form-data; name=\"file\"; filename=\"a.ogg\"\\r\\nContent-Type: audio/ogg\\r\\n\\r\\n'.encode() + f.read() + f'\\r\\n--{boundary}--\\r\\n'.encode()
    req = urllib.request.Request(f'{API}/files', data=body,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    file_id = json.loads(urllib.request.urlopen(req).read())['id']

# 2. create
req = urllib.request.Request(f'{API}/transcriptions',
    data=json.dumps({'model': 'stt-async-preview', 'file_id': file_id, 'language_hints': ['ru','en']}).encode(),
    headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'})
tr_id = json.loads(urllib.request.urlopen(req).read())['id']

# 3. poll
for _ in range(60):
    time.sleep(3)
    req = urllib.request.Request(f'{API}/transcriptions/{tr_id}',
        headers={'Authorization': f'Bearer {KEY}'})
    st = json.loads(urllib.request.urlopen(req).read())
    if st['status'] == 'completed':
        req = urllib.request.Request(f'{API}/transcriptions/{tr_id}/transcript',
            headers={'Authorization': f'Bearer {KEY}'})
        print(json.loads(urllib.request.urlopen(req).read())['text'])
        break
    if st['status'] in ('failed','error'):
        sys.exit(f'failed: {st}')
" audio.ogg
```

## Fallback цепочка

Если Soniox недоступен/превышен лимит:

1. **OpenAI Whisper API** (`whisper-1` endpoint) — `POST https://api.openai.com/v1/audio/transcriptions` (multipart, `model=whisper-1`, `file=@audio.ogg`)
2. **Локальный whisper.cpp** (оффлайн, если установлен) — `whisper-cli audio.ogg --language ru --output-txt`
3. Сообщение оператору: «голосовое получено, распознать не удалось, дайте текст»

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{SONIOX_API_KEY}}` | env |
| `{{OPENAI_API_KEY}}` | env (fallback) |
| `{{LANGUAGE_HINTS}}` | `["ru","en"]` по ситуации |
| `{{MEDIA_PATH}}` | абсолютный путь к voice-файлу |

## Ключевые файлы

- `telegram_files/<file_id>.ogg` — исходники от Telegram
- `interviews/<slug>/<date>/voice-sample-NN.transcript.md` — курированная транскрипция (с timestamps, если нужно)
- `interviews/<slug>/<date>/voice-sample-NN.transcript.txt` — raw text

## Rules

- Голосовые старше **7 дней** в Telegram истекают — скачивать сразу при приёме.
- Для долгих (> 5 мин) — асинхронный режим Soniox (не streaming).
- Для короткой realtime-транскрипции (< 30 с) — OpenAI Whisper streaming быстрее.
- Сохранять **и raw text**, **и curated summary** — первый для точности, второй для LLM-обработки.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| Transcription stuck on `queued` | Soniox queue full, подождать 30+ сек; попробовать fallback |
| Плохое качество распознавания | Проверить `language_hints`; для шумных записей — сначала denoise через `ffmpeg -af highpass=200,lowpass=3000` |
| Telegram voice → ogg OPUS не принимается | Конвертировать в WAV: `ffmpeg -i voice.ogg -ar 16000 -ac 1 voice.wav` |
| 401 Unauthorized | Проверить `$SONIOX_API_KEY`, срок действия ключа |

## References

- [Soniox docs](https://soniox.com/docs)
- [OpenAI Whisper API](https://platform.openai.com/docs/api-reference/audio)
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp)

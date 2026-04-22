# channel-publisher — автопостинг в мессенджер-канал

> **Status:** stable
> **Category:** publish · automation
> **Depends on:** Telegram Bot API (или др. мессенджер), cron

## Purpose

Регулярная публикация контента (тексты, фото, видео) в канал по расписанию. Типовой сценарий: 3–5 постов в день в Telegram-канал с разным характером (утренний thoughtful post, дневной research, вечерний digest, ночной reflection).

## When to use

- Нужно автоматизировать публикации в канал без ручного ведения.
- Есть контент-план или набор рубрик / тем.
- Есть способ генерации контента (text + image) — через `nano-banana-openrouter`, `video-pipeline`, LLM-агента.

## Prerequisites

| Что | Как получить |
|-----|--------------|
| Канал (Telegram / Matrix / VK) | Создать в клиенте |
| Бот-админ канала | BotFather → создать бота → добавить в канал как admin с правом Post Messages |
| Bot token | от BotFather |
| Chat ID канала | `curl https://api.telegram.org/bot<TOKEN>/getUpdates` после любого действия в канале, либо через `@getmyid_bot` |

Добавить в config / env:
```
CHANNEL_BOT_TOKEN={{CHANNEL_BOT_TOKEN}}
CHANNEL_ID={{CHANNEL_CHAT_ID}}   # формат -100XXXXXXXXXX для supergroup/channel
```

## Типовой дневной цикл (пример — 5 постов)

```
09:00  morning reflection    — тон: созерцательный, короткий (100–200 символов)
11:00  research digest       — тон: аналитический, средний (300–500 символов), ссылка
14:00  visual post           — картинка + короткая подпись (50–100 символов)
17:00  evening thought       — тон: уютный, средний
21:00  night summary         — тон: спокойный, короткий
```

## Публикация поста

### Telegram Bot API — sendMessage

```bash
curl -s "https://api.telegram.org/bot${CHANNEL_BOT_TOKEN}/sendMessage" \
  -d chat_id="${CHANNEL_ID}" \
  -d text="<text>" \
  -d parse_mode=MarkdownV2
```

### С фото

```bash
curl -s -F "chat_id=${CHANNEL_ID}" \
        -F "photo=@/absolute/path/to/image.png" \
        -F "caption=<caption>" \
        -F "parse_mode=MarkdownV2" \
     "https://api.telegram.org/bot${CHANNEL_BOT_TOKEN}/sendPhoto"
```

### С видео

```bash
curl -s -F "chat_id=${CHANNEL_ID}" \
        -F "video=@/absolute/path/to/video.mp4" \
        -F "caption=<caption>" \
        -F "supports_streaming=true" \
     "https://api.telegram.org/bot${CHANNEL_BOT_TOKEN}/sendVideo"
```

## Mood state — непрерывный тон

Для поддержания единого голоса канала — ежедневная генерация `mood.yaml`:

```yaml
# workspace/projects/<channel>/mood/{{YYYY-MM-DD}}.yaml
date: 2026-04-22
mood: "contemplative, quiet morning, light rain"
theme_of_day: "rhythm vs. noise"
tone_hints:
  - short sentences
  - concrete images, no abstractions
  - avoid exclamation marks
  - no emojis before 14:00
```

Каждый cron-job читает этот файл → подмешивает в prompt генерации.

## Cron schedule — пример

```
# workspace/cron_jobs.json
[
  {"name": "morning-post",  "schedule": "0 9 * * *",  "command": "publish.sh morning_reflection"},
  {"name": "research-post", "schedule": "0 11 * * *", "command": "publish.sh research_digest"},
  {"name": "visual-post",   "schedule": "0 14 * * *", "command": "publish.sh visual_post"},
  {"name": "evening-post",  "schedule": "0 17 * * *", "command": "publish.sh evening_thought"},
  {"name": "night-post",    "schedule": "0 21 * * *", "command": "publish.sh night_summary"}
]
```

## Шаг 1 — Проверка лога перед каждым постом

Не публиковать если за последние 2 часа уже был пост этого же типа (защита от дублей после перезапуска):

```python
# в publish.sh / publish.py
log = read_json("workspace/projects/<channel>/posts_log.json")
last = [p for p in log if p["type"] == post_type][-1:]
if last and now - last[0]["at"] < timedelta(hours=2):
    sys.exit("already posted this type in last 2h, skip")
```

## Шаг 2 — Research (для некоторых рубрик)

Для `research_digest` и `evening_thought` — сначала собрать материал через WebSearch / RSS / запрос к LLM:

```python
research_prompt = f"""
Find 3 interesting angles on topic: {theme_of_day}.
Format: each angle as 2-sentence summary + 1 source link.
"""
# run via claude/gpt/gemini subprocess
```

Результат кэшировать в `workspace/projects/<channel>/research/{YYYY-MM-DD}-<topic>.md`.

## Шаг 3 — Выбор рубрики

Рубрики определяются по `post_type` + текущему `mood.yaml`. Формат каждой рубрики описан в `workspace/projects/<channel>/rubrics/<name>.md`:

```markdown
# Rubric: morning_reflection
Length: 100–200 chars
Tone: contemplative, 1st person, no advice
Structure: 1–2 sentences, poetic but grounded
Must NOT: exclamation marks, emojis, "you should", motivational
Example style:
> The morning is always a new negotiation with the light.
```

## Шаг 4 — Генерация поста

```python
prompt = read(rubric_file) + read(mood_file)
text = llm_generate(prompt, max_chars=200)
image = maybe_generate_image_via_openrouter(text) if rubric.has_image else None
```

## Шаг 5 — Публикация + логирование

```python
resp = tg_send(text, image)
log.append({
    "at": now.isoformat(),
    "type": post_type,
    "message_id": resp["result"]["message_id"],
    "chat_id": CHANNEL_ID,
    "text_preview": text[:80],
})
write_json("workspace/projects/<channel>/posts_log.json", log)
```

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{CHANNEL_BOT_TOKEN}}` | `.env` / `config.json` |
| `{{CHANNEL_CHAT_ID}}` | `.env` / cron-команда |
| `{{CHANNEL_NAME}}` | Slug для папки `workspace/projects/<channel>/` |

## Rules

- **Никогда не постить дубль** в течение 2 часов того же типа.
- **Не писать сразу пачку 5 постов** при catch-up (после выключения) — постить только текущий, остальные пропустить.
- **Mood переключается постепенно** — не менять тон резко между постами одного дня.
- **Модерация контента** перед публикацией: автоматический check на стоп-слова / политический / NSFW (через regex или LLM-gate) + логирование отклонённых.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| Telegram: 400 "chat not found" | Проверить `chat_id` (должен начинаться с `-100`), бот добавлен в канал как admin |
| Telegram: 400 "message is too long" | Text > 4096 символов — разбить или обрезать |
| Дубли постов | Не было `posts_log.json` check; включить логику шага 1 |
| Картинка публикуется как файл, не превью | Отправлять через `sendPhoto`, не `sendDocument`; размер < 10 MB |
| Пост публикуется с опечатками markdown | MarkdownV2 требует экранирования: `_ * [ ] ( ) ~ > # + - = | { } . !` — см. `tg-message-editor` |

## References

- Related: `tg-message-editor` (форматирование), `publisher-site` (параллельно дублирование на сайт), `learning-loop` (анализ метрик постов)
- [Telegram Bot API — sendMessage](https://core.telegram.org/bots/api#sendmessage)

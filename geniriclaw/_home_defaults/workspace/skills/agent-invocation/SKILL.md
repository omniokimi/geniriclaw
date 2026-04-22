# agent-invocation — как вызывать L2-суб-агентов и фоновые задачи

> **Status:** stable
> **Category:** meta · orchestration

## Purpose

Убрать частое недоразумение: «мне не разрешён pairing / agent system недоступна». L2-агенты (scriptwriter, image-gen, video-gen, editor и т.д.) — это **инструкции-роли**, которые агент (ты) играет в рамках собственного LLM-цикла, плюс стандартные Bash/Python-инструменты. Никакой специальный «agent pairing» не нужен.

## Важное уточнение

Есть две разные вещи:

1. **Рабочий L2-агент** (scriptwriter, image-gen, storyboarder, ...) — это просто папка `workspace/agents/<name>/` с `AGENT.md` (инструкция как выполнять роль). Для вызова — прочитай `AGENT.md`, следуй инструкциям внутри своего LLM-цикла. Ничего запускать отдельно не нужно.

2. **Sub-agent на уровне фреймворка** — отдельный процесс `geniriclaw` с собственным Telegram-ботом и workspace. Нужен только для архитектурной изоляции (разные клиенты, разные Claude-подписки). Для content-production задач обычно **не нужен**.

Если приходит ошибка «локальный контур для субагентов не спарен» / «pairing required» — это про #2 (system-level sub-agents фреймворка), **не** про #1 (твои L2-роли). Твой pipeline не заблокирован — продолжай через собственные tools.

## Как на практике вызывать L2-агентов

### Тип A — Inline LLM-prompt (роли для творческой работы)

Примеры: `scriptwriter`, `storyboarder`, `prompt-engineer`.

**Не нужно запускать subprocess.** Просто:
1. Прочитай `workspace/agents/<name>/AGENT.md`
2. Применяй инструкции внутри своего текущего LLM-контекста
3. Производи output в нужном формате (текст, JSON, YAML)

```
# ❌ Неправильно:
subprocess.run(["python3", "tools/agent_tools/ask_agent.py", "scriptwriter", brief])

# ✅ Правильно:
role = read("agents/scriptwriter/AGENT.md")
# следуй role как part of current session
# output в expected формате (например, saved to drafts/<job>/script.md)
```

### Тип B — Bash/Python скрипты (генеративные инструменты)

Примеры: `image-gen`, `video-gen`, `voice-over`, `music-scoring`, `editor`, `publisher-multi`, `metrics-tracker`.

Для этих — **реальные скрипты** в `scripts/` или в `agents/<name>/`:

```bash
# image-gen через OpenRouter (Gemini Image / Nano Banana)
python3 workspace/scripts/gen_image_via_openrouter.py \
    --prompt "..." --ref-url "..." --output drafts/<job>/shots/shot_01.png

# editor — ffmpeg concat
bash workspace/scripts/editor_concat.sh \
    drafts/<job>/videos/*.mp4 > drafts/<job>/build/final.mp4

# publisher-multi — на 3 платформы параллельно
python3 workspace/scripts/publish_multi.py \
    --file drafts/<job>/build/final.mp4 \
    --platforms telegram,instagram,tiktok
```

### Тип C — Внешние провайдеры с собственным SDK

Примеры: `avatar-talking-head` (HeyGen), `voice-clone` (ElevenLabs).

Это обёртки вокруг API провайдера:

```python
# avatar-talking-head через HeyGen
import os, urllib.request, json
body = {
    "video_inputs": [{
        "character": {"type": "avatar", "avatar_id": "{{HEYGEN_AVATAR_ID}}"},
        "voice": {"type": "text", "input_text": "...", "voice_id": "{{HEYGEN_VOICE_ID}}"}
    }],
    "dimension": {"width": 1080, "height": 1920}
}
# POST к https://api.heygen.com/v2/video/generate с X-API-KEY
```

### Тип D — FFmpeg склейка (editor)

Editor — это не AI, это серия ffmpeg-команд. Конкретные шаблоны — в `agents/editor/AGENT.md` и `templates/ffmpeg/`.

### Тип E — Публикация (publisher-multi)

Параллельно: Telegram Bot API + Meta Graph (IG/FB) + TikTok API + VK API + (опц.) Ayrshare как унифицированный gateway.

## Когда нужен real sub-agent (Тип 2)

Редко. Случаи:
- **Клиент A и клиент B** на одной VM — разные Telegram-боты, разные workspace, разные Claude-подписки. Sub-agent изоляция.
- **Эксперимент «автономный L3-агент»** — отдельный процесс который мониторит что-то 24/7, со своим state.

Создание:
```bash
geniriclaw agents add <name>
# Creates: ~/.geniriclaw/agents/<name>/{workspace,config}
# Scaffolds Telegram bot, prompts for token
```

Это поднимет **отдельный процесс** `geniriclaw` с отдельным ботом. Главный агент + sub-agent общаются через `ask_agent.py` (InterAgent Bus).

## Background tasks (долгие задачи)

Для задач > 30 сек (рендер видео, батч-генерация) — **фоновая задача**:

```
# В диалоге с главным агентом:
"делегируй: regen_zakalivanie_v7.py — 6 shots, кусок на 15–25 мин, результат в published.json"

# Агент создаст background task:
# - workspace/tasks/<task_id>/TASKMEMORY.md — описание задачи
# - запустит subprocess в фоне с отдельной Claude-сессией
# - после завершения — результат вернётся в главный чат
```

См. встроенную команду `/tasks` в Telegram для просмотра активных.

## Rules

- **L2 роли не нужен pairing** — это внутренние инструкции, не отдельные процессы.
- **Вызывать L2 без ожидания** — в том же ответе запустил → показал evidence → идёшь дальше (см. `plan-to-action-bridge`).
- **Sub-agent** (Тип 2) только когда нужна архитектурная изоляция — для 99% задач не нужен.
- **Background tasks** для длинных операций — не держать главную session занятой 20 минут.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| «pairing required» ошибка | Ты про system-level sub-agent, а нужен L2 роль — читаешь `agents/<name>/AGENT.md` и делаешь inline. |
| Agent tools недоступны | Для L2 ролей tools не нужны — это inline prompt. Для scripts — стандартные Bash/Python работают. |
| Background task «застрял» | `/tasks` → check status → `/tasks kill <id>` при необходимости |
| Sub-agent не отвечает | Проверить что его процесс запущен: `pgrep -fa geniriclaw` + логи в `~/.geniriclaw/agents/<name>/logs/` |

## References

- `workspace/agents/*/AGENT.md` — инструкции L2-ролей
- `plan-to-action-bridge`, `autonomous-action`, `video-pipeline`

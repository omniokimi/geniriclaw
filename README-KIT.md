# README-KIT.md — Enterprise Starter Kit для GeniriClaw

Этот kit разворачивается автоматически при первом запуске `geniriclaw` в `~/.geniriclaw/workspace/`. Содержит готовые building blocks для полного цикла content-production: от приёма брифа до публикации в соцсети + сбора метрик + обучения по результатам.

## Что внутри

### 14 Skills (workspace/skills/)

#### Content production — image & video

| Skill | Назначение |
|-------|-----------|
| [`nano-banana-openrouter`](geniriclaw/_home_defaults/workspace/skills/nano-banana-openrouter/SKILL.md) | Генерация изображений через OpenRouter (Gemini Image / Nano Banana + Nano Banana Pro) — img2img с face reference, multi-ref, text2img |
| [`kling-i2v-transition`](geniriclaw/_home_defaults/workspace/skills/kling-i2v-transition/SKILL.md) | Image→Video через Kling v2.1 (Replicate), включая start→end morph-переходы |
| [`video-pipeline`](geniriclaw/_home_defaults/workspace/skills/video-pipeline/SKILL.md) | End-to-end сборка ролика: script → storyboard → images → videos → voice → music → edit → publish |
| [`video-revision-pipeline`](geniriclaw/_home_defaults/workspace/skills/video-revision-pipeline/SKILL.md) | Итеративные правки уже смонтированного ролика со style-anchor'ом |
| [`directors-cut-pipeline`](geniriclaw/_home_defaults/workspace/skills/directors-cut-pipeline/SKILL.md) | Режиссёрская склейка с операторскими переходами |
| [`storyboard-designer`](geniriclaw/_home_defaults/workspace/skills/storyboard-designer/SKILL.md) | Двухэтапная раскадровка: sketch (B&W, 1K, дёшево) → final (2K, pro) |

#### Publishing

| Skill | Назначение |
|-------|-----------|
| [`channel-publisher`](geniriclaw/_home_defaults/workspace/skills/channel-publisher/SKILL.md) | Регулярные публикации в мессенджер-канал по расписанию (cron) |
| [`publisher-site`](geniriclaw/_home_defaults/workspace/skills/publisher-site/SKILL.md) | Публикация HTML/медиа на собственный домен (nginx + SSL) |
| [`tg-message-editor`](geniriclaw/_home_defaults/workspace/skills/tg-message-editor/SKILL.md) | Редактирование / удаление Telegram-сообщений |

#### Input processing

| Skill | Назначение |
|-------|-----------|
| [`voice-recognition`](geniriclaw/_home_defaults/workspace/skills/voice-recognition/SKILL.md) | Транскрипция voice notes через Soniox (русский) / Whisper |

#### Meta / execution discipline

| Skill | Назначение |
|-------|-----------|
| [`plan-to-action-bridge`](geniriclaw/_home_defaults/workspace/skills/plan-to-action-bridge/SKILL.md) | Не застревать на плане — всегда NEXT_EXECUTABLE_STEP с доказательством старта работы |
| [`autonomous-action`](geniriclaw/_home_defaults/workspace/skills/autonomous-action/SKILL.md) | Делать, не спрашивать. Промежуточный ОК — только для необратимых внешних действий |
| [`agent-invocation`](geniriclaw/_home_defaults/workspace/skills/agent-invocation/SKILL.md) | Как вызывать L2-суб-агентов и background tasks |
| [`learning-loop`](geniriclaw/_home_defaults/workspace/skills/learning-loop/SKILL.md) | Превращать правки клиента в обновлённые prompt-packs |

### 12 L2 Agents (workspace/agents/)

Каждый — папка с `AGENT.md` (инструкция как агент играет роль) и потенциально набором шаблонов. Группируются по типу:

**Pre-production (inline LLM prompts):**
- `scriptwriter` — сценарий по брифу
- `storyboarder` — структурированная раскадровка
- `prompt-engineer` — адаптация prompts под провайдеров

**Generation (subprocess scripts):**
- `image-gen` — через OpenRouter (Gemini Image / Nano Banana)
- `video-gen` — через Kling
- `voice-over` — через ElevenLabs / OpenAI TTS
- `music-scoring` — через Suno / library
- `avatar-talking-head` — через HeyGen
- `editor` — FFmpeg concat + mix

**Publishing & feedback:**
- `publisher-multi` — параллельная публикация в TG/IG/TikTok/VK
- `metrics-tracker` — сбор метрик +24h после публикации
- `media-scout` — ежедневный сбор тем / трендов

### Orchestrator

- [`pipeline.yaml`](geniriclaw/_home_defaults/workspace/orchestrator/pipeline.yaml) — декларативные stages + checkpoints + fallback policy
- [`AGENT.md`](geniriclaw/_home_defaults/workspace/orchestrator/AGENT.md) — как играть роль orchestrator'а
- [`checkpoints.md`](geniriclaw/_home_defaults/workspace/orchestrator/checkpoints.md) — формат сообщений оператору на checkpoint'ах

### References

- [`references/providers/README.md`](geniriclaw/_home_defaults/workspace/references/providers/README.md) — полный справочник внешних API (image, video, voice, music, STT, LLM, publishing) с ценами и env-переменными

### Templates

- [`templates/publish/publish.sh`](geniriclaw/_home_defaults/workspace/templates/publish/publish.sh) — утилита публикации на собственный сайт
- [`templates/storyboard/storyboard.schema.json`](geniriclaw/_home_defaults/workspace/templates/storyboard/storyboard.schema.json) — JSON Schema для storyboard.json

## Ключевые принципы kit'а

1. **Enterprise-grade документация** — каждый скилл с Purpose, When, Prerequisites, Usage, Config placeholders, Rules, Troubleshooting, References.
2. **Все секреты через env** — никакие токены не захардкожены. Используются `{{PLACEHOLDER}}` в скриптах, оператор заполняет env при развёртывании.
3. **Fallback-first** — каждая stage pipeline имеет 2–3 уровня fallback. «Ошибка на одном shot'е не должна блокировать весь ролик».
4. **Autopilot by default** — control checkpoints только в критичных точках (script approval, final publish). Остальное идёт без confirm.
5. **Motion через provider, не ffmpeg** — правило I2V оператора: движение камеры через prompt модели. Editor (ffmpeg) только concat/trim/audio.
6. **Learning-loop** — каждая итерация улучшает prompts: правка клиента → обновлённый promptpack.yaml → следующий batch без той же ошибки.

## Типовой use-case

Оператор в Telegram: *«Сделай короткий ролик 45 секунд про утреннюю рутину для IG Reels, формат 9:16»*.

Что происходит:

```
1. [autopilot]  parse_brief          (1с)
2. [autopilot]  scriptwriter         (~30с)   → script.md
3. [control]    ✋ Показать script оператору, дождаться go
4. [autopilot]  storyboarder         (~20с)   → storyboard.json (10 shots × 4.5с)
5. [autopilot]  prompt-engineer      (~10с)   → provider-payload per shot
6. [autopilot]  image-gen × 10       (~3 мин в 4 параллели) → sketches/
7. [control]    ✋ HTML preview sketches → оператор одобряет направление
8. [autopilot]  image-gen finals × 10 (~10 мин) → shots/
9. [autopilot]  video-gen × 10 (Kling) (~20 мин в 3 параллели) → videos/
10.[autopilot]  voice-over            (~1 мин) → voice.wav
11.[autopilot]  music-scoring         (~2 мин) → music.mp3
12.[autopilot]  editor (ffmpeg concat + mix) → final.mp4
13.[control]    ✋ final.mp4 → оператор подтверждает или правит
14.[autopilot]  publisher-multi (TG + IG + TikTok) → published.json
15.[scheduled]  +24h: metrics-tracker → metrics.json → learning-loop
```

**Общее время** от брифа до публикации: ~35–45 минут (в зависимости от длительности Kling-генерации).

## Что не входит в kit (добавляется отдельно)

- Специфичные для конкретного бренда **tone-of-voice** скиллы
- Персоналия конкретного агента (имя, характер, режим Companion)
- Собственные face REFs
- Специфичные cron-расписания под конкретный канал
- Интеграции с CRM / аналитикой / платежами

Эти вещи — **per-project** и должны писаться отдельно поверх kit'а.

## Как расширять kit

При создании нового скилла:

1. Создать папку `~/.geniriclaw/workspace/skills/<name>/`
2. Написать `SKILL.md` по шаблону других скилов (Purpose, When, Prerequisites, Usage, Config placeholders, Rules, Troubleshooting, References)
3. Опционально: добавить `template_*.py` / `template_*.sh` рядом
4. Перезапустить `geniriclaw restart` — skill_sync автоматически подхватит и слинкует в `~/.claude/skills/`

При создании нового L2-agent:

1. `~/.geniriclaw/workspace/agents/<name>/AGENT.md`
2. Опциональные `EXAMPLES.md`, `promptpack.yaml`
3. Если роль — subprocess-based, положить скрипт в `workspace/scripts/` или в `agents/<name>/`

## References

- [INSTALL.md](INSTALL.md) — как поставить GeniriClaw на новый сервер
- [docs/](docs/) — полная документация фреймворка
- [pyproject.toml](pyproject.toml) — метаданные пакета

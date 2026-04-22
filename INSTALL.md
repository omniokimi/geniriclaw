# INSTALL.md — установка и первый запуск GeniriClaw

**GeniriClaw** — Python-фреймворк для управления AI CLI (Claude Code / Codex / Gemini) через Telegram или Matrix. Включает enterprise starter kit: 14 готовых скилов, 12 L2-ролей, оркестратор pipeline, шаблоны публикации.

Эта инструкция — для оператора (тебя или твоего AI-агента), который будет разворачивать GeniriClaw на новом сервере.

## Что в этой папке

```
GeniriClaw_EVG/
├── INSTALL.md                ← этот файл
├── README-KIT.md             ← что входит в starter kit
├── README.md                 ← оригинальная документация фреймворка
├── pyproject.toml            ← метаданные пакета (name=geniriclaw, author=IgorFabrus)
├── LICENSE                   ← MIT © 2026 IgorFabrus
├── install.bat / run.bat / stop.bat  ← Windows-утилиты
├── docs/                     ← детальная документация фреймворка
│   ├── installation.md       ← универсальный гайд по установке (все платформы)
│   ├── config.md             ← полный конфиг-справочник
│   ├── architecture.md       ← как устроено внутри
│   ├── automation.md         ← cron, webhooks, heartbeat
│   ├── matrix-setup.md       ← Matrix transport
│   └── modules/              ← per-module deep dives
├── geniriclaw/               ← Python-пакет (движок фреймворка)
│   ├── _home_defaults/       ← ⭐ STARTER KIT (развернётся в ~/.geniriclaw при первом запуске)
│   │   └── workspace/
│   │       ├── skills/       ← 14 enterprise скилов
│   │       ├── agents/       ← 12 L2 ролей
│   │       ├── orchestrator/ ← pipeline.yaml + checkpoints
│   │       ├── references/   ← справочник провайдеров
│   │       └── templates/    ← шаблоны публикации / storyboard
│   ├── messenger/            ← Telegram / Matrix адаптеры
│   ├── cli/, orchestrator/, session/, ...  ← внутренности
└── tests/                    ← тестовый набор (для разработки)
```

## Системные требования

| Что | Минимум | Рекомендовано |
|-----|---------|---------------|
| ОС | Ubuntu 22.04+ / macOS 12+ / Windows 10+ | Ubuntu 24.04 LTS на VPS |
| Python | 3.11 | 3.12 |
| Node.js | 18+ (нужен для Claude Code CLI) | 22 |
| RAM | 2 GB | 4 GB |
| Disk | 5 GB | 20 GB (с запасом под media) |
| Постоянный IP | — | Yes (для publishing через webhooks) |

## Требуется хотя бы один CLI-провайдер

Один из:
- **Claude Code CLI** (рекомендуется) — `npm install -g @anthropic-ai/claude-code`
- **OpenAI Codex CLI** — `npm install -g @openai/codex`
- **Gemini CLI** — `npm install -g @google/gemini-cli`

## Требуется один messenger transport

Один из:
- **Telegram bot token** — создать через [@BotFather](https://t.me/BotFather)
- **Matrix account** — homeserver, user_id, access_token

## Установка — 3 способа

### A. На Linux VPS (рекомендовано для production)

```bash
# 1. Подготовить VPS
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git

# 2. Скопировать папку GeniriClaw_EVG на сервер
#    Варианты:
#    a) rsync с локальной машины:
#       rsync -av --exclude='.venv' --exclude='__pycache__' \
#             ./GeniriClaw_EVG/ user@server:/opt/geniriclaw/
#    b) scp + tar:
#       tar czf /tmp/gc.tgz GeniriClaw_EVG/
#       scp /tmp/gc.tgz user@server:/tmp/
#       ssh user@server 'cd /opt && tar xzf /tmp/gc.tgz && mv GeniriClaw_EVG geniriclaw'

# 3. На сервере — установить Python-пакет в editable-режиме
cd /opt/geniriclaw
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# 4. Сделать symlink в /usr/local/bin (чтобы geniriclaw работал в любой shell)
sudo ln -sf /opt/geniriclaw/.venv/bin/geniriclaw /usr/local/bin/geniriclaw

# 5. Установить Claude Code CLI
sudo npm install -g @anthropic-ai/claude-code

# 6. Авторизовать Claude
#    Вариант A — OAuth через браузер (интерактивно, на локальной машине):
#      claude setup-token   # даст sk-ant-oat01-... на 1 год
#      # положи этот token на сервер:
#      echo "CLAUDE_CODE_OAUTH_TOKEN=<paste>" | sudo tee -a /etc/environment
#    Вариант B — Anthropic API key:
#      echo "ANTHROPIC_API_KEY=sk-ant-api03-..." | sudo tee -a /etc/environment
#    Для root работы с --dangerously-skip-permissions также добавить:
#      echo "IS_SANDBOX=1" | sudo tee -a /etc/environment

# 7. Первый запуск — пройдёт onboarding wizard
geniriclaw
#    Введёт: выбор CLI (claude), transport (telegram), bot token, user_id, timezone
#    После завершения — бот начнёт работать.
```

### B. На macOS (для разработки или маленького домашнего сервера типа Mac Mini)

```bash
# 1. Установить системные зависимости
brew install python@3.12 node

# 2. Скопировать GeniriClaw_EVG в ~/geniriclaw (или любую другую папку)
cp -r /path/to/GeniriClaw_EVG ~/geniriclaw
cd ~/geniriclaw

# 3. Создать venv и установить
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# 4. Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 5. Авторизовать
claude setup-token
# экспортировать токен в shell:
echo 'export CLAUDE_CODE_OAUTH_TOKEN="sk-ant-oat01-..."' >> ~/.zshrc
source ~/.zshrc

# 6. Запустить
geniriclaw
```

### C. На Windows (для разработки)

Используй готовые `.bat` скрипты в корне:
```cmd
install.bat   :: создаст .venv и установит всё
run.bat       :: запустит geniriclaw (с UTF-8 workaround)
stop.bat      :: остановит
```

## Первый запуск — onboarding wizard

```
┌───────────── GENIRICLAW ─────────────┐
│  (ASCII-баннер)                     │
└──── geniriclaw.dev ────────────────┘

Disclaimer — прочитай перед продолжением.
GeniriClaw runs Claude/Codex/Gemini CLIs in full permission mode:
read, write, delete, execute — no confirmation.
Unintended actions can occur (data loss, file changes, commands).
Strongly recommended: run inside a Docker container.

[ ] I understand the risks / Понимаю риски, продолжить

→ Выбор CLI backend: [Claude] [Codex] [Gemini]
→ Transport: [Telegram] [Matrix]
→ Bot token: <paste>
→ Allowed user_id: <your Telegram user_id>
→ Timezone: <Europe/Moscow или auto>
→ Docker sandbox: [y/N]       ← опционально, рекомендуется для VPS
→ Install as background service: [y/N]   ← systemd на Linux, launchd на macOS

Готово! Бот запущен, слушает polling.
```

После первого запуска:
- Workspace развернётся в `~/.geniriclaw/`
- Starter kit (skills, agents, orchestrator, templates) автоматически сидится туда
- Config лежит в `~/.geniriclaw/config/config.json`

## Проверка что работает

1. В Telegram найди своего бота — напиши `/start` или любое сообщение
2. Бот должен ответить (через Claude)
3. В меню бота (`/`) должны быть команды: `/new`, `/stop`, `/interrupt`, `/model`, `/help`, `/diagnose`, `/restart`

## Как использовать starter kit

После первого запуска в `~/.geniriclaw/workspace/` будут:

- **`skills/`** — 14 enterprise скилов для content-production и meta-behavior. Claude Code CLI видит их автоматически через sync → при разговоре можно вызывать `/skill-name` или просто ссылаться по назначению.
- **`agents/`** — 12 L2-ролей (scriptwriter, image-gen, video-gen, editor, publisher-multi и т.д.). Используются внутри pipeline, агент играет роль читая `AGENT.md`.
- **`orchestrator/pipeline.yaml`** — декларативное описание видео-production pipeline. Orchestrator читает и запускает stages.
- **`references/providers/README.md`** — справочник API (GRSAI, Replicate/Kling, HeyGen, ElevenLabs, Soniox, Ayrshare). Ключи в env, см. ниже.
- **`templates/publish/publish.sh`** — универсальная утилита публикации на собственный сайт.
- **`templates/storyboard/storyboard.schema.json`** — schema для структурированной раскадровки.

### Настройка провайдеров (опционально)

Если планируешь генерировать изображения, видео, голос — добавь соответствующие ключи. Минимальный working-set:

```bash
# /etc/environment (Linux) или ~/.zshrc (macOS)
export GRSAI_API_KEY="<your-grsai-key>"          # image gen
export REPLICATE_API_TOKEN="<your-replicate>"    # video (Kling)
export ELEVENLABS_API_KEY="<your-eleven>"        # voice clone (опц.)
export SONIOX_API_KEY="<your-soniox>"            # voice recognition (опц.)
# ... остальные по мере необходимости (см. references/providers/README.md)
```

После добавления ключей — рестарт:
```bash
geniriclaw restart
```

### Публичный сайт (опционально, для публикации артефактов)

Если хочешь публиковать HTML-презентации / mp4 на свой домен:

1. Купить домен (любой registrar)
2. На VPS настроить nginx + SSL (см. `geniriclaw/_home_defaults/workspace/skills/publisher-site/SKILL.md`)
3. В env добавить:
   ```bash
   export PUBLIC_DOMAIN="your-domain.com"
   export PUBLIC_SITE_ROOT="/var/www/your-domain.com/"
   ```
4. `publish.sh` (в templates/publish/) начнёт работать

## Команды управления (на сервере)

```bash
geniriclaw              # запустить в foreground
geniriclaw stop         # остановить
geniriclaw restart      # перезапустить
geniriclaw status       # runtime status, провайдеры, session
geniriclaw upgrade      # проверить обновления пакета
geniriclaw reset        # полный сброс + повторная настройка
geniriclaw help         # все команды

geniriclaw service install   # установить как systemd/launchd/Task Scheduler сервис
geniriclaw service start     # запустить сервис
geniriclaw service stop
geniriclaw service logs --tail 50

geniriclaw docker enable     # Docker sandbox (рекомендуется для production)
geniriclaw docker rebuild
```

## Команды в Telegram

Когда бот работает:

| Команда | Что делает |
|---------|-----------|
| `/new` | Сброс активной сессии, чистый контекст |
| `/stop` | Прервать текущий ответ + очередь |
| `/interrupt` | Прервать текущий, очередь оставить |
| `/model` | Интерактивный выбор модели/провайдера |
| `/help` | Справка |
| `/diagnose` | Runtime diagnostics |
| `/restart` | Перезапуск бота |

## Troubleshooting

### Бот не отвечает
- Проверить `geniriclaw status`
- Лог: `tail -f ~/.geniriclaw/logs/agent.log`
- Telegram Bot Privacy Mode — см. `docs/installation.md` раздел Troubleshooting

### Claude CLI не залогинен
- `echo test | claude -p` — должен ответить
- Проверить env: `echo $CLAUDE_CODE_OAUTH_TOKEN` (или `$ANTHROPIC_API_KEY`)
- Если OAuth token истёк (год прошёл) — пересоздать через `claude setup-token` на локали

### Docker sandbox не стартует
- `docker ps` — Docker работает?
- `geniriclaw docker rebuild` — пересобрать

### Webhooks не приходят
- Сервер должен иметь публичный IP и открытый port
- Проверить nginx/firewall

## Следующие шаги

1. **Пройти onboarding** (первый запуск geniriclaw)
2. **Протестировать** — написать боту любое сообщение, получить ответ от Claude
3. **Настроить провайдеров** — добавить API ключи для image/video/voice
4. **Попробовать content-production pipeline** — написать боту «сделай короткий ролик про <тема>» и следить что orchestrator делает
5. **Адаптировать скилы** под свой контекст — правки в `~/.geniriclaw/workspace/skills/<name>/SKILL.md` hot-reload'ятся при следующем старте
6. **Настроить production-инфру** — `service install` + Docker sandbox + nginx + SSL

## References

- `README-KIT.md` — детальный обзор starter kit
- `docs/installation.md` — универсальный гайд (macOS/Linux/Windows/WSL)
- `docs/config.md` — все опции конфига
- `docs/architecture.md` — как устроен фреймворк внутри
- `geniriclaw/_home_defaults/workspace/skills/*/SKILL.md` — каждый скилл с prerequisites и usage

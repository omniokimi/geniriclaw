# INSTALL_NEW_MAC.md — гайд для развёртывания GeniriClaw setup на новом маке

**Аудитория:** другая сессия Claude / любой оператор. Вошёл с нуля, контекста нет.
**Версия гайда:** 2026-04-22 (после установки на Mac Mini Евгения)
**Цель:** воспроизвести working setup — geniriclaw + Claude Code CLI с Opus 4.7 1M контекст + 68 Claude Skills (15 native + 53 импорт OpenClaw) + OpenRouter (Nano Banana) для генерации картинок.

---

## TL;DR что мы ставим

1. **geniriclaw** — Python multi-transport orchestrator (Telegram bot wrapper для Claude Code CLI)
2. **Claude Code CLI** — официальный Anthropic CLI, использует подписку Claude Pro/Max через OAuth
3. **Модель:** `claude-opus-4-7[1m]` (Opus 4.7 c 1M context window)
4. **Skills:** 15 нативных geniriclaw + 53 импортированных из openclaw/openclaw repo (префикс `oc-`)
5. **Image gen:** через OpenRouter (`google/gemini-3-pro-image-preview` + `google/gemini-2.5-flash-image`, aka Nano Banana Pro / Flash)
6. **Service:** macOS launchd LaunchAgent `dev.geniri.claw` (auto-restart on crash, RunAtLoad на login)

---

## Референсы — где источники истины

### Свой код / форк

- **GitHub репо (точка истины кода):** https://github.com/omniokimi/geniriclaw
  - Это **форк** официального geniriclaw от IgorFabrus с патчем `CLAUDE_MODELS_ORDERED` (commit `932976a` и далее).
  - Основная ветка — `main`.
- **Локальный snapshot репо:** `C:\www_agents\SERVERS\05_MAC_Mini_EVG\GeniriClaw_EVG\` (Windows-машина оператора).

### Внешние

- **Upstream (официальный) geniriclaw:** https://github.com/igorfabrus/geniriclaw — актуальные обновления, апдейты, MIT.
- **OpenClaw skills:** https://github.com/openclaw/openclaw/tree/main/skills — 53 skill'а, импортируем оптом с префиксом `oc-`.
- **Anthropic Claude Code CLI:** `npm install -g @anthropic-ai/claude-code`. Доки: https://docs.anthropic.com/en/docs/claude-code
- **OpenRouter:** https://openrouter.ai/keys (создать API key), https://openrouter.ai/google/gemini-3-pro-image-preview (Nano Banana Pro), https://openrouter.ai/google/gemini-2.5-flash-image (Nano Banana).
- **Soniox STT** (если будешь подключать voice transcription): https://soniox.com — async STT API. (В Mac Mini Евгения он подключён к OpenClaw, не к geniriclaw — для geniriclaw отдельная тема.)

### Память проекта (где Claude хранит контекст)

- `C:\www_agents\SERVERS\.claude\memory\MEMORY.md` — индекс памяти проекта SERVERS (на Windows-машине оператора).
- `C:\Users\MLR\.claude\projects\c--www-agents-SERVERS\memory\` — копия для авто-загрузки.

---

## Архитектура (понять что куда)

```text
┌─────────────────────────────────────────────────────────────────┐
│ macOS (целевой мак)                                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ LaunchAgent: dev.geniri.claw                            │    │
│  │   PATH: ~/.local/bin/geniriclaw                         │    │
│  │   EnvironmentVariables:                                 │    │
│  │     OPENROUTER_API_KEY (для image gen)                  │    │
│  │     CLAUDE_CODE_MODEL  (опц., но важно для 1M)          │    │
│  │     ANTHROPIC_MODEL    (опц., дублирует выше)           │    │
│  │     PATH               (включает /opt/homebrew/bin)     │    │
│  │   KeepAlive: true (auto-restart on crash)               │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                        ↓                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ geniriclaw (Python, pipx-installed)                     │    │
│  │   ~/.local/pipx/venvs/geniriclaw/                       │    │
│  │   home: ~/.geniriclaw/                                  │    │
│  │   ├── config/config.json   ← model, allowed_user_ids,   │    │
│  │   │                          telegram_token             │    │
│  │   ├── sessions.json        ← per-chat session state     │    │
│  │   ├── workspace/                                        │    │
│  │   │   ├── CLAUDE.md         ← system prompt for agent   │    │
│  │   │   ├── memory_system/MAINMEMORY.md ← long memory     │    │
│  │   │   └── skills/           ← 68 директорий (15 native +│    │
│  │   │                            53 oc-*)                 │    │
│  │   └── logs/agent.log                                    │    │
│  │                                                          │    │
│  │   spawns subprocess →                                    │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                        ↓                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Claude Code CLI (/opt/homebrew/bin/claude, npm)         │    │
│  │   ~/.claude/                                            │    │
│  │   ├── skills/        ← симлинки на ~/.geniriclaw/.../skills│  │
│  │   ├── projects/-Users-XX--geniriclaw-workspace/         │    │
│  │   │     <session-uuid>.jsonl  ← cache convers по сессии │    │
│  │   └── settings.json                                     │    │
│  │                                                          │    │
│  │   Auth: macOS Keychain entry "Claude Code-credentials"  │    │
│  │   (создаётся командой `claude` → /login через браузер)  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
       ↑                                                  ↑
       │ Telegram polling                                 │ subprocess
       │ aiogram → @BotFather token                       │ spawn from geniriclaw
       │                                                  │
   Telegram users (allowed_user_ids фильтр)
```

### Главные файлы — что где живёт

| Путь | Назначение |
|---|---|
| `~/.geniriclaw/config/config.json` | Главный конфиг geniriclaw — model, transport, telegram_token, allowed_user_ids, language, timezone |
| `~/.geniriclaw/sessions.json` | per-chat сессии (provider, model, message_count, claude session_id) |
| `~/.geniriclaw/workspace/CLAUDE.md` | system prompt для Claude (Zone 2, framework-managed, перезаписывается при init) |
| `~/.geniriclaw/workspace/memory_system/MAINMEMORY.md` | long-term память (Zone 3, user-owned, **не перезаписывается** при reinstall) |
| `~/.geniriclaw/workspace/skills/CLAUDE.md` | index скиллов (custom, наш) |
| `~/.geniriclaw/workspace/skills/<name>/SKILL.md` | каждый скилл с frontmatter `name`/`description` (Anthropic Skills spec) |
| `~/.local/pipx/venvs/geniriclaw/lib/python3.X/site-packages/geniriclaw/config.py` | внутренний код geniriclaw — `CLAUDE_MODELS_ORDERED`, `provider_for()` |
| `~/Library/LaunchAgents/dev.geniri.claw.plist` | macOS service definition |
| `~/.claude/.credentials.json` или Keychain "Claude Code-credentials" | OAuth токен Claude (создаётся `claude /login`) |
| `~/.zshrc`, `~/.zshenv` | env vars (для interactive и non-interactive shell соответственно) |

---

## Pre-requisites (что нужно от пользователя)

1. **Доступ к маку** — SSH или физический. Если SSH — нужен публичный IP мака **или** туннель/proxy.
2. **macOS 12+** (тестилось на Tahoe 26 / arm64 M-чип).
3. **Подписка Claude Pro / Claude Max** (для аутентификации Claude Code CLI через OAuth — без неё придётся вместо OAuth использовать `ANTHROPIC_API_KEY`, но OAuth дешевле и проще).
4. **Telegram бот:**
   - Создать через @BotFather: `/newbot` → имя → username → получить `bot_token` (формат `123456789:AA...`)
   - Узнать numeric Telegram user_id оператора (через @userinfobot или @getmyid_bot)
5. **OpenRouter API key** (опционально, если нужны картинки): https://openrouter.ai/keys → Generate → ~$5 баланс. Формат `sk-or-v1-...`.
6. **Homebrew** установлен на маке (`/opt/homebrew/bin/brew`). Если нет:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

---

## Шаг 0 — Подключение к маку через SSH

Если ты как Claude в другой сессии работаешь удалённо — нужно SSH-доступ.

### 0.1. На маке: включить sshd + добавить ключ

```bash
sudo systemsetup -setremotelogin on
sudo systemsetup -getremotelogin                  # должно показать "On"

# Application Firewall может блокировать sshd — разрешить:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/sbin/sshd

# Проверить что слушает на *:22 (а не только loopback):
sudo lsof -iTCP:22 -sTCP:LISTEN
# Ожидаем: launchd ... TCP *:ssh (LISTEN)
```

Добавить SSH public key оператора в `~/<user>/.ssh/authorized_keys`:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys <<'EOF'
ssh-ed25519 AAAA... <comment>
EOF
chmod 600 ~/.ssh/authorized_keys
```

### 0.2. У оператора (Windows): обнови `~/.ssh/config`

Если у мака **прямой публичный IP** (например провайдер Verizon/T-Mobile US часто даёт):
```ssh-config
Host mac-<имя>-direct
    HostName <публичный_IP>
    User <user>
    IdentityFile ~/.ssh/id_ed25519_nopass
    IdentitiesOnly yes
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
```

Если за NAT — нужен ProxyJump через любой публично-доступный мак/VPS в той же сети, либо Tailscale, либо reverse SSH tunnel.

### 0.3. Особенности Windows-операторской машины

- На Windows может быть активен **Meta Tunnel VPN** (`198.18.0.2`) который перехватывает маршруты на близкие IP. Симптом: `ping <ip_мака>` даёт 0ms latency. Проверка: `Get-NetRoute -DestinationPrefix '<ip>/32'`. Решение: ProxyJump через другой мак, либо Static route в обход VPN (требует admin).
- Используй `ssh <alias> "<command>"` для one-shot. Для интерактивной работы — `ssh <alias>` без аргументов.

---

## Шаг 1 — Базовые пакеты на маке

```bash
brew install python@3.12 pipx node
pipx ensurepath
source ~/.zshrc      # или открой новый терминал

# Sanity check
python3 --version    # >= 3.11
pipx --version
node --version       # >= 18
which claude         # пока пусто, поставим ниже
```

---

## Шаг 2 — Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code

# Авторизация ИНТЕРАКТИВНО — нужен GUI-браузер на маке.
# Делать локально на маке (не через SSH non-interactive!):
claude
# В открывшемся TUI:
#   /login
# Откроется браузер → войти под Claude Pro/Max аккаунтом → Authorize
# Закрыть TUI: Ctrl+C или /quit

# Проверить:
claude -p "say OK"
# Должен вернуть "OK", не "Not logged in"
```

**Важно про SSH:** Если ты Claude-сессия в SSH non-interactive shell, у тебя **нет доступа к macOS Keychain** где хранится OAuth токен. `claude -p` через SSH будет давать "Not logged in", даже если на маке всё прекрасно работает. Это **нормально** — geniriclaw service работает под launchd `gui/UID` доменом, у которого keychain доступен. Не паникуй, проверяй через бота.

---

## Шаг 3 — Установить geniriclaw из forka omniokimi

```bash
git clone https://github.com/omniokimi/geniriclaw.git ~/geniriclaw-src
pipx install ~/geniriclaw-src
geniriclaw --version       # 0.15.0+
```

**Если репо приватный** — нужен Personal Access Token. Лучше сделать публичным.

**Альтернатива** — установить из upstream PyPI: `pipx install geniriclaw`. Но **нет патча `CLAUDE_MODELS_ORDERED`** для 1M-моделей → придётся патчить руками (см. Шаг 7 ниже).

---

## Шаг 4 — Onboarding wizard

```bash
geniriclaw
```

Ответы:

| Вопрос | Ответ |
|---|---|
| Disclaimer (понимаю риски) | `y` |
| CLI backend | `Claude` |
| Transport | `Telegram` |
| Bot token | `<paste token from BotFather>` |
| Allowed Telegram user_id | `<your numeric ID>` |
| Docker sandbox | `N` (рекомендуется на VPS, не на домашнем маке) |
| Timezone | твой часовой пояс (`America/New_York`, `Europe/Moscow` и т.д.) |
| Install as background service | `Y` |

Wizard создаст:
- `~/.geniriclaw/config/config.json`
- `~/.geniriclaw/workspace/` (полный starter kit, Zone 2 + Zone 3)
- `~/Library/LaunchAgents/dev.geniri.claw.plist`
- зарегистрирует launchd service
- запустит бота

---

## Шаг 5 — Smoke-тест

В Telegram открой бота → напиши "привет".

```bash
# На маке — лог:
tail -F ~/.geniriclaw/logs/agent.log
# Жди CLI stream cmd: ... --model opus ...
# и Streaming flow completed fallback=False content=True
```

Если ответ пришёл — базовый setup работает. Дальше — апгрейды.

---

## Шаг 6 — Установить 1M контекст модель

### 6.1. Поправить config.json

```bash
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path.home() / ".geniriclaw/config/config.json"
c = json.loads(p.read_text())
c["model"] = "claude-opus-4-7[1m]"
c["provider"] = "claude"
p.write_text(json.dumps(c, indent=2, ensure_ascii=False))
print("set:", c["model"], c["provider"])
EOF
```

### 6.2. Если установлен из PyPI (без omniokimi-форка) — патчить `config.py`

```bash
# Найти точный путь
PYVER=$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')
CFG="$HOME/.local/pipx/venvs/geniriclaw/lib/python$PYVER/site-packages/geniriclaw/config.py"
echo "$CFG"

cp "$CFG" "$CFG.bak"
sed -i '' 's|("haiku", "sonnet", "opus")|("haiku", "sonnet", "opus", "claude-opus-4-7[1m]", "claude-sonnet-4-6[1m]", "claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001")|' "$CFG"

# Verify
grep "CLAUDE_MODELS_ORDERED" "$CFG"
```

**Без патча** — geniriclaw `provider_for("claude-opus-4-7[1m]")` вернёт `"codex"` (default fallback), и при первом запросе бот упадёт в `FileNotFoundError: codex CLI not found on PATH`. Это **главный gotcha**.

Если ставил из омниокими-форка — патч уже есть, шаг 6.2 пропускай.

### 6.3. Очистить старые сессии (важно после смены модели)

```bash
echo "{}" > ~/.geniriclaw/sessions.json
rm -f ~/.claude/projects/-Users-*--geniriclaw-workspace/*.jsonl 2>/dev/null
```

Без этого geniriclaw будет резюмить старые сессии с прежним provider/model.

### 6.4. Перезапустить service

```bash
launchctl kickstart -k gui/$(id -u)/dev.geniri.claw
sleep 3
launchctl list | grep dev.geniri.claw      # PID > 0
```

### 6.5. Проверка через бота

В Telegram: "какая модель и сколько контекста?"
В логе должно появиться `--model claude-opus-4-7[1m]` и `Streaming flow completed`.

---

## Шаг 7 — Установить OpenRouter (для image generation)

### 7.1. Получить API key

https://openrouter.ai/keys → залогиниться (Google/GitHub) → пополнить баланс ($5+) → Generate API key.

### 7.2. Прокинуть в env (3 места для надёжности)

```bash
KEY="sk-or-v1-..."

# 1) plist (для launchd service)
PLIST=~/Library/LaunchAgents/dev.geniri.claw.plist
/usr/libexec/PlistBuddy -c "Delete :EnvironmentVariables:OPENROUTER_API_KEY" "$PLIST" 2>/dev/null
/usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:OPENROUTER_API_KEY string $KEY" "$PLIST"

# 2) ~/.zshrc (для interactive shell)
grep -q OPENROUTER_API_KEY ~/.zshrc || echo "export OPENROUTER_API_KEY=\"$KEY\"" >> ~/.zshrc

# 3) ~/.zshenv (для non-interactive SSH)
grep -q OPENROUTER_API_KEY ~/.zshenv || echo "export OPENROUTER_API_KEY=\"$KEY\"" >> ~/.zshenv

# Проверить
curl -sS https://openrouter.ai/api/v1/auth/key -H "Authorization: Bearer $KEY" | python3 -m json.tool
# Должен вернуть {"data": {"label": "...", "usage": 0, "limit": null, ...}}

launchctl kickstart -k gui/$(id -u)/dev.geniri.claw
```

В `nano-banana-openrouter` skill (входит в geniriclaw native) есть полная инструкция как Claude вызывает OpenRouter для image gen — `~/.geniriclaw/workspace/skills/nano-banana-openrouter/SKILL.md`.

---

## Шаг 8 — Импортировать 53 скилла из OpenClaw

```bash
# Клонировать openclaw (или git pull если уже есть)
[ -d /tmp/openclaw-src ] && (cd /tmp/openclaw-src && git pull) || git clone --depth 1 https://github.com/openclaw/openclaw.git /tmp/openclaw-src

# Скопировать каждый skill с префиксом oc-
SRC=/tmp/openclaw-src/skills
DST=~/.geniriclaw/workspace/skills
for d in $SRC/*/; do
    name=$(basename "$d")
    if [ -f "$d/SKILL.md" ]; then
        rm -rf "$DST/oc-$name"
        cp -r "$d" "$DST/oc-$name"
    fi
done

# Проверить
ls "$DST" | grep -c '^oc-'        # должно быть 53
ls ~/.claude/skills | grep -c '^oc-'  # симлинки появятся после kickstart, ~30 сек

# Перезапустить — skill_sync пересоберёт симлинки
launchctl kickstart -k gui/$(id -u)/dev.geniri.claw
```

**Конфликт имён:** `oc-skill-creator` дублирует нативный `skill-creator`. Не страшно — оба будут жить, но рекомендуется при upgrade использовать нативный.

### 8.1. Записать в инструкции что есть OpenClaw skills

Это файл `~/.geniriclaw/workspace/skills/CLAUDE.md` — Claude его читает при старте сессии. Добавь туда секцию "Skill Inventory" с перечислением. Готовый шаблон — на Mac Mini Евгения, можно скопировать:

```bash
# Скачать готовый skills/CLAUDE.md с эталонной мак-машины (если доступ есть)
scp mac-evgeniy-via-studio:~/.geniriclaw/workspace/skills/CLAUDE.md \
    /tmp/skills_CLAUDE.md
# Адаптировать paths под новую машину и положить
cp /tmp/skills_CLAUDE.md ~/.geniriclaw/workspace/skills/CLAUDE.md
```

Либо написать заново — структура: `## Sync Topology`, `## Sync Rules`, `## Skill Inventory` с разбивкой на native/oc-*.

### 8.2. Записать про скиллы в long memory

Обнови `~/.geniriclaw/workspace/memory_system/MAINMEMORY.md` — добавь под `## Learned Facts` блок:

```markdown
### Skills inventory (обновлено YYYY-MM-DD)

- 15 native geniriclaw skills (content/publishing/execution/meta).
- 53 imported OpenClaw skills (prefix `oc-`) from https://github.com/openclaw/openclaw/tree/main/skills.
- All oc-* — generic Claude Skills, требуют внешние CLI или API. Перед использованием — читай SKILL.md каждого.
- Default model: claude-opus-4-7[1m] (Opus 4.7, 1M context).
- OPENROUTER_API_KEY в env — для nano-banana-openrouter skill (image generation).
```

`SharedKnowledgeSync` подхватит изменение MAINMEMORY.md за 30 секунд и распространит на всех агентов.

---

## Шаг 9 — Финальный health-check

```bash
# 1. Service alive
launchctl list | grep dev.geniri.claw     # PID > 0

# 2. Last log entries
tail -30 ~/.geniriclaw/logs/agent.log
# Жди:
#   "Provider [claude]: authenticated"
#   "Bot online: @<your_bot> (id=...)"

# 3. Skills count
ls ~/.geniriclaw/workspace/skills/ | grep -v '\.md$' | wc -l    # 68
ls ~/.claude/skills/ | wc -l                                    # 68

# 4. Config sanity
cat ~/.geniriclaw/config/config.json | python3 -m json.tool | grep -E '"model"|"provider"|"allowed_user_ids"'

# 5. Telegram test
# В Telegram: "какая модель?" — должен ответить про Opus 4.7 1M

# 6. Image gen test (опц., если OPENROUTER_API_KEY стоит)
# В Telegram: "сгенерируй картинку: горный пейзаж на закате"
# Claude должен вызвать nano-banana-openrouter skill через OpenRouter
```

---

## Известные подводные камни

| Симптом | Причина | Лечение |
|---|---|---|
| `claude -p` из SSH говорит `Not logged in`, но через бот работает | Keychain доступен только в gui domain, не в SSH non-interactive | Игнорируй, проверяй через telegram |
| Бот: `An internal error occurred. Please try again.` + `FileNotFoundError: codex CLI not found` | `provider_for(model)` упал на codex по дефолту, потому что `claude-opus-4-7[1m]` не в `CLAUDE_MODELS` | Патч `config.py` — Шаг 6.2 |
| Бот после смены модели всё равно отвечает на старой | `--resume <session_id>` использует model из сохранённой Claude сессии | Очисти `sessions.json` + `~/.claude/projects/.../*.jsonl` (Шаг 6.3) |
| `pipx install` поставил, но `geniriclaw: command not found` | `~/.local/bin` не в PATH | `pipx ensurepath; source ~/.zshrc` (или новый терминал) |
| sshd на маке слушает, но connect viset на banner | macOS Application Firewall блочит sshd | `socketfilterfw --add /usr/sbin/sshd && --unblockapp /usr/sbin/sshd` |
| После `pipx upgrade geniriclaw` — снова падает codex error | Патч CLAUDE_MODELS затёрт upgrade | Перепатчить (Шаг 6.2). Долгосрочно — ставить из omniokimi-форка где патч в коде |
| Skills из workspace не видны Claude'у | Не прошёл skill_sync watcher (симлинки не созданы) | `launchctl kickstart -k gui/$(id -u)/dev.geniri.claw` + подожди 10 сек |
| Старые упоминания deprecated провайдера в ответах бота | Cached в Claude session jsonl | Удалить `~/.claude/projects/.../<session>.jsonl`, очистить `sessions.json`, рестарт |
| `[incoming file]` команды падают с codex not found | geniriclaw для voice transcription пытается Codex по дефолту | Установить codex CLI: `npm install -g @openai/codex` ИЛИ адаптировать `voice-recognition` skill под Soniox |

---

## Что **не делать**

- **Не редактировать** `geniriclaw/config.py` в pipx venv напрямую без бэкапа — `pipx upgrade` сотрёт. Делай патч и сохраняй `.bak`. Долгосрочно — PR в omniokimi/geniriclaw.
- **Не удалять** `~/.geniriclaw/sessions.json` без `kickstart` после — geniriclaw может писать в него рандомно при graceful shutdown.
- **Не коммитить** в git репо `config.json` (там телеграм токен!) или `.credentials.json` (Claude OAuth!).
- **Не ставить** Docker sandbox если не понимаешь зачем — на домашнем маке прирост безопасности маленький, а проблем больше.
- **Не добавлять** `claude-opus-4-7[1m]` в `--model` Claude CLI **на оригинальном (не запатченном) geniriclaw** — упадёт в codex provider, как описано в подводных камнях.

---

## Если что-то идёт не так — куда смотреть

1. `~/.geniriclaw/logs/agent.log` — последние ~50 строк, ищи `ERROR` / `WARNING`.
2. `~/.geniriclaw/logs/service.err` — stderr от launchd процесса.
3. `launchctl print gui/$(id -u)/dev.geniri.claw 2>&1 | head -30` — состояние service'а.
4. `cat ~/.geniriclaw/sessions.json` — что в текущих сессиях (provider, model — должны совпадать с config).
5. `ls -la ~/.claude/skills/ | head` — есть ли симлинки.
6. `claude -p "test"` локально на маке (не через SSH!) — работает ли Claude напрямую.

---

## Контакты / источники

- **Канон код:** https://github.com/omniokimi/geniriclaw (форк с патчем)
- **Upstream:** https://github.com/igorfabrus/geniriclaw
- **OpenClaw skills:** https://github.com/openclaw/openclaw/tree/main/skills
- **Anthropic Claude Code:** https://docs.anthropic.com/en/docs/claude-code
- **OpenRouter:** https://openrouter.ai
- **Reference deployment (рабочий пример):** Mac Mini Евгения — SSH alias `mac-evgeniy-via-studio` (через ProxyJump `mac-studio`), user `syntrix`. Можно `scp` любые рабочие конфиги/скиллы с него для шаблонов.

---

**Гайд написан после успешной установки на Mac Mini Евгения 2026-04-22.** Если что-то меняется в архитектуре geniriclaw upstream — обновляй этот файл первым делом и запушь в `omniokimi/geniriclaw`.

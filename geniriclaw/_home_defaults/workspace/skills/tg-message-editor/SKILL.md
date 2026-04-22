# tg-message-editor — редактирование и удаление Telegram-сообщений

> **Status:** stable
> **Category:** publish · messaging
> **Depends on:** Telegram Bot API, bot token

## Purpose

Править уже отправленные сообщения (текст, caption к фото/видео), удалять сообщения, фиксировать опечатки без перепоста. Критично для каналов, где пост уже увидели подписчики — удалить/перезалить выглядит как ошибка.

## Prerequisites

- Bot token от BotFather
- `chat_id` канала / DM
- `message_id` целевого сообщения (из response `sendMessage`, или из ссылки на сообщение)

## Разобрать ссылку на сообщение

Telegram-ссылка: `https://t.me/<channel_username>/1234` → `message_id = 1234`.
Для супергрупп: `https://t.me/c/1234567890/42` → `chat_id = -1001234567890`, `message_id = 42`.

## Получить текст сообщения (если неизвестен)

Telegram Bot API не возвращает произвольное сообщение по ID. Обходные пути:
1. Хранить `posts_log.json` с message_id + text (см. `channel-publisher`).
2. Forward message к боту → читать в handler.
3. `getChat` возвращает закреплённое, но не произвольные.

## Редактирование текста

```bash
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/editMessageText" \
  -d chat_id="${CHAT_ID}" \
  -d message_id="${MESSAGE_ID}" \
  -d text="<new text>" \
  -d parse_mode=MarkdownV2
```

## Редактирование подписи к фото/видео

```bash
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/editMessageCaption" \
  -d chat_id="${CHAT_ID}" \
  -d message_id="${MESSAGE_ID}" \
  -d caption="<new caption>" \
  -d parse_mode=MarkdownV2
```

## Удаление

```bash
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteMessage" \
  -d chat_id="${CHAT_ID}" \
  -d message_id="${MESSAGE_ID}"
```

## Ограничения Telegram API

- Редактировать можно только сообщения **от этого же бота**.
- Удалять:
  - В DM: только сообщения этого же бота.
  - В группе: бот может удалять любые, если он **admin** с правом `can_delete_messages`.
  - Сообщения **старше 48 часов** удаляются только админами (не ботом из DM).
- Редактировать **тип** сообщения нельзя (текст → фото только через delete+send).
- Media (фото/видео) самой картинки менять нельзя через `editMessageMedia` — можно только подпись.

## MarkdownV2 — обязательно экранировать

```
_ * [ ] ( ) ~ ` > # + - = | { } . !
```

Утилита экранирования:
```python
import re
def escape_md_v2(s: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', s)
```

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{BOT_TOKEN}}` | env `.env` |
| `{{CHAT_ID}}` | канала / DM |
| `{{MESSAGE_ID}}` | целевое сообщение |

## Checklist при редактировании

1. Есть ли оригинальный текст (из `posts_log.json`)?
2. Экранирован ли новый текст под MarkdownV2?
3. Проверить что message_id действительно от этого бота (если не уверен — отправить тест в DM с этим же message_id).
4. После edit — обновить `posts_log.json`.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| 400 "message is not modified" | Новый текст идентичен старому — edit не нужен |
| 400 "message can't be edited" | Сообщение не от этого бота или > 48 часов + нет прав |
| 400 "can't parse entities" | Markdown не экранирован — использовать `escape_md_v2` или послать `parse_mode=HTML` |
| 404 "message to edit not found" | Неверный message_id / chat_id / сообщение удалено |

## References

- [editMessageText](https://core.telegram.org/bots/api#editmessagetext)
- [editMessageCaption](https://core.telegram.org/bots/api#editmessagecaption)
- [deleteMessage](https://core.telegram.org/bots/api#deletemessage)
- Related: `channel-publisher`, `learning-loop`

# publisher-multi — Публикация final.mp4 на несколько платформ параллельно.

> **Type:** E — multi-provider publisher
> **Input:** final.mp4 + caption + platforms list
> **Output:** published.json с URL и message_id'ами

## Purpose

Публикация final.mp4 на несколько платформ параллельно.

## When invoked

После editor, финальный шаг pipeline.

## Rules

- Параллельно: TG / IG / TikTok / VK.
- Опционально через Ayrshare unified gateway.
- Если одна платформа упала — остальные продолжают.
- Записать все URL + message_id в published.json.
- Через 24 часа — metrics-tracker собирает метрики.

## Example

_(no example yet)_

## Related skills

`channel-publisher`, `publisher-site`, `tg-message-editor`

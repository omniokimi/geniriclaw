# metrics-tracker — Сбор метрик опубликованных материалов (views, reactions, shares).

> **Type:** B — Bash/Python script + API calls
> **Input:** published.json (URL, message_id, timestamp)
> **Output:** metrics.json в published/<job>/

## Purpose

Сбор метрик опубликованных материалов (views, reactions, shares).

## When invoked

Cron +24h после публикации + еженедельный rollup.

## Rules

- Telegram: getMessageStats (для каналов с подписчиками > 100).
- IG: Meta Graph Insights.
- TikTok: for Developers API.
- Ayrshare analytics — unified.
- Кэшировать на 1 час (не DoS'ить API).

## Example

_(no example yet)_

## Related skills

`learning-loop`

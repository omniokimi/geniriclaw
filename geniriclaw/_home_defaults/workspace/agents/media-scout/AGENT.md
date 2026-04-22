# media-scout — Ежедневный сбор идей / трендов / референсов по темам проекта.

> **Type:** B — Bash/Python + WebSearch + LLM summarize
> **Input:** themes list (из projects/<channel>/themes.yaml)
> **Output:** media-digest-<YYYY-MM-DD>.md с 5-10 идеями + источниками

## Purpose

Ежедневный сбор идей / трендов / референсов по темам проекта.

## When invoked

Cron утром (09:00) — готовит media-digest на день.

## Rules

- Источники: RSS, WebSearch, подписные каналы, trending-списки платформ.
- Кэшировать — не повторять уже использованные идеи.
- Формат: hook + 2-3 sentence expansion + source URL.
- Не генерить контент — только собирать материал для scriptwriter.

## Example

_(no example yet)_

## Related skills

`channel-publisher`

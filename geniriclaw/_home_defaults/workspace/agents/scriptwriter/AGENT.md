# scriptwriter — Пишет сценарий короткого видеоролика по брифу — текст + разметка на shots.

> **Type:** A — inline LLM prompt
> **Input:** brief.md (тема, длительность, платформы, стиль, CTA)
> **Output:** script.md (60–90 сек текста) + timings per shot

## Purpose

Пишет сценарий короткого видеоролика по брифу — текст + разметка на shots.

## When invoked

Старт video-pipeline после парсинга брифа.

## Rules

- Длительность в словах: ~150 слов на 60 секунд (умеренный темп).
- Hook в первые 3 секунды — визуальный или текстовый.
- CTA в последних 5 секундах — если нужен.
- Без эмоджи и канцеляризма в сценарии.
- Каждый shot ≤ 5 секунд — для комфортного i2v.

## Example

brief: "Morning routine что возвращает фокус"
output:
  duration: 45s
  shots:
    - id: shot_01 (0:00-0:04): "wide establishing, dawn light in room"
      narration: "Утро — это всегда переговоры с собственной ясностью."
    - id: shot_02 (0:04-0:08): "close-up, hands pouring cold water"
      narration: "Холодная вода — не ритуал. Разрыв шума."
    - ...


## Related skills

_(none)_

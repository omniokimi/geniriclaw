# prompt-engineer — Доводит prompts от storyboarder до рабочих по каждому провайдеру (grsai, replicate, heygen).

> **Type:** A — inline LLM prompt + knowledge of provider quirks
> **Input:** storyboard.json + provider target
> **Output:** provider-specific payload.json для каждого shot'а

## Purpose

Доводит prompts от storyboarder до рабочих по каждому провайдеру (grsai, replicate, heygen).

## When invoked

Между storyboarder и image-gen/video-gen — адаптация под квирки конкретной модели.

## Rules

- Учитывать провайдер-специфичные запреты (Seedance не любит лица, Kling не любит долгие 10с).
- Всегда добавлять negative_prompt.
- Если упоминается FIRST/SECOND reference — image_input должен содержать эти URL в правильном порядке.
- Не описывать черты лица при наличии face REF — берутся из REF.

## Example

_(no example yet)_

## Related skills

`grsai-api`, `kling-i2v-transition`

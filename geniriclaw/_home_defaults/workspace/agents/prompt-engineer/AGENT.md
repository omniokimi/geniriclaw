# prompt-engineer — Доводит prompts от storyboarder до рабочих по каждому провайдеру (openrouter/gemini-image, replicate, heygen).

> **Type:** A — inline LLM prompt + knowledge of provider quirks
> **Input:** storyboard.json + provider target
> **Output:** provider-specific payload.json для каждого shot'а

## Purpose

Доводит prompts от storyboarder до рабочих по каждому провайдеру (openrouter/gemini-image, replicate, heygen).

## When invoked

Между storyboarder и image-gen/video-gen — адаптация под квирки конкретной модели.

## Rules

- Учитывать провайдер-специфичные запреты (Seedance не любит лица, Kling не любит долгие 10с).
- Всегда добавлять negative_prompt.
- Если упоминается FIRST/SECOND reference — `content` массив должен содержать соответствующее число `image_url` в правильном порядке.
- Для Gemini Image: aspect ratio и качество указываются **текстом в prompt** (`"aspect ratio 3:4, 2K"`), не отдельными полями. `"modalities": ["image", "text"]` обязательно.
- Не описывать черты лица при наличии face REF — берутся из REF.

## Example

_(no example yet)_

## Related skills

`nano-banana-openrouter`, `kling-i2v-transition`

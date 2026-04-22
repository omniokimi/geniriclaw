# image-gen — Генерация статичных кадров через nano-banana-openrouter (Gemini Image).

> **Type:** B — Bash/Python script
> **Input:** provider payload.json + output path
> **Output:** PNG 2K в drafts/<job>/shots/shot_NN.png

## Purpose

Генерация статичных кадров через OpenRouter (модели `google/gemini-3-pro-image-preview` и `google/gemini-2.5-flash-image`, семейство Nano Banana).

## When invoked

После prompt-engineer, перед video-gen.

## Rules

- Параллелизм 4 shot'а одновременно (rate-limit OpenRouter либерален, но осторожно).
- Проверять реальный размер PNG header — если меньше целевого, перегенерировать с усиленным prompt.
- Face REF передавать как `{"type": "image_url", "image_url": {"url": "..."}}` в `content` массиве; `"modalities": ["image", "text"]` обязателен, иначе вернётся только текст.
- При failure — 1 retry с упрощённым prompt, потом понизить модель (`gemini-3-pro-image-preview` → `gemini-2.5-flash-image`), потом still/skip.
- Перед production батчем сделай 1–2 черновика на `gemini-2.5-flash-image` (дёшево, ~$0.003), шлифуй prompt, потом final на `gemini-3-pro-image-preview`.

## Example

_(no example yet)_

## Related skills

`nano-banana-openrouter`

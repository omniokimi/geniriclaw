# image-gen — Генерация статичных кадров через grsai-api (nano-banana семейство).

> **Type:** B — Bash/Python script
> **Input:** provider payload.json + output path
> **Output:** PNG 2K в drafts/<job>/shots/shot_NN.png

## Purpose

Генерация статичных кадров через grsai-api (nano-banana семейство).

## When invoked

После prompt-engineer, перед video-gen.

## Rules

- Параллелизм 4 shot'а одновременно (rate limit).
- Проверять реальный размер PNG header — если меньше 2K, перегенерировать.
- Face REF в image_input, не в urls.
- При failure — 1 retry с упрощённым prompt, потом понизить модель (pro → 2 → fast), потом still/skip.

## Example

_(no example yet)_

## Related skills

`grsai-api`

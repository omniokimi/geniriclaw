# video-gen — Превращает каждый PNG в 5/10-сек клип через Kling v2.1 (Replicate).

> **Type:** B — Bash/Python script
> **Input:** shot PNG + motion_prompt + duration
> **Output:** MP4 в drafts/<job>/videos/shot_NN.mp4

## Purpose

Превращает каждый PNG в 5/10-сек клип через Kling v2.1 (Replicate).

## When invoked

После image-gen, перед editor.

## Rules

- Kling standard 5s — default. Pro 1080p или end_image — использовать осознанно.
- Параллелизм 3 одновременно (Replicate fair-use).
- Motion только через prompt модели, не через ffmpeg.
- При failure — 1 retry; потом still (использовать PNG как статичное видео на длительность shot'а).

## Example

_(no example yet)_

## Related skills

`kling-i2v-transition`, `directors-cut-pipeline`

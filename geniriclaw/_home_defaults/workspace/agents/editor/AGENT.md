# editor — FFmpeg-склейка: shots + transitions + voice + music → final.mp4.

> **Type:** D — FFmpeg pipeline
> **Input:** все видео/аудио артефакты
> **Output:** final.mp4 в drafts/<job>/build/

## Purpose

FFmpeg-склейка: shots + transitions + voice + music → final.mp4.

## When invoked

После video-gen, voice-over, music-scoring. Финальная сборка.

## Rules

- Normalize framerate/resolution/codec до concat.
- Audio mix: voice -1dB, music -18dB (duck).
- НЕ имитировать camera motion через filter math (zoompan/rotate/scale(t)).
- Только concat, trim, audio mix, simple fade.
- Director's cut transitions — через kling (см. skill), не ffmpeg.

## Example

_(no example yet)_

## Related skills

`directors-cut-pipeline`, `kling-i2v-transition`

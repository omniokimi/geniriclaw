# voice-over — Генерация закадрового голоса из script-narration.

> **Type:** C — provider SDK (ElevenLabs / OpenAI TTS / Microsoft Edge TTS)
> **Input:** text per shot (из script.md)
> **Output:** WAV / MP3 в drafts/<job>/audio/voice_shot_NN.wav

## Purpose

Генерация закадрового голоса из script-narration.

## When invoked

После storyboard готов, параллельно с image-gen.

## Rules

- ElevenLabs voice clone — для одного повторяющегося голоса.
- OpenAI TTS — fallback если ElevenLabs недоступен.
- Microsoft Edge TTS — бесплатная альтернатива (хуже качество, но для черновиков ок).
- Выравнивать длительность с длительностью shot'а (speed adjust если нужно).

## Example

_(no example yet)_

## Related skills

_(none)_

# kling-i2v-transition — image→video переходы через Kling v2.1

> **Status:** stable
> **Category:** content-production · video-generation
> **Depends on:** `REPLICATE_API_TOKEN`, стартовое и (опц.) конечное изображение

## Purpose

Превращает одно изображение в короткий видеоклип (5 или 10 секунд) с движением камеры и/или объектов через модель **Kling v2.1** на Replicate. Поддерживает **start-image → end-image** переходы (плавная морфинг-анимация между двумя кадрами).

## When to use

- Нужно оживить статичный кадр с движением камеры (push-in, orbit, handheld).
- Нужен плавный переход между двумя связанными кадрами.
- Важно сохранить лицо персонажа в движении (Kling сильнее Seedance на лицах).
- Кадры для Reels/Shorts/TikTok 9:16, 720p/1080p.

**НЕ подходит** для: длинных клипов (>10 сек), сложных многокадровых склеек, генерации от чистого текста (только image→video).

## Prerequisites

| Что | Где получить | Переменная |
|-----|--------------|------------|
| Replicate API token | [replicate.com/account](https://replicate.com/account/api-tokens) | `REPLICATE_API_TOKEN` |
| Start image | PNG/JPEG, публичный URL или base64 | `{{START_IMAGE_URL}}` |
| End image (опц.) | Для end-frame transition | `{{END_IMAGE_URL}}` |

Регистрация Replicate требует карту (даже для pay-as-you-go).

## Models & pricing

| Модель | Качество | Длительность | Цена | Когда |
|--------|----------|--------------|------|-------|
| `kwaivgi/kling-v2.1-standard` | 720p | 5 / 10 с | ~$0.28 / 5s | **Default** для большинства задач с лицами |
| `kwaivgi/kling-v2.1-master` | 1080p | 5 / 10 с | ~$1.40 / 5s | Когда критично 1080p или нужен `end_image` |

Альтернативы на Replicate (не тестировано глубоко): `minimax/hailuo-02`, `pixverse/v4.5`, `alibaba/wan-2.5-i2v`.

## API

```
POST https://api.replicate.com/v1/models/kwaivgi/kling-v2.1-standard/predictions
Headers:
  Authorization: Bearer {{REPLICATE_API_TOKEN}}
  Content-Type: application/json

Body:
{
  "input": {
    "start_image": "{{START_IMAGE_URL}}",
    "end_image": "{{END_IMAGE_URL}}",       // optional
    "prompt": "<motion description>",
    "duration": 5,                           // 5 or 10
    "negative_prompt": "<artifacts to avoid>"
  }
}
```

Polling: `GET https://api.replicate.com/v1/predictions/{id}`.

## Prompt rules — motion через `motion_prompt`, не через ffmpeg

**Жёсткое правило:** операторская техника (push-in, orbit, handheld, drift, dutch angle) — **только** внутри `prompt` самой модели. Editor-step (ffmpeg) **не имеет права** имитировать движение через time-driven filter math:

| Запрещено в ffmpeg | Почему |
|---------------------|--------|
| `zoompan=z='1+t*0.05'` | Псевдо push-in — видно zoom-артефакты |
| `rotate='t*0.02'` | Псевдо-качание — получается дёргано |
| `scale=w='iw*(1+t*0.1)'` | Псевдо-приближение |
| `crop=...:x='...sin(t)...'` | Псевдо-handheld |

**Разрешено в ffmpeg:** concat готовых mp4, наложение аудио, trim, простые fade-переходы между уже готовыми видео.

Если реального I2V нет — шот остаётся **статичным** (честно помечается как `still`).

## Prompt pattern

```
<subject from reference image> moving [describe motion].
Camera: [shot type] with [movement].
Lighting: [preserve lighting from source].
Duration: smooth natural motion throughout.
```

### Рабочий пример (waterfall → shower)

```
prompt: "Water streams naturally transitioning from waterfall to modern shower.
Camera: wide establishing shot slowly drifting closer.
Natural water flow, consistent lighting."

negative_prompt: "jump cut, flicker, camera shake, strobe,
double exposure, identity change, distorted face"
```

### Рабочий пример (static portrait → living breath)

```
prompt: "Subject from reference image breathes naturally,
subtle chest rise, minimal head movement, eyes blink once.
Camera: locked off, no zoom, no pan."

negative_prompt: "jump cut, face distortion, extra limbs,
identity change, AI artifacts, strong camera movement"
```

## Negative prompt — обязательно включать

Минимум чтобы убрать типовые артефакты Kling:

```
jump cut, flicker, strobe, double exposure,
identity change, face morph, distorted features,
extra limbs, malformed hands, AI artifacts,
sudden lighting change
```

## Config placeholders

| Placeholder | Что это |
|-------------|---------|
| `{{REPLICATE_API_TOKEN}}` | Bearer-токен Replicate |
| `{{START_IMAGE_URL}}` | Публичный URL первого кадра (png/jpg) |
| `{{END_IMAGE_URL}}` | (опц.) URL последнего кадра для morph |
| `{{MOTION_PROMPT}}` | Описание движения камеры/объектов |
| `{{DURATION_SEC}}` | `5` или `10` |
| `{{OUTPUT_DIR}}` | Куда сохранять mp4 (default: `workspace/output/videos/`) |

## Minimal working script

См. [`template_transition.py`](template_transition.py) рядом — параметризованный запуск + polling + скачивание.

## Извлечение граничных кадров

Если нужен `end_image` из существующего видео (чтобы плавно перейти из клипа A в клип B):

```bash
# Последний кадр клипа A
ffmpeg -sseof -0.1 -i clip_a.mp4 -vframes 1 -q:v 2 last_frame.jpg

# Первый кадр клипа B
ffmpeg -i clip_b.mp4 -vframes 1 -q:v 2 first_frame.jpg
```

Потом оба кадра заливаются на публичный URL, передаются в `start_image` / `end_image`.

## Rules

- **motion только через prompt модели**, ffmpeg не имитирует — см. выше.
- Для консистентности лица в серии шотов используй **одинаковый** стартовый промптпак (см. skill `learning-loop`).
- Для end-image transition модель работает лучше если кадры **похожи по освещению** (тот же час дня, та же схема света). Слишком разные кадры → морфинг-артефакт.
- 5с предпочтительнее 10с — меньше накопления дрейфа лица.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| Лицо "плывёт" за 5 секунд | Использовать `master` вместо `standard`; уменьшить duration до 5с; уточнить в prompt `minimal head movement, stable subject` |
| Прерывистые цвета / flicker | Добавить `no flicker, stable lighting` в prompt + расширить negative_prompt |
| `safety block` (отказ модели) | Переформулировать prompt — убрать триггеры (nudity, violence, gore) |
| Prediction 429 / queue full | Экспоненциальный backoff, 3 попытки с паузой 30с / 60с / 120с |
| Output видео чёрное / пустое | Неверный URL `start_image` (Replicate не смог скачать) — проверить что URL публично доступен |

## References

- [Replicate — Kling v2.1 standard](https://replicate.com/kwaivgi/kling-v2.1-standard)
- [Replicate — Kling v2.1 master](https://replicate.com/kwaivgi/kling-v2.1-master)
- Related skills: `video-pipeline`, `directors-cut-pipeline`, `storyboard-designer`, `learning-loop`

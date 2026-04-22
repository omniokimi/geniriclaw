# nano-banana-openrouter — генерация изображений через OpenRouter (Gemini Image)

> **Status:** stable
> **Category:** content-production · image-generation
> **Depends on:** `OPENROUTER_API_KEY` (env), `curl` / `requests`

## Purpose

Обёртка над API `openrouter.ai/api/v1/chat/completions` для генерации статичных изображений моделями семейства **Nano Banana** от Google (Gemini Image): портреты, b-roll, сцены, художественные концепты. Поддерживает **img2img с face-reference** (character consistency), **multi-image input** и **text2img**.

Один API-ключ OpenRouter даёт доступ ко всему семейству + фолбэк на сотни других моделей при необходимости. OpenAI-compatible endpoint — работает с любым OpenAI SDK.

## When to use

- Нужен кадр с конкретным лицом — img2img: отправить REF-фото в `content` как `image_url`.
- Нужен кадр без персонажа — text2img по одному `text` content.
- Нужен batch-рендер раскадровки перед I2V.
- Нужна сохранность персонажа через серию кадров → `google/gemini-3-pro-image-preview`.
- Бюджет малый и скорость важнее максимального качества → `google/gemini-2.5-flash-image`.

Если нужны 3D-сцены, композиции с множеством персонажей или очень специфичные стили — рассмотреть `replicate` с Flux/SDXL, `krea` для фотореалистичных портретов.

## Prerequisites

| Что | Где получить | Переменная окружения |
|-----|--------------|----------------------|
| API key | [openrouter.ai/keys](https://openrouter.ai/keys) — регистрация (GitHub/Google OAuth), top-up от $5 | `OPENROUTER_API_KEY` |
| Публичный URL для face REF (опц.) | любой статический хостинг (собственный домен, S3, CDN, Telegram CDN) | — (подставляется как `image_url`) |

Добавить в `.env` или `/etc/environment`:
```bash
OPENROUTER_API_KEY=sk-or-v1-<YOUR_KEY>
```

OpenRouter использует prepaid credit: пополнил баланс → тратится по цене за токены. Ни подписок, ни rate-лимитов по ключам с оплатой.

## Models & pricing

| Model ID | Назначение | Input | Output | Примерная цена за кадр | Скорость |
|----------|-----------|-------|--------|------------------------|----------|
| `google/gemini-2.5-flash-image` | **Nano Banana** — fast/budget, text2img и простой img2img | text, image | image | ~$0.003–0.005 | ~15–30 с |
| `google/gemini-3-pro-image-preview` | **Nano Banana Pro** — flagship, img2img с face consistency, multi-ref | text, image | image, text | ~$0.04–0.08 | ~40–90 с |

Выбор:
- **`gemini-3-pro-image-preview`** — когда критично сохранение лица через кадры (production portrait, серия для раскадровки).
- **`gemini-2.5-flash-image`** — черновики, A/B-тест промпта, b-roll без лица, массовый batch.

Цена зависит от output-токенов (картинка ≈ 3000–4000 output-токенов в Pro, ≈ 1300 в Flash).

## API endpoint

Единый endpoint для всех моделей OpenRouter, OpenAI-compatible:

```
POST https://openrouter.ai/api/v1/chat/completions
```

Headers:
```
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json
HTTP-Referer: <your_domain>   # опционально, для рейтинга в OpenRouter ленте
X-Title: geniriclaw            # опционально, имя приложения
```

## Payload — критические поля

**Обязательно** для image output добавить `"modalities": ["image", "text"]`, иначе модель вернёт только текст (описание вместо картинки).

### text2img

```json
{
  "model": "google/gemini-2.5-flash-image",
  "modalities": ["image", "text"],
  "messages": [
    {
      "role": "user",
      "content": "Wide cinematic shot of a mountain lake at sunrise, misty fog, 85mm lens, photorealistic, no people. Aspect ratio 16:9, 2K quality."
    }
  ]
}
```

### img2img с одним face REF

```json
{
  "model": "google/gemini-3-pro-image-preview",
  "modalities": ["image", "text"],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Using the same person from the reference image (same face, same features, consistent likeness): confident founder portrait in modern office, soft natural window light, wearing charcoal knit sweater, three-quarter angle, Sony A7R IV 85mm f/1.4, shallow depth of field, cinematic, natural skin texture with pores and micro imperfections, aspect ratio 3:4."
        },
        {
          "type": "image_url",
          "image_url": {"url": "<PUBLIC_FACE_REF_URL>"}
        }
      ]
    }
  ]
}
```

### img2img с двумя REF — person + scene / second person

```json
{
  "model": "google/gemini-3-pro-image-preview",
  "modalities": ["image", "text"],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Use the woman's face from the FIRST reference image and the man's face from the SECOND reference image. They stand together reviewing a monitor in a production studio. Use face ONLY from FIRST for the woman, face ONLY from SECOND for the man. Natural studio lighting, 35mm lens. Aspect ratio 16:9."
        },
        {"type": "image_url", "image_url": {"url": "<URL_FACE_1>"}},
        {"type": "image_url", "image_url": {"url": "<URL_FACE_2>"}}
      ]
    }
  ]
}
```

**Порядок `image_url` критичен** — первый = первое упомянутое в промпте лицо.

### Правила prompt'а при REF

- Явно пиши: `"same person from the reference image, consistent likeness, same face"`.
- **Не описывай черты лица** (цвет глаз, волос, форму лица) — модель берёт их из REF. Описывай только сцену, одежду, свет, позу, камеру.
- Для фотореалистичности подмешай `"natural skin texture with pores and micro imperfections, not airbrushed, no CGI, photorealistic"`.
- Aspect ratio и качество указывай **в тексте промпта** (`"aspect ratio 3:4, 2K"`) — у Gemini Image нет отдельных полей `aspectRatio`/`imageSize` в payload.

### Aspect ratios (пишутся текстом в prompt)

| Соотношение | Применение |
|-------------|------------|
| `3:4` | Портреты, studio headshots |
| `9:16` | Вертикаль для соцсетей (Reels, Shorts, VK Clips) |
| `1:1` | Обложки, квадраты для профилей |
| `16:9` | Горизонтальные баннеры, thumbnails, YouTube |
| `4:3` | Классическое фото |

## Response format

Ответ — стандартный OpenAI chat completion, но в `message` появляется поле `images` с массивом base64-data-URL:

```json
{
  "id": "gen-...",
  "model": "google/gemini-3-pro-image-preview",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<optional text>",
        "images": [
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
            }
          }
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 812, "completion_tokens": 3584, "total_tokens": 4396}
}
```

Распарсить base64 → сохранить в PNG/JPEG файл.

## Config placeholders

| Placeholder | Что это | Где задать |
|-------------|---------|------------|
| `{{OPENROUTER_API_KEY}}` | Bearer-токен OpenRouter | `.env` / `/etc/environment` |
| `{{PUBLIC_FACE_REF_URL}}` | URL на реальное фото (JPEG/PNG) | в payload `image_url.url` |
| `{{TARGET_ASPECT_RATIO}}` | `3:4`, `9:16`, `1:1`, `16:9` | пишется текстом в prompt |
| `{{OUTPUT_DIR}}` | Куда сохранять скачанные картинки | в скрипте (по умолчанию `workspace/output/`) |

## Minimal working script

```python
#!/usr/bin/env python3
"""nano_banana_openrouter_generate.py — один кадр через OpenRouter и сохранить PNG."""
import base64
import json
import os
import urllib.request

API_KEY = os.environ["OPENROUTER_API_KEY"]
PUBLIC_REF = os.environ.get("FACE_REF_URL", "").strip()  # пустая строка = text2img
MODEL = os.environ.get("NB_MODEL", "google/gemini-3-pro-image-preview")
PROMPT = os.environ.get(
    "NB_PROMPT",
    "Confident founder portrait in a modern office, soft natural window light, "
    "charcoal knit sweater, three-quarter angle, Sony A7R IV 85mm f/1.4, "
    "shallow depth of field, cinematic, natural skin texture with pores, "
    "aspect ratio 3:4, 2K.",
)
OUTPUT = os.path.expanduser(
    os.environ.get("NB_OUTPUT", "~/.geniriclaw/workspace/output/generated.png")
)

def build_payload():
    if PUBLIC_REF:
        content = [
            {
                "type": "text",
                "text": (
                    f"Using the same person from the reference image "
                    f"(same face, consistent likeness). {PROMPT}"
                ),
            },
            {"type": "image_url", "image_url": {"url": PUBLIC_REF}},
        ]
    else:
        content = PROMPT
    return {
        "model": MODEL,
        "modalities": ["image", "text"],
        "messages": [{"role": "user", "content": content}],
    }

def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(build_payload()).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://geniriclaw.local",
            "X-Title": "geniriclaw-image-gen",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        body = json.loads(r.read())

    try:
        images = body["choices"][0]["message"]["images"]
    except (KeyError, IndexError):
        raise SystemExit(
            "No image in response. Убедись что включил modalities=['image','text'].\n"
            f"Response: {json.dumps(body, indent=2, ensure_ascii=False)[:800]}"
        )

    data_url = images[0]["image_url"]["url"]
    b64 = data_url.split(",", 1)[1]
    with open(OUTPUT, "wb") as f:
        f.write(base64.b64decode(b64))
    usage = body.get("usage", {})
    print(f"saved: {OUTPUT}  tokens: {usage}")

if __name__ == "__main__":
    main()
```

## curl — ручной тест одной команды

```bash
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash-image",
    "modalities": ["image", "text"],
    "messages": [
      {"role": "user", "content": "Cinematic mountain lake at sunrise, misty fog, no people, 16:9"}
    ]
  }' | python3 -c "
import json, sys, base64, pathlib
r = json.load(sys.stdin)
url = r['choices'][0]['message']['images'][0]['image_url']['url']
pathlib.Path('/tmp/out.png').write_bytes(base64.b64decode(url.split(',', 1)[1]))
print('saved /tmp/out.png, tokens:', r.get('usage'))
"
```

## Rules

- **Никогда** не ставь свои прошлые AI-рендеры в REF — лицо «поплывёт». REF — только оригинальные фото.
- **Один** face-REF = одно лицо в выходе. Два `image_url` — первый для первого упомянутого лица, второй либо второе лицо, либо сцена без лица.
- При retry сохраняй **тот же** seed/promptpack в `promptpack.yaml` (см. skill `learning-loop`) — чтобы правки были воспроизводимы.
- Перед production серией сделай 1–2 черновика на `gemini-2.5-flash-image` (дешёво), шлифуй prompt, потом final batch через `gemini-3-pro-image-preview`.
- Gemini Image НЕ принимает параметры `aspectRatio` / `imageSize` как отдельные поля — пиши размер в тексте промпта.
- REF-фото должны быть **публично доступны** по URL (not pre-signed с коротким TTL, иначе модель может не успеть загрузить). Или передавай data URL `data:image/jpeg;base64,...` — тоже работает.

## Troubleshooting

| Симптом | Причина | Решение |
|---------|---------|---------|
| В ответе только текст, нет `images` | Не указан `modalities` | Добавить `"modalities": ["image", "text"]` |
| В результате случайное лицо | REF-URL недоступен / Gemini не смог загрузить | Проверить URL в браузере, или передавать base64 data URL |
| HTTP 401 `"No auth credentials found"` | Неверный/отсутствующий Bearer | `echo $OPENROUTER_API_KEY` — должен быть `sk-or-v1-...` |
| HTTP 402 `"insufficient credits"` | Баланс OpenRouter на нуле | Пополнить на [openrouter.ai/credits](https://openrouter.ai/credits) |
| HTTP 429 | Rate limit (редко) | Retry через 10–30 с |
| `safety block` / `content policy` | Модель отказалась (NSFW / политика Google) | Переформулировать prompt, убрать триггеры |
| Картинка размыта / 768×1024 | Flash-модель, низкий детализатор | Переключить на `gemini-3-pro-image-preview` |
| Лицо похоже, но не точное | Prompt описывает черты лица (цвет глаз, форму) | Убрать описание лица — модель берёт из REF, не дублируй |

## Env setup snippet (для CLAUDE.md или AGENT.md)

Добавь в `~/.zshrc` / `~/.bashrc` / `/etc/environment`:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

Проверить:
```bash
curl -sS https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | python3 -m json.tool
# должно вернуть {"data": {"label": "...", "usage": 0, "limit": null}}
```

## References

- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) — общая документация API
- [google/gemini-3-pro-image-preview](https://openrouter.ai/google/gemini-3-pro-image-preview) — Nano Banana Pro model card
- [google/gemini-2.5-flash-image](https://openrouter.ai/google/gemini-2.5-flash-image) — Nano Banana Flash model card
- [OpenRouter — Image Generation](https://openrouter.ai/docs/features/multimodal/image-generation) — официальные доки по image generation
- Related skills: `kling-i2v-transition` (анимация результатов в видео), `storyboard-designer` (batch-рендер для раскадровок), `learning-loop` (обратная связь по prompt'ам), `publisher-site` (хостинг face-REF URL)

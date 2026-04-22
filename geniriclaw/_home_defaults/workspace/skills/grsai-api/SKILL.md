# grsai-api — генерация изображений через GRSAI

> **Status:** stable
> **Category:** content-production · image-generation
> **Depends on:** `GRSAI_API_KEY` (env), `curl` / `requests`

## Purpose

Обёртка над API `api.grsai.com` (модели семейства `nano-banana`) для генерации статичных изображений: портреты, b-roll, сцены, художественные концепты. Поддерживает **img2img с face-reference** (character consistency) и **text2img**.

## When to use

- Нужен кадр с конкретным лицом — img2img по `image_input` (ссылка на REF-фото).
- Нужен кадр без персонажа — text2img по одному только `prompt`.
- Нужен batch-рендер раскадровки перед I2V.
- Бюджет малый и скорость важнее максимального качества (< $0.012 / кадр).

Если нужны 3D-сцены, композиции с множеством персонажей или специфичные стили — рассмотреть `replicate` с Flux/SDXL, `krea` для фотореалистичных портретов.

## Prerequisites

| Что | Где получить | Переменная окружения |
|-----|--------------|----------------------|
| API key | [api.grsai.com](https://api.grsai.com) — регистрация, подтверждение email | `GRSAI_API_KEY` |
| Публичный URL для face REF | любой статический хостинг (собственный домен, S3, CDN) | — (подставляется в prompt) |

Добавить в `.env`:
```bash
GRSAI_API_KEY=<YOUR_GRSAI_KEY>
```

## Models & pricing

| Модель | Цена за кадр | Время | Use case |
|--------|--------------|-------|----------|
| `nano-banana-fast` | ~$0.003 | ~30 с | Быстрый черновик, A/B-тест промпта |
| `nano-banana-2` | ~$0.010 | ~60–90 с | Дефолт для большинства кадров |
| `nano-banana-pro` | ~$0.012 | ~90 с | Production, face-consistency через REF |

Выбор: `pro` когда критично сохранение лица, иначе `2`.

## API endpoints

| Операция | URL | Метод |
|----------|-----|-------|
| Create task | `https://api.grsai.com/v1/draw/nano-banana` | POST |
| Poll result | `https://api.grsai.com/v1/draw/result` | POST |

Auth: `Authorization: Bearer $GRSAI_API_KEY`.

## Payload — критические поля

```json
{
  "model": "nano-banana-pro",
  "prompt": "<your prompt>",
  "aspectRatio": "3:4",
  "imageSize": "2K",
  "webHook": "-1",
  "image_input": ["<PUBLIC_FACE_REF_URL>"]
}
```

### Правила заполнения (частые ошибки)

| Поле | Правило | Частая ошибка |
|------|---------|---------------|
| `image_input` | **Массив URL**, не `urls`. Пустой при text2img. | `"urls": []` — поле не существует |
| `webHook` | **camelCase с большой H**, значение `"-1"` для polling | `"webhook"` — lowercase не работает |
| `aspectRatio` | **camelCase**, не `aspect_ratio` | snake_case игнорируется |
| `imageSize` | `"1K"` / `"2K"` / `"4K"` (camelCase) | Цифры без суффикса не принимаются |
| `prompt` + REF | Если упоминаешь "FIRST/SECOND reference" — `image_input` обязан содержать соответствующее число URL в правильном порядке | Пустой массив при упоминании REF → модель рисует случайное лицо |

### Aspect ratios

| `aspectRatio` | Применение |
|---------------|------------|
| `3:4` | Портреты, studio headshots |
| `9:16` | Вертикаль для соцсетей (Reels, Shorts, VK Clips) |
| `1:1` | Обложки, квадраты для профилей |
| `16:9` | Горизонтальные баннеры, thumbnails |
| `4:3` | Классическое фото |

## Usage modes

### 1. text2img — без REF

Для первичных генераций, b-roll, общих сцен.

```json
{
  "model": "nano-banana-2",
  "prompt": "Wide cinematic shot of a mountain lake at sunrise, misty fog, 85mm lens, photorealistic, no people",
  "aspectRatio": "16:9",
  "imageSize": "2K",
  "webHook": "-1"
}
```

### 2. img2img с одним face REF — character consistency

Для портретов конкретного человека.

```json
{
  "model": "nano-banana-pro",
  "prompt": "Same person from FIRST reference image, same facial features, confident founder portrait in modern office, soft natural window light, wearing charcoal knit sweater, three-quarter angle, Sony A7R IV 85mm f/1.4, shallow depth of field, cinematic, natural skin texture",
  "aspectRatio": "3:4",
  "imageSize": "2K",
  "webHook": "-1",
  "image_input": ["<PUBLIC_FACE_REF_URL>"]
}
```

**Правила prompt'а при REF:**
- `Same person/woman/man from FIRST reference image, consistent likeness, same person`
- **Не описывай черты лица** (цвет глаз, волос) — модель берёт их из REF. Описывай только сцену, одежду, свет, позу.
- Для likeness подмешай `natural skin texture with pores and micro imperfections, not airbrushed, no CGI`.

### 3. img2img с двумя REF — person + scene/second person

```json
{
  "image_input": [
    "<URL_FACE_1>",
    "<URL_FACE_2_or_SCENE>"
  ],
  "prompt": "Same woman from FIRST reference image (face, features). Same man from SECOND reference image (face, features). They stand together reviewing a monitor in a production studio. Use face ONLY from FIRST for woman, face ONLY from SECOND for man. ..."
}
```

**Порядок URL критичен:** первый = первое упомянутое в промпте лицо.

## Polling

После `Create task` → получишь `{"id": "3-abc123..."}`. Каждые ~3 с опрашивай:

```json
POST /v1/draw/result
{"id": "3-abc123..."}
```

Status: `running` → `succeeded` | `failed` | `error`.
При `succeeded` — `data.results[0].url` = итоговая картинка (короткоживущий URL, скачать сразу).

Max polling: ~60 попыток (3 мин).

## Config placeholders

| Placeholder | Что это | Где задать |
|-------------|---------|------------|
| `{{GRSAI_API_KEY}}` | Bearer-токен API | `.env` / `/etc/environment` |
| `{{PUBLIC_FACE_REF_URL}}` | URL на реальное фото (JPEG/PNG) | в payload `image_input` |
| `{{TARGET_ASPECT_RATIO}}` | `3:4`, `9:16`, `1:1`, `16:9` | в payload `aspectRatio` |
| `{{OUTPUT_DIR}}` | Куда сохранять скачанные картинки | в скрипте (по умолчанию `workspace/output/`) |

## Minimal working script

```python
#!/usr/bin/env python3
"""grsai_generate.py — создать один кадр и скачать результат."""
import json, os, subprocess, time, urllib.request

API_KEY = os.environ["GRSAI_API_KEY"]
PUBLIC_REF = os.environ.get("FACE_REF_URL", "")  # пустая строка = text2img
PROMPT = "Professional portrait in a studio, soft key light, 85mm lens, natural skin texture"
OUTPUT = os.path.expanduser("~/.geniriclaw/workspace/output/generated.png")

def post(url, payload):
    p = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-X", "POST", url,
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {API_KEY}",
         "-d", json.dumps(payload)],
        capture_output=True, text=True)
    return json.loads(p.stdout)

payload = {
    "model": "nano-banana-pro",
    "prompt": PROMPT,
    "aspectRatio": "3:4",
    "imageSize": "2K",
    "webHook": "-1",
}
if PUBLIC_REF:
    payload["image_input"] = [PUBLIC_REF]

r = post("https://api.grsai.com/v1/draw/nano-banana", payload)
if r.get("code") != 0:
    raise SystemExit(f"create failed: {r}")
task_id = r["data"]["id"]
print(f"task: {task_id}")

for _ in range(60):
    time.sleep(3)
    pr = post("https://api.grsai.com/v1/draw/result", {"id": task_id})
    status = pr.get("data", {}).get("status")
    if status == "succeeded":
        url = pr["data"]["results"][0]["url"]
        urllib.request.urlretrieve(url, OUTPUT)
        print(f"saved: {OUTPUT}")
        break
    if status in ("failed", "error"):
        raise SystemExit(f"generation failed: {pr}")
```

## Rules

- **Никогда** не ставь свои прошлые AI-рендеры в `image_input` как REF — лицо «поплывёт». REF — только оригинальные фото.
- **Одна** лицо-REF = одно face в выходе. Два URL — первый для первого упомянутого лица, второй либо второе лицо, либо сцена без лица.
- При retry сохраняй **тот же** seed/promptpack в `promptpack.yaml` (см. skill `learning-loop`) — чтобы правки были воспроизводимы.
- Проверяй реальный размер выхода (PNG header) — иногда `2K` отдаёт 1K (половина). Если мельче — перегенерируй.

## Troubleshooting

| Симптом | Причина | Решение |
|---------|---------|---------|
| В результате случайное лицо | Пустой `image_input` при упоминании REF в prompt | Заполнить `image_input` URLом |
| HTTP 401 | Неверный/отсутствующий `Authorization` | Проверить `$GRSAI_API_KEY` |
| Task застрял `running` >3 мин | Перегрузка провайдера | Отменить и запустить заново; или снизить модель до `nano-banana-2` |
| `safety block E005` | Модель отказалась (NSFW / политика) | Переформулировать prompt, убрать триггеры |
| Выход 768×1376 вместо 1536×2752 | Модель отдала `1K` вместо `2K` | Перегенерировать; упростить prompt |

## References

- [GRSAI API docs](https://api.grsai.com/docs) — официальная документация
- Related skills: `kling-i2v-transition` (анимация результатов в видео), `storyboard-designer` (batch-рендер для раскадровок), `learning-loop` (обратная связь по prompt'ам)

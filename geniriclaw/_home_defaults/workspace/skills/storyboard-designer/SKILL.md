# storyboard-designer — двухэтапная раскадровка (sketch → final)

> **Status:** stable
> **Category:** content-production · pre-production
> **Depends on:** `nano-banana-openrouter`, опционально `publisher-site` для HTML-дайджеста

## Purpose

Перед тратой $0.04–0.08/кадр на финальный рендер (Nano Banana Pro) — дешёво (~$0.003–0.005/кадр на Nano Banana Flash) прогнать раскадровку в sketch-mode, получить одобрение оператора, потом тратить на finals только то что одобрено.

## Workflow

```
Brief → storyboard.json → sketches (1K, fast) → HTML preview
  → operator feedback → adjust prompts → finals (2K, pro)
  → publish finals HTML
```

## Sketch mode — параметры генерации

### Prompt паттерн

Для sketch **лицо не важно** (не используем face REF — дешевле и быстрее):

```
Black and white pencil storyboard sketch, hand-drawn style,
clean line art, minimal shading, <scene description>,
<composition: wide/medium/close-up>, <action/mood>,
16:9 aspect ratio framing
```

### Параметры API (nano-banana-openrouter)

```json
{
  "model": "google/gemini-2.5-flash-image",
  "modalities": ["image", "text"],
  "messages": [
    {"role": "user", "content": "<sketch prompt with '16:9 aspect ratio, 1K' in text>"}
  ]
}
```

**Нет** `image_url` в content — sketch рисуется без face REF. Aspect ratio и качество пишутся **текстом в prompt**, не отдельными полями (у Gemini Image нет `aspectRatio`/`imageSize`).

### Стиль

Чёрно-белые pencil-style наброски. Задача — **проверить композицию и сюжет**, не detail. Цветные finals делаются после одобрения.

## Финальный mode

После одобрения sketches — те же промпты (с добавлением face REF и style-anchor):

```json
{
  "model": "google/gemini-3-pro-image-preview",
  "modalities": ["image", "text"],
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "<full color prompt with '9:16 aspect ratio, 2K' in text>"},
        {"type": "image_url", "image_url": {"url": "<FACE_REF_URL>"}}
      ]
    }
  ]
}
```

Prompt — цветной, детальный, с описанием света и стиля (см. `nano-banana-openrouter/SKILL.md`).

## storyboard.json — структурированный формат

```json
{
  "job_id": "{{JOB_ID}}",
  "duration_sec": 45,
  "aspect": "9:16",
  "shots": [
    {
      "id": "shot_01",
      "timing": "0:00–0:04",
      "composition": "wide establishing",
      "sketch_prompt": "Black and white storyboard sketch: wide shot of ...",
      "final_prompt": "<full color prompt with REF rules>",
      "has_face": true,
      "face_ref": "<FACE_REF_URL>",
      "motion_prompt": "<motion description for i2v>",
      "duration_sec": 4,
      "status": "pending"  // pending / sketched / approved / rendered / final
    },
    ...
  ]
}
```

## HTML preview

После батча sketches — автосгенерить HTML для оператора:

```html
<!DOCTYPE html>
<html><head><style>
  body{font-family:system-ui;background:#0a0a0a;color:#eee;padding:20px}
  .shot{border:1px solid #333;margin:20px 0;padding:15px}
  .shot img{max-width:100%;border-radius:4px}
  .prompt{font-family:monospace;font-size:13px;color:#aaa}
</style></head><body>
  <h1>Storyboard — {{JOB_ID}}</h1>
  <div class="shot">
    <h3>shot_01 · 0:00–0:04 · wide establishing</h3>
    <img src="sketches/shot_01.png" alt="shot_01">
    <div class="prompt">{{sketch_prompt}}</div>
  </div>
  ...
</body></html>
```

Опубликовать через `publisher-site` (см.) и отправить оператору ссылку.

## Approval workflow (Mode Control)

1. Создать `storyboard.json` → отправить оператору summary («10 shots, 45 сек, тема X, стиль Y»)
2. Дождаться подтверждения темы/направления
3. Запустить batch sketches (параллель 4 одновременно)
4. Собрать HTML preview, отправить ссылку
5. Оператор правит → обновить prompts
6. Повторить 3–5 до одобрения (обычно 1–2 итерации)
7. Запустить finals (параллель 3 одновременно, чтобы не упереться в rate-limit)
8. Собрать HTML финалов, отправить оператору с пометкой «finals, идём в i2v?»
9. После `go` → `video-pipeline` продолжает с i2v, voice, music, edit, publish

## Rules

- **Sketch mode всегда Nano Banana Flash** (`google/gemini-2.5-flash-image`) — задача проверить композицию, не detail. Тратить на sketches Pro-модель — перерасход.
- **Нет face REF в sketch** — без разницы кто на кадре, сюжет важнее.
- **Если оператор просит перерисовать shot** — перерисовывать sketch, не final. Обновлять final только когда sketch одобрен.
- Parallelism 4 одновременно на sketch, 3 — на final (OpenRouter рейт-лимит обычно либеральный, но Pro-модель медленнее — не перегружай).
- HTML preview **включает prompt под каждым shot'ом** — оператор видит что модель «понимает», может править семантику.

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{JOB_ID}}` | Slug ролика |
| `{{FACE_REF_URL}}` | (опц.) для finals с лицом |
| `{{ASPECT}}` | `9:16` / `16:9` / `3:4` |
| `{{STYLE_ANCHOR}}` | Блок prompt'а для единого стиля во всех shot'ах |

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| Sketches все похожи | Уточнить в каждом shot'е композицию (`tight close-up` vs `wide establishing`) и позу/действие |
| Finals не совпадают со sketches | В final prompt скопировать action-строку из sketch prompt'а, не переписывать |
| Оператор правит одни и те же shot'ы | Собрать style-anchor block, добавить во все shot'ы (см. skill `video-revision-pipeline`) |

## References

- Related: `nano-banana-openrouter`, `video-pipeline`, `video-revision-pipeline`, `publisher-site`

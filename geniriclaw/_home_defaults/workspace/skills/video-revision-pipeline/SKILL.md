# video-revision-pipeline — итеративные правки уже смонтированного ролика

> **Status:** stable
> **Category:** content-production · iteration
> **Depends on:** `video-pipeline`, `storyboard-designer`, `learning-loop`

## Purpose

Когда оператор присылает правки на готовый ролик (типа «поправь shot 03 и 06, shot 07 переснять в другом стиле»), нужно итеративно переделать только эти шоты, сохранив консистентность со всем роликом.

## When to use

- Ролик уже собран (v1 / v2), есть comment-лист правок от оператора.
- Нужно переделать 1–4 shot'а из 8–12, не тронув остальные.
- Важно сохранить единый визуальный стиль (свет, палитра, тон лица).

## Базовая проблема

**Naïve refresh** (перегенерация правленных кадров «с нуля») даёт **визуальный дрейф** — новые shot'ы выглядят чужеродно: другой свет, другая палитра, лицо немного иное. После склейки это бросается в глаза.

## Два обязательных контроллера

### 1. Промежуточные sketches — 2 варианта на каждый правленый shot

Перед финальной генерацией — **sketch-mode**:
- 2 варианта low-res (`1K`, `nano-banana-fast`)
- Оператор выбирает направление (вариант A или B)
- Только потом финальный `pro` 2K

Экономия: если направление неверное, тратим $0.006 на sketches вместо $0.024 на финал.

### 2. Style anchor (визуальный ключ)

Чтобы v2 не плыл от v1, используется 3 уровня anchor'а:

#### A. Style anchor prompt (вшивается в каждый shot с человеком)

```
<scene description>, <action>, consistent visual style with previous shots:
muted teal-orange cinematic grading, natural skin texture with visible pores,
Sony A7R IV 85mm f/1.4, shallow depth of field, soft key light,
documentary cinematic aesthetic, matching atmosphere of base storyboard
```

Этот фрагмент **идентичен** во всех shot'ах ролика → модель воспроизводит одинаковый визуальный тон.

#### B. Face & style REFs (в `image_input`)

```yaml
image_input:
  - "<face_ref_url>"           # канонический портрет персонажа
  - "<previous_shot_url>"      # один из уже одобренных финальных shot'ов (для стиля)
```

Второй REF — это **«якорь»**: модель смотрит на цветовую гамму, текстуры, глубину резкости одобренного shot'а.

#### C. Что НЕ требует style anchor

- B-roll без людей (природа, объекты, абстракция) — достаточно style prompt
- Опенер / логотип / титры — собственный стиль
- Кадры где нужен дрейф нарочно (dream sequence, flash-back)

#### D. Запрет на дрейф

Если замечаешь что v2-кадр визуально сильно отличается от одобренных — **не принимать**, перегенерировать с усиленным anchor'ом.

## Workflow

```
1. Collect revision comments         → revision.md (slug = date + shot_ids)
2. Lock approved shots               → shots_approved/ (не трогать)
3. For each revision:
   a. Read original prompt           → prompts/shot_NN/base.yaml
   b. Apply revision patch           → prompts/shot_NN/v2.yaml
   c. Generate 2 sketches (1K)       → drafts/<job>/sketches/shot_NN/
   d. Operator picks A or B
   e. Generate final (2K pro)        → drafts/<job>/shots_v2/shot_NN.png
   f. QA against style anchor        → reject if drift visible
4. Regenerate i2v for changed shots  → videos_v2/shot_NN.mp4
5. Re-concat final video             → build/final_v2.mp4
6. Publish, записать в revision.md
```

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{JOB_ID}}` | slug ролика (тот же что в v1) |
| `{{REVISION_ID}}` | `v2`, `v3`, ... |
| `{{APPROVED_SHOT_URL}}` | URL shot'а из v1 (используется как style anchor) |
| `{{REVISION_COMMENTS}}` | текст от оператора (список правок) |

## Rules

- **Правка одного shot'а НЕ оправдание для перегенерации соседних** — оставить то что одобрено.
- **style anchor обязателен** для портретных шотов. Без него консистентность ломается на 3-й итерации.
- Sketches всегда 2 (не 1, не 3). Два — достаточно для выбора направления, три — избыточность.
- Sketch-to-final ratio: 90% одобрений достаточно → идти в final, 10% правок → перегенерировать sketch (не final).
- После v3-v4 — если всё ещё дрейф, проблема в base prompt'е, не в правках. Обновить style anchor.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| v2 лицо другое, хотя face REF тот же | Добавить второй REF = одобренный shot; усилить `same facial features, same age, same hairline` |
| v2 цветокор резко отличается | Скопировать style block из одобренных shot'ов byte-to-byte, не переписывать своими словами |
| Sketches все одинаковые | Вариативность в prompt'е мала — явно разделить: «A: tight closeup / B: wide establishing» |
| После 4 ревизий промпт превратился в спагетти | Консолидировать — вынести общий style в `styleanchor.md`, в prompt оставить только дельту |

## References

- Related: `video-pipeline`, `storyboard-designer`, `grsai-api`, `kling-i2v-transition`, `learning-loop`

# learning-loop — обратная связь и обновление промптов по результатам

> **Status:** stable
> **Category:** meta · continuous-improvement

## Purpose

Превращать реальные правки оператора в обновлённые промпты/скилы/примеры — чтобы **следующая** генерация учла урок с первого раза, а не повторяла ту же ошибку.

## When to use

- Ролик вышел, оператор написал правки/метрики.
- Серия кадров была отвергнута → нужно обновить prompt-pack.
- Появился новый паттерн «X не работает, работает Y» → хочется зафиксировать.
- Раз в неделю — свести daily memory в курированный `MAINMEMORY.md`.

## Принцип

Учиться **из факта**, не из мнений. Реальные правки оператора > предположения. Ошибка однажды → патч правил, чтобы не повторить.

## Цикл

```
1. Factual verdict  — что реально произошло (accepted/rejected и почему)
2. Pattern extraction  — что из этого общий паттерн, не частный случай
3. Update EXAMPLES.md / prompt-packs  — добавить negative example + positive
4. Validate  — следующий batch проходит без этой ошибки
```

## Шаг 1. Вердикт (factual)

Для каждого артефакта (кадр / ролик / пост) собрать:

```yaml
artifact: shots/shot_03_v2.png
verdict: rejected
operator_comment: "slow motion должно быть внутри душа, а не снаружи; камера слишком далеко"
root_cause: prompt_ambiguity  # не bug, а неточная формулировка
patch_target: prompts/shot_03/base.yaml
patch_type: camera_distance_explicit
```

Verdict'ы:
- `accepted` — оператор одобрил без правок
- `accepted_with_notes` — одобрил но есть пожелания на следующий раз
- `rejected_minor` — правка на том же shot'е (1 итерация)
- `rejected_major` — полный reshoot (direction или стиль иной)
- `rejected_safety` — модель заблокировала (NSFW, deepfake и пр.)

## Шаг 2. Извлечение паттернов

Из 10 verdict'ов — найти **общее**. Примеры реальных паттернов (из накопленного опыта):

### Pattern: «cold shower ≠ steam»

**Симптом:** prompt «cold shower» генерит steam/fog (модель ассоциирует «душ» с тёплой водой).
**Фикс:** явно прописать:
```
NO STEAM, NO HOT VAPOR, NO FOG. Cold shower, crisp clean air, cool blue-cyan rim light.
```

### Pattern: «in the shower ≠ under shower head»

**Симптом:** prompt «in the shower» ставит фигуру **рядом** с душем, не в струе.
**Фикс:**
```
directly UNDER the shower head, tight crop on shoulder, camera is close,
he fills the frame, not beside the shower, not far from it
```

### Pattern: «likeness drift в casual портретах»

**Симптом:** при описании «after shower / after workout» модель рисует **идеализированного 30-летнего** с прессом, теряет возраст и черты реального субъекта.
**Фикс:** 2–3 face REF (вместо одного) + явные параметры:
```
age 45-50, real hairline, natural grey-blond hair, mixed grey-brown stubble,
wearing T-shirt (not bare chest), no accented abs, no bodybuilder body
```

### Pattern: «energy = posture, not face»

**Симптом:** prompt «energized, strong» + описание позы как «casual by the wall» → модель рисует **слабую** фигуру.
**Фикс:** явная поза:
```
standing tall, chin up, shoulders squared, center of frame,
not leaning on any wall, not slouching
```

### Pattern: «2K output размер не гарантирован»

**Симптом:** `imageSize=2K` иногда отдаёт 768×1376 (половина).
**Фикс:** после каждого shot проверять реальный размер через PNG header:
```python
import struct
with open(path, "rb") as f:
    f.seek(16)
    w, h = struct.unpack(">II", f.read(8))
    if w < 1024:
        print(f"BAD: only {w}×{h}, regenerate")
```

## Шаг 3. Обновление EXAMPLES.md

Каждый L2-агент имеет `agents/<name>/EXAMPLES.md` — позитивные и негативные примеры. После каждого learning-cycle — дописывается:

```markdown
## Example: shot with "after cold shower" feel

### ❌ Was (rejected)
prompt:
```
Portrait of a man after a cold shower, energized, strong, confident.
```
issue: generated idealized 30yo bodybuilder, lost likeness.

### ✅ Fixed
prompt:
```
Portrait of a 45-50 year old man from FIRST reference image,
standing tall, chin up, shoulders squared, wearing henley t-shirt,
water droplets on shoulders (no steam), cool blue-cyan rim light,
natural skin texture with visible pores, real hairline,
mixed grey-brown stubble.
```
ref: drafts/<job>/shots/shot_07_v3_after_shower_henley.png
```

Этот EXAMPLES.md читается агентом при формировании prompt'а для похожей задачи в будущем.

## Шаг 4. Validate

Перед закрытием learning-cycle — прогнать batch с новыми prompt'ами на **исторических** задачах (где раньше была ошибка). Если ошибка не повторилась — патч принят. Если повторилась — patch недостаточен, ищем что ещё.

## Когда запускать

- **После каждой публикации** — через 24 часа собрать метрики + operator comments → апдейт.
- **После rejected-round** (серия отказов внутри одной итерации) — немедленно.
- **Раз в неделю** — сводка daily memory в MAINMEMORY.md.
- **Перед новым проектом** — перечитать EXAMPLES.md релевантных агентов.

## Input / Output

Вход:
- `workspace/memory/<YYYY-MM-DD>.md` — daily log
- `drafts/<job>/revision.md` — комментарии оператора
- `published/<job>/metrics.json` — метрики (views, reactions)

Выход:
- Обновлённые `agents/<name>/EXAMPLES.md`
- Обновлённые `agents/<name>/promptpack.yaml`
- Запись в `MAINMEMORY.md` — сводка lessons

## Rules

- Factual > opinion. Только реальные verdict'ы оператора, не «я думаю что».
- Один урок — один патч. Не запихивать 10 правил в один commit.
- Negative example обязателен — показать что было не так, иначе следующий раз повторится.
- Не создавать новые скиллы из разовых правок — ждать **3+** повторений того же паттерна.
- Lessons пишутся **как проверяемые правила**, не как абстракции («использовать cool rim light» плохо, «добавить `cool blue-cyan rim light` в prompt для холодных сцен» хорошо).

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| EXAMPLES.md разрастается до 10 MB | Сгруппировать по темам в подсекции; вынести старые в `archive/` |
| Lessons конфликтуют между собой | Новый lesson обычно умнее старого — удалить/переписать старый |
| Ошибка повторилась после патча | Патч недостаточен — нужен более сильный constraint (попробовать negative prompt expansion) |

## References

- Related: `video-revision-pipeline`, `storyboard-designer`, `grsai-api`
- Best practice: «one rejected result = one lesson extracted = one prompt update»

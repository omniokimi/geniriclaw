# directors-cut-pipeline — режиссёрская склейка с операторскими переходами

> **Status:** stable
> **Category:** content-production · video-editing
> **Depends on:** `kling-i2v-transition`, ffmpeg

## Purpose

Превращает набор из 6–20 готовых коротких шотов (i2v клипов) в связный director's-cut с плавными операторскими переходами между сценами.

## When to use

Когда есть серия уже сгенерированных i2v-клипов, но между ними **чувствуется "монтажный шов"** — hard cut, резкое изменение освещения, несовпадение движения камеры. Director's cut сглаживает это через **transitions** — короткие (1–2 с) связующие клипы сгенерированные специально.

## Pipeline (6 шагов)

### 1. Inventory — собрать все исходники

```bash
ls drafts/<job>/videos/*.mp4 | sort > /tmp/shots_list.txt
```

Для каждого: длительность, resolution, framerate — должны совпадать (иначе нормализовать через ffmpeg).

### 2. Extract boundary frames

Из каждой пары соседних шотов вытянуть последний кадр первого и первый кадр второго:

```bash
# shot_01 last frame
ffmpeg -sseof -0.1 -i shots/shot_01.mp4 -vframes 1 -q:v 2 boundaries/01_last.jpg

# shot_02 first frame
ffmpeg -i shots/shot_02.mp4 -vframes 1 -q:v 2 boundaries/02_first.jpg
```

### 3. Design transition map

Для каждой пары (N, N+1) — определить тип перехода:

| Тип | Когда |
|-----|-------|
| `hard-cut` | Контрастное переключение сцены/тона — оставить как есть |
| `morph` | Плавный переход через kling с `start_image=last` и `end_image=next_first` |
| `motion-bridge` | Переход через движение камеры (push-out → push-in в следующую сцену) |
| `match-cut` | Совпадение по форме/цвету между кадрами — оставить hard-cut |

Записать в `transitions_map.yaml`:

```yaml
transitions:
  - from: shot_01
    to: shot_02
    type: morph
    duration: 2
    prompt: "Camera smoothly drifts from <describe last frame scene> to <next frame scene>, consistent lighting, natural transition"
  - from: shot_02
    to: shot_03
    type: hard-cut
```

### 4. Submit transitions в параллель

Запустить kling batch по `type == morph` (см. skill `kling-i2v-transition`):

```python
for tr in transitions_map:
    if tr["type"] == "morph":
        submit_kling(
            start=boundaries[f"{tr['from']}_last.jpg"],
            end=boundaries[f"{tr['to']}_first.jpg"],
            prompt=tr["prompt"],
            duration=tr["duration"],
            output=f"transitions/{tr['from']}_to_{tr['to']}.mp4",
        )
```

Параллелизм 3–4 одновременно.

### 5. Concat — trim main shots + insert transitions

Важно: transition занимает последние K секунд первого shot'а + первые K секунд второго. Поэтому main shots **тримируются** (удаляется K/2 секунд с каждой стороны где идёт transition).

```bash
# Пример concat-списка для ffmpeg concat demuxer
# shot_01 (trim -1s) → transition_01_to_02 (2s) → shot_02 (trim both sides) → ...
cat > concat.txt <<EOF
file 'shots/shot_01_trimmed.mp4'
file 'transitions/shot_01_to_shot_02.mp4'
file 'shots/shot_02_trimmed.mp4'
file 'transitions/shot_02_to_shot_03.mp4'
...
EOF

ffmpeg -f concat -safe 0 -i concat.txt -c copy final.mp4
```

### 6. Audio re-sync

После добавления transitions длительность изменилась — voice-over и music нужно re-sync:

```bash
ffmpeg -i final.mp4 -i voice.wav -i music.mp3 \
    -filter_complex "[1:a][2:a]amix=inputs=2:duration=longest[a]" \
    -map 0:v -map "[a]" -c:v copy final_with_audio.mp4
```

## Transition library (готовые паттерны)

| Имя | Prompt base | Duration |
|-----|-------------|----------|
| `water-flow-morph` | "Water streams naturally transitioning from <A> to <B>" | 2с |
| `push-to-detail` | "Camera slowly pushes in from wide shot to detail of <subject>" | 1–2с |
| `lighting-shift` | "Light gradually shifts from <A lighting> to <B lighting>, subject remains in frame" | 2с |
| `location-walk` | "Subject walks through doorway from <location A> to <location B>" | 3с |
| `slow-reveal` | "Camera pans up from ground detail to full scene of <B>" | 2с |

## Config placeholders

| Placeholder | Что это |
|-------------|---------|
| `{{JOB_ID}}` | Slug ролика |
| `{{SHOTS_DIR}}` | Путь к папке с исходными i2v-клипами |
| `{{TRANSITIONS_MAP_PATH}}` | YAML с описанием переходов |
| `{{OUTPUT_FINAL}}` | Путь к final.mp4 |

## Rules

- Не делай morph-transition между **радикально** разными сценами (ночь → день, интерьер → бассейн) — получится waterworld-артефакт. В таких точках — честный hard-cut с музыкальным акцентом.
- Длительность transition ≤ 2с — дольше выглядит затянуто. 10-секундные morph бывают кинематографично, но дорого.
- **Правило I2V-оператора**: все motion — внутри promt'а kling. ffmpeg только concat, trim, audio. См. skill `kling-i2v-transition`.
- Audio sync проверять визуально (не по длительности). Если voice должен идти на shot_05, а он теперь сдвинулся на 4.5с — выровнять smart (не компрессией audio).

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| Transition выглядит «рваным» (jump) | Проверить что start_image = **точно** последний кадр первого shot'а, не случайный |
| Лицо в transition «плывёт» | Duration 2с → 1с; добавить `subject remains in same position` в prompt |
| После concat звук съехал | Рассчитать суммарную длительность с transitions, re-align audio через `atrim` / `adelay` |
| Цвет в transition другой | В prompt вписать `matching cinematic grade, teal-orange tint consistent with both shots` |

## References

- Related: `video-pipeline`, `kling-i2v-transition`, `storyboard-designer`

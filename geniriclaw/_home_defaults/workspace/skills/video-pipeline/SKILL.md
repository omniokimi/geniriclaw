# video-pipeline — end-to-end сборка короткого видеоролика

> **Status:** stable
> **Category:** content-production · orchestration
> **Depends on:** `grsai-api`, `kling-i2v-transition`, `storyboard-designer`, `publisher-site`

## Purpose

Полная последовательность от бриф → опубликованный ролик: script → storyboard → images → video shots → voice → music → montage → publish. Ориентирован на вертикальный short-form контент (Reels/Shorts/TikTok, 9:16, 30–60 с).

## When to use

Когда приходит бриф «сделай ролик про X для Y». Активирует серию L2-ролей (см. `agents/` рядом): scriptwriter → storyboarder → prompt-engineer → image-gen → video-gen → voice-over → music-scoring → editor → publisher-multi → metrics-tracker.

## Pipeline (9 этапов)

```
1. Brief parsing       → topic, target platforms, duration, style
2. Script (scriptwriter)  → 30–60с текст, hooks, CTA
3. Storyboard (storyboarder) → 6–12 shots с описанием
4. Prompt engineering  → image+motion prompts + negative prompts
5. Image generation    → grsai-api / replicate (batch параллель)
6. Image → Video       → kling-i2v-transition (параллель, 3-4 одновременно)
7. Voice-over          → ElevenLabs / OpenAI TTS
8. Music scoring       → Suno / library track
9. Editor + Publisher  → ffmpeg concat + publisher-multi (TG/IG/TikTok/VK)
```

## Retry / fallback policy

**Принцип `fallback-first, autopilot-by-default, downgrade-before-stop`:**

- Если **image-gen провалился** → 1 retry с упрощённым prompt; не получилось → понизить модель (`pro` → `2` → `fast`); не получилось → помечаем shot как `still` и идём дальше.
- Если **i2v провалился** → 1 retry с `minimal motion` prompt; не получилось → оставляем still image на длительность shot'а (concat как statischen клип через ffmpeg).
- Если **voice/music провалился** → продолжаем без (silent preview), эскалируем оператору.
- Блокер эскалируется **только** когда результат без него нельзя собрать вообще.

## Parallelism policy

| Этап | Параллелизм | Почему |
|------|-------------|--------|
| Image generation | 4–6 одновременно | GRSAI rate-limit ~10/мин |
| I2V Kling | 3–4 одновременно | Replicate fair-use |
| Voice segments | 2–3 | ElevenLabs rate-limit |
| FFmpeg | 1 (последовательно) | CPU-bound |

## Execution discipline

**После каждого planning-шага обязателен `NEXT_EXECUTABLE_STEP`** — запуск скрипта/subprocess с доказательством (pid/session_id/file_path/url). См. skill `plan-to-action-bridge`.

**Сначала 100% ближайшего логического результата, потом правки** — не ждать промежуточных апрувов на часть кадров. Собрать весь комплект finals → принять правки одним проходом.

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{BRIEF}}` | Входной запрос оператора |
| `{{FACE_REF_URL}}` | Публичный URL face REF (если ролик с лицом) |
| `{{TARGET_PLATFORMS}}` | `telegram,instagram,tiktok,vk` |
| `{{DURATION_SEC}}` | Общая длительность, обычно 30–60 |
| `{{ASPECT_RATIO}}` | `9:16` дефолт |
| `{{JOB_ID}}` | Уникальный slug для папки `drafts/<job_id>/` |

## Output structure

```
workspace/drafts/{{JOB_ID}}/
├── brief.md                   # raw brief + parsed parameters
├── script.md                  # финальный текст
├── storyboard.json            # структурированная раскадровка
├── prompts/                   # image+motion prompts, negative prompts
├── shots/                     # PNG — финальные кадры после QA
├── videos/                    # MP4 — i2v-клипы по каждому shot'у
├── audio/                     # voice-over.wav, music.mp3
├── build/                     # final.mp4 + промежуточные concat-файлы
└── published.json             # URL'ы публикаций, message_ids, метрики
```

## Rules

- **I2V оператор** (см. `kling-i2v-transition`): движение камеры — только через `motion_prompt` модели. ffmpeg НЕ имитирует push-in / orbit / handheld через math-выражения.
- **Face consistency**: 1 face-REF = 1 лицо. В img2img с лицом используется ТОЛЬКО оригинальное фото, не собственные AI-генерации.
- **Delivery-check**: после публикации — подтверждение по Message ID / реакции / явному ответу; нет подтверждения → короткий resend.
- **Learning-loop** (см. skill): после успешной публикации, через 24 часа — собираем метрики, обновляем promptpack под разделы (likeness, lighting, motion) по факту что сработало.

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| Лицо "плывёт" между шотами | Упростить scene-prompt, добавить 2–3 face REF, прописать возраст/одежду явно, запретить bare chest / accented abs |
| Prompt даёт не тот freezing-эффект | См. `kling-i2v-transition` — motion вероятно слабо прописан; уточнить через `camera locked off, minimal movement` |
| Батч падает на 3-м shot | rate-limit провайдера — включить backoff; снизить параллелизм до 2 |
| Output MP4 не склеивается | Разные codec/resolution/framerate у шотов — нормализовать через `ffmpeg -vf scale=...` перед concat |

## References

- Related skills: `grsai-api`, `kling-i2v-transition`, `storyboard-designer`, `video-revision-pipeline`, `directors-cut-pipeline`, `learning-loop`, `publisher-site`
- Agents: `scriptwriter`, `storyboarder`, `prompt-engineer`, `image-gen`, `video-gen`, `voice-over`, `music-scoring`, `editor`, `publisher-multi`, `metrics-tracker`

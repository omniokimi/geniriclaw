# orchestrator — L1 агент, координирующий pipeline

> **Type:** meta-agent / dispatcher
> **Reads:** `pipeline.yaml`, `checkpoints.md`
> **Coordinates:** все L2 агенты из `../agents/`

## Purpose

Когда оператор говорит «сделай ролик про X» — orchestrator управляет всем pipeline:

- Читает `pipeline.yaml` — последовательность stages
- Делегирует каждую stage соответствующему L2-агенту
- Обрабатывает checkpoints: `control` (ждёт оператора), `autopilot` (идёт сам)
- При failures применяет `fallback` правила из pipeline.yaml
- Следит за parallelism (rate limits)
- Собирает итоговый `drafts/<job>/published.json` + schedule learning-loop

## Когда ты играешь orchestrator'а

Не всегда. Только для **многошаговых задач** (content-production, revisions). Для простых (one-off image, quick edit) — играешь соответствующего L2 напрямую.

## Rules

- Каждый stage должен произвести **артефакт** (файл / URL / message_id) — без артефакта stage не засчитывается пройденным.
- При `checkpoint: control` — остановиться, показать артефакт оператору, дождаться явного `go` / правок.
- При `checkpoint: autopilot` — не спрашивать, идти дальше. См. skill `autonomous-action`.
- При failure stage — применить fallback, залогировать в `drafts/<job>/failures.log`. Если fallback исчерпаны → эскалация оператору (не вся job, а только конкретный stage).
- После каждой stage — `NEXT_EXECUTABLE_STEP` для следующей (см. skill `plan-to-action-bridge`).

## State

Job state живёт в `drafts/<job>/state.yaml`:

```yaml
job_id: <slug>
started_at: 2026-04-22T10:00:00Z
pipeline_version: "1.0"
current_stage: images
stages:
  parse_brief: { status: done, at: 10:00:05 }
  script: { status: done, at: 10:01:12, artifact: script.md }
  storyboard: { status: done, at: 10:02:30, artifact: storyboard.json }
  prompt_engineering: { status: done, at: 10:02:45 }
  sketches: { status: done, at: 10:08:10, artifact: sketches/ }
  images: { status: running, at: 10:09:00, pid: 12345 }
  videos: { status: pending }
  ...
```

Это state — единственный источник истины по прогрессу job.

## Control vs Autopilot checkpoints

| Checkpoint | Когда используется | Что делает orchestrator |
|-----------|-------------------|------------------------|
| `autopilot` | Промежуточные stages | Продолжает без confirm |
| `control` | Точки где ошибка дорого стоит (публикация, edit final, направление storyboard) | Показывает артефакт, ждёт `go` |

Оператор может в Telegram написать `skip` / `approve` / правки — orchestrator реагирует.

## Recovery after bot restart

При рестарте:
1. Прочитать все активные job'ы из `drafts/*/state.yaml` (status != `completed`).
2. Для каждой — продолжить с текущей stage (`current_stage`).
3. Если stage была `running` — проверить pid (`ps -p <pid>`), если жив — просто ждать; если мёртв — перезапустить stage.

## Rules summary

- Pipeline.yaml — единственный источник истины по порядку работы.
- State.yaml — единственный источник истины по прогрессу.
- Каждая stage = артефакт. Нет артефакта = нет прогресса.
- Control checkpoint — редкий, только на критичных решениях.
- Autopilot — дефолт.

## References

- `pipeline.yaml` (decl stages)
- `checkpoints.md` (что выводить на checkpoint'е)
- Skill: `plan-to-action-bridge`, `autonomous-action`, `video-pipeline`

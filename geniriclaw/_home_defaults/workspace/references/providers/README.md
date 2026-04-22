# providers/ — справочник внешних API

Список внешних сервисов, которые использует starter kit. Для каждого — как подключиться, сколько стоит, когда использовать.

## Image generation

| Провайдер | Для чего | Env var | Цена / кадр | Сайт |
|-----------|----------|---------|-------------|------|
| **OpenRouter** (Gemini Image / Nano Banana) | img2img с face REF, text2img, multi-ref | `OPENROUTER_API_KEY` | $0.003–0.08 | [openrouter.ai](https://openrouter.ai) |
| **Krea AI** | реалистичные портреты | `KREA_API_KEY` | per image | [krea.ai](https://krea.ai) |
| **Replicate** (любые модели) | универсальный gateway (Flux, SDXL, Ideogram) | `REPLICATE_API_TOKEN` | per model | [replicate.com](https://replicate.com) |

## Video generation (image-to-video)

| Модель | Через | Плюсы | Минусы | Цена |
|--------|-------|-------|--------|------|
| **Kling v2.1 standard** | Replicate | лица хорошо сохраняет, стабильный | 720p | ~$0.28 / 5с |
| **Kling v2.1 master** | Replicate | 1080p, end_image | дороже | ~$1.40 / 5с |
| **Seedance 2.0** | Replicate | B-roll, native audio | лица блокирует (E005 safety) | per 5s |
| MiniMax Hailuo-02 | Replicate | альтернатива | не тестировано на лицах | per 5s |

## Talking head / avatar

| Провайдер | Для чего | Цена |
|-----------|----------|------|
| **HeyGen** | Custom avatar или stock avatars | ~$0.25/мин |

## Voice / TTS

| Провайдер | Качество | Цена |
|-----------|----------|------|
| **ElevenLabs** (`eleven_multilingual_v2`) | voice clone, топ русского | $0.0003/char |
| **OpenAI TTS** (`tts-1-hd`) | хороший fallback | $0.030/1K chars |
| **Microsoft Edge TTS** | бесплатно, достаточно для черновика | 0 |

## Music

| Провайдер | Тип | Стоимость |
|-----------|-----|-----------|
| **Suno AI** | AI-generated custom | unofficial API, риск |
| **Artlist / Epidemic Sound** | Library | $12–$25/мес |
| **YouTube Audio Library** | Free library | 0 |

## Speech-to-text

| Провайдер | Для чего | Env var |
|-----------|----------|---------|
| **Soniox** (`stt-async-preview`) | русский голос, long-form | `SONIOX_API_KEY` |
| **OpenAI Whisper** (`whisper-1`) | fallback, короткие | `OPENAI_API_KEY` |
| **whisper.cpp** | offline, локально | — |

## LLM backends

| Провайдер | Для чего | Env var |
|-----------|----------|---------|
| **Anthropic Claude** (Claude Code CLI) | default, OAuth или API | `CLAUDE_CODE_OAUTH_TOKEN` или `ANTHROPIC_API_KEY` |
| **OpenAI** | alternate | `OPENAI_API_KEY` |
| **Google Gemini** | alternate (official CLI) | through `gemini` CLI |

## Publishing

| Канал | Метод | Требования |
|-------|-------|-----------|
| **Telegram** | Bot API | bot token от BotFather |
| **VK** | API | OAuth, подтверждение группы |
| **Instagram** | Meta Graph API | Business verification + IG Creator account |
| **TikTok** | for Developers | Business verification |
| **Ayrshare** (unified) | single API across platforms | `AYRSHARE_API_KEY`, $149/мес |

## Как подключить

Для каждого провайдера создать аккаунт, получить API key, добавить в env:

```bash
# В /etc/environment на сервере (или в .env)
OPENROUTER_API_KEY=<your-key>           # Gemini Image / Nano Banana / любые LLM
REPLICATE_API_TOKEN=<your-token>
ELEVENLABS_API_KEY=<your-key>
SONIOX_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
# и т.д. — только те что реально используешь
```

**Не все нужны сразу.** Минимальный starting-set:
- `CLAUDE_CODE_OAUTH_TOKEN` (для LLM — обязательно)
- `OPENROUTER_API_KEY` **или** `REPLICATE_API_TOKEN` (image generation)
- Telegram bot token (publishing)

Остальные — по мере необходимости.

## См. также

- Каждый provider имеет детальный SKILL в `../../skills/<provider-or-pipeline>/SKILL.md`
- В `references/providers/` можно создавать отдельные `.md` файлы под каждый (endpoints, quirks, примеры прошлых запросов)

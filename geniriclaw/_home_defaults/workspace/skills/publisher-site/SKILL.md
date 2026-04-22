# publisher-site — публикация HTML-артефактов и медиа на собственный домен

> **Status:** stable
> **Category:** publish · infrastructure
> **Depends on:** своя VM с nginx / CDN, SSL (Let's Encrypt или CloudFlare)

## Purpose

Публикация готовых артефактов (storyboard HTML, ролики, дайджесты, презентации) на собственный публичный домен. Даёт permanent URL, которые можно пересылать заказчику / в соцсети / в команду.

## When to use

- Нужно отдать клиенту ссылку на результат работы (HTML-презентация, MP4, изображение в 2K).
- Нужен permanent URL для img2img/i2v генерации (face REFs, scene anchors).
- Нужна приватная галерея («studio», доступна по ссылке, не индексируется).

**НЕ подходит** когда: клиент не хочет чтобы материал лежал на публичном хостинге. Тогда → приватный Telegram-канал или S3 с signed URL.

## Infrastructure

| Что | Пример | Комментарий |
|-----|--------|-------------|
| VPS с публичным IP | DigitalOcean, Linode, Hetzner, Contabo | 2 vCPU / 4 GB достаточно |
| Домен | `{{YOUR_DOMAIN}}` | купить на REG.RU / Namecheap / Gandi |
| Nginx | v1.18+ | стандартный веб-сервер |
| SSL | Let's Encrypt (certbot) | бесплатно, автопродление 90 дней |
| Хранилище | `/var/www/{{YOUR_DOMAIN}}/` | монтировано в nginx |

## Структура публичного сайта

```
/var/www/{{YOUR_DOMAIN}}/
├── index.html              ← главная, индекс с разделами
├── docs/                   ← HTML-артефакты (презентации, дайджесты)
├── faces/                  ← референсные портреты (если нужны для img2img)
├── media/                  ← статичные медиа-ассеты
├── sketches/{{JOB_ID}}/    ← раскадровки под конкретный ролик
├── published/{{JOB_ID}}/   ← опубликованные финальные mp4 + превью
├── studio/                 ← приватный индекс работ (noindex/nofollow)
└── photos/                 ← произвольные фото
```

## Nginx-конфиг — starter

```nginx
# /etc/nginx/sites-available/{{YOUR_DOMAIN}}
server {
    listen 443 ssl http2;
    server_name {{YOUR_DOMAIN}};

    ssl_certificate     /etc/letsencrypt/live/{{YOUR_DOMAIN}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{YOUR_DOMAIN}}/privkey.pem;

    root /var/www/{{YOUR_DOMAIN}};
    index index.html;

    # faces — короткий кэш, чтобы обновления референсов быстро расходились
    location /faces/ {
        expires 5m;
        add_header Cache-Control "public, max-age=300, must-revalidate";
    }

    # studio — приватный индекс, запрет индексации
    location /studio/ {
        add_header X-Robots-Tag "noindex, nofollow, noarchive";
        try_files $uri $uri/ =404;
    }

    # остальные файлы — стандартный кэш 1 день
    location / {
        add_header X-Robots-Tag "noindex" always;  # для всего сайта по желанию
        try_files $uri $uri/ =404;
    }
}

server {
    listen 80;
    server_name {{YOUR_DOMAIN}};
    return 301 https://$host$request_uri;
}
```

Тест и reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## SSL через Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d {{YOUR_DOMAIN}}
sudo systemctl status certbot.timer   # автопродление
```

## Утилита publish.sh — один шаг публикации

См. [`../../templates/publish/publish.sh`](../../templates/publish/publish.sh) (пример).

Использование:

```bash
# Опубликовать HTML-презентацию с автодобавлением в индекс /studio/
./publish.sh \
  --local  ./drafts/my-project/presentation.html \
  --remote /var/www/{{YOUR_DOMAIN}}/docs/my-project.html \
  --title  "My Project presentation" \
  --index

# Опубликовать mp4 БЕЗ индекса (для референсов / media)
./publish.sh \
  --local  ./drafts/my-project/final.mp4 \
  --remote /var/www/{{YOUR_DOMAIN}}/published/my-project/final.mp4
```

## Markdown → HTML конвертер

В `templates/publish/md_to_site.py` — конвертер Markdown в HTML с единым стилем сайта. Читает MD, применяет шаблон (встроенный CSS, tmpl header/footer), сохраняет готовый HTML.

```bash
python3 md_to_site.py input.md output.html --title "Daily digest 2026-04-22"
```

## Приватный индекс / `studio`

Для демонстраций клиенту без публикации в поиске:

- URL `https://{{YOUR_DOMAIN}}/studio/` с `X-Robots-Tag: noindex, nofollow, noarchive`
- Опционально — добавить basic-auth на nginx level:

```nginx
location /studio/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/studio.htpasswd;
    add_header X-Robots-Tag "noindex, nofollow, noarchive";
}
```

Создать паролик:
```bash
sudo htpasswd -c /etc/nginx/studio.htpasswd operator
```

## Face REFs на сайте

Если проект использует image2image с face reference (см. `grsai-api`), референсные фото **обязательно публикуются** на сайте (для подстановки URL в API):

```
/var/www/{{YOUR_DOMAIN}}/faces/
├── REF_01.jpg     ← реальное фото человека (портрет)
├── REF_02.jpg     ← вариант
├── ...
└── COLLEAGUE.png  ← для совместных кадров
```

Правила:
- Только **реальные** фото, не собственные AI-генерации.
- Permission от человека, чьё лицо публикуется (RGPD, персональные данные).
- Добавить `X-Robots-Tag: noindex` на `/faces/` чтобы не попадали в поиск.

## Config placeholders

| Placeholder | Где задать |
|-------------|-----------|
| `{{YOUR_DOMAIN}}` | имя домена без протокола (`example.com`) |
| `{{PUBLIC_SITE_ROOT}}` | `/var/www/{{YOUR_DOMAIN}}/` |
| `{{SSH_HOST}}` | хост VPS для `scp` / `rsync` |
| `{{SSH_USER}}` | `root` или имя пользователя |
| `{{SSH_KEY_PATH}}` | `~/.ssh/<keyname>` |

## Rules

- **Чувствительное НЕ на публичный сайт**. Если контент содержит персональные данные, внутренние заметки, коммерческую тайну — публиковать в приватном канале Telegram или в `/studio/` с basic-auth.
- **Все публичные HTML содержат** `<meta name="robots" content="noindex, nofollow, noarchive">` в `<head>` по умолчанию. Индексацию включать явно только для контента который ты хочешь продвигать в поиске.
- **Cache busting** для faces: при обновлении REF — `touch` файла (обновит Last-Modified), и добавить `?v=<timestamp>` в URL если преследует кэш провайдера.
- **Bандшить широко по размеру** — перед публикацией сжимать через `pngquant` / `jpegoptim` / `ffmpeg` (для видео).

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| 403 Forbidden | Проверить `chown www-data:www-data` и `chmod 644` на файле/папке |
| HTTP вместо HTTPS | nginx redirect не работает — проверить 80-порт listen, перезагрузить |
| Cert expired | `sudo certbot renew && sudo systemctl reload nginx` |
| Картинка отдаётся старая | nginx cache или browser cache — `curl -sI` глянуть `Last-Modified`; при необходимости ставить `Cache-Control: no-cache` на папку |
| PNG слишком большой | `pngquant --force --output out.png in.png` (lossy), или `optipng` (lossless) |

## References

- [Nginx docs](https://nginx.org/en/docs/)
- [Let's Encrypt / certbot](https://certbot.eff.org/)
- Related: `channel-publisher` (параллельная публикация в мессенджер), `tg-message-editor`

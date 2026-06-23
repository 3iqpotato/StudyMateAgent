# AI Test Helper

Локален AI асистент с FastAPI, векторна памет, инструменти и Telegram интеграция. Моделът работи изцяло на твоя лаптоп — без облак, без API такси.

---

## Какво може

### Чат
- Разговори с локален AI модел (qwen3.5:9b)
- До 3 разговора на потребител
- Пълна история — разговорите се помнят между сесии
- Преименуване и изтриване на разговори
- Markdown рендиране на отговорите

### Инструменти на агента
| Инструмент | Описание |
|---|---|
| `calculator` | Математически изрази — sin, cos, sqrt, factorial, log и др. |
| `search_memory` | Търси в качени документи (PDF, DOCX, TXT) |
| `get_weather` | Текущо време за всеки град (wttr.in) |
| `fetch_webpage` | Взима информация от Wikipedia и др. сайтове |
| `search_recipe` | Търси рецепти по TheMealDB |
| `send_telegram` | Изпраща съобщения в Telegram |

### Документи и снимки
- Качване на PDF, DOCX и TXT файлове
- Файловете се нарязват на части и се записват в ChromaDB
- Агентът автоматично търси в тях при въпроси
- При изтриване на разговор — документите се изтриват също
- Качване на снимки (JPEG, PNG, WebP, GIF)
- Моделът извлича текст от снимки и отговаря на въпроси

### Сигурност
- JWT автентикация
- Rate limiting (slowapi)
- Brute force защита при логин
- Security HTTP headers
- Input санитизация и injection detection
- AST-базиран калкулатор (без eval)
- Whitelist на позволени домейни за web scraping

---

## Технологии

| Слой | Технология |
|---|---|
| API | FastAPI + Uvicorn |
| База данни | PostgreSQL 16 (SQLAlchemy + Alembic) |
| Векторна база | ChromaDB |
| AI модел | Ollama (qwen3.5:9b) |
| Embeddings | sentence-transformers (chromadb default) |
| UI | Jinja2 + ванилен JS |
| Сигурност | JWT (python-jose) + passlib + slowapi |

---

## Архитектура

```
┌─────────────────────────────────────────┐
│              Браузър                    │
└──────────────────┬──────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────┐
│           FastAPI (локално)             │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │  Web routes │  │   API v1 routes  │  │
│  │  (Jinja2)   │  │  (JSON/REST)     │  │
│  └──────┬──────┘  └────────┬─────────┘  │
│         │                  │            │
│  ┌──────▼──────────────────▼─────────┐  │
│  │           AI Agent                │  │
│  │  ┌─────────┐  ┌────────────────┐  │  │
│  │  │ Runner  │  │ Vision (2-step)│  │  │
│  │  │ + Tools │  │ снимки→текст   │  │  │
│  │  └─────────┘  └────────────────┘  │  │
│  └───────────────────────────────────┘  │
└──┬─────────────┬──────────────┬─────────┘
   │             │              │
   ▼             ▼              ▼
PostgreSQL    ChromaDB       Ollama
(Docker)      (Docker)       (Docker)
```

---

## Изисквания

- Python 3.11+
- Docker Desktop
- NVIDIA GPU (препоръчително) или CPU
- 8GB+ RAM
- 10GB+ свободно място (за модела)

---

## Инсталация

### 1. Клонирай проекта

```bash
git clone https://github.com/3iqpotato/ai-test-helper.git
cd ai-test-helper
```

### 2. Създай виртуална среда

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Инсталирай зависимостите

```bash
pip install -r app/requirements.txt
```

### 4. Създай `.env` файл

Копирай `.env.example` и попълни стойностите:

```bash
cp .env.example .env
```

```env
# База данни
POSTGRES_USER=твоя_потребител
POSTGRES_PASSWORD=твоята_парола
POSTGRES_DB=ai_test_helper
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# За локално пускане на Alembic
DATABASE_URL=postgresql+asyncpg://потребител:парола@localhost:5433/ai_test_helper
DATABASE_URL_LOCAL=postgresql://потребител:парола@localhost:5433/ai_test_helper

# JWT — генерирай с: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=генерирай-случаен-стринг-минимум-32-символа
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:9b

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Telegram (опционално)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Приложение
APP_NAME=AI Test Helper
DEBUG=True
MAX_CONVERSATIONS_PER_USER=3
```

### 5. Създай папките за Docker volumes

```bash
# Windows
mkdir D:\docker-volumes\ollama
mkdir D:\docker-volumes\postgres
mkdir D:\docker-volumes\chromadb

# Linux/Mac
mkdir -p ~/docker-volumes/ollama
mkdir -p ~/docker-volumes/postgres
mkdir -p ~/docker-volumes/chromadb
```

> Ако ползваш Linux/Mac — смени пътищата в `docker-compose.yml` от `D:/docker-volumes/...` на `~/docker-volumes/...`

### 6. Стартирай Docker контейнерите

```bash
docker compose up -d
```

Това стартира:
- `ollama` — AI модел сървър на порт 11434
- `postgres` — база данни на порт 5433
- `chromadb` — векторна база на порт 8001

### 7. Изтегли модела

```bash
docker exec -it ollama ollama pull qwen3.5:9b
```

> Това ще изтегли ~6.6GB. Изчакай да приключи.

Провери че моделът е готов:

```bash
docker exec -it ollama ollama list
```

### 8. Пусни миграциите

```bash
alembic -c app/alembic.ini revision --autogenerate -m "initial"
alembic -c app/alembic.ini upgrade head
```

### 9. Стартирай приложението

```bash
uvicorn app.main:app --reload
```

Отвори браузъра на [http://localhost:8000](http://localhost:8000)

---

## Структура на проекта

```
AI_Test_Helper/
├── docker-compose.yml
├── .env
├── .gitignore
└── app/
    ├── requirements.txt
    ├── main.py
    ├── alembic.ini
    │
    ├── core/
    │   ├── config.py          # настройки от .env
    │   ├── database.py        # SQLAlchemy async engine
    │   ├── security.py        # JWT и bcrypt
    │   ├── chroma.py          # ChromaDB клиент
    │   ├── rate_limiter.py    # slowapi rate limiting
    │   ├── brute_force.py     # защита при логин
    │   └── security_headers.py
    │
    ├── models/
    │   ├── user.py
    │   └── conversation.py
    │
    ├── schemas/
    │   ├── user.py
    │   └── conversation.py
    │
    ├── services/
    │   ├── auth_service.py
    │   ├── conversation_service.py
    │   └── document_service.py    # PDF/DOCX/TXT → ChromaDB
    │
    ├── api/
    │   ├── web.py                 # HTML routes (Jinja2)
    │   └── v1/
    │       ├── dependencies.py        # get_current_user_flexible
    │       ├── router.py
    │       ├── auth.py
    │       ├── conversations.py
    │       └── chat.py
    │
    ├── agent/
    │   ├── runner.py              # главният агент
    │   ├── vision.py              # обработка на снимки
    │   ├── system_prompt.py
    │   ├── guardrails.py          # injection detection
    │   └── tools/
    │       ├── registry.py
    │       ├── calculator.py
    │       ├── weather.py
    │       ├── web_search.py
    │       ├── memory.py
    │       ├── search_recipes.py
    │       └── telegram.py
    │
    ├── migrations/
    │   └── versions/
    │
    ├── templates/
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── register.html
    │   └── chat.html
    │
    └── static/
        └── css/
            └── style.css
```

---

## Telegram интеграция (опционално)

1. Пиши на [@BotFather](https://t.me/BotFather) в Telegram и създай бот с `/newbot`
2. Вземи токена и го сложи в `.env` като `TELEGRAM_BOT_TOKEN`
3. Пиши на [@userinfobot](https://t.me/userinfobot) за да вземеш своя `chat_id`
4. Сложи го в `.env` като `TELEGRAM_CHAT_ID`
5. Напиши `/start` на своя бот за да го активираш

След това можеш да кажеш на агента: `изпрати ми съобщение в телеграм: тест`

---

## Как работи агентът

Агентът следва ReAct (Reasoning + Acting) паттерн:

```
Потребителят пише съобщение
        ↓
Guardrails проверяват за injection attacks
        ↓
Съобщението + история + system prompt → Ollama
        ↓
Ollama решава дали да извика tool или да отговори
        ↓
Ако извика tool → изпълнява се → резултатът се връща на Ollama
        ↓
Ollama формулира финален отговор
        ↓
Output validation (leak detection)
        ↓
Отговорът се записва в PostgreSQL
```

### Обработка на снимки (двустъпков процес)

```
Снимката се изпраща към Ollama (без tools)
        ↓
Ollama извлича текста от снимката
        ↓
Текстът се подава към агента като контекст
        ↓
Агентът може да ползва tools върху извлечения текст
```

---

## Спиране и пускане

```bash
# Спри само базите (запазва данните)
docker compose stop postgres chromadb

# Спри всичко
docker compose down

# Пусни отново
docker compose up -d
uvicorn app.main:app --reload
```

---

## Troubleshooting

**Ollama е бавен при първото съобщение**
Моделът се зарежда от диск в VRAM. Нормално е да отнеме 30-60 секунди при студен старт. Добави `OLLAMA_KEEP_ALIVE=24h` в docker-compose.yml за да остане зареден.

**`column conversations.is_processing does not exist`**
Пусни миграциите: `alembic -c app/alembic.ini upgrade head`

**`password authentication failed`**
Изтрий и пресъздай postgres volume: `docker compose down`, изтрий `D:\docker-volumes\postgres`, `docker compose up -d`

**Агентът се върти в цикъл**
Моделът понякога дава празни отговори (thinking режим). Вградена защита спира след 3 поредни празни отговора.

---

## Планирано

- [ ] Redis + Celery за async задачи
- [ ] Playwright за JavaScript-rendered сайтове (Kaufland, Lidl)
- [ ] Jarvis — личен асистент с достъп до системата
- [ ] Поддръжка на повече файлови формати

---

## Лиценз

MIT

# SIVA Bot — FAQ Program Magang (FAQ-only)

Bot Telegram khusus menjawab FAQ seputar Program Magang. Tidak ada
fitur pendaftaran/status/jadwal magang (sudah dibuang dari versi ini).

## Alur menjawab pertanyaan (user biasa)

1. **Dataset match** — cosine similarity (TF-IDF) antara pertanyaan user
   vs seluruh `patterns` di `data/intents_magang_v3.json`.
2. **Keyword match** — kalau lapis 1 gagal mengenali, dicoba cocokkan ke
   `keywords` per intent (field opsional).
3. **Ollama (LLM lokal)** — kalau dua-duanya gagal, dilempar ke Ollama
   (`OLLAMA_MODEL` di `.env`) dengan konteks FAQ sebagai fallback.

Lihat `app/ml/faq_matcher.py` untuk detail implementasi.

## Command admin (chat_id di ADMIN_CHAT_IDS)

Edit dataset FAQ langsung dari Telegram, realtime, tanpa training ulang
dan tanpa restart bot:

- `/list_intent` — lihat semua tag intent
- `/lihat_intent [tag]` — detail satu intent
- `/tambah_keyword [tag] [keyword]`
- `/hapus_keyword [tag] [keyword]`
- `/edit_jawaban [tag] [jawaban baru]`
- `/tambah_intent [tag] | pattern1;pattern2;... | jawaban`
- `/hapus_intent [tag]`
- `/reload_faq` — reload manual (jarang perlu, command di atas sudah auto-reload)

## Setup

1. `pip install -r requirements.txt` (lihat daftar dependency di bawah)
2. Copy `.env.example` -> `.env`, isi `TELEGRAM_BOT_TOKEN`
3. Jalankan bot: `python main.py`
4. Kirim `/myid` ke bot untuk dapat chat_id kamu, isi ke `ADMIN_CHAT_IDS`
   di `.env`, lalu restart bot sekali supaya kamu terdaftar sebagai admin

## Dependency utama

- `python-telegram-bot`
- `scikit-learn` (TF-IDF + cosine similarity)
- `Sastrawi` (stemming & stopword Bahasa Indonesia)
- `python-dotenv`
- `httpx` atau `requests` (dipakai `ollama_service.py` untuk panggil Ollama)
- Ollama terpasang & jalan lokal (`ollama serve`, model sudah di-`pull`)

## Struktur project

```
main.py
app/
  config.py              # baca .env
  bot/
    webhook.py           # entry point Telegram (polling mode)
    router.py            # admin vs user routing
  handlers/
    faq_handler.py        # alur jawab pertanyaan user
    faq_menu_handler.py    # command /faq (daftar topik)
    admin_handler.py       # command edit intent khusus admin
  ml/
    faq_matcher.py         # mesin matching (cosine + keyword)
    text_normalizer.py     # slang->formal, stopword, stemming
    slang_by_intent.csv    # kamus slang
  services/
    intent_service.py      # CRUD ke data/intents_magang_v3.json
    ollama_service.py      # panggil Ollama API
data/
  intents_magang_v3.json  # dataset FAQ (tag/patterns/responses/keywords)
```

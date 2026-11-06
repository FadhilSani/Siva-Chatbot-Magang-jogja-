"""
Fallback jawaban pakai LLM lokal (Ollama) untuk pertanyaan yang tidak
dikenali oleh IntentClassifier (SVM + cosine similarity).

Butuh Ollama jalan di background (`ollama serve`, biasanya otomatis aktif
setelah install) dan model sudah ditarik, misalnya:
    ollama pull qwen2.5:7b-instruct-q4_0
"""

import json
import os
import httpx

from app.ml.faq_matcher import DATA_PATH as _FAQ_PATH

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_0")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "30"))

# Path dataset FAQ/intent di-reuse langsung dari app/ml/faq_matcher.py (satu-satunya
# sumber path yang valid) -- supaya kalau nama/lokasi file JSON-nya diganti, cukup
# ubah DATA_PATH di faq_matcher.py, tidak perlu diingat & diubah manual di sini juga.

SYSTEM_PROMPT = (
    "Kamu adalah SIVA, asisten virtual untuk layanan pendaftaran magang. "
    "Tugasmu membantu calon peserta magang: menjelaskan cara daftar, "
    "jadwal, shift, kantor penempatan, dan peraturan magang.\n\n"
    "ATURAN PENTING:\n"
    "1. Jawab singkat, ramah, dan pakai Bahasa Indonesia santai tapi sopan.\n"
    "2. Kamu TIDAK tahu data pribadi pendaftar, status pendaftaran, atau "
    "jadwal terbaru secara real-time — untuk itu arahkan pengguna memakai "
    "perintah bot seperti /pendaftaran, /status, atau /jadwal_magang.\n"
    "3. Kalau pertanyaan di luar topik magang/SIVA, atau kamu tidak yakin "
    "jawabannya, katakan terus terang tidak tahu dan sarankan hubungi Admin "
    "Magang. JANGAN mengarang kebijakan, tanggal, syarat, atau prosedur "
    "yang tidak ada di konteks berikut.\n\n"
    "Berikut daftar FAQ resmi sebagai referensi (pakai kalau relevan, "
    "jangan disalin mentah-mentah, sampaikan dengan gaya sendiri):\n"
    "{faq_context}"
)


def _load_faq_context(max_items: int = None) -> str:
    """Ambil ringkasan FAQ resmi untuk dijadikan konteks (mini-RAG).

    Sumbernya sama persis dengan yang dipakai IntentClassifier
    (data/intents_magang_v3.json), format: {"intents": [{"tag", "patterns",
    "responses"}, ...]}. Diambil 1 contoh pertanyaan (pattern pertama) dan
    jawaban resminya (response pertama) per intent.

    max_items=None (default) -> ambil SEMUA intent, bukan cuma 30 pertama.
    Dulu dibatasi 30 padahal dataset sudah 47 intent, jadi 17 intent
    terakhir gak pernah masuk konteks Ollama sama sekali. Kalau nanti
    dataset makin besar dan mulai kepanjangan buat context window LLM,
    baru pertimbangkan batasi lagi (mis. ringkas tiap response, bukan
    balikin ke limit jumlah intent).
    """
    try:
        with open(_FAQ_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "(tidak ada data FAQ tambahan)"

    intents = data.get("intents", [])
    if max_items is not None:
        intents = intents[:max_items]

    lines = []
    for intent in intents:
        patterns = intent.get("patterns") or []
        responses = intent.get("responses") or []
        if not patterns or not responses:
            continue
        pertanyaan = patterns[0]
        jawaban = responses[0]
        lines.append(f"- Q: {pertanyaan}\n  A: {jawaban}")

    return "\n".join(lines) if lines else "(tidak ada data FAQ tambahan)"


# Dibangun sekali saat module diimport, bukan tiap request masuk
_FAQ_CONTEXT = _load_faq_context()
_SYSTEM_PROMPT = SYSTEM_PROMPT.format(faq_context=_FAQ_CONTEXT)

_FALLBACK_IF_OLLAMA_DOWN = (
    "Maaf, saya belum memahami pertanyaan tersebut dan sistem bantuan AI "
    "sedang tidak tersedia 🙏\nSilakan hubungi Admin Magang untuk info "
    "lebih lanjut."
)


async def ask_ollama(user_text: str) -> str:
    """Kirim pertanyaan ke Ollama, kembalikan jawaban teks."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,  # rendah, biar jawaban tidak ngarang liar
        },
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, ValueError) as e:
        print(f"[ollama_service] Gagal memanggil Ollama ({type(e).__name__}): {e!r}")
        return _FALLBACK_IF_OLLAMA_DOWN
from app.ml.faq_matcher import FaqMatcher
from app.services.ollama_service import ask_ollama

# Load sekali saat module ini pertama kali diimport (saat bot start),
# bukan tiap ada pesan masuk -> supaya responnya cepat.
#
# Kalau intent diedit lewat interface admin (tambah/hapus/ubah intent,
# jawaban, atau keyword di data/intents_magang_v3.json), panggil
# reload_matcher() di bawah supaya perubahan langsung kepakai TANPA
# training ulang dan TANPA restart bot. Lihat command /reload_faq di
# admin_handler.py.
_matcher = FaqMatcher()


async def handle(update, context, text: str):
    answer, method, score = _matcher.get_answer(text)

    if answer is not None:
        # Intent dikenali (keyword match atau cosine similarity) ->
        # pakai jawaban dari FAQ/intents JSON seperti biasa.
        response = answer
    else:
        # Tidak dikenali sama sekali -> lempar ke Ollama (LLM lokal)
        # supaya tetap dapat jawaban yang masuk akal, bukan cuma
        # "maaf saya tidak paham".
        response = await ask_ollama(text)

    await update.message.reply_text(response)


def reload_matcher():
    """Muat ulang data/intents_magang_v3.json + fit ulang TF-IDF.
    Dipanggil dari admin_handler setelah intent ditambah/diedit/dihapus."""
    _matcher.reload()

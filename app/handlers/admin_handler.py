"""
Command khusus admin (chat_id ada di ADMIN_CHAT_IDS) untuk mengedit
dataset FAQ (data/intents_magang_v3.json) secara realtime lewat Telegram.

Semua command yang mengubah data otomatis simpan ke JSON DAN langsung
memanggil faq_handler.reload_matcher() -- jadi perubahan langsung
kepakai saat itu juga, tidak perlu restart bot atau training ulang.
"""

from app.services import intent_service
from app.handlers import faq_handler


async def handle(update, context, text: str):
    if text.startswith("/list_intent"):
        await _list_intent(update)
    elif text.startswith("/lihat_intent"):
        await _lihat_intent(update, text)
    elif text.startswith("/tambah_keyword"):
        await _tambah_keyword(update, text)
    elif text.startswith("/hapus_keyword"):
        await _hapus_keyword(update, text)
    elif text.startswith("/edit_jawaban"):
        await _edit_jawaban(update, text)
    elif text.startswith("/tambah_pattern"):
        await _tambah_pattern(update, text)
    elif text.startswith("/tambah_intent"):
        await _tambah_intent(update, text)
    elif text.startswith("/hapus_intent"):
        await _hapus_intent(update, text)
    elif text.startswith("/reload_faq"):
        await _reload_faq(update)
    else:
        await update.message.reply_text(
            "Halo Admin \U0001F44B\n\n"
            "Command FAQ/intent:\n"
            "/list_intent - lihat semua tag intent\n"
            "/lihat_intent [tag] - detail satu intent\n"
            "/tambah_keyword [tag] [keyword] - tambah keyword ke intent\n"
            "/hapus_keyword [tag] [keyword] - hapus keyword dari intent\n"
            "/edit_jawaban [tag] [jawaban baru] - ganti jawaban intent\n"
            "/tambah_pattern [tag] [pattern1;pattern2;...] - tambah pattern ke "
            "intent yang SUDAH ADA (tanpa ganti jawaban)\n"
            "/tambah_intent [tag] | pattern1;pattern2;... | jawaban - buat intent baru\n"
            "/hapus_intent [tag] - hapus intent\n"
            "/reload_faq - muat ulang FAQ/intent manual (jarang perlu -- "
            "command di atas sudah auto-reload)"
        )


async def _reload_faq(update, silent: bool = False):
    try:
        faq_handler.reload_matcher()
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal reload FAQ: {e}")
        return False

    if not silent:
        await update.message.reply_text(
            "✅ FAQ/intent berhasil dimuat ulang dari data/intents_magang_v3.json."
        )
    return True


async def _list_intent(update):
    intents = intent_service.list_intents()
    if not intents:
        await update.message.reply_text("Belum ada intent sama sekali.")
        return

    lines = [f"📚 Total {len(intents)} intent:\n"]
    for it in intents:
        lines.append(
            f"• {it['tag']} ({it['category']}) — "
            f"{it['n_patterns']} pattern, {it['n_keywords']} keyword"
        )
    lines.append("\nKetik /lihat_intent [tag] untuk detail.")
    await update.message.reply_text("\n".join(lines))


async def _lihat_intent(update, text: str):
    tag = text[len("/lihat_intent"):].strip()
    if not tag:
        await update.message.reply_text("Format: /lihat_intent [tag]\nContoh: /lihat_intent uang_saku")
        return

    intent = intent_service.get_intent(tag)
    if intent is None:
        await update.message.reply_text(f"Intent '{tag}' tidak ditemukan. Cek /list_intent.")
        return

    patterns = "\n".join(f"  - {p}" for p in intent.get("patterns", []))
    keywords = ", ".join(intent.get("keywords", [])) or "(belum ada)"
    responses = intent.get("responses", [""])[0]

    await update.message.reply_text(
        f"🏷 {intent['tag']} ({intent.get('category', '-')})\n\n"
        f"Jawaban:\n  {responses}\n\n"
        f"Keywords: {keywords}\n\n"
        f"Patterns ({len(intent.get('patterns', []))}):\n{patterns}"
    )


async def _tambah_keyword(update, text: str):
    parts = text[len("/tambah_keyword"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Format: /tambah_keyword [tag] [keyword]\n"
            "Contoh: /tambah_keyword uang_saku biaya"
        )
        return

    tag, keyword = parts[0], parts[1]
    status = intent_service.add_keyword(tag, keyword)

    if status == "not_found":
        await update.message.reply_text(f"Intent '{tag}' tidak ditemukan. Cek /list_intent.")
        return

    if status == "duplicate":
        await update.message.reply_text(
            f"⚠️ Keyword '{keyword}' sudah ada di intent '{tag}', tidak ada perubahan."
        )
        return

    await _reload_faq(update, silent=True)
    await update.message.reply_text(f"✅ Keyword '{keyword}' ditambahkan ke intent '{tag}' & FAQ sudah di-reload.")


async def _hapus_keyword(update, text: str):
    parts = text[len("/hapus_keyword"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Format: /hapus_keyword [tag] [keyword]\n"
            "Contoh: /hapus_keyword uang_saku biaya"
        )
        return

    tag, keyword = parts[0], parts[1]
    if not intent_service.remove_keyword(tag, keyword):
        await update.message.reply_text(f"Intent '{tag}' tidak ditemukan. Cek /list_intent.")
        return

    await _reload_faq(update, silent=True)
    await update.message.reply_text(f"✅ Keyword '{keyword}' dihapus dari intent '{tag}' & FAQ sudah di-reload.")


async def _edit_jawaban(update, text: str):
    parts = text[len("/edit_jawaban"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Format: /edit_jawaban [tag] [jawaban baru]\n"
            "Contoh: /edit_jawaban uang_saku Tidak, program magangnya unpaid."
        )
        return

    tag, jawaban_baru = parts[0], parts[1]
    if not intent_service.set_response(tag, jawaban_baru):
        await update.message.reply_text(f"Intent '{tag}' tidak ditemukan. Cek /list_intent.")
        return

    await _reload_faq(update, silent=True)
    await update.message.reply_text(f"✅ Jawaban intent '{tag}' diperbarui & FAQ sudah di-reload.")


async def _tambah_pattern(update, text: str):
    parts = text[len("/tambah_pattern"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Format: /tambah_pattern [tag] [pattern1;pattern2;...]\n\n"
            "Contoh:\n"
            "/tambah_pattern kontak_admin ada wa ngga min;kontak admin dong;nomor wa admin apa\n\n"
            "Cuma nambah pertanyaan baru ke intent yang SUDAH ADA -- jawabannya "
            "tetap pakai yang lama, gak perlu diisi ulang."
        )
        return

    tag, patterns_str = parts[0], parts[1]
    patterns = [p.strip() for p in patterns_str.split(";") if p.strip()]
    if not patterns:
        await update.message.reply_text("Minimal 1 pattern harus diisi.")
        return

    added, duplicate, not_found = intent_service.add_patterns(tag, patterns)

    if not_found:
        await update.message.reply_text(f"Intent '{tag}' tidak ditemukan. Cek /list_intent.")
        return

    if not added:
        await update.message.reply_text(
            f"⚠️ Semua pattern itu sudah ada di intent '{tag}', tidak ada perubahan."
        )
        return

    await _reload_faq(update, silent=True)
    msg = f"✅ {len(added)} pattern ditambahkan ke intent '{tag}'"
    if duplicate:
        msg += f" ({len(duplicate)} lainnya sudah ada sebelumnya, dilewati)"
    msg += " & FAQ sudah di-reload."
    await update.message.reply_text(msg)


FORMAT_TAMBAH_INTENT = (
    "Format: /tambah_intent [tag] | pattern1;pattern2;... | jawaban\n\n"
    "Contoh:\n"
    "/tambah_intent jam_operasional_kantor | Jam kerja kantor jam berapa?;Kantor buka jam berapa? | "
    "Kantor buka Senin-Jumat, 08.00-16.00 WIB."
)


async def _tambah_intent(update, text: str):
    body = text[len("/tambah_intent"):].strip()
    if not body:
        await update.message.reply_text(FORMAT_TAMBAH_INTENT)
        return

    parts = [p.strip() for p in body.split("|")]
    if len(parts) < 3 or not parts[0] or not parts[1] or not parts[2]:
        await update.message.reply_text(f"Format salah.\n\n{FORMAT_TAMBAH_INTENT}")
        return

    tag = parts[0].replace(" ", "_")
    patterns = [p.strip() for p in parts[1].split(";") if p.strip()]
    jawaban = parts[2]

    try:
        intent_service.add_intent(tag, patterns, jawaban)
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    await _reload_faq(update, silent=True)
    await update.message.reply_text(
        f"✅ Intent '{tag}' berhasil dibuat ({len(patterns)} pattern) & FAQ sudah di-reload.\n"
        f"Tambahkan keyword kalau perlu: /tambah_keyword {tag} [keyword]"
    )


async def _hapus_intent(update, text: str):
    tag = text[len("/hapus_intent"):].strip()
    if not tag:
        await update.message.reply_text("Format: /hapus_intent [tag]\nContoh: /hapus_intent jam_operasional_kantor")
        return

    if not intent_service.delete_intent(tag):
        await update.message.reply_text(f"Intent '{tag}' tidak ditemukan. Cek /list_intent.")
        return

    await _reload_faq(update, silent=True)
    await update.message.reply_text(f"✅ Intent '{tag}' dihapus & FAQ sudah di-reload.")
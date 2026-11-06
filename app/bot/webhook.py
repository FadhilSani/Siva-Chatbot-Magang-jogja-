"""
Entry point bot Telegram. Untuk development, pakai polling (paling gampang,
tidak butuh domain/HTTPS). Untuk production, bisa dipindah ke webhook mode.

Bot ini khusus menangani FAQ (Program Magang) -- tidak ada fitur
pendaftaran/status/jadwal magang.
"""
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from app.config import TELEGRAM_BOT_TOKEN, is_admin
from app.bot.router import route_message
from app.handlers import faq_menu_handler, admin_handler


async def start(update, context):
    chat_id = update.effective_chat.id

    if is_admin(chat_id):
        # Admin: langsung tampilkan menu admin (bukan sambutan user biasa).
        # Pakai text kosong -> jatuh ke branch "else" di admin_handler.handle(),
        # yaitu pesan "Halo Admin" + daftar command lengkap.
        await admin_handler.handle(update, context, "")
        return

    await update.message.reply_text(
        "Halo! 👋 Saya SIVA, asisten FAQ Program Magang.\n\n"
        "Tanyakan apa saja seputar magang, misalnya:\n"
        "• Bagaimana cara daftar magang?\n"
        "• Apa saja syarat magang?\n"
        "• Jam kerja magang bagaimana?\n\n"
        "Ketik /faq untuk lihat daftar topik yang bisa ditanyakan."
    )


async def faq_command(update, context):
    """Command /faq: khusus user biasa. Admin diarahkan ke command admin
    supaya tidak ada 2 "pengalaman" tercampur di akun yang sama."""
    chat_id = update.effective_chat.id

    if is_admin(chat_id):
        await update.message.reply_text(
            "ℹ️ /faq itu tampilan untuk user biasa.\n\n"
            "Kamu login sebagai admin -- pakai /list_intent untuk lihat "
            "semua topik FAQ beserta jumlah pattern & keyword-nya, atau "
            "kirim pesan apa saja (tanpa /) untuk lihat menu command admin."
        )
        return

    await faq_menu_handler.show_menu(update, context)


async def myid(update, context):
    """Command bantuan: /myid -> menampilkan chat_id pengirim.
    Dipakai sekali saja untuk mengisi ADMIN_CHAT_IDS di .env, boleh
    dihapus/diabaikan setelah itu."""
    chat_id = update.effective_chat.id
    status = "✅ terdaftar sebagai admin" if is_admin(chat_id) else "bukan admin"
    await update.message.reply_text(
        f"Chat ID kamu: {chat_id} ({status})\n\n"
        "Copy angka ini ke ADMIN_CHAT_IDS di file .env kalau kamu mau "
        "jadi admin bot ini."
    )


def build_app():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))
    app.add_handler(MessageHandler(filters.COMMAND, route_message))
    return app


def run_polling():
    app = build_app()
    print("SIVA Bot (FAQ-only) berjalan (polling mode)...")
    app.run_polling()


if __name__ == "__main__":
    run_polling()
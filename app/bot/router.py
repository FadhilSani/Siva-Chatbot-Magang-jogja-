from app.config import is_admin
from app.handlers import faq_handler, admin_handler


async def route_message(update, context):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # 1. Cek apakah pengirim adalah admin -> command edit intent/FAQ
    if is_admin(chat_id):
        return await admin_handler.handle(update, context, text)

    # 2. Bukan admin -> anggap ini pertanyaan FAQ bebas
    #    (dataset/cosine -> keyword -> Ollama, lihat faq_handler.py)
    await faq_handler.handle(update, context, text)
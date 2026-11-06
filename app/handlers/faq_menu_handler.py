import json

from app.ml.faq_matcher import DATA_PATH as FAQ_PATH

# Path FAQ di-reuse dari app/ml/faq_matcher.py (satu-satunya sumber path
# yang valid) -- kalau nama/lokasi file JSON-nya diganti, cukup ubah
# DATA_PATH di faq_matcher.py saja.


async def show_menu(update, context):
    """Menampilkan seluruh topik FAQ yang tersedia."""

    try:
        with open(FAQ_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        intents = data["intents"]

        lines = [
            " *Pusat Bantuan SIVA*",
            "",
            "Halo! Saya siap membantu menjawab berbagai pertanyaan mengenai Program Magang SIVA.",
            "",
            " *Topik yang dapat ditanyakan:*",
            ""
        ]

        for i, item in enumerate(intents, start=1):
            lines.append(f"{i}. {item['tag']}")

        lines.extend([
            "",
            "💬 Kamu tidak harus mengetik nama topiknya persis seperti di atas.",
            "Cukup tanyakan menggunakan kalimat yang natural, misalnya:",
            "",
            "• Bagaimana cara daftar magang?",
            "• Apa saja syarat magang?",
            "• Jam kerja magang bagaimana?",
            "• Apakah mendapat sertifikat?",
            "• Jadwal magang fleksibel tidak?",
            "",
            "Saya akan mencoba memahami pertanyaanmu dan memberikan jawaban yang sesuai. 😊"
        ])

        await update.message.reply_text(
            "\n".join(lines)
        )

    except FileNotFoundError:
        await update.message.reply_text(
            "❌ File intents_magang_v3.json tidak ditemukan."
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Terjadi kesalahan:\n{e}"
        )
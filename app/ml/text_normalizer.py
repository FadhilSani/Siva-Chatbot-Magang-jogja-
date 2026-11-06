import csv
import re
import os

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SLANG_PATH = os.path.join(BASE_DIR, "slang_by_intent.csv")

_stemmer = StemmerFactory().create_stemmer()
_stopword_remover = StopWordRemoverFactory().create_stop_word_remover()


def _load_slang_dict() -> dict:
    mapping = {}
    with open(SLANG_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slang = row["slang"].strip().lower()
            formal = row["formal"].strip().lower()
            if slang:
                mapping[slang] = formal
    return mapping


_SLANG_DICT = _load_slang_dict()


def normalize(text: str) -> str:
    """
    Ubah kata-kata slang/informal jadi bentuk formalnya, berdasarkan
    kamus slang.csv. Kata yang tidak ada di kamus dibiarkan apa adanya.

    Contoh: "gmn cr daftar magang" -> "gimana cara daftar magang"
    (tergantung isi kamus slang.csv)
    """
    words = re.findall(r"[a-zA-Z]+", text.lower())
    normalized_words = [_SLANG_DICT.get(w, w) for w in words]
    return " ".join(normalized_words)


def preprocess_full(text: str) -> str:
    """
    Versi lengkap: normalize (slang -> formal) -> hapus stopword -> stemming
    Bahasa Indonesia (Sastrawi). Dipakai oleh app/ml/faq_matcher.py untuk
    menormalisasi baik teks input user maupun "patterns"/"keywords" di
    dataset supaya perbandingannya konsisten (apple-to-apple).
    """
    text = normalize(text)
    text = _stopword_remover.remove(text)
    text = _stemmer.stem(text)
    return text

"""
FaqMatcher: pengganti IntentClassifier (SVM) yang dirancang supaya intent
bisa ditambah/diedit/dihapus lewat interface admin TANPA training ulang.

Beda dengan intent_model.pkl (SVM) yang vocabulary TF-IDF-nya beku (di-fit
sekali saat training), di sini vectorizer di-fit ULANG dari
data/intents_magang_v3.json setiap kali reload() dipanggil -- prosesnya
murah (hitungan milidetik-detik untuk ukuran data FAQ), bukan training
model ML beneran. Jadi alurnya: edit JSON -> panggil reload() -> langsung
kepakai.

Prioritas deteksi (predict()):
    1. Dataset match (cosine similarity) -- TF-IDF antara input user vs
       seluruh "patterns" di dataset. Ini pengecekan utama.
    2. Keyword match -- kalau lapis 1 gagal mengenali kata dari user
       (skor di bawah threshold), baru dicoba cocokkan ke "keywords".
       Ini jaring pengaman untuk kata pendek/khas yang polanya tidak
       persis sama dengan "patterns" di dataset.
    3. None -> caller (faq_handler.py) yang melempar ke Ollama sebagai
       fallback generatif.

Skema intent di JSON (field "keywords" opsional, boleh tidak diisi):
    {
      "tag": "cara_daftar_magang",
      "category": "...",
      "patterns": ["Bagaimana cara mendaftar magang?", ...],
      "responses": ["..."],
      "keywords": ["daftar", "pendaftaran"]
    }
"""

import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.text_normalizer import preprocess_full

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # .../app/ml -> .../app -> project root

# Sumber data sama persis dengan yang dipakai IntentClassifier lama --
# satu-satunya dataset intent yang valid ada di sini.
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "intents_magang_v3.json")

COSINE_SIMILARITY_THRESHOLD = 0.35

FALLBACK_ANSWER = (
    "Maaf, saya belum memahami pertanyaan tersebut 🙏\n"
    "Silakan coba gunakan kalimat lain atau hubungi Admin Magang "
    "untuk informasi lebih lanjut."
)


class FaqMatcher:
    def __init__(self, data_path: str = DATA_PATH, threshold: float = COSINE_SIMILARITY_THRESHOLD):
        self.data_path = data_path
        self.threshold = threshold
        self.reload()

    def reload(self):
        """Baca ulang data/intents_magang_v3.json dan fit ulang TF-IDF.

        Panggil ini setiap kali intent ditambah/diedit/dihapus (baik lewat
        edit manual file JSON maupun nanti dari web dashboard admin) --
        murah & instan, BUKAN training model ML (tidak ada cross-validation,
        tidak ada model .pkl yang disimpan).
        """
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        answers = {}
        keyword_map = {}  # keyword ternormalisasi -> tag
        pattern_texts = []
        pattern_tags = []

        for intent in data.get("intents", []):
            tag = intent["tag"]

            responses = intent.get("responses") or []
            if responses:
                answers[tag] = responses[0]

            for kw in intent.get("keywords", []):
                kw_norm = preprocess_full(kw)
                if kw_norm:
                    keyword_map[kw_norm] = tag

            for pattern in intent.get("patterns", []):
                pattern_texts.append(preprocess_full(pattern))
                pattern_tags.append(tag)

        self.answers = answers
        self.keyword_map = keyword_map
        self.pattern_tags = pattern_tags

        if pattern_texts:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            self.pattern_vectors = self.vectorizer.fit_transform(pattern_texts)
        else:
            self.vectorizer = None
            self.pattern_vectors = None

    def _keyword_match(self, normalized_text: str):
        """Cocokkan keyword sebagai substring dari teks yang sudah
        ternormalisasi (slang->formal, stopword removal, stemming)."""
        for kw_norm, tag in self.keyword_map.items():
            if kw_norm and kw_norm in normalized_text:
                return tag
        return None

    def _cosine_match(self, normalized_text: str):
        if self.pattern_vectors is None:
            return None, 0.0

        vec = self.vectorizer.transform([normalized_text])
        similarities = cosine_similarity(vec, self.pattern_vectors)[0]

        best_index = int(similarities.argmax())
        best_score = float(similarities[best_index])

        if best_score >= self.threshold:
            return self.pattern_tags[best_index], best_score

        return None, best_score

    def predict(self, text: str):
        """Return (tag, method, score). method: 'cosine' | 'keyword' | 'fallback'."""
        normalized_text = preprocess_full(text)

        # 1. Dataset match dulu (cosine similarity ke "patterns")
        tag, score = self._cosine_match(normalized_text)
        if tag is not None:
            return tag, "cosine", score

        # 2. Kalau dataset tidak mengenali -> coba keyword sebagai jaring pengaman
        tag = self._keyword_match(normalized_text)
        if tag is not None:
            return tag, "keyword", 1.0

        # 3. Tetap tidak ketemu -> caller (faq_handler.py) lempar ke Ollama
        return None, "fallback", 0.0

    def get_answer(self, text: str):
        """Return (answer_or_None, method, score). answer None -> caller
        yang lempar ke fallback (Ollama)."""
        tag, method, score = self.predict(text)

        if tag is None:
            return None, method, score

        return self.answers.get(tag, FALLBACK_ANSWER), method, score

# Yerel Geoteknik Soru-Cevap Asistanı (Offline RAG)

Microsoft **Foundry Local** ile **tamamen çevrimdışı** çalışan, geoteknik belgeler
üzerinde soru-cevap yapan bir RAG (Retrieval-Augmented Generation) uygulaması.
Kullanıcının sorusunu yerel bilgi tabanından getirdiği belge parçalarıyla
zenginleştirir ve cihaz üzerindeki bir dil modeliyle **kaynak göstererek** cevaplar.

> Çevrimdışı (offline) yerel RAG uygulaması. İnternet yalnızca ilk kurulumda gerekir;
> çalışma anında hiçbir buluta/servise veri gitmez.

---

## Özellikler

- 🔒 **%100 offline / cihazda** — LLM, embedding ve veritabanı hepsi yerelde.
- 📚 **Kaynak gösterir** — her cevabın altında hangi belgeden geldiği yazar.
- 🙅 **Uydurmaz** — bağlamda yoksa "bilmiyorum" der.
- 🌍 **Çok dilli** — Türkçe soruya Türkçe, İngilizce soruya İngilizce cevap.
- 🖥️ **İki arayüz** — masaüstünden çift tıkla açılan web arayüzü (Streamlit) + terminal (CLI).

---

## Mimari

Her şey tek makinede, buluta çıkmadan:

```
   Kullanıcı sorusu
        │
        ▼
   [ Arayüz ]  Streamlit web UI  /  CLI
        │
        ▼
   [ Pipeline ]  rag_pipeline.py  — Getir → Zenginleştir → Üret
        │
        ├──► [ Embedding ]  sentence-transformers (çok dilli, CPU)
        │
        ├──► [ Veri ]  SQLite: belge parçaları + embedding vektörleri
        │
        └──► [ LLM ]  Foundry Local (phi-4-mini, GPU) — OpenAI uyumlu API
        │
        ▼
   Kaynaklı cevap
```

## Teknoloji Yığını

| Bileşen | Seçim | Not |
|---|---|---|
| LLM çalışma zamanı | Microsoft Foundry Local | Cihazda offline LLM, OpenAI uyumlu REST |
| Dil modeli | `phi-4-mini` (GPU) | 4 GB VRAM'e sığıyor; Türkçe cevap kalitesi iyi, 7-15 sn |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` | Çok dilli; Türkçe eşleşme için kritik |
| Veritabanı | SQLite | Sunucusuz, tek dosya |
| Retrieval | Hibrit (vektör + anahtar kelime) | Kosinüs benzerliği + kelime eşleşme katkısı |
| Arayüz | Streamlit + CLI | Masaüstü kısayolundan başlar |

---

## Kurulum (bir kez, internet gerekir)

**1. Foundry Local** (Microsoft'un cihaz-üstü LLM çalışma zamanı):
```powershell
winget install Microsoft.FoundryLocal
foundry server start
foundry model download phi-4-mini
foundry model load phi-4-mini
```

**2. Python ortamı ve paketler:**
```powershell
python setup.py          # venv + bağımlılıklar
```

**3. Yapılandırma:** `.env` dosyası `.env.example`'dan üretilir; gerekirse düzenle.

**4. Bilgi tabanını kur** (belgeleri parçala, embed'le, SQLite'a yaz):
```powershell
venv\Scripts\python.exe src\ingest.py
```

---

## Kullanım

**Yol 1 — Masaüstü kısayolu (en kolay):** Masaüstündeki **"Geoteknik Asistan"**
kısayoluna çift tıkla. Servis + model başlar, tarayıcıda `http://localhost:8501`
açılır. (`run_app.bat` bunu yapar.)

**Yol 2 — Web arayüzü (elle):**
```powershell
foundry server start
foundry model load phi-4-mini
venv\Scripts\python.exe -m streamlit run app.py
```

**Yol 3 — Terminal (CLI):**
```powershell
venv\Scripts\python.exe src\chat.py
```

Örnek sorular:
- `Zemin etüdünde kaç adet sondaj kuyusu açılır?`
- `Yüzeysel temelin taşıma gücünü hangi faktörler etkiler?`
- `What is the minimum factor of safety for bearing capacity?`

---

## Bilgi Tabanı

Gerçek kurumsal kaynaklardan derlenmiş ~2.000 belge parçası (`data/raw/`):

| Kaynak | Kurum | Belge |
|---|---|---|
| 🇹🇷 DSİ | Devlet Su İşleri | Jeoteknik Etüt Şartnamesi |
| 🇹🇷 KGM | Karayolları Gn. Md. | Teknik Şartname |
| 🇺🇸 FHWA | ABD Karayolları | Shallow Foundations (GEC-6) + Soils and Foundations |
| 🇪🇺 Eurocode 7 | TS EN 1997-2 | Zemin araştırma ve deneyleri |

PDF → metin (`pypdf`; Türkçe tablolar için `pdfplumber`) → 1200 karakterlik
örtüşen parçalar → embedding → SQLite.

---

## Nasıl Çalışır

```
1. INGEST     Belge → parçala → embed'le → SQLite'a yaz            (src/ingest.py)
2. RETRIEVE   Soru → embed → hibrit benzerlik → en iyi K parça     (rag_pipeline.retrieve)
3. GENERATE   Soru + bağlam → Foundry LLM → kaynaklı cevap         (rag_pipeline.generate)
```

## Proje Yapısı

```
├── app.py                 # Streamlit web arayüzü
├── run_app.bat            # Servis+model+arayüz başlatıcı (masaüstü kısayolu buna işaret eder)
├── setup.py               # Otomatik kurulum
├── src/
│   ├── embeddings.py      # Metin → vektör (çok dilli, offline)
│   ├── database.py        # SQLite işlemleri
│   ├── rag_pipeline.py    # RAG çekirdeği (ingest/retrieve/generate)
│   ├── ingest.py          # data/raw/*.txt → bilgi tabanı
│   └── chat.py            # Terminal (CLI) arayüzü
├── tests/
│   ├── test_setup.py      # Kurulum doğrulama
│   ├── test_foundry_hello.py  # Foundry "Hello Model" testi
│   └── test_rag_eval.py   # Fonksiyonel değerlendirme
├── data/raw/              # Kaynak belgeler (PDF + çıkarılmış metin)
└── .env                   # Yapılandırma
```

---

## Tasarım Kararları

- **Neden Foundry Local?** Projenin amacı cihaz-üstü, offline LLM. Buluta (Azure OpenAI)
  veri göndermeden çalışır.
- **Neden embedding sentence-transformers?** Foundry Local kataloğunda embedding modeli
  yok; embedding yerel bir çok dilli modelle yapılıyor (plan da "local ones" diyor).
- **Neden CPU?** Makinedeki GPU (RTX 4060 Laptop, ~4 GB) modelin TensorRT sürümüne
  yetmedi (CUDA out-of-memory); CPU'da sorunsuz çalışıyor.
- **Neden hibrit retrieval?** Tekrar eden şartnamelerde saf vektör araması bazı
  spesifik kuralları kaçırabiliyor; anahtar kelime katkısı bunu iyileştirir.

## Sınırlamalar

- Çok tekrar eden belgelerde spesifik bir kural her zaman ilk K sonuca girmeyebilir
  (retrieval recall). Daha küçük chunk veya bir reranker ile iyileştirilebilir.
- `phi-4-mini` GPU'da bir yanıt tipik olarak 7-15 saniye sürer.
- Tüm embedding'ler her sorguda bellekte taranır; çok büyük ölçekte gerçek bir
  vektör indeksi (FAISS/sqlite-vec) gerekir.

## Kaynaklar

- [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/)
- [Sentence Transformers](https://www.sbert.net/)
- [SQLite](https://www.sqlite.org/docs.html)

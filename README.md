# Yerel Geoteknik RAG Asistanı

Microsoft Foundry Local ve SQLite kullanarak geliştirdiğim, tamamen çevrimdışı (offline) çalışan geoteknik soru-cevap uygulaması. DSİ, KGM, FHWA ve Eurocode 7 gibi kaynak dokümanlar üzerinden soru sorulduğunda ilgili kaynakları göstererek yanıt verir.

## Mimari

- **LLM:** Microsoft Foundry Local (`phi-4-mini`)
- **Embedding:** `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Veritabanı:** SQLite
- **Arayüz:** Streamlit + CLI

## Kurulum ve Çalıştırma

1. Foundry Local servisini ve modeli başlatın:
```bash
foundry server start
foundry model load phi-4-mini
```

2. Gerekli kütüphaneleri kurun:
```bash
python setup.py
```

3. Verileri işleyin:
```bash
venv\Scripts\python.exe src\ingest.py
```

4. Uygulamayı çalıştırın:
- **Web Arayüzü (Streamlit):** `run_app.bat` dosyasına çift tıklayın veya:
  ```bash
  venv\Scripts\python.exe -m streamlit run app.py
  ```
- **Terminal (CLI):**
  ```bash
  venv\Scripts\python.exe src\chat.py
  ```

## Proje Yapısı

- `app.py`: Streamlit web arayüzü
- `src/rag_pipeline.py`: RAG boru hattı (retrieval & generation)
- `src/database.py`: SQLite veritabanı yönetimi
- `src/embeddings.py`: Yerel metin vektörleştirme
- `src/ingest.py`: Veri yükleme ve veritabanına yazma
- `data/raw/`: Kaynak geoteknik kılavuzlar ve şartnameler
- `tests/`: Test scriptleri

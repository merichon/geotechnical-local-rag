# Jeoteknik Veri Kurulumu - Setup Guide

## Veri Kaynakları (Data Sources)

### 1. **Örnek Veriler (Included)**
Projede önceden hazırlanmış jeoteknik verileri vardır:

- `data/raw/sample_boring_log.txt` - Kazı kuyusu sonuçları
- `data/raw/foundation_design_guide.txt` - Temeller tasarım kılavuzu
- `data/raw/soil_test_results.txt` - Laboratuvar test sonuçları

### 2. **Türkiye Jeoloji Kurumu (TJK)**
- Web: https://www.jmo.org.tr/
- Jeolojik haritalar
- Bölgesel zemin profilleri

### 3. **USGS - United States Geological Survey**
- Web: https://www.usgs.gov/
- Dünya zemin veri tabanları
- Serbest indirilebilir veriler

### 4. **OpenStreetMap - Geological Maps**
- Bölgesel jeoloji verileri
- Serbest erişim

### 5. **ASCE 7 & Turkish Building Code**
- Tasarım standartları
- Zemin sınıflandırması tabloları

## Veriyi Yükleme

### Seçenek 1: Örnek Verileri Kullan (Recommended)

```bash
# Kurulum yapıldıktan sonra
python src/ingest.py
```

Bu script:
- `data/raw/` klasöründeki tüm dosyaları okur
- Embedding oluşturur
- SQLite veritabanına kaydeder
- Test sorgularıyla doğrular

### Seçenek 2: Kendi Verilerini Ekle

Adım 1: Jeoteknik dokümenta `data/raw/` klasörüne yerleştir
```
data/raw/
  ├── boring_log_istanbul.txt
  ├── soil_test_gaziantep.txt
  └── foundation_design_ankara.txt
```

Adım 2: Python scriptinden yükle
```python
from src.rag_pipeline import RAGPipeline

rag = RAGPipeline()

# Dosyayı oku ve yükle
with open("data/raw/boring_log_istanbul.txt") as f:
    content = f.read()

rag.ingest_document(content, "boring_log_istanbul.txt")

# Sorgula
result = rag.answer("Zemin taşıma kapasitesi nedir?")
print(result['answer'])
```

### Seçenek 3: Toplu Yükleme Scripti Oluştur

```python
# bulk_ingest.py
from src.rag_pipeline import RAGPipeline
from pathlib import Path

rag = RAGPipeline()
data_dir = Path("data/raw")

for doc_file in data_dir.glob("*.txt"):
    content = doc_file.read_text()
    rag.ingest_document(content, doc_file.name)
    print(f"✓ {doc_file.name}")

rag.close()
```

## Veri Formatı Önerileri

### Boring Log Format
```
BORING LOG
Location: [şehir, koordinatlar]
Depth: X meters
Date: YYYY-MM-DD

STRATUM:
0-2m: [zemin türü, yoğunluk]
2-5m: [zemin türü, yoğunluk]

GROUNDWATER:
Water table at X meters

SPT RESULTS:
Depth | N-value
1m    | 4
3m    | 8
```

### Lab Test Format
```
SAMPLE: [derinlik, tarafından]
Moisture: X%
Liquid Limit: X%
Plasticity Index: X
Cohesion: X kPa
Friction Angle: X°
```

### Tasarım Kılavuzu Format
```
SECTION: [başlık]
- Gereksinim 1
- Gereksinim 2
- Öneriler
```

## SQL Sorguları - Veri Kontrol

```bash
# Terminal açıp:
sqlite3 data/rag.db

# Komutlar:
.tables
SELECT COUNT(*) FROM documents;
SELECT original_file, COUNT(*) FROM documents GROUP BY original_file;
SELECT * FROM documents LIMIT 5;
```

## Test Sorguları (Turkish)

Örnek sorgular:
- "Zemin taşıma kapasitesi nedir?"
- "Su seviyesi ne derinlikte?"
- "Şantiye derinliği kaç metre?"
- "Clay örneğinin özelikleri nelerdir?"
- "Temelin minimum derinliği nedir?"
- "Konsolidasyon oturması ne kadar?"
- "SPT sonuçları nedir?"

## Veri Kalitesi

RAG kalitesi için önemli:
1. **Açıklık**: Dokümanda başlık, bölüm, tablolar olmalı
2. **Tamlık**: İlgili tüm detaylar olması
3. **Doğruluk**: Test sonuçları, hesaplamalar doğru
4. **Format**: Tutarlı yazım, standart birimler

## İleri Seçenekler

### Metadata Ekleme
```python
db.insert_document(
    content=text,
    embedding=embed,
    original_file="report.pdf",
    chunk_index=0,
    chunk_id="report_pdf_section_1_chunk_5"
)
```

### Veri Filtreleme
```python
# Spesifik dosyadan ara
results = db.search_by_content("bearing capacity")
filtered = [r for r in results if "Istanbul" in r['original_file']]
```

### PDF Desteği (Gelecek)
```bash
pip install pdfplumber
# PDF → text dönüştür → ingest et
```

## Sorun Giderme

**Soru: "No relevant documents found"**
- Veri eklendi mi? → `SELECT COUNT(*) FROM documents;`
- Chunk boyutu uygun mu? → Daha büyük chunk dene

**Soru: Cevaplar alakasız**
- Sorgu Türkçe mi İngilizce mi?
- Veri teknik içerik mi yoksa genel mi?

**Soru: Yavaş arama**
- Veritabanı büyük mü? → İndeks ekle
- Model parametreleri? → Temperature azalt

## Next: Week 2

- Foundry Local optimization
- Çok dillililik (Türkçe/İngilizce)
- Web arayüzü
- API servisi

---

**Hazır mısın? Başla:**
```bash
python src/ingest.py
```

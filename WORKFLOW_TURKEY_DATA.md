# Türkiye Veri → Local LLM Workflow

## Tam Süreç (5 Adım)

```
1. Download (KGM/DSI/MTA'dan indir)
        ↓
2. Convert (PDF/Word → Text)
        ↓
3. Prepare (Metadata ekle)
        ↓
4. Ingest (SQLite'e yükle)
        ↓
5. Query (RAG'ı test et)
```

---

## ADIM 1: DOWNLOAD (İndirme)

### A. KGM'den İndirme

**Seçenek 1: Web Sitesi (Hızlı)**
```
1. https://www.kgm.gov.tr/ aç
2. "Teknik Şartnameler" ara
3. PDF'leri indir
4. Örnek: teknik_sartname_2024.pdf
```

**Seçenek 2: Bölge Müdürlüğü (Kapsamlı)**
```
1. Ankara KGM 4. Bölge → https://www.ankara.gov.tr/karayollari-4bolge-mudurlugu
2. E-mail: ist1bm@kgm.gov.tr
3. Talep: "Boğaziçi Tüneli jeoteknik veri istiyorum"
4. Yanıt: ZIP dosya alırsın
```

### B. DSI'dan İndirme

**Seçenek 1: Teknik Döküman (PDF)**
```
1. https://www.dsi.gov.tr/ aç
2. "Jeoteknik Etüt Şartnamesi" PDF indir
3. Dosya: jeoteknik-etüt-şartnamesi.pdf
```

**Seçenek 2: Proje Verileri**
```
1. DSI 1. Bölge Müdürlüğü iletişim
2. E-mail: dsi1@dsi.gov.tr
3. Talep: "Asuan Barajı jeoteknik raporu"
4. Yanıt: Word/PDF dosya
```

### C. MTA'dan İndirme

**Otomatik (Web Portal)**
```
1. https://dergi.mta.gov.tr/ aç
2. "Geotechnical" ara
3. PDF makaleleri indir
4. ZIP'le birden fazlası indir
```

**Haritalar**
```
1. MTA Geosciences Portal
2. İstediğin bölgenin jeoloji haritasını indir
3. Açıklama metni kopyala
```

---

## ADIM 2: CONVERT (Dönüştürme)

### A. PDF → Text

**Seçenek 1: Online (Hızlı, Basit)**
```
https://www.ilovepdf.com/pdf_to_word
1. PDF yükle
2. "Convert to Word" tıkla
3. .docx indir
4. Word'ü text'e kopyala
```

**Seçenek 2: Python (Otomatik)**
```bash
pip install pdfplumber

python
>>> import pdfplumber
>>> with pdfplumber.open("report.pdf") as pdf:
...     text = "\n".join([page.extract_text() for page in pdf.pages])
...     with open("report.txt", "w", encoding="utf-8") as f:
...         f.write(text)
```

**Seçenek 3: Command Line (Linux/Mac)**
```bash
# Kurulum
brew install poppler  # Mac
sudo apt-get install poppler-utils  # Linux

# Kullanım
pdftotext report.pdf report.txt
```

### B. Word → Text

```bash
# Python
pip install python-docx

python
>>> from docx import Document
>>> doc = Document("report.docx")
>>> text = "\n".join([p.text for p in doc.paragraphs])
>>> with open("report.txt", "w", encoding="utf-8") as f:
...     f.write(text)
```

### C. Excel/CSV → Text

```python
import pandas as pd

# Excel'den oku
df = pd.read_excel("lab_tests.xlsx")

# Text'e çevir
text = df.to_string()

# Kaydet
with open("lab_tests.txt", "w", encoding="utf-8") as f:
    f.write(text)
```

---

## ADIM 3: PREPARE (Hazırlama)

### Dosya Adlandırması

```
[BÖLGE]_[KURUM]_[PROJE]_[YIL].txt

Örnekler:
- istanbul_kgm_bosphorus_tunnel_2023.txt
- ankara_dsi_asuan_dam_2022.txt
- izmir_mta_geology_2024.txt
```

### Metadata Başlığı Ekle

Dosyayı `data/raw/` klasörüne koy ve başına şunu ekle:

```
================================================================================
JEOTEKNIK VERİ KAYNAĞINDA
================================================================================
KURUM: Karayolları Genel Müdürlüğü
BÖLGE: İstanbul 1. Bölge
PROJE: Boğaziçi Tüneli Jeoteknik Etüdü
YIL: 2023
TİP: Boring Log / Laboratuvar Testi / Jeoloji Raporu

KONUM (GPS): 41.0082°N, 29.1761°E
DERINLIK: 0-50 meter
KAYNAK URL: https://www.kgm.gov.tr/...
İNDİRİLME TARİHİ: 2024-06-20
ORİJİNAL DOSYA: bogazici_tunnel_geo_survey.pdf

AÇIKLAMA:
[Proje hakkında 2-3 cümle yazıyorsun]

================================================================================
[ASIL VERİ İÇERİĞİ BAŞLADI]
================================================================================

[Boring log veya test sonuçları vb...]
```

### Örnek Hazırlık

**Ön:**
```
istanbul_kgm_bosphorus_tunnel_2023.txt
```

**Sonra:**
```
================================================================================
JEOTEKNIK VERİ KAYNAĞINDA
================================================================================
KURUM: Karayolları Genel Müdürlüğü
BÖLGE: İstanbul 1. Bölge
PROJE: Boğaziçi Tüneli Jeoteknik Etüdü
YIL: 2023
TİP: Boring Log

KONUM (GPS): 41.0082°N, 29.1761°E
DERINLIK: 0-50 meter
KAYNAK URL: https://www.kgm.gov.tr/
İNDİRİLME TARİHİ: 2024-06-20

AÇIKLAMA:
Boğaziçi Tüneli inşaatı için yapılan jeoteknik etüdü.
Kaya zemin özellikeleri ve jeoteknik parametreler içerir.

================================================================================

BORING LOG - BH-001

Derinlik: 0-50 meter
Konum: 41.0082°N, 29.1761°E

0-2m: Dolgu malzeme, kahverengi kumlu toprak, gevşek
2-5m: Kumlu silt, sarı kahverengi, orta yoğun
5-10m: Kil, gri-kahverengi, orta katı

SPT SONUÇLARI:
Derinlik (m) | Vuru Sayısı | N-değeri
1.0          | 4           | 4
3.0          | 8           | 8
5.0          | 12          | 12

...
```

---

## ADIM 4: INGEST (Yükleme)

### Otomatik Script

```bash
# data/raw/ klasörüne tüm .txt dosyalarını koy

cd /path/to/project
python scripts/process_downloaded_data.py
```

### Manuel Yükleme

```python
import sys
sys.path.insert(0, 'src')

from rag_pipeline import RAGPipeline

# Başlat
rag = RAGPipeline()

# Dosya oku
with open("data/raw/istanbul_kgm_bosphorus_tunnel_2023.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Yükle
rag.ingest_document(content, "istanbul_kgm_bosphorus_tunnel_2023.txt", chunk_size=400)

print("✓ Yükleme başarılı!")
```

### Kontrol Et

```bash
# SQLite'te check
sqlite3 data/rag.db
> SELECT COUNT(*) FROM documents;
> SELECT original_file, COUNT(*) as chunks FROM documents GROUP BY original_file;
> .quit
```

---

## ADIM 5: QUERY (Test Et)

### Komut Satırı

```python
import sys
sys.path.insert(0, 'src')
from rag_pipeline import RAGPipeline

rag = RAGPipeline()

# Sorgula
result = rag.answer("Boğaziçi Tüneli hangi derinlikte inşa edilecek?", top_k=3)

print("SORU:", result['query'])
print("\nCEVAP:", result['answer'])
print("\nKAYNAKLAR:")
for source in result['sources']:
    print(f"  - {source['file']} (benzerlik: {source['similarity']:.3f})")

rag.close()
```

### Web UI (Gelecek)

```bash
# Şimdilik mevcut değil, Week 2'de yapılacak
# python web_ui.py
# http://localhost:5000
```

---

## Komple Workflow Scripti

```bash
#!/bin/bash

# workflow.sh - Türkiye veri → Local LLM

echo "📥 ADIM 1: VERİ İNDİR"
echo "1. KGM/DSI/MTA'dan .pdf indir"
echo "2. data/raw/ klasörüne koy"
read -p "Devam? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📄 ADIM 2: PDF → TEXT (Online kullan ya da Python)"
    
    echo "🔧 ADIM 3: Metadata başlığını ekle"
    echo "   Örnek: KURUM, BÖLGE, PROJE, YIL vb"
    
    echo "⚙️  ADIM 4: İngestion"
    python scripts/process_downloaded_data.py
    
    echo "🔍 ADIM 5: Test sorgusu yap"
    python -c "
import sys
sys.path.insert(0, 'src')
from rag_pipeline import RAGPipeline

rag = RAGPipeline()
result = rag.answer('En önemli buluntu nedir?', top_k=2)
print(f'\\nCEVAP: {result[\"answer\"]}')
rag.close()
    "
    
    echo "✅ TAMAM!"
fi
```

---

## Hızlı Başlama (5 Dakika)

```bash
# 1. Bir PDF indir (KGM sitesinden)
# → https://www.kgm.gov.tr/

# 2. PDF'yi text'e çevir (online tool)
# → https://www.ilovepdf.com/pdf_to_word

# 3. Metadata ekle ve kaydet
# → data/raw/kgm_report_2024.txt

# 4. Yükle
python scripts/process_downloaded_data.py

# 5. Test et
python src/rag_pipeline.py

# Soru sor: "Bu raporda neler var?"
```

---

## Troubleshooting

**Soru: "PDF text'e çevirirken karakter sorunları oluyor"**
```python
# Çözüm: Encoding belirt
with open("file.txt", "w", encoding="utf-8") as f:
    f.write(text)

# Ya da temizle
text = text.encode('utf-8', 'ignore').decode('utf-8')
```

**Soru: "Dosya çok büyük, yükleme yavaş"**
```python
# Çözüm: Parçala
chunk_size = 600  # Daha büyük chunk
rag.ingest_document(content, filename, chunk_size=chunk_size)
```

**Soru: "Turkish karakterler (ç, ğ, ş vb) kötü görülüyor"**
```bash
# Terminal encoding'i ayarla
export PYTHONIOENCODING=utf-8
```

---

## İleri Seviye

### Otomatik Web Scraping

```python
import requests
from bs4 import BeautifulSoup

# KGM PDF listesini çek
url = "https://www.kgm.gov.tr/teknik-sartnameler"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# PDF linklerini bul ve indir
for link in soup.find_all('a', href=True):
    if 'pdf' in link['href']:
        print(f"Bulundu: {link.text}")
        # İndirme kodu...
```

### Database Sorguları

```sql
-- Hangi dosyalar yüklü?
SELECT DISTINCT original_file, COUNT(*) as chunks 
FROM documents 
GROUP BY original_file;

-- KGM verisi ara
SELECT content FROM documents 
WHERE original_file LIKE '%kgm%' 
LIMIT 5;

-- "Boğaziçi" ile ilgili
SELECT * FROM documents 
WHERE content LIKE '%Boğaziçi%';
```

---

## Next Steps

✅ **Week 1:** Veri kaynakları buldum  
→ **Week 2:** Türkiye veri ingest ettir  
→ **Week 3:** Multilingual RAG (TR/EN)  
→ **Week 4:** Web UI ve API  
→ **Week 5-6:** Deploy ve demo  

---

**Hazır mısın? Başla:**

```bash
# Terminal'de
cd ~/Claude/Projects/local\ llm\ deneme

# 1. Bir dosya indir ve koy
# data/raw/sample_report.txt

# 2. Yükle
python scripts/process_downloaded_data.py

# 3. Test et
python src/rag_pipeline.py
```

**💡 TİPİ:** İlk run yavaş olabilir (model yükleme), sonrası hızlı 🚀

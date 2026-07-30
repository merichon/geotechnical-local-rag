# Gerçek Jeoteknik Veri Kaynakları

## 1. USGS GeoLog Locator ⭐ (En İyi)
**Link:** https://webapps.usgs.gov/geologlocator/

- 7,000+ dijital borehole logs
- 1,700+ lokasyon (USA)
- Ücretsiz indirme
- Harita arayüzü

**Nasıl Kullanılır:**
1. Haritada bölge seç
2. Borehole tıkla
3. GIF/PDF indir
4. Text'e çevir → data/raw/ klasörüne kaydet

**Veri İçeriği:**
- Boring derinliği
- Zemin tasviri
- SPT sonuçları
- Jeolojik sınıflandırma

---

## 2. Utah Geological Survey
**Link:** https://borehole.geology.utah.gov/

- Komplett zemin verileri
- Interaktif harita
- Laboratuvar testleri
- Taşıma kapasitesi tahminleri

**Veri Türleri:**
- Boring logs
- SPT results
- Laboratory analysis
- Consolidation data

---

## 3. National Geotechnical Properties Database (BGS - UK) ⭐⭐ (En Kapsamlı)
**Link:** https://www.bgs.ac.uk/geological-research/science-facilities/engineering-geotechnical-capability/national-geotechnical-properties-database/

- 7,370 proje
- 178,436 borehole
- 5+ milyon lab testi
- CSV/Excel indir

**Veri Kalitesi:** En iyi (resmi test raporları)

---

## 4. ABD Eyalet Jeoloji Servisleri

### New York
https://www.usgs.gov/tools/new-york-borehole-well-log-viewer

### New Jersey
https://www.nj.gov/transportation/refdata/geologic/

### Kentucky
https://kgs.uky.edu/kgsmap/kytclinks.asp

### Massachusetts
https://mgs.geo.umass.edu/resources/subsurface

---

## 5. Geoengineer.org Online Library
**Link:** https://www.geoengineer.org/publications/online-library

- 25,000+ ücretsiz dokümant
- Araştırma makaleleri
- Teknik kitaplar
- Uygulamalı örnekler

**İçerik:**
- Geotechnical case studies
- Test prosedürleri
- Tasarım örnekleri
- Field observations

---

## 6. Türkiye Devlet Kaynakları ⭐⭐⭐

### Karayolları Genel Müdürlüğü (KGM) - Yol Projeleri
https://www.kgm.gov.tr/
- Tüm karayolu projeleri jeoteknik verileri
- Boring logs, SPT sonuçları
- 33 bölge müdürlüğü
- **EN KAPSAMLI TÜRKIYE VERİSİ**

### DSI - Devlet Su İşleri - Su Projeleri
https://www.dsi.gov.tr/
- Baraj, tünel, köprü jeoteknik etütleri
- Laboratuvar testleri (7+ milyon)
- 23 bölge müdürlüğü
- Permeabilite, stabilite, taşıma kapasitesi

### MTA - Maden Tetkik ve Arama
https://www.mta.gov.tr/
- Türkiye jeoloji+jeofizik haritaları
- Aktif fay haritaları
- Heyelan haritaları
- Open access dergi: https://dergi.mta.gov.tr/

### JMO (Jeoloji Mühendisleri Odası)
https://www.jmo.org.tr/
- Mühendislik standartları
- Teknik kılavuzlar

### AFAD - Afet ve Acil Durum Yönetimi
https://www.afad.gov.tr/
- Deprem zemin etkileri
- Risk haritaları
- Sismik veri

**ÖNEMLİ:** Detaylı rehber için `TURKEY_DATA_SOURCES.md` dosyasını oku!

---

## Download Stratejisi

### ADIM 1: Hızlı Test (2-3 dosya)
1. USGS GeoLog → 1 borehole indir
2. Utah Database → 1 lab test indir
3. BGS → 1 sample download

### ADIM 2: Gerçek Veri (5-10 dosya)
- Farklı coğrafyalar
- Farklı zemin türleri
- Farklı derinlikler
- Farklı yıllar

### ADIM 3: Toplu Veri (50+ dosya)
- Tüm eyaletten örnekler
- Belirli bölgeyi derinlemesine
- Uzun vadeli trend analizi

---

## Veri Formatı Dönüşümü

### PDF → Text
```bash
# Mac/Linux
pdftotext boring_log.pdf boring_log.txt

# Windows - https://www.xpdfreader.com/
xpdftotext boring_log.pdf boring_log.txt

# Python
pip install pdfplumber
python scripts/pdf_to_text.py
```

### CSV → Text
```python
import pandas as pd

df = pd.read_csv('lab_tests.csv')
text = df.to_string()

with open('lab_tests.txt', 'w') as f:
    f.write(text)
```

---

## Test Etme

```bash
# Dosyaları indir ve data/raw/ klasörüne koy
python scripts/process_downloaded_data.py

# System test et
python tests/test_setup.py

# RAG ile sorgula
python src/rag_pipeline.py
```

---

## Tips

✅ Farklı kaynakları karıştır (data çeşitliliği)
✅ Lokasyon bilgisi tut (metadata)
✅ Kaynak URL'sini dokümante et
✅ Başında tarih/yer belirtisi yaz
✅ Encoding UTF-8 kullan

❌ Sadece 1 kaynak kullanma
❌ Tesadüfi sırada kaydet
❌ Metadata bilgisi silme
❌ Çok büyük dosyalar (böl)

---

## Örnek İndirme

**Scenario:** New York'dan borehole log indir

1. USGS GeoLog Locator aç
2. "New York" ara
3. Manhattan bölge seç
4. BH-NYC-001 tıkla
5. PDF indir
6. Text'e çevir
7. Adlandır: `nyc_manhattan_boring_bh001_2024.txt`
8. Kaydet: `data/raw/nyc_manhattan_boring_bh001_2024.txt`
9. İçeriğin başına ekle:
   ```
   SOURCE: USGS GeoLog Locator
   LOCATION: Manhattan, New York, USA
   DATE_ACCESSED: 2024-06-20
   ORIGINAL_URL: [URL buraya]
   
   [Boring log içeriği]
   ```

---

## İlgili Araçlar

- **pdfplumber**: PDF text extraction (Python)
- **pandoc**: Dokümant dönüşümü
- **qgis**: GIS verileri görüntüleme
- **sqlite**: Veri depolama ve arama

---

**Ready? Kaynakları ziyaret et, veri indir, yükle! 🚀**

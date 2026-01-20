# Trafo Matcher

Trafo dizayn eşleştirme uygulaması. Doğal dil sorguları ile Excel dosyalarındaki trafo dizaynları arasında en uygun eşleşmeleri bulur.

## Özellikler

- **Doğal Dil Arama**: "100 kVA, 11000/415V Dyn11 trafo" gibi sorgularla arama
- **Akıllı Parametre Çıkarma**: Ollama LLM ile sorgulardan otomatik parametre çıkarma
- **Benzerlik Hesaplama**: Ağırlıklı parametre eşleştirme algoritması
- **Modern Arayüz**: React tabanlı chat arayüzü
- **Excel Desteği**: .xlsx ve .xlsm dosyalarını otomatik parse etme

## Kurulum

### 1. Gereksinimler

- Python 3.10+
- Node.js 18+
- Ollama (opsiyonel, AI desteği için)

### 2. Backend Kurulumu

```bash
cd backend

# Virtual environment oluştur (önerilen)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
copy .env.example .env
```

`.env` dosyasını düzenleyin:
```env
DESIGNS_DIRECTORY=C:/path/to/your/designs
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 3. Frontend Kurulumu

```bash
cd frontend

# Bağımlılıkları yükle
npm install
```

### 4. Ollama Kurulumu (Opsiyonel)

AI destekli parametre çıkarma için Ollama'yı kurun:

```bash
# Ollama'yı indirin: https://ollama.ai

# Model indirin (sunucu gücüne göre seçin)
ollama pull llama3.2        # 3B - düşük RAM
ollama pull phi3:mini       # 3.8B - düşük RAM
ollama pull llama3.2:7b     # 7B - orta RAM
```

## Çalıştırma

### Backend

```bash
cd backend
python run.py
```

API http://localhost:8000 adresinde çalışacak.

### Frontend

```bash
cd frontend
npm run dev
```

Uygulama http://localhost:3000 adresinde açılacak.

## Kullanım

1. Tarayıcıda http://localhost:3000 adresine gidin
2. Chat kutusuna aradığınız trafo özelliklerini yazın:
   - "100 kVA, 11000/415V Dyn11 trafo"
   - "250 kVA ONAN soğutmalı bakır sargılı"
   - "Boşta kayıp 150W altında 160 kVA"
3. En uygun dizaynlar benzerlik skorlarıyla listelenecek

## API Endpoints

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/search` | POST | Doğal dil ile arama |
| `/api/designs` | GET | Tüm dizaynları listele |
| `/api/designs/{id}` | GET | Tek dizayn detayı |
| `/api/refresh` | POST | Dizayn listesini yenile |
| `/api/health` | GET | Sistem durumu |

### Örnek Arama İsteği

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "100 kVA 11000/415V trafo", "max_results": 5}'
```

## Excel Dosya Yapısı

Uygulama aşağıdaki sheet'lerden veri okur:
- **Input specifications**: Güç, gerilim, kayıp, empedans vb.
- **Output**: Boyut, ağırlık, verimlilik, nüve bilgileri

### Desteklenen Parametreler

| Parametre | Açıklama |
|-----------|----------|
| rating_kva | Güç (kVA) |
| high_voltage_v | Yüksek gerilim (V) |
| low_voltage_v | Alçak gerilim (V) |
| vector_group | Bağlantı grubu (Dyn11, Yyn0) |
| no_load_loss_w | Boşta kayıp (W) |
| load_loss_w | Yük kaybı (W) |
| impedance_percent | Empedans (%) |
| cooling_type | Soğutma tipi (ONAN, ONAF) |
| core_material | Nüve malzemesi |

## Proje Yapısı

```
trafo-matcher/
├── backend/
│   ├── app/
│   │   ├── models/         # Pydantic modeller
│   │   ├── routers/        # API endpoint'leri
│   │   ├── services/       # İş mantığı
│   │   └── main.py         # FastAPI uygulama
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/     # React bileşenleri
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

## Geliştirme

### Yeni Parametre Ekleme

1. `backend/app/models/transformer.py` - TransformerSpecs modeline ekle
2. `backend/app/services/excel_parser.py` - Parse mantığını ekle
3. `backend/app/services/similarity.py` - Ağırlık ve tolerans ekle
4. `backend/app/services/ollama_service.py` - Prompt'a ekle

## Lisans

MIT

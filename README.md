# Araç Takip ve Anomali Analiz Sistemi

SQL Server, Python, FastAPI ve Streamlit ile geliştirilmiş toplu taşıma araç takip projesidir. Araçların GPS kayıtlarını ve durak geçişlerini saklar, bu verilerdeki anomalileri tespit eder, günlük rapor üretir ve sonuçları bir REST API ile dashboard üzerinden sunar.

## Özellikler

- **Veritabanı:** Araç, hat, durak, sefer, GPS takip, durak geçişi ve uyarı tabloları; raporlama için stored procedure'ler
- **Anomali tespiti:** Tespit edilen sorunlar `Alerts` tablosuna kaydedilir
  - `LOCATION_MISSING`: Belirli bir süredir konum göndermeyen araç
  - `STOP_MISSED`: Atlanan durak
  - `STOP_ORDER_ERROR`: Durakların yanlış sırayla geçilmesi
  - `SPEED_WARNING`: Hız sınırının aşılması
  - `TRIP_INCOMPLETE`: Tamamlanmamış sefer
- **Raporlama:** Hat ve araç bazında problem grafikleri, saatlik yoğunluk analizi ve `daily_report.xlsx` Excel raporu
- **REST API (FastAPI):** Araç, hat performansı, uyarı ve özet verileri için endpoint'ler
- **Dashboard (Streamlit):** Araç geçmişi, problemli araçlar, hat performansı ve son uyarılar

## Kullanılan Teknolojiler

- Microsoft SQL Server 2022 (Docker)
- Python 3.10+ (pyodbc, pandas, matplotlib, openpyxl)
- FastAPI
- Streamlit

## Proje Yapısı

```text
.
├── 01_database.sql           # Veritabanı ve tabloların oluşturulması
├── 02_sample_data.py         # Örnek test verilerinin üretilmesi
├── 02_anomaly_data.py        # Anomali senaryoları için test verileri
├── 03_queries.sql            # Kontrol sorguları
├── 04_stored_procedures.sql  # Raporlama stored procedure'leri
├── 05_anomaly_service.py     # Anomali tespit servisi
├── 06_reporting.py           # Grafik ve Excel raporu üretimi
├── 07_api/main.py            # FastAPI uygulaması
├── 08_dashboard/app.py       # Streamlit dashboard
├── requirements.txt
└── .env.example
```

## API Endpoint'leri

| Metot | Endpoint | Açıklama |
|-------|----------|----------|
| GET | `/` | API durum kontrolü |
| GET | `/vehicles` | Araç listesi |
| GET | `/vehicles/{plate}/history` | Plakaya göre araç hareket geçmişi |
| GET | `/routes/{routeCode}/performance` | Hat performansı |
| GET | `/alerts` | Uyarılar |
| GET | `/summary` | Günlük özet |

## Kurulum

### 1. SQL Server'ı başlatma

Mevcut Docker container'ını başlatın:

```bash
docker start sqlserver
docker ps
```

Yeni bir container gerekiyorsa:

```bash
export SQL_PASSWORD='<GÜÇLÜ_SQL_PAROLASI>'

docker run --name sqlserver \
  -e 'ACCEPT_EULA=Y' \
  -e "MSSQL_SA_PASSWORD=${SQL_PASSWORD}" \
  -p 1433:1433 \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

Bağlantı bilgileri:

```text
Sunucu     : localhost,1433
Veritabanı : AracTakipSistemi
Kullanıcı  : sa
Sürücü     : ODBC Driver 18 for SQL Server
```

### 2. Python ortamını hazırlama

Python 3.10+ ve ODBC Driver 18 kurulu olmalıdır.

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. SQL parolasını tanımlama

Python dosyaları parolayı `SQL_PASSWORD` environment variable üzerinden okur:

```bash
export SQL_PASSWORD='<GÜÇLÜ_SQL_PAROLASI>'
```

Gerçek parola README'ye veya Python dosyalarına yazılmamalıdır. Yeni terminal açıldığında değişkeni tekrar tanımlayın.

Alternatif olarak `.env.example` dosyasını `.env` olarak kopyalayıp parolayı oraya yazabilir ve terminalde yükleyebilirsiniz (`.env` git'e eklenmez):

```bash
cp .env.example .env
set -a; source .env; set +a
```

### 4. Veritabanını oluşturma

SQL Server'a bağlanın ve dosyaları şu sırayla çalıştırın:

1. `01_database.sql`
2. `04_stored_procedures.sql`

Doğru veritabanını kontrol etmek için:

```sql
SELECT DB_NAME() AS CurrentDatabase;
```

Sonuç `AracTakipSistemi` olmalıdır.

## Çalıştırma

Proje ana klasöründe aşağıdaki sırayı izleyin:

```bash
# Ana test verileri
python 02_sample_data.py

# Veri kesintisi ve durak atlama testleri
python 02_anomaly_data.py

# Anomalileri tespit edip Alerts tablosuna kaydet
python 05_anomaly_service.py

# Grafikleri ve daily_report.xlsx dosyasını üret
python 06_reporting.py
```

> `02_sample_data.py` ve `02_anomaly_data.py` yalnızca birer kez çalıştırılmalıdır. Tekrar çalıştırılmaları fazladan veya duplicate kayıt oluşturabilir.

`03_queries.sql` dosyası, oluşturulan verileri SQL Server üzerinde kontrol etmek için isteğe bağlı olarak çalıştırılabilir.

### FastAPI

Yeni bir terminal açın, sanal ortamı etkinleştirin ve parolayı tanımlayın:

```bash
source .venv/bin/activate
export SQL_PASSWORD='<GÜÇLÜ_SQL_PAROLASI>'
fastapi dev 07_api/main.py
```

```text
API : http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs
```

### Streamlit

Başka bir terminal açın, sanal ortamı etkinleştirin ve parolayı tanımlayın:

```bash
source .venv/bin/activate
export SQL_PASSWORD='<GÜÇLÜ_SQL_PAROLASI>'
streamlit run 08_dashboard/app.py
```

Dashboard adresi:

```text
http://localhost:8501
```

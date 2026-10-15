# Araç Takip ve Anomali Analiz Sistemi

SQL Server, Python, FastAPI ve Streamlit ile geliştirilmiş toplu taşıma araç takip projesidir.

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
python -m pip install pyodbc pandas matplotlib openpyxl "fastapi[standard]" streamlit
```

### 3. SQL parolasını tanımlama

Python dosyaları parolayı `SQL_PASSWORD` environment variable üzerinden okur:

```bash
export SQL_PASSWORD='<GÜÇLÜ_SQL_PAROLASI>'
```

Gerçek parola README'ye veya Python dosyalarına yazılmamalıdır. Yeni terminal açıldığında değişkeni tekrar tanımlayın.

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

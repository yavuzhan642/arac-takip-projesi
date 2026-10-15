
import pyodbc
import pandas as pd
import os
import matplotlib.pyplot as plt

def get_connection():
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=AracTakipSistemi;"
        "UID=sa;"
        f"PWD={os.getenv('SQL_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )

    return connection

# günlük toplam sefer sayısı
connection = get_connection()

daily_trips_df = pd.read_sql(
    """
    SELECT
        CAST(StartTime AS DATE) AS TripDate,
        COUNT(*) AS TripCount
    FROM Trips
    GROUP BY CAST(StartTime AS DATE)
    ORDER BY TripDate
    """,
    connection
)

print("\n--- Gunluk Toplam Sefer Sayisi ---")
print(daily_trips_df)

#aktif araç sayısı
active_vehicles_df = pd.read_sql(
    """
    SELECT
        COUNT(*) AS ActiveVehicleCount
    FROM Vehicle
    WHERE IsActive = 1
    """,
    connection
)

print("\n--- Aktif Arac Sayisi ---")
print(active_vehicles_df)

#konum göndermeyen araç sayısı
missing_vehicles_df = pd.read_sql(
    """
    SELECT
        COUNT(*) AS MissingVehicleCount
    FROM
    (
        SELECT
            Vehicle.VehicleId
        FROM Vehicle
        LEFT JOIN VehicleTracking
            ON Vehicle.VehicleId = VehicleTracking.VehicleId
        WHERE Vehicle.IsActive = 1
        GROUP BY Vehicle.VehicleId
        HAVING
            MAX(VehicleTracking.TrackingTime) < DATEADD(MINUTE, -15, GETDATE())
            OR MAX(VehicleTracking.TrackingTime) IS NULL
    ) AS MissingVehicles
    """,
    connection
)

print("\n--- Konum Gondermeyen Arac Sayisi ---")
print(missing_vehicles_df)

#hat bazında problem sayısı
route_problems_df = pd.read_sql(
    """
    SELECT
        Routes.RouteId,
        Routes.RouteCode,
        Routes.RouteName,
        COUNT(Alerts.AlertId) AS ProblemCount
    FROM Routes
    LEFT JOIN Alerts
        ON Routes.RouteId = Alerts.RouteId
    GROUP BY
        Routes.RouteId,
        Routes.RouteCode,
        Routes.RouteName
    ORDER BY ProblemCount DESC
    """,
    connection
)

print("\n--- Hat Bazinda Problem Sayisi ---")
print(route_problems_df)
#grafik oluşturma(route_problems)
plt.figure(figsize=(10, 5))

plt.bar(
    route_problems_df["RouteCode"],
    route_problems_df["ProblemCount"]
)

plt.title("Hatlara Gore Problem Sayisi")
plt.xlabel("Hat")
plt.ylabel("Problem Sayisi")

plt.tight_layout()
plt.show()

#araç bazında kaçırılan durak sayısı
missed_stops_df = pd.read_sql(
    """
    SELECT
        Vehicle.VehicleId,
        Vehicle.Plate,
        COUNT(MissedStops.StopId) AS MissedStopCount
    FROM Vehicle
    LEFT JOIN
    (
        SELECT
            Trips.VehicleId,
            RouteStops.StopId
        FROM Trips
        JOIN RouteStops
            ON Trips.RouteId = RouteStops.RouteId
        LEFT JOIN StopPassages
            ON Trips.TripId = StopPassages.TripId
            AND RouteStops.StopId = StopPassages.StopId
        WHERE StopPassages.PassageId IS NULL
    ) AS MissedStops
        ON Vehicle.VehicleId = MissedStops.VehicleId
    GROUP BY
        Vehicle.VehicleId,
        Vehicle.Plate
    ORDER BY MissedStopCount DESC
    """,
    connection
)

print("\n--- Arac Bazinda Kacirilan Durak Sayisi ---")
print(missed_stops_df)

#grafik oluşturma(missed_stops)
plt.figure(figsize=(10, 5))

plt.bar(
    missed_stops_df["Plate"],
    missed_stops_df["MissedStopCount"]
)

plt.title("En Fazla Durak Kaciran Araclar")
plt.xlabel("Plaka")
plt.ylabel("Kacirilan Durak Sayisi")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

#saatlik gps yoğunluğu
hourly_gps_df = pd.read_sql(
    """
    SELECT
        DATEPART(HOUR, TrackingTime) AS TrackingHour,
        COUNT(*) AS GPSCount
    FROM VehicleTracking
    GROUP BY
        DATEPART(HOUR, TrackingTime)
    ORDER BY
        TrackingHour
    """,
    connection
)

print("\n--- Saatlik GPS Kayit Yogunlugu ---")
print(hourly_gps_df)

#en problemli 5 araç ve 5 hat
top_5_routes_df = pd.read_sql(
    """
    SELECT TOP 5
        Routes.RouteId,
        Routes.RouteCode,
        Routes.RouteName,
        COUNT(Alerts.AlertId) AS ProblemCount
    FROM Routes
    JOIN Alerts
        ON Routes.RouteId = Alerts.RouteId
    GROUP BY
        Routes.RouteId,
        Routes.RouteCode,
        Routes.RouteName
    ORDER BY ProblemCount DESC
    """,
    connection
)

print("\n--- En Problemli 5 Hat ---")
print(top_5_routes_df)

#saatlere göre aktif araç sayısı
active_vehicles_hourly_df = pd.read_sql(
    """
    SELECT
        DATEPART(HOUR, TrackingTime) AS TrackingHour,
        COUNT(DISTINCT VehicleId) AS ActiveVehicleCount
    FROM VehicleTracking
    GROUP BY DATEPART(HOUR, TrackingTime)
    ORDER BY TrackingHour
    """,
    connection
)

print("\n--- Saatlere Gore Aktif Arac Sayisi ---")
print(active_vehicles_hourly_df)

#grafik oluşturma(active_vehicles)
plt.figure(figsize=(10, 5))

plt.bar(
    active_vehicles_hourly_df["TrackingHour"],
    active_vehicles_hourly_df["ActiveVehicleCount"]
)

plt.title("Saatlere Gore Aktif Arac Sayisi")
plt.xlabel("Saat")
plt.ylabel("Aktif Arac Sayisi")

plt.tight_layout()
plt.show()

#excel
#ozet
summary_df = pd.DataFrame(
    {
        "Metrik": [
            "Toplam Sefer Sayisi",
            "Aktif Arac Sayisi",
            "Konum Gondermeyen Arac Sayisi",
            "Toplam Problem Sayisi"
        ],
        "Deger": [
            daily_trips_df["TripCount"].sum(),
            active_vehicles_df["ActiveVehicleCount"].iloc[0],
            missing_vehicles_df["MissingVehicleCount"].iloc[0],
            route_problems_df["ProblemCount"].sum()
        ]
    }
)

print("\n--- Ozet ---")
print(summary_df)

#araclar
vehicles_report_df = pd.read_sql(
    """
    SELECT
        VehicleId,
        Plate,
        Brand,
        Model,
        IsActive
    FROM Vehicle
    ORDER BY VehicleId
    """,
    connection
)

print("\n--- Araclar ---")
print(vehicles_report_df)

#hatlar
routes_report_df = pd.read_sql(
    """
    SELECT
        RouteId,
        RouteCode,
        RouteName
    FROM Routes
    ORDER BY RouteId
    """,
    connection
)

print("\n--- Hatlar ---")
print(routes_report_df)

#kaçırılan duraklar
missed_stops_report_df = pd.read_sql(
    """
    SELECT
        Trips.TripId,
        Vehicle.VehicleId,
        Vehicle.Plate,
        Routes.RouteCode,
        RouteStops.StopId,
        Stops.StopName,
        RouteStops.StopSequence
    FROM Trips
    JOIN Vehicle
        ON Trips.VehicleId = Vehicle.VehicleId
    JOIN Routes
        ON Trips.RouteId = Routes.RouteId
    JOIN RouteStops
        ON Trips.RouteId = RouteStops.RouteId
    JOIN Stops
        ON RouteStops.StopId = Stops.StopId
    LEFT JOIN StopPassages
        ON Trips.TripId = StopPassages.TripId
        AND RouteStops.StopId = StopPassages.StopId
    WHERE StopPassages.PassageId IS NULL
    ORDER BY Trips.TripId, RouteStops.StopSequence
    """,
    connection
)

print("\n--- Kacirilan Duraklar ---")
print(missed_stops_report_df)

#uyarılar
alerts_report_df = pd.read_sql(
    """
    SELECT
        Alerts.AlertId,
        Alerts.AlertType,
        Alerts.AlertDate,
        Vehicle.Plate,
        Routes.RouteCode,
        Alerts.TripId,
        Alerts.Description
    FROM Alerts
    JOIN Vehicle
        ON Alerts.VehicleId = Vehicle.VehicleId
    LEFT JOIN Routes
        ON Alerts.RouteId = Routes.RouteId
    ORDER BY Alerts.AlertDate DESC
    """,
    connection
)

print("\n--- Uyarilar ---")
print(alerts_report_df)

#excel oluşturma kısmı
with pd.ExcelWriter(
    "daily_report.xlsx",
    engine="openpyxl"
) as writer:

    summary_df.to_excel(
        writer,
        sheet_name="Ozet",
        index=False
    )

    alerts_report_df.to_excel(
        writer,
        sheet_name="Uyarilar",
        index=False
    )

    missed_stops_report_df.to_excel(
        writer,
        sheet_name="Kacirilan Duraklar",
        index=False
    )

    vehicles_report_df.to_excel(
        writer,
        sheet_name="Araclar",
        index=False
    )

    routes_report_df.to_excel(
        writer,
        sheet_name="Hatlar",
        index=False
    )
connection.close()


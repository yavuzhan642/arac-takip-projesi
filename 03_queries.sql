
USE AracTakipSistemi;
GO

--sql sorguları

--aktif araçlar listesi
SELECT
    VehicleId,
    Plate,
    Brand,
    Model,
    IsActive
FROM Vehicle
WHERE IsActive = 1;

--son 15 dakikada konum göndermeyen araçlar
SELECT
    Vehicle.VehicleId,
    Vehicle.Plate,
    MAX(VehicleTracking.TrackingTime) AS LastTrackingTimr
FROM Vehicle
LEFT JOIN VehicleTracking ON Vehicle.VehicleId = VehicleTracking.VehicleId
WHERE Vehicle.IsActive = 1
GROUP BY
    Vehicle.VehicleId,
    Vehicle.Plate
HAVING
    MAX(VehicleTracking.TrackingTime) < DATEADD(MINUTE, -15, GETDATE())
    OR MAX(VehicleTracking.TrackingTime) IS NULL;

--bir aracın belirli tarih aralığındaki konum geçmişi
DECLARE @VehicleId INT = 1;
DECLARE @StartDate DATETIME = '2026-08-11 00:00:00';
DECLARE @EndDate DATETIME = '2026-08-13 00:00:00';

SELECT * FROM VehicleTracking
WHERE VehicleId = @VehicleId
    AND TrackingTime BETWEEN @StartDate AND @EndDate
ORDER BY TrackingTime;

--hat bazında çalışan araç sayısı
SELECT
    Routes.RouteId,
    Routes.RouteCode,
    Routes.RouteName,
    COUNT(DISTINCT Trips.VehicleId) AS VehicleCount
FROM Routes
LEFT JOIN Trips ON Routes.RouteId = Trips.RouteId
GROUP BY
    Routes.RouteId,
    Routes.RouteCode,
    Routes.RouteName
ORDER BY Routes.RouteId;

--araçların günlük sefer sayısı
SELECT
    Trips.VehicleId,
    CAST(Trips.StartTime AS DATE) AS TripDate,
    COUNT(*) AS TripCount
FROM Trips
GROUP BY
    Trips.VehicleId,
    CAST(Trips.StartTime AS DATE)
ORDER BY
    Trips.VehicleId,
    TripDate;

--hat bazında toplam durak geçiş sayısı
SELECT
    Routes.RouteId,
    Routes.RouteCode,
    Routes.RouteName,
    COUNT(StopPassages.PassageId) AS PassageCount
FROM Routes
LEFT JOIN Trips ON Routes.RouteId = Trips.RouteId
LEFT JOIN StopPassages ON Trips.TripId = StopPassages.TripId
GROUP BY
    Routes.RouteId,
    Routes.RouteCode,
    Routes.RouteName
ORDER BY Routes.RouteId;

--seferde geçilmesi gereken fakat geçilmeyen durakları bulma
SELECT
    Trips.TripId,
    Trips.RouteId,
    RouteStops.StopId,
    Stops.StopName,
    RouteStops.StopSequence
FROM Trips
JOIN RouteStops ON Trips.RouteId = RouteStops.RouteId
JOIN Stops ON RouteStops.StopId = Stops.StopId
LEFT JOIN StopPassages ON Trips.TripId = StopPassages.TripID
    AND RouteStops.StopId = StopPassages.StopId
WHERE StopPassages.PassageId IS NULL
ORDER BY 
    Trips.TripId,
    RouteStops.StopSequence;

--en fazla durak kaçıran ilk 10 araç
SELECT TOP 10
    Vehicle.VehicleId,
    Vehicle.Plate,
    COUNT(*) AS MissedStopCount
FROM Trips
JOIN Vehicle ON Trips.VehicleId = Vehicle.VehicleId
JOIN RouteStops ON Trips.RouteId = RouteStops.RouteId
LEFT JOIN StopPassages ON Trips.TripId = StopPassages.TripId
    AND RouteStops.StopId = StopPassages.StopId
WHERE StopPassages.PassageId IS NULL
GROUP BY
    Vehicle.VehicleId,
    Vehicle.Plate
ORDER BY MissedStopCount DESC;

--en fazla problem oluşan hatları sırala
SELECT
    Routes.RouteId,
    Routes.RouteCode,
    Routes.RouteName,
    COUNT(Alerts.AlertId) AS ProblemCount
FROM Routes
JOIN Alerts ON Routes.RouteId = Alerts.AlertId
GROUP BY
    Routes.RouteId,
    Routes.RouteCode,
    Routes.RouteName
ORDER BY ProblemCount DESC;

--araçların son gps kaydını ROW_NUMBER() vb. window function kullanarak getir

WITH LatestTracking AS
(
    SELECT
        VehicleTracking.*,
        ROW_NUMBER() OVER
        (
            PARTITION BY VehicleId
            ORDER BY TrackingTime DESC
        ) AS RowNumber 
    FROM VehicleTracking
)

SELECT *
FROM LatestTracking
WHERE RowNumber = 1
ORDER BY VehicleId;



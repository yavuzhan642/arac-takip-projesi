
--sp_GetVehicleHistory araç ve tarih parametrelerine göre konum geçmişi
GO
CREATE OR ALTER PROCEDURE sp_GetVehicleHistory
    @VehicleId INT,
    @StartDate DATETIME,
    @EndDate DATETIME
AS
BEGIN

    IF @VehicleId IS NULL
    BEGIN
        THROW 50001, 'VehicleId bos olamaz.', 1;
    END;

    IF @StartDate IS NULL OR @EndDate IS NULL
    BEGIN
        THROW 50002, 'Baslangic ve bitis tarihi bos olamaz.', 1;
    END;

    IF @StartDate > @EndDate
    BEGIN
        THROW 50003, 'Baslangic tarihi bitis tarihinden buyuk olamaz', 1;
    END;
    
    IF NOT EXISTS(
        SELECT 1
        FROM Vehicle
        WHERE VehicleId = @VehicleId
    )
    BEGIN
        THROW 50004, 'Arac bulunamadi.', 1;
    END;

    
    SELECT *
    FROM VehicleTracking
    WHERE VehicleId = @VehicleId
        AND TrackingTime BETWEEN @StartDate AND @EndDate
    ORDER BY TrackingTime;

END;
GO

EXEC sp_GetVehicleHistory
    @VehicleId = 1,
    @StartDate = '2026-08-11 00:00:00',
    @EndDate = '2026-08-13 00:00:00';

--sp_GetMissingVehicles belirlenen dakika boyunca konum göndermeyen araçlar
GO
CREATE OR ALTER PROCEDURE sp_GetMissingVehicles
    @Minutes INT = 15
AS
BEGIN

    IF @Minutes IS NULL OR @Minutes <= 0
    BEGIN
        THROW 50005, 'Dakika degeri 0 dan buyuk olmalidir', 1;
    END;

    SELECT
        Vehicle.VehicleId,
        Vehicle.Plate,
        MAX(VehicleTracking.TrackingTime) AS LastTrackingTime
    FROM Vehicle
    LEFT JOIN VehicleTracking ON Vehicle.VehicleId = VehicleTracking.VehicleId
    WHERE Vehicle.IsActive = 1
    GROUP BY
        Vehicle.VehicleId,
        Vehicle.Plate
    HAVING
        MAX(VehicleTracking.TrackingTime) < DATEADD(MINUTE, -@Minutes, GETDATE())
        OR MAX(VehicleTracking.TrackingTime) IS NULL;

END;
GO

EXEC sp_GetMissingVehicles @Minutes = 30;

--sp_GetMissedStops seferde atlanan durakların tespiti
GO
CREATE OR ALTER PROCEDURE sp_GetMissedStops
    @TripId INT

AS
BEGIN
    IF @TripId IS NULL
    BEGIN
        THROW 50006, 'TripId bos olamaz.', 1;
    END;

    IF NOT EXISTS 
    (
        SELECT 1
        FROM Trips
        WHERE TripId = @TripId
    )
    BEGIN
        THROW 50007, 'Sefer bulunamadi.', 1;
    END;

    SELECT
        Trips.TripId,
        Trips.RouteId,
        RouteStops.StopId,
        Stops.StopName,
        RouteStops.StopSequence
    FROM Trips
    JOIN RouteStops ON Trips.RouteId = RouteStops.RouteId
    JOIN Stops ON RouteStops.StopId = Stops.StopId
    LEFT JOIN StopPassages ON Trips.TripId = StopPassages.TripId
        AND RouteStops.StopId = StopPassages.StopId
    WHERE Trips.TripId = @TripId
        AND StopPassages.PassageId IS NULL
    ORDER BY RouteStops.StopSequence;

END;
GO

EXEC sp_GetMissedStops @TripId = 1;

--sp_GetRoutePerformance hat bazında sefer ve problem performansı
GO
CREATE OR ALTER PROCEDURE sp_GetRoutePerformance
    @RouteId INT = NULL
AS
BEGIN
    IF @RouteId IS NOT NULL
        AND NOT EXISTS 
        (
            SELECT 1
            FROM Routes
            WHERE RouteId = @RouteId
        )
    BEGIN
        THROW 50008, 'Hat bulunamadi.', 1;
    END;

    SELECT
        Routes.RouteId,
        Routes.RouteCode,
        Routes.RouteName,
        COUNT(DISTINCT Trips.TripId) AS TripCount,
        COUNT(DISTINCT Alerts.AlertId) AS ProblemCount
    FROM Routes
    LEFT JOIN Trips ON Routes.RouteId = Trips.RouteId
    LEFT JOIN Alerts ON Trips.TripId = Alerts.TripId
    WHERE @RouteId IS NULL OR Routes.RouteId = @RouteId
    GROUP BY
        Routes.RouteId,
        Routes.RouteCode,
        Routes.RouteName
    ORDER BY Routes.RouteId;

END;
GO

EXEC sp_GetRoutePerformance @RouteId = 4;

--sp_GetDailySummary günlük sistem özeti
GO
CREATE OR ALTER PROCEDURE sp_GetDailySummary
    @SummaryDate DATE = NULL
AS
BEGIN

    IF @SummaryDate IS NULL
    BEGIN
        SET @SummaryDate = CAST(GETDATE() AS DATE);
    END;

    SELECT
        @SummaryDate AS SummaryDate,
    (
        SELECT COUNT(*)
        FROM Vehicle
        WHERE IsActive = 1
    )AS ActiveVehicleCount,

    (
        SELECT COUNT(*)
        FROM Trips
        WHERE CAST(StartTime AS DATE) = @SummaryDate
    )AS TripCount,

    (
        SELECT COUNT(*)
        FROM VehicleTracking
        WHERE CAST(TrackingTime AS DATE) = @SummaryDate
    )AS TrackingCount,

    (
        SELECT COUNT(*)
        FROM StopPassages
        WHERE CAST(PassageTime AS DATE) = @SummaryDate
    )AS PassageCount,

    (
        SELECT COUNT(*)
        FROM Alerts
        WHERE CAST(AlertDate AS DATE) = @SummaryDate
    )AS AlertCount;

END;
GO

EXEC sp_GetDailySummary
    @SummaryDate = '2026-08-11';
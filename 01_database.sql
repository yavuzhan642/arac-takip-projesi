
CREATE DATABASE AracTakipSistemi;
GO

USE AracTakipSistemi;
GO

--tablolarımızı oluşturalım
CREATE TABLE Vehicle
(
    VehicleId INT IDENTITY(1,1) PRIMARY KEY,
    Plate NVARCHAR(20) NOT NULL UNIQUE,
    Brand NVARCHAR(30) NOT NULL,
    Model NVARCHAR(30) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE Routes
(
    RouteId INT IDENTITY(1,1) PRIMARY KEY,
    RouteCode NVARCHAR(20) NOT NULL UNIQUE,
    RouteName NVARCHAR(70) NOT NULL
);
GO

CREATE TABLE Stops
(
    StopId INT IDENTITY(1,1) PRIMARY KEY,
    StopCode NVARCHAR(20) NOT NULL UNIQUE,
    StopName NVARCHAR(70) NOT NULL,
    Latitude DECIMAL(9,6) NOT NULL
        CHECK (Latitude BETWEEN -90 AND 90),
    Longitude DECIMAL(9,6) NOT NULL
        CHECK (Longitude BETWEEN -90 AND 90)
);
GO

CREATE TABLE RouteStops
(
    RouteId INT NOT NULL REFERENCES Routes(RouteId),
    StopId INT NOT NULL REFERENCES Stops(StopId),
    StopSequence INT NOT NULL CHECK (StopSequence > 0),

    PRIMARY KEY (RouteId, StopId),
    UNIQUE (RouteId, StopSequence)
);
GO

CREATE TABLE Trips
(
    TripId INT IDENTITY(1,1) PRIMARY KEY,
    VehicleId INT NOT NULL REFERENCES Vehicle(VehicleId),
    RouteId INT NOT NULL REFERENCES Routes(RouteId),
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NULL,

    CHECK (EndTime IS NULL OR EndTime >= StartTime)
);
GO

CREATE TABLE VehicleTracking
(
    TrackingId INT IDENTITY(1,1) PRIMARY KEY,
    VehicleId INT NOT NULL REFERENCES Vehicle(VehicleId),
    TripId INT NULL REFERENCES Trips(TripId),

    Latitude DECIMAL(9,6) NOT NULL
        CHECK (Latitude BETWEEN -90 AND 90),

    Longitude DECIMAL(9,6) NOT NULL
        CHECK (Longitude BETWEEN -180 AND 180),
    
    Speed DECIMAL(6,2) NOT NULL
        CHECK (Speed >= 0),

    TrackingTime DATETIME NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE StopPassages
(
    PassageId INT IDENTITY(1,1) PRIMARY KEY,
    TripId INT NOT NULL REFERENCES Trips(TripId),
    StopId INT NOT NULL REFERENCES Stops(StopId),
    PassageTime DATETIME NOT NULL DEFAULT GETDATE(),
    PassageSequence INT NOT NULL CHECK (PassageSequence > 0)
);
GO

CREATE TABLE Alerts
(
    AlertId INT IDENTITY(1,1) PRIMARY KEY,

    AlertType NVARCHAR(50) NOT NULL
        CHECK (AlertType IN
        (
            'LOCATION_MISSING',
            'STOP_MISSED',
            'STOP_ORDER_ERROR',
            'SPEED_WARNING',
            'TRIP_INCOMPLETE'
        )),

    VehicleId INT NOT NULL REFERENCES Vehicle(VehicleId),
    RouteId INT NULL REFERENCES Routes(RouteId),
    TripId INT NULL REFERENCES Trips(TripId),

    AlertDate DATETIME NOT NULL DEFAULT GETDATE(),
    Description NVARCHAR(300) NOT NULL
);
GO

--veri sözlüğü:
--Vehicle: sistemdeki araç bilgilerini tutar
--Routes: toplu taşıma hatlarını ve bilgilerini tutar
--Stops: durak bilgilerini ve gps konumlarını tutar
--Routestops: hatlar ile duraklar arasındaki ilişkiyi tutar
--Trips: belirli bir aracın belirli bi aralıkta yaptığı hattı tutar
--VehicleTracking: araçlardan gelen gps, hız ve zaman gibi bilgileri tutar
--StopPassages: bir seferde gerçekleşen durak geçişlerini tutar
--Alerts: anormal durumları ve uyarılarını tutar

USE AracTakipSistemi
GO 

SELECT * FROM AracTakipSistemi;
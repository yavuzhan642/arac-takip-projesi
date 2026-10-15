
import pyodbc
import os

# 20 araç oluşturuyoruz
vehicles = []

for i in range(1,21):
    vehicle = (
        f"34 ABC {i:03}",
        "Mercedes",
        "Conecto",
        1
    )

    vehicles.append(vehicle)

for vehicle in vehicles:
    print(vehicle)


#5 hat oluşturma
routes = []

for i in range(1,6):
    route = (
        f"R{i:02}",
        f"Hat {i}"
    )

    routes.append(route)

for route in routes:
    print(route)


#50 durak oluşturma
stops = []

for i in range(1,51):
    stop = (
        f"D{i:03}",
        f"Durak {i}",
        round(41.000000 + (i*0.001),6),
        round(28.900000 + (i*0.001),6)
    )

    stops.append(stop)

for stop in stops:
    print(stop)


#hatlara sıralı durakları ata
route_stops = []

stop_id = 1

for route_id in range(1,6):

    for sequence in range(1,11):

        route_stop = (
            route_id,
            stop_id,
            sequence
        )

        route_stops.append(route_stop)

        stop_id += 1

for route_stop in route_stops:
    print(route_stop)


#trips e veri ekleme
from datetime import datetime,timedelta

trips = []

start_time = datetime.now() - timedelta(hours=2)

for vehicle_id in range(1,21):

    route_id = ((vehicle_id -1) % 5) + 1

    trip_start = start_time + timedelta(minutes=(vehicle_id - 1)*3)

    trip_end = trip_start + timedelta(hours=1)

    trip = (
        vehicle_id,
        route_id,
        trip_start,
        trip_end
    )

    trips.append(trip)

for trip in trips:
    print(trip)


#vehicletracking e veri ekleme
import random

vehicle_trackings = []

for trip_id, trip in enumerate(trips, start=1):

    vehicle_id = trip[0]
    route_id = trip[1]
    trip_start = trip[2]

    first_stop_id = ((route_id - 1) * 10) + 1

    for i in range(10):

        stop_id = first_stop_id + i

        latitude = stops[stop_id - 1][2]
        longitude = stops[stop_id - 1][3]

        speed = random.randint(20,60)

        tracking_time = trip_start + timedelta(minutes=i * 5)

        vehicle_tracking = (
            vehicle_id,
            trip_id,
            latitude,
            longitude,
            speed,
            tracking_time
        )

        vehicle_trackings.append(vehicle_tracking)

for vehicle_tracking in vehicle_trackings:
    print(vehicle_tracking)


#database ile bağlantı kuralım

connection = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=AracTakipSistemi;"
    "UID=sa;"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)

print("SQL Server baglantisi basarili")

cursor = connection.cursor()

#datamızı insertleyelim
cursor.executemany(
    """
    INSERT INTO Vehicle
    (
        Plate,
        Brand,
        Model,
        IsActive
    )
    VALUES (?, ?, ?, ?)
    """,
    vehicles
)

print("Vehicles hazir")

cursor.executemany(
    """
    INSERT INTO Routes
    (
        RouteCode,
        RouteName
    )
    VALUES (?, ?)
    """,
    routes
)

print("Routes hazir")

cursor.executemany(
    """
    INSERT INTO Stops
    (
        StopCode,
        StopName,
        Latitude,
        Longitude
    )
    VALUES (?, ?, ?, ?)
    """,
    stops
)

print("Stops hazir")

cursor.executemany(
    """
    INSERT INTO RouteStops
    (
        RouteId,
        StopId,
        StopSequence
    )
    VALUES (?, ?, ?)
    """,
    route_stops
)

print("RouteStops hazir")

cursor.executemany(
    """
    INSERT INTO Trips
    (
        VehicleId,
        RouteId,
        StartTime,
        EndTime
    )
    VALUES (?, ?, ?, ?)
    """,
    trips
)

print("Trips hazir")

cursor.executemany(
    """
    INSERT INTO VehicleTracking
    (
        VehicleId,
        TripId,
        Latitude,
        Longitude,
        Speed,
        TrackingTime
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    vehicle_trackings
)

print("VehicleTracking hazir")

connection.commit()

print("Tum veriler SQL Server'a basariyla eklendi")

connection.close()
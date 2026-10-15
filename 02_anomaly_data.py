
import pyodbc
from datetime import datetime, timedelta
import os

connection = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=AracTakipSistemi;"
    "UID=sa;"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)

cursor = connection.cursor()


# 3 ve 8. araca veri kesintisi uygulama
missing_vehicles_ids = [3,8]

for vehicle_id in range(1,21):

    if vehicle_id in missing_vehicles_ids:
        continue

    route_id = ((vehicle_id - 1) % 5) + 1
    stop_id = ((route_id - 1) * 10) + 1

    cursor.execute(
        """
        SELECT Latitude, Longitude
        FROM Stops
        WHERE StopId = ?
        """,
        stop_id
    )

    location = cursor.fetchone()

    tracking_time = datetime.now() - timedelta(
        minutes=(vehicle_id % 10) + 1
    )

    cursor.execute(
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
        VALUES (?, NULL, ?, ?, ?, ?)
        """,
        vehicle_id,
        location[0],
        location[1],
        30,
        tracking_time
    )

#trip4 te 4. durağı atlayalım, trip9 da 9. durağı atlayalım

cursor.execute(
    """
    SELECT TripId, RouteId, StartTime
    FROM Trips
    ORDER BY TripId
    """
)

trip_rows = cursor.fetchall()

for trip in trip_rows:

    trip_id = trip[0]
    route_id = trip[1]
    trip_start = trip[2]

    first_stop_id = ((route_id - 1) * 10) + 1

    passage_sequence = 1

    for expected_sequence in range(1, 11):

        if trip_id == 4 and expected_sequence == 4:
            continue

        if trip_id == 9 and expected_sequence == 9:
            continue

        stop_id = first_stop_id + expected_sequence - 1

        passage_time = trip_start + timedelta(
            minutes=(expected_sequence - 1) * 5
        )

        cursor.execute(
            """
            INSERT INTO StopPassages
            (
                TripId,
                StopId,
                PassageTime,
                PassageSequence
            )
            VALUES (?, ?, ?, ?)
            """,
            trip_id,
            stop_id,
            passage_time,
            passage_sequence
        )

        passage_sequence += 1

connection.commit()

print("Veri kesintisi ve durak atlama senaryolari eklendi")

connection.close()
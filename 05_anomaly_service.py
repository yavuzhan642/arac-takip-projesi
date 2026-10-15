
import pyodbc
import os
import pandas as pd

#sql server bağlantı kurma fonksiyonu
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

#alert e veri ekleme fonksiyonu
def insert_alert(
    cursor,
    alert_type,
    vehicle_id,
    route_id,
    trip_id,
    description
):

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM Alerts
        WHERE AlertType = ?
            AND VehicleId = ?
            AND ISNULL(RouteId, -1) = ISNULL(?, -1)
            AND ISNULL(TripId, -1) = ISNULL(?, -1)
            AND Description = ?
        """,
        alert_type,
        vehicle_id,
        route_id,
        trip_id,
        description
    )

    alert_count = cursor.fetchone()[0]

    if alert_count > 0:
        return

    cursor.execute(
        """
        INSERT INTO Alerts
        (
            AlertType,
            VehicleId,
            RouteId,
            TripId,
            Description
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        alert_type,
        vehicle_id,
        route_id,
        trip_id,
        description
    )

#LOCATION_MISSING
def check_location_missing(cursor, minutes=15):

    cursor.execute(
        """
        EXEC sp_GetMissingVehicles
            @Minutes = ?
        """,
        minutes
    )

    missing_vehicles = cursor.fetchall()

    for vehicle in missing_vehicles:

        vehicle_id = vehicle[0]
        plate = vehicle[1]
        last_tracking_time = vehicle[2]

        description = (
            f"{plate} plakali arac {minutes} dakikadir "
            f"GPS verisi gondermiyor. "
            f"Son konum zamani: {last_tracking_time}"
        )

        insert_alert(
            cursor,
            "LOCATION_MISSING",
            vehicle_id,
            None,
            None,
            description
        )

#STOP_MISSED
def check_stop_missed(cursor):

    cursor.execute(
        """
        SELECT TripId, VehicleId
        FROM Trips
        """
    )

    trips = cursor.fetchall()

    for trip in trips:

        trip_id = trip[0]
        vehicle_id = trip[1]

        cursor.execute(
            """
            EXEC sp_GetMissedStops
                @TripId = ?
            """,
            trip_id
        )

        missed_stops = cursor.fetchall()

        for missed_stop in missed_stops:

            route_id = missed_stop[1]
            stop_id = missed_stop[2]
            stop_name = missed_stop[3]
            stop_sequence = missed_stop[4]

            description = (
                f"Trip {trip_id} seferinde "
                f"{stop_name} (StopId: {stop_id}, "
                f"Sira: {stop_sequence}) duragi atlandi."
            )

            insert_alert(
                cursor,
                "STOP_MISSED",
                vehicle_id,
                route_id,
                trip_id,
                description
            )

#STOP_ORDER_ERROR
def check_stop_order_error(cursor):

    cursor.execute(
        """
        WITH PassageOrder AS
        (
            SELECT
                StopPassages.TripId,
                Trips.VehicleId,
                Trips.RouteId,
                StopPassages.StopId,
                Stops.StopName,
                RouteStops.StopSequence,

                LAG(RouteStops.StopSequence) OVER
                (
                    PARTITION BY StopPassages.TripId
                    ORDER BY StopPassages.PassageTime
                ) AS PreviousStopSequence

            FROM StopPassages

            JOIN Trips
                ON StopPassages.TripId = Trips.TripId

            JOIN RouteStops
                ON Trips.RouteId = RouteStops.RouteId
                AND StopPassages.StopId = RouteStops.StopId

            JOIN Stops
                ON StopPassages.StopId = Stops.StopId
        )

        SELECT
            TripId,
            VehicleId,
            RouteId,
            StopId,
            StopName,
            StopSequence,
            PreviousStopSequence
        FROM PassageOrder
        WHERE StopSequence < PreviousStopSequence
        """
    )

    order_errors = cursor.fetchall()

    for error in order_errors:

        trip_id = error[0]
        vehicle_id = error[1]
        route_id = error[2]
        stop_id = error[3]
        stop_name = error[4]
        stop_sequence = error[5]
        previous_sequence = error[6]

        description = (
            f"Trip {trip_id} seferinde durak sirasi hatali. "
            f"{stop_name} (StopId: {stop_id}) "
            f"beklenen sira: {stop_sequence}, "
            f"onceki durak sirasi: {previous_sequence}."
        )

        insert_alert(
            cursor,
            "STOP_ORDER_ERROR",
            vehicle_id,
            route_id,
            trip_id,
            description
        )

#SPEED_WARNING
def check_speed_warning(cursor, speed_limit=80):

    cursor.execute(
        """
        SELECT
            VehicleTracking.VehicleId,
            VehicleTracking.TripId,
            Trips.RouteId,
            VehicleTracking.Speed,
            VehicleTracking.TrackingTime
        FROM VehicleTracking
        LEFT JOIN Trips
            ON VehicleTracking.TripId = Trips.TripId
        WHERE VehicleTracking.Speed > ?
        """,
        speed_limit
    )

    speed_warnings = cursor.fetchall()

    for warning in speed_warnings:

        vehicle_id = warning[0]
        trip_id = warning[1]
        route_id = warning[2]
        speed = warning[3]
        tracking_time = warning[4]

        description = (
            f"Arac hiz limitini asti. "
            f"Hiz: {speed} km/h, "
            f"Limit: {speed_limit} km/h, "
            f"Zaman: {tracking_time}."
        )

        insert_alert(
            cursor,
            "SPEED_WARNING",
            vehicle_id,
            route_id,
            trip_id,
            description
        )

#TRIP_INCOMPLETE
def check_trip_incomplete(cursor):

    cursor.execute(
        """
        SELECT
            Trips.TripId,
            Trips.VehicleId,
            Trips.RouteId,
            COUNT(DISTINCT RouteStops.StopId) AS ExpectedStopCount,
            COUNT(DISTINCT StopPassages.StopId) AS PassedStopCount
        FROM Trips
        JOIN RouteStops
            ON Trips.RouteId = RouteStops.RouteId
        LEFT JOIN StopPassages
            ON Trips.TripId = StopPassages.TripId
            AND RouteStops.StopId = StopPassages.StopId
        WHERE Trips.EndTime IS NOT NULL
        GROUP BY
            Trips.TripId,
            Trips.VehicleId,
            Trips.RouteId
        HAVING
            COUNT(DISTINCT StopPassages.StopId)
            <
            COUNT(DISTINCT RouteStops.StopId)
        """
    )

    incomplete_trips = cursor.fetchall()

    for trip in incomplete_trips:

        trip_id = trip[0]
        vehicle_id = trip[1]
        route_id = trip[2]
        expected_stop_count = trip[3]
        passed_stop_count = trip[4]

        description = (
            f"Trip {trip_id} tamamlanmadan sona erdi. "
            f"Beklenen durak sayisi: {expected_stop_count}, "
            f"gecilen durak sayisi: {passed_stop_count}."
        )

        insert_alert(
            cursor,
            "TRIP_INCOMPLETE",
            vehicle_id,
            route_id,
            trip_id,
            description
        )

#bütün anomaly kontrollerini tek yerde toplama
def run_anomaly_checks(cursor):

    check_location_missing(cursor, 15)
    check_stop_missed(cursor)
    check_stop_order_error(cursor)
    check_speed_warning(cursor, 80)
    check_trip_incomplete(cursor)

    print("Anomali kontrolleri tamamlandi.")


try:
    connection = get_connection()
    cursor = connection.cursor()

    #select işlemi
    cursor.execute(
        """
        SELECT
            VehicleId,
            Plate,
            Brand,
            Model
        FROM Vehicle
        WHERE IsActive = 1
        """
    )

    vehicles = cursor.fetchall()

    columns = [column[0] for column in cursor.description]

    vehicle_df = pd.DataFrame(
        [tuple(vehicle) for vehicle in vehicles],
        columns=columns
    )
    print("\n----- Aktif Araclar DataFrame -----")
    print(vehicle_df)

    #for vehicle in vehicles:
    #    print(vehicle)

    #stored procedure çağırma
    cursor.execute(
        """
        EXEC sp_GetVehicleHistory
            @VehicleId = ?,
            @StartDate = ?,
            @EndDate = ?
        """,
        1,
        "2026-08-11",
        "2026-08-13"
    )

    history_rows = cursor.fetchall()

    history_columns = [column[0] for column in cursor.description]

    history_df = pd.DataFrame(
        [tuple(row) for row in history_rows],
        columns=history_columns
    )

    print("\n--- Arac Konum Gecmisi DataFrame ---")
    print(history_df)

    #anomali kontrolü
    run_anomaly_checks(cursor)
    connection.commit()
    print("Tespit edilen uyarilar Alerts tablosuna kaydedildi.")

except pyodbc.Error as error:
    if connection:
        connection.rollback()

    print("SQL Server hatasi:", error)

finally:
    if cursor:
        cursor.close()

    if connection:
        connection.close()


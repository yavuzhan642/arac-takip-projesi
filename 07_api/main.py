
from fastapi import FastAPI, HTTPException
import pyodbc
import os
from datetime import date

app = FastAPI()

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

@app.get("/")
def root():
    return{
        "message": "Arac Takip Sistemi API calisiyor"
    }

#GET /vehicles – araç listesi
@app.get("/vehicles")
def get_vehicles():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                VehicleId,
                Plate,
                Brand,
                Model,
                IsActive
            FROM Vehicle
            ORDER BY VehicleId
            """
        )

        rows = cursor.fetchall()

        vehicles = []

        for row in rows:
            vehicles.append(
                {
                    "vehicleId": row[0],
                    "plate": row[1],
                    "brand": row[2],
                    "model": row[3],
                    "isActive": bool(row[4])
                }
            )

        return vehicles

    except pyodbc.Error:
        raise HTTPException(
            status_code=500,
            detail="Veritabani hatasi olustu."
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

#GET /vehicles/{plate}/history – aracın hareket geçmişi
@app.get("/vehicles/{plate}/history")
def get_vehicle_history(plate: str):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Once plakadan araci bul
        cursor.execute(
            """
            SELECT VehicleId
            FROM Vehicle
            WHERE Plate = ?
            """,
            plate
        )

        vehicle = cursor.fetchone()

        if vehicle is None:
            raise HTTPException(
                status_code=404,
                detail="Arac bulunamadi."
            )

        vehicle_id = vehicle[0]

        # Aracin konum gecmisini getir
        cursor.execute(
            """
            SELECT
                TrackingId,
                VehicleId,
                TripId,
                Latitude,
                Longitude,
                Speed,
                TrackingTime
            FROM VehicleTracking
            WHERE VehicleId = ?
            ORDER BY TrackingTime
            """,
            vehicle_id
        )

        rows = cursor.fetchall()

        history = []

        for row in rows:
            history.append(
                {
                    "trackingId": row[0],
                    "vehicleId": row[1],
                    "tripId": row[2],
                    "latitude": float(row[3]),
                    "longitude": float(row[4]),
                    "speed": float(row[5]),
                    "trackingTime": row[6].isoformat()
                }
            )

        return history

    except HTTPException:
        raise

    except pyodbc.Error:
        raise HTTPException(
            status_code=500,
            detail="Veritabani hatasi olustu."
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

#GET /routes{routeCode}/performance - hat performansı
@app.get("/routes/{routeCode}/performance")
def get_route_performance(routeCode: str):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # RouteCode ile RouteId bul
        cursor.execute(
            """
            SELECT RouteId
            FROM Routes
            WHERE RouteCode = ?
            """,
            routeCode
        )

        route = cursor.fetchone()

        if route is None:
            raise HTTPException(
                status_code=404,
                detail="Hat bulunamadi."
            )

        route_id = route[0]

        # Stored Procedure cagirma
        cursor.execute(
            """
            EXEC sp_GetRoutePerformance
                @RouteId = ?
            """,
            route_id
        )

        row = cursor.fetchone()

        return {
            "routeId": row[0],
            "routeCode": row[1],
            "routeName": row[2],
            "tripCount": row[3],
            "problemCount": row[4]
        }

    except HTTPException:
        raise

    except pyodbc.Error:
        raise HTTPException(
            status_code=500,
            detail="Veritabani hatasi olustu."
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

#GET /alerts - uyarı listesi
@app.get("/alerts")
def get_alerts():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
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
            """
        )

        rows = cursor.fetchall()

        alerts = []

        for row in rows:
            alerts.append(
                {
                    "alertId": row[0],
                    "alertType": row[1],
                    "alertDate": row[2].isoformat(),
                    "plate": row[3],
                    "routeCode": row[4],
                    "tripId": row[5],
                    "description": row[6]
                }
            )

        return alerts

    except pyodbc.Error:
        raise HTTPException(
            status_code=500,
            detail="Veritabani hatasi olustu."
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

#GET /summary - sistem özeti
@app.get("/summary")
def get_summary(summaryDate: date | None = None):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            EXEC sp_GetDailySummary
                @SummaryDate = ?
            """,
            summaryDate
        )

        row = cursor.fetchone()

        return {
            "summaryDate": str(row[0]),
            "activeVehicleCount": row[1],
            "tripCount": row[2],
            "trackingCount": row[3],
            "passageCount": row[4],
            "alertCount": row[5]
        }

    except pyodbc.Error:
        raise HTTPException(
            status_code=500,
            detail="Veritabani hatasi olustu."
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()



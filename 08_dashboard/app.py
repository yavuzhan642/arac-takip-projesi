import streamlit as st
import pyodbc
import pandas as pd
import os

#sayfa ayarları
st.set_page_config(
    page_title="Arac Takip Sistemi",
    page_icon="🚌",
    layout="wide"
)

st.title("Arac Takip ve Anomali Analiz Sistemi")
st.write("Toplu tasima arac takip sistemi yonetim paneli.")

#sql server bağlantısı
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


# SQL sonucunu DataFrame'e cevirmek icin yardimci fonksiyon
def get_dataframe(cursor, query, params=None):

    if params:
        cursor.execute(query, *params)
    else:
        cursor.execute(query)

    rows = cursor.fetchall()

    columns = [
        column[0]
        for column in cursor.description
    ]

    dataframe = pd.DataFrame(
        [tuple(row) for row in rows],
        columns=columns
    )

    return dataframe


connection = None
cursor = None


try:

    connection = get_connection()
    cursor = connection.cursor()

    #toplam aktif araç sayısı
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM Vehicle
        WHERE IsActive = 1
        """
    )

    active_vehicle_count = cursor.fetchone()[0]

    #bugunku sefer sayısı
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM Trips
        WHERE CAST(StartTime AS DATE) = CAST(GETDATE() AS DATE)
        """
    )

    today_trip_count = cursor.fetchone()[0]

    #bugunku uyarı sayısı
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM Alerts
        WHERE CAST(AlertDate AS DATE) = CAST(GETDATE() AS DATE)
        """
    )

    today_alert_count = cursor.fetchone()[0]

    #ust bilgi kartları
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Aktif Arac Sayisi",
            value=active_vehicle_count
        )

    with col2:
        st.metric(
            label="Bugunku Sefer Sayisi",
            value=today_trip_count
        )

    with col3:
        st.metric(
            label="Bugunku Uyari Sayisi",
            value=today_alert_count
        )


    st.divider()

    #hat secme filtresi
    routes_df = get_dataframe(
        cursor,
        """
        SELECT
            RouteId,
            RouteCode,
            RouteName
        FROM Routes
        ORDER BY RouteId
        """
    )

    route_options = ["Tumu"] + routes_df["RouteCode"].tolist()

    #arac secme filtresi
    vehicles_df = get_dataframe(
        cursor,
        """
        SELECT
            VehicleId,
            Plate
        FROM Vehicle
        ORDER BY VehicleId
        """
    )

    vehicle_options = vehicles_df["Plate"].tolist()


    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        selected_route = st.selectbox(
            "Hat Sec",
            route_options
        )

    with filter_col2:
        selected_vehicle = st.selectbox(
            "Arac Sec",
            vehicle_options
        )


    st.divider()

    #arac hareket gecmisi
    st.subheader("Arac Hareket Gecmisi")

    vehicle_history_df = get_dataframe(
        cursor,
        """
        SELECT
            VehicleTracking.TrackingId,
            Vehicle.Plate,
            VehicleTracking.TripId,
            VehicleTracking.Latitude,
            VehicleTracking.Longitude,
            VehicleTracking.Speed,
            VehicleTracking.TrackingTime
        FROM VehicleTracking
        JOIN Vehicle
            ON VehicleTracking.VehicleId = Vehicle.VehicleId
        WHERE Vehicle.Plate = ?
        ORDER BY VehicleTracking.TrackingTime
        """,
        (selected_vehicle,)
    )

    st.dataframe(
        vehicle_history_df,
        width="stretch",
        hide_index=True
    )


    st.divider()

    #problemli araclar
    st.subheader("Problemli Araclar")

    problematic_vehicles_df = get_dataframe(
        cursor,
        """
        SELECT TOP 5
            Vehicle.VehicleId,
            Vehicle.Plate,
            COUNT(Alerts.AlertId) AS ProblemCount
        FROM Vehicle
        JOIN Alerts
            ON Vehicle.VehicleId = Alerts.VehicleId
        LEFT JOIN Routes
            ON Alerts.RouteId = Routes.RouteId
        WHERE
            ? = 'Tumu'
            OR Routes.RouteCode = ?
        GROUP BY
            Vehicle.VehicleId,
            Vehicle.Plate
        ORDER BY ProblemCount DESC
        """,
        (
            selected_route,
            selected_route
        )
    )

    st.dataframe(
        problematic_vehicles_df,
        width="stretch",
        hide_index=True
    )


    st.divider()

    #hat performans grafikleri
    st.subheader("Hat Performansi")

    route_performance_df = get_dataframe(
        cursor,
        """
        SELECT
            Routes.RouteCode,
            Routes.RouteName,
            COUNT(DISTINCT Trips.TripId) AS TripCount,
            COUNT(DISTINCT Alerts.AlertId) AS ProblemCount
        FROM Routes

        LEFT JOIN Trips
            ON Routes.RouteId = Trips.RouteId

        LEFT JOIN Alerts
            ON Routes.RouteId = Alerts.RouteId

        WHERE
            ? = 'Tumu'
            OR Routes.RouteCode = ?

        GROUP BY
            Routes.RouteCode,
            Routes.RouteName

        ORDER BY Routes.RouteCode
        """,
        (
            selected_route,
            selected_route
        )
    )


    graph_col1, graph_col2 = st.columns(2)

    with graph_col1:

        st.write("Hatlara Gore Sefer Sayisi")

        st.bar_chart(
            route_performance_df,
            x="RouteCode",
            y="TripCount"
        )


    with graph_col2:

        st.write("Hatlara Gore Problem Sayisi")

        st.bar_chart(
            route_performance_df,
            x="RouteCode",
            y="ProblemCount"
        )


    st.divider()

    #son oluşan uyarılar
    st.subheader("Son Olusan Uyarilar")

    latest_alerts_df = get_dataframe(
        cursor,
        """
        SELECT TOP 10
            Alerts.AlertType,
            Vehicle.Plate,
            Routes.RouteCode,
            Alerts.TripId,
            Alerts.AlertDate,
            Alerts.Description
        FROM Alerts

        JOIN Vehicle
            ON Alerts.VehicleId = Vehicle.VehicleId

        LEFT JOIN Routes
            ON Alerts.RouteId = Routes.RouteId

        WHERE
            ? = 'Tumu'
            OR Routes.RouteCode = ?

        ORDER BY Alerts.AlertDate DESC
        """,
        (
            selected_route,
            selected_route
        )
    )

    st.dataframe(
        latest_alerts_df,
        width="stretch",
        hide_index=True
    )


except pyodbc.Error as error:

    st.error(
        f"Veritabani hatasi olustu: {error}"
    )


finally:

    if cursor:
        cursor.close()

    if connection:
        connection.close()
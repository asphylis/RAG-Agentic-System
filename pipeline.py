import requests
import mysql.connector
from datetime import datetime

def fetch_fda_data():
    url = "https://api.fda.gov/drug/event.json?search=receivedate:[20250101+TO+20251231]&limit=10"
    response = requests.get(url)
    return response.json().get("results", [])


def store_to_mysql(data):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="test"
    )
    cursor = conn.cursor()
    for entry in data:
        safety_report_id = entry.get("safetyreportid")
        received_date = entry.get("receivedate")
        cursor.execute(
            "REPLACE INTO drug_event (report_id, received_date) VALUES (%s, %s)",
            (safety_report_id, received_date)
        )
    conn.commit()
    cursor.close()
    conn.close()


def run_pipeline():
    data = fetch_fda_data()
    store_to_mysql(data)


if __name__ == "__main__":
    run_pipeline()

import pandas as pd
import requests
import sqlite3
import os


def extract():
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()  # Converts JSON response to a Python dictionary
    else:
        print(f"Error: {response.status_code}")
    return data

def transform(data):
    new_data = data['Time Series (Daily)']
    df = pd.DataFrame.from_dict(new_data)
    df = df.T
    df.columns = df.columns.str[3:]
    df.index.name = "dates"
    df.index = pd.to_datetime(df.index).date
    df.sort_index(ascending=True,inplace = True)
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    df["volume"] = df["volume"].astype(int)
    print("NaN Values Per Column")
    print(df.isna().sum())
    df.dropna(inplace=True)

    print("Negative Values per Column")
    for col in df.columns:
        print(f"{col:<7} {(df[col] < 0).sum():3}")
    df = df[(df >= 0).all(axis=1)]

    return df

def load(df):
    with sqlite3.connect("StockData.db") as conn:

        # Create table if it doesn't exist
        conn.execute("""
        CREATE TABLE IF NOT EXISTS IBM_Stock_Data (
            date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER
        )
        """)

        # Read existing dates from database
        existing_dates = pd.read_sql_query(
            "SELECT date FROM IBM_Stock_Data",
            conn
        )

        # Keep only rows not already in database
        new_rows = df[~df.index.astype(str).isin(existing_dates["date"])]

        # Insert only new rows
        if not new_rows.empty:
            new_rows.to_sql(
                "IBM_Stock_Data",
                conn,
                if_exists="append",
                index=True,
                index_label="date"
            )

            print(f"{len(new_rows)} new rows inserted.")

        else:
            print("Database already up to date.")


def main():
    data = extract()
    df = transform(data)
    load(df)


if __name__ == "__main__":
    main()
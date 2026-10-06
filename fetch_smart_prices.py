import pandas as pd
import requests

# SMARD API Filter 4169: Wholesale Day-Ahead Spot Prices (DE-LU bidding zone, Hourly)
INDEX_URL = "https://www.smard.de/app/chart_data/4169/DE-LU/index_hour.json"
BASE_DATA_URL = "https://www.smard.de/app/chart_data/4169/DE-LU/4169_DE-LU_hour_{}.json"


def fetch_latest_german_prices():
    print("1. Connecting to Bundesnetzagentur (SMARD.de)...")
    headers = {"User-Agent": "EnergyAnalytics/1.0"}
    res = requests.get(INDEX_URL, headers=headers, timeout=15)
    res.raise_for_status()

    # Grab the latest available time chunks
    timestamps = res.json().get("timestamps", [])
    if not timestamps:
        raise ValueError("No timestamps returned by SMARD API.")

    # Pull the last 2 weekly data chunks to ensure a healthy dataset
    latest_chunks = timestamps[-2:]
    all_records = []

    print(f"2. Downloading latest market price data ({len(latest_chunks)} chunks)...")
    for ts in latest_chunks:
        chunk_url = BASE_DATA_URL.format(ts)
        chunk_res = requests.get(chunk_url, headers=headers, timeout=15)
        if chunk_res.status_code == 200:
            series = chunk_res.json().get("series", [])
            all_records.extend(series)

    # 3. Clean and convert to DataFrame
    df = pd.DataFrame(all_records, columns=["timestamp_ms", "price_eur_per_mwh"])
    df = df.dropna().drop_duplicates(subset=["timestamp_ms"])

    # 4. Standardize timestamps to Europe/Berlin timezone
    df["datetime_utc"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df["datetime_berlin"] = df["datetime_utc"].dt.tz_convert("Europe/Berlin")

    clean_df = df[["datetime_berlin", "price_eur_per_mwh"]].sort_values("datetime_berlin")

    # 5. Export to CSV for tomorrow's SQL exercises
    output_filename = "smard_day_ahead_prices.csv"
    clean_df.to_csv(output_filename, index=False)

    print(f"\n[DONE] Successfully saved {len(clean_df)} hours to '{output_filename}'.")
    print("\n--- Latest 5 Hours Sample (DE-LU Day-Ahead Spot) ---")
    print(clean_df.tail().to_string(index=False))


if __name__ == "__main__":
    fetch_latest_german_prices()
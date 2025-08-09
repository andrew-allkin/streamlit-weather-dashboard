import os
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import statistics

load_dotenv()

API_KEY = os.environ.get("OPENWEATHER_API_KEY")

GEOCODING_API_URL = "http://api.openweathermap.org/geo/1.0/direct"
TIMEMACHINE_API_URL = "https://api.openweathermap.org/data/3.0/onecall/timemachine"

DATA_FILE = Path("weather_data.csv")

CITIES = {
    "Cape Town": {"country_code": "ZA"},
    "Kigali": {"country_code": "RW"},
    "Kampala": {"country_code": "UG"},
}

def get_city_coordinates(city_name, country_code):
    """
    Get the latitude and longitude of a city using the OpenWeatherMap API.

    Args:
        city_name (str): The name of the city.
        country_code (str): The code of the country.

    Returns:
        tuple: A tuple containing the latitude and longitude of the city.

    Raises:
        requests.exceptions.RequestException: If the request to the OpenWeatherMap API fails.
    """
    params = {
        "q": f"{city_name},{country_code}",
        "limit": 1,
        "appid": API_KEY,
    }
    try:
        response = requests.get(GEOCODING_API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if data:
            print(f"Coordinates for {city_name}: {data[0]['lat']}, {data[0]['lon']}")
            return data[0]["lat"], data[0]["lon"]
        else:
            print(f"Error: Could not find coordinates for {city_name}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates for {city_name}: {e}")
        return None, None

def fetch_stable_weather_data(lat, lon, timestamp, attempts=3):
    """
    Fetches weather data multiple times and returns the median value for stability.
    """
    temperatures = []
    humidities = []
    
    print(f"  > Performing {attempts} checks for a stable reading...")
    for i in range(attempts):
        weather_data = fetch_hourly_weather_data(lat, lon, timestamp)
        if weather_data and "data" in weather_data and weather_data["data"]:
            record = weather_data["data"][0]
            temperatures.append(record["temp"])
            humidities.append(record["humidity"])
        
        # Small delay between API calls
        if i < attempts - 1:
            time.sleep(0.5)

    if not temperatures or not humidities:
        return None # Return None if we failed to get any valid data

    # Calculate the median value from the collected lists
    stable_temp = statistics.median(temperatures)
    stable_humidity = statistics.median(humidities)

    print(f"  > Raw Temps: {temperatures}, Stable: {stable_temp}")
    print(f"  > Raw Humidities: {humidities}, Stable: {stable_humidity}")

    # Return a dictionary in the same format as your original record
    return {
        "timestamp": timestamp,
        "temperature": stable_temp,
        "humidity": stable_humidity,
    }

def fetch_hourly_weather_data(lat, lon, timestamp):
    """
    Fetch hourly weather data for a given latitude, longitude, and timestamp.

    Args:
        lat (str): The latitude of the location.
        lon (str): The longitude of the location.
        timestamp (int): The timestamp in seconds since the Unix epoch.

    Returns:
        dict: The weather data for the given latitude, longitude, and timestamp.

    Raises:
        requests.exceptions.RequestException: If the request to the OpenWeatherMap API fails.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "dt": timestamp,
        "units": "metric",
        "appid": API_KEY
    }
    try:
        timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Fetching weather data for lat={lat}, lon={lon}, timestamp={timestamp_str}")
        response = requests.get(TIMEMACHINE_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data for lat={lat}, lon={lon}: {e}")
        return None


def main_history():
    if not API_KEY:
        print("Error: OPENWEATHER_API_KEY environment variable not set.")
        return

    # Get the current time rounded to the start of the current hour
    current_time = int(time.time())
    start_of_current_hour = current_time - (current_time % 3600)

    all_weather_data = []

    # Loop through each of the past 48 hours
    print("Starting to fetch data for the past 48 hours...")
    for hour_ago in range(24, 0, -1):  # This will loop from 1 to 48
        # Calculate the Unix timestamp for the target hour
        target_timestamp = start_of_current_hour - (hour_ago * 3600)
        
        # Convert to a readable format for logging
        readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target_timestamp))
        print(f"\n--- Fetching data for hour: {readable_time} ({hour_ago} hours ago) ---")

        # Loop through each city for that specific hour
        for city_name, city_info in CITIES.items():
            print(f"Fetching for {city_name}...")
            lat, lon = get_city_coordinates(city_name, city_info["country_code"])

            if lat is not None and lon is not None:
                # v-- The only change is here --v
                stable_record = fetch_stable_weather_data(lat, lon, target_timestamp)

                if stable_record:
                    all_weather_data.append({
                        "timestamp": stable_record["timestamp"],
                        "city": city_name,
                        "temperature": stable_record["temperature"],
                        "humidity": stable_record["humidity"],
                    })
                    print(f"  > Success: Got stable data for {city_name}.")
                else:
                    print(f"  > Failure: Could not retrieve a stable reading for {city_name}.")
                # ^-- The only change is here --^
            
            # Respect API rate limits
            time.sleep(1) 

    if not all_weather_data:
        print("\nNo weather data was fetched in the last 48 hours.")
        return

    # Create a DataFrame and append all collected data to the CSV at once
    print(f"\nCollected a total of {len(all_weather_data)} records.")
    new_data_df = pd.DataFrame(all_weather_data)

    if DATA_FILE.exists():
        new_data_df.to_csv(DATA_FILE, mode='a', header=False, index=False)
        print(f"Appended new records to {DATA_FILE}")
    else:
        new_data_df.to_csv(DATA_FILE, mode='w', header=True, index=False)
        print(f"Created {DATA_FILE} and wrote new records.")

def main():
    if not API_KEY:
        print("Error: OPENWEATHER_API_KEY environment variable not set.")
        return

    current_time = int(time.time())
    previous_hour_timestamp = current_time - (current_time % 3600) - 3600

    # format the timestamp to a readable format
    readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(previous_hour_timestamp))
    print(f"Fetching data for {readable_time}...")

    all_weather_data = []

    for city_name, city_info in CITIES.items():
        print(f"Fetching data for {city_name}...")
        lat, lon = get_city_coordinates(city_name, city_info["country_code"])

        if lat is not None and lon is not None:
            stable_record = fetch_stable_weather_data(lat, lon, previous_hour_timestamp)

        if stable_record:
            # Append the stable data to your list
            all_weather_data.append({
                "timestamp": stable_record["timestamp"],
                "city": city_name,
                "temperature": stable_record["temperature"],
                "humidity": stable_record["humidity"],
            })
            print(f"Successfully fetched stable data for {city_name}.")
        else:
            print(f"Could not retrieve a stable reading for {city_name}.")
        
        # A longer sleep here since each city now involves multiple API calls
        time.sleep(1) 

    # --- The rest of the main function (writing to CSV) remains exactly the same ---
    if not all_weather_data:
        print("No weather data was fetched.")
        return

    new_data_df = pd.DataFrame(all_weather_data)

    if DATA_FILE.exists():
        new_data_df.to_csv(DATA_FILE, mode='a', header=False, index=False)
        print(f"Appended {len(all_weather_data)} new records to {DATA_FILE}")
    else:
        new_data_df.to_csv(DATA_FILE, mode='w', header=True, index=False)
        print(f"Created {DATA_FILE} and wrote {len(all_weather_data)} new records.")

if __name__ == "__main__":
    # main_history()
    main()

import os
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

API_KEY = "90ef9cf2a391a51ddd18bb2d3dc2f416"

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
            return data[0]["lat"], data[0]["lon"]
            print(f"Coordinates for {city_name}: {data[0]['lat']}, {data[0]['lon']}")
        else:
            print(f"Error: Could not find coordinates for {city_name}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates for {city_name}: {e}")
        return None, None

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


# lat = "-33.9288301"
# lon = "18.4172197"

# current_time = int(time.time())
# previous_hour_timestamp = current_time - (current_time % 3600) - 3600

# weather_data = fetch_hourly_weather_data(lat, lon, previous_hour_timestamp)

# if weather_data:
#     print(weather_data)

def main():
    if not API_KEY:
        print("Error: OPENWEATHER_API_KEY environment variable not set.")
        return

    # Calculate the Unix timestamp for the start of the previous hour
    current_time = int(time.time())
    previous_hour_timestamp = current_time - (current_time % 3600) - 3600

    all_weather_data = []

    for city_name, city_info in CITIES.items():
        print(f"Fetching data for {city_name}...")
        lat, lon = get_city_coordinates(city_name, city_info["country_code"])

        if lat is not None and lon is not None:
            weather_data = fetch_hourly_weather_data(lat, lon, previous_hour_timestamp)

            if weather_data and "data" in weather_data and weather_data["data"]:
                record = weather_data["data"][0]
                all_weather_data.append({
                    "timestamp": record["dt"],
                    "city": city_name,
                    "temperature": record["temp"],
                    "humidity": record["humidity"],
                })
                print(f"Successfully fetched data for {city_name}.")
            else:
                print(f"Could not retrieve weather data for {city_name}.")

        time.sleep(1)

    if not all_weather_data:
        print("No weather data was fetched.")
        return

    # Create a DataFrame and append to CSV
    new_data_df = pd.DataFrame(all_weather_data)

    if DATA_FILE.exists():
        # Append without header
        new_data_df.to_csv(DATA_FILE, mode='a', header=False, index=False)
        print(f"Appended {len(all_weather_data)} new records to {DATA_FILE}")
    else:
        # Create new file with header
        new_data_df.to_csv(DATA_FILE, mode='w', header=True, index=False)
        print(f"Created {DATA_FILE} and wrote {len(all_weather_data)} new records.")

# def main_history():
#     if not API_KEY:
#         print("Error: OPENWEATHER_API_KEY environment variable not set.")
#         return

#     # Get the current time rounded to the start of the current hour
#     current_time = int(time.time())
#     start_of_current_hour = current_time - (current_time % 3600)

#     all_weather_data = []

#     # Loop through each of the past 48 hours
#     print("Starting to fetch data for the past 48 hours...")
#     for hour_ago in range(1, 49):  # This will loop from 1 to 48
#         # Calculate the Unix timestamp for the target hour
#         target_timestamp = start_of_current_hour - (hour_ago * 3600)
        
#         # Convert to a readable format for logging
#         readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target_timestamp))
#         print(f"\n--- Fetching data for hour: {readable_time} ({hour_ago} hours ago) ---")

#         # Loop through each city for that specific hour
#         for city_name, city_info in CITIES.items():
#             print(f"Fetching for {city_name}...")
#             lat, lon = get_city_coordinates(city_name, city_info["country_code"])

#             if lat is not None and lon is not None:
#                 weather_data = fetch_hourly_weather_data(lat, lon, target_timestamp)

#                 if weather_data and "data" in weather_data and weather_data["data"]:
#                     record = weather_data["data"][0]
#                     all_weather_data.append({
#                         "timestamp": record["dt"],
#                         "city": city_name,
#                         "temperature": record["temp"],
#                         "humidity": record["humidity"],
#                     })
#                     print(f"  > Success for {city_name}.")
#                 else:
#                     print(f"  > Could not retrieve weather data for {city_name}.")
            
#             # Respect API rate limits
#             time.sleep(1) 

#     if not all_weather_data:
#         print("\nNo weather data was fetched in the last 48 hours.")
#         return

#     # Create a DataFrame and append all collected data to the CSV at once
#     print(f"\nCollected a total of {len(all_weather_data)} records.")
#     new_data_df = pd.DataFrame(all_weather_data)

#     if DATA_FILE.exists():
#         new_data_df.to_csv(DATA_FILE, mode='a', header=False, index=False)
#         print(f"Appended new records to {DATA_FILE}")
#     else:
#         new_data_df.to_csv(DATA_FILE, mode='w', header=True, index=False)
#         print(f"Created {DATA_FILE} and wrote new records.")

if __name__ == "__main__":
    # main_history()
    main()

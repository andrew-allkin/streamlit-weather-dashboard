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
    Fetch geographical coordinates (latitude and longitude) for a given city.
    
    Uses the OpenWeatherMap Geocoding API to convert city name and country code
    into precise coordinates required for weather data retrieval.
    
    Args:
        city_name (str): Name of the city to get coordinates for
        country_code (str): ISO 3166 country code (e.g., 'ZA' for South Africa)
    
    Returns:
        tuple: A tuple containing (latitude, longitude) as floats, or (None, None)
               if coordinates could not be retrieved
    
    Raises:
        requests.exceptions.RequestException: If there's an error with the API request
    """
    params = {
        "q": f"{city_name},{country_code}",
        "limit": 1,
        "appid": API_KEY,
    }
    try:
        response = requests.get(GEOCODING_API_URL, params=params)
        response.raise_for_status()
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
    Fetch weather data multiple times and return median values for stability.
    
    This function performs multiple API calls to get consistent weather readings
    by fetching data several times and calculating the median temperature and
    humidity to reduce variability in the data.
    
    Args:
        lat (float): Latitude coordinate for the location
        lon (float): Longitude coordinate for the location
        timestamp (int): Unix timestamp for the specific hour to fetch data
        attempts (int, optional): Number of API calls to make for stability. Defaults to 3.
    
    Returns:
        dict or None: Dictionary containing stable weather data with keys:
                     - 'timestamp': Unix timestamp
                     - 'temperature': Median temperature in Celsius
                     - 'humidity': Median humidity percentage
                     Returns None if no valid data could be retrieved.
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
        return None

    # Calculate the median value from the collected lists
    stable_temp = statistics.median(temperatures)
    stable_humidity = statistics.median(humidities)

    print(f"  > Raw Temps: {temperatures}, Stable: {stable_temp}")
    print(f"  > Raw Humidities: {humidities}, Stable: {stable_humidity}")

    return {
        "timestamp": timestamp,
        "temperature": stable_temp,
        "humidity": stable_humidity,
    }

def fetch_hourly_weather_data(lat, lon, timestamp):
    """
    Fetch historical weather data for a specific location and time.
    
    Makes a single API call to OpenWeatherMap's Time Machine API to retrieve
    historical weather data for a specific hour at given coordinates.
    
    Args:
        lat (float): Latitude coordinate for the location
        lon (float): Longitude coordinate for the location
        timestamp (int): Unix timestamp for the specific hour to fetch data
    
    Returns:
        dict or None: JSON response from the API containing weather data,
                     or None if the request fails
    
    Raises:
        requests.exceptions.RequestException: If there's an error with the API request
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

def main():
    """
    Main function to fetch and store weather data for multiple cities.
    
    This function orchestrates the entire weather data collection process:
    1. Validates that the API key is configured
    2. Calculates the timestamp for the previous complete hour
    3. Iterates through predefined cities to fetch their coordinates
    4. Retrieves stable weather data for each city
    5. Saves all collected data to a CSV file
    
    The function fetches weather data for the previous hour to ensure
    complete data availability. It handles both creating a new CSV file
    and appending to an existing one.
    
    Global Variables Used:
        API_KEY (str): OpenWeatherMap API key from environment variables
        CITIES (dict): Dictionary of cities with their country codes
        DATA_FILE (Path): Path to the CSV file for storing weather data
    
    Side Effects:
        - Prints progress messages to console
        - Creates or appends to weather_data.csv file
        - Makes multiple API calls with rate limiting delays
    
    Raises:
        SystemExit: Implicitly exits if API_KEY is not configured
    """
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
            all_weather_data.append({
                "timestamp": stable_record["timestamp"],
                "city": city_name,
                "temperature": stable_record["temperature"],
                "humidity": stable_record["humidity"],
            })
            print(f"Successfully fetched stable data for {city_name}.")
        else:
            print(f"Could not retrieve a stable reading for {city_name}.")
        
        time.sleep(1) 

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
    main()

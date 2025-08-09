import streamlit as st
import pandas as pd
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="African Cities Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# --- Data Loading and Caching ---
# In a real Streamlit Cloud app, the path would be relative to the repo root.
DATA_FILE = Path("weather_data.csv")

@st.cache_data
def load_data():
    """Load weather data from CSV, convert timestamp, and set index."""
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        # Convert Unix timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
    return pd.DataFrame()

# --- Main Application ---
st.title("Hourly Weather Dashboard for African Cities")
st.markdown("This dashboard visualizes the latest hourly temperature and humidity data for Cape Town, Kigali, and Kampala.")

data_df = load_data()

if data_df.empty:
    st.warning("No weather data available. Make sure `weather_data.csv` is in the repository and the fetching script has run.")
else:
    # Display the last update time
    last_update_time = data_df['timestamp'].max()
    st.caption(f"Data last updated on: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Create a list of cities for selections
    cities = ['Cape Town', 'Kigali', 'Kampala']
    
    # Pivot data once for efficiency
    temp_df_wide = data_df.pivot_table(index='timestamp', columns='city', values='temperature')[cities]
    humidity_df_wide = data_df.pivot_table(index='timestamp', columns='city', values='humidity')[cities]


    # --- Visualizations ---
    st.header("Temperature Trends (°C)")
    
    # Temperature chart with selection mechanism
    temp_selection_options = ['All'] + cities
    selected_city_temp = st.selectbox(
        "Select a city to view its temperature or choose 'All' to compare:",
        options=temp_selection_options,
        index=0 # Default to 'All'
    )

    if selected_city_temp == 'All':
        st.line_chart(temp_df_wide, height=400)
    else:
        st.line_chart(temp_df_wide[selected_city_temp], height=400)


    st.header("Humidity Trends (%)")
    st.write("A line chart showing humidity trends across all three cities.")
    # Humidity chart as a line graph for all 3 cities
    st.line_chart(
        humidity_df_wide,
        height=400
    )

    # --- Raw Data Display ---
    with st.expander("Show Raw Data"):
        st.dataframe(data_df.sort_values('timestamp', ascending=False))
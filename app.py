import streamlit as st
import pandas as pd
import altair as alt
import pytz  # Import pytz for timezone handling
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="African Cities Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# --- Data Loading and Caching ---
# Note: The data is assumed to be in UTC in the CSV file.
DATA_FILE = Path("weather_data.csv")

@st.cache_data
def load_data():
    """Load weather data from CSV and convert timestamp column to datetime."""
    # This function now requires the pytz library.
    # You may need to run: pip install pytz
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        # Convert Unix timestamp to datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        # 1. Make timestamp column timezone-aware (localize to UTC)
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        return df
    return pd.DataFrame()

# --- Main Application ---
st.title("Hourly Weather Dashboard for African Cities")
st.markdown("This dashboard visualizes the latest hourly temperature and humidity data for Cape Town, Kigali, and Kampala.")

data_df = load_data()

if data_df.empty:
    st.warning("No weather data available. Make sure `weather_data.csv` is in the repository and the fetching script has run.")
else:
    # --- Timezone Toggle and Conversion ---
    use_sast = st.toggle('Display time in SAST (UTC+2)', value=True)
    
    display_df = data_df.copy()
    active_timezone_str = "UTC"
    
    if use_sast:
        sast_tz = pytz.timezone('Africa/Johannesburg')
        # 2. Convert from UTC to SAST
        display_df['timestamp'] = display_df['timestamp'].dt.tz_convert(sast_tz)
        active_timezone_str = "SAST"

    last_update_time = display_df['timestamp'].max()
    st.caption(f"Data last updated on: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')} {active_timezone_str}")

    cities = ['Cape Town', 'Kigali', 'Kampala']
    
    # --- Visualizations ---
    st.header("Temperature Trends (°C)")
    
    temp_selection_options = ['All'] + cities
    selected_city_temp = st.selectbox(
        "Select a city to view its temperature or choose 'All' to compare:",
        options=temp_selection_options,
        index=1 
    )
    
    # Use the (potentially timezone-converted) display_df for charting
    if selected_city_temp == 'All':
        chart_data = display_df
    else:
        chart_data = display_df[display_df['city'] == selected_city_temp]

    temp_chart = alt.Chart(chart_data).mark_line(
        interpolate='monotone',
        point=False
    ).encode(
        x=alt.X('yearmonthdatehours(timestamp):T', 
                axis=alt.Axis(title=f'Time ({active_timezone_str})', format="%b %d, %H:00")
               ),
        y=alt.Y('mean(temperature):Q', title='Temperature (°C)'),
        color=alt.Color('city:N', title='City'),
        tooltip=[alt.Tooltip('yearmonthdatehours(timestamp):T', title='Hour'), 
                 alt.Tooltip('mean(temperature):Q', title='Avg. Temp (°C)', format='.1f'), 
                 'city:N']
    ).properties(
        height=400
    ).interactive()

    st.altair_chart(temp_chart, use_container_width=True)

    st.header("Humidity Trends (%)")
    st.write("A smoothed line chart showing humidity trends across all three cities.")
    
    # Also use the display_df for the humidity chart
    humidity_chart = alt.Chart(display_df).mark_line(
        interpolate='monotone'
    ).encode(
        x=alt.X('yearmonthdatehours(timestamp):T', axis=alt.Axis(title=f'Time ({active_timezone_str})', format="%b %d, %H:00")),
        y=alt.Y('mean(humidity):Q', title='Humidity (%)'),
        color=alt.Color('city:N', title='City'),
        tooltip=[alt.Tooltip('yearmonthdatehours(timestamp):T', title='Hour'),
                 alt.Tooltip('mean(humidity):Q', title='Avg. Humidity (%)', format='.0f'),
                 'city:N']
    ).properties(
        height=400
    ).interactive()

    st.altair_chart(humidity_chart, use_container_width=True)

    with st.expander("Show Raw Data"):
        st.dataframe(display_df.sort_values('timestamp', ascending=False))
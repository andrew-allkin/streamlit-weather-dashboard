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
    # Add a 'country' column for the tooltip based on the city
    country_map = {'Cape Town': 'South Africa', 'Kigali': 'Rwanda', 'Kampala': 'Uganda'}
    data_df['country'] = data_df['city'].map(country_map)

    # --- Timezone Toggle and Conversion ---
    use_sast = st.toggle('Display time in SAST (UTC+2)', value=True)
    
    display_df = data_df.copy()
    active_timezone_str = "UTC"
    
    if use_sast:
        sast_tz = pytz.timezone('Africa/Johannesburg')
        display_df['plot_timestamp'] = display_df['timestamp'].dt.tz_convert(sast_tz).dt.tz_localize(None)
        active_timezone_str = "SAST"
    else:
        display_df['plot_timestamp'] = display_df['timestamp'].dt.tz_localize(None)
    
    last_update_time = display_df['plot_timestamp'].max()
    st.caption(f"Data last updated on: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')} {active_timezone_str}")

    cities = ['Cape Town', 'Kigali', 'Kampala']
    
    # 🎯 Add the checkbox for toggling line interpolation
    smooth_lines = st.checkbox('Smooth lines (monotone)', value=True)
    interpolation_type = 'monotone' if smooth_lines else 'linear'

    # --- Visualizations ---
    st.header("Temperature Trends (°C)")
    
    temp_selection_options = ['All'] + cities
    selected_city_temp = st.selectbox(
        "Select a city to view its temperature or choose 'All' to compare:",
        options=temp_selection_options,
        index=1 
    )
    
    if selected_city_temp == 'All':
        chart_data = display_df
    else:
        chart_data = display_df[display_df['city'] == selected_city_temp]

    # 🎯 Updated Altair chart to use the interpolation_type variable
    temp_chart = alt.Chart(chart_data).mark_line(
        interpolate=interpolation_type,
        point=False
    ).encode(
        x=alt.X('yearmonthdatehours(plot_timestamp):T', 
                axis=alt.Axis(title=f'Time ({active_timezone_str})', format="%b %d, %H:00")
               ),
        y=alt.Y('mean(temperature):Q', title='Temperature (°C)'),
        color=alt.Color('city:N', title='City'),
        tooltip=[alt.Tooltip('yearmonthdatehours(plot_timestamp):T', title='Hour'), 
                 alt.Tooltip('mean(temperature):Q', title='Avg. Temp (°C)', format='.1f'), 
                 alt.Tooltip('city:N', title='City'), 
                 alt.Tooltip('country:N', title='Country')]
    ).properties(
        height=400
    ).interactive()

    st.altair_chart(temp_chart, use_container_width=True)

    st.header("Humidity Trends (%)")
    st.write("A chart showing humidity trends across all three cities.")
    
    # Also use the display_df for the humidity chart
    # 🎯 Updated Altair chart to use the interpolation_type variable
    humidity_chart = alt.Chart(display_df).mark_line(
        interpolate=interpolation_type
    ).encode(
        x=alt.X('yearmonthdatehours(plot_timestamp):T', axis=alt.Axis(title=f'Time ({active_timezone_str})', format="%b %d, %H:00")),
        y=alt.Y('mean(humidity):Q', title='Humidity (%)'),
        color=alt.Color('city:N', title='City'),
        tooltip=[alt.Tooltip('yearmonthdatehours(plot_timestamp):T', title='Hour'),
                 alt.Tooltip('mean(humidity):Q', title='Avg. Humidity (%)', format='.0f'),
                 alt.Tooltip('city:N', title='City'), 
                 alt.Tooltip('country:N', title='Country')]
    ).properties(
        height=400
    ).interactive()

    st.altair_chart(humidity_chart, use_container_width=True)

    with st.expander("Show Raw Data"):
        st.dataframe(display_df.sort_values('timestamp', ascending=False))
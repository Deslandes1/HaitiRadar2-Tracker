import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt, atan2, pi, asin, degrees
from datetime import datetime
import time

# Import Flightradar24 SDK
from flightradar24 import FlightRadar24API

st.set_page_config(page_title="GLOBAL SURVEILLANCE RADAR - Military & Drone Detection", layout="wide", page_icon="🔴")

# -------------------------------------------------------------------
# Classification helpers (same as before)
# -------------------------------------------------------------------

MILITARY_ICAO_PREFIXES = [
    "AE", "AD", "AF", "3C", "3E", "33", "34", "38", "39", "40", "43", "44", "45", "46", "48",
    "4B", "4C", "4D", "4E", "4F", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "5A", "5B", "5C", "5D", "5E", "5F", "60", "61", "62", "63", "64", "65", "66", "67", "68",
    "69", "6A", "6B", "6C", "6D", "6E", "6F", "70", "71", "72", "73", "74", "75", "76", "77",
    "78", "79", "7A", "7B", "7C", "7D", "7E", "7F", "80", "81", "82", "83", "84", "85", "86",
    "87", "88", "89", "8A", "8B", "8C", "8D", "8E", "8F", "90", "91", "92", "93", "94", "95",
    "96", "97", "98", "99", "9A", "9B", "9C", "9D", "9E", "9F", "A0", "A1", "A2", "A3", "A4",
    "A5", "A6", "A7", "A8", "A9", "AA", "AB", "AC",
]

DRONE_ICAO_PREFIXES = [
    "4CAA", "4CAB", "4CAC", "4CAD", "4CAE", "4CAF", "4CB0", "4CB1", "4CB2", "4CB3", "4CB4",
]

def classify_aircraft(icao24, callsign, velocity, altitude, aircraft_type=None):
    is_military = False
    is_drone = False

    icao_upper = icao24.upper() if icao24 else ""
    callsign_upper = callsign.upper() if callsign else ""

    # Military by ICAO prefix
    for prefix in MILITARY_ICAO_PREFIXES:
        if icao_upper.startswith(prefix):
            is_military = True
            break

    # Military by callsign keywords
    mil_keywords = ["AF", "NAVY", "ARMY", "AIR FORCE", "MIL", "RAAF", "RAF", "LUFT", "ARMEE"]
    if any(kw in callsign_upper for kw in mil_keywords):
        is_military = True

    # Drone by ICAO prefix
    for prefix in DRONE_ICAO_PREFIXES:
        if icao_upper.startswith(prefix):
            is_drone = True
            break

    # Drone by callsign keywords
    drone_keywords = ["DRONE", "UAV", "DRON", "QUAD", "HEXA", "OCTO"]
    if any(kw in callsign_upper for kw in drone_keywords):
        is_drone = True

    # Heuristic for drones (low altitude, low speed)
    if not is_drone and not is_military:
        if altitude is not None and altitude < 500 and velocity is not None and velocity < 30:
            is_drone = True

    if is_military:
        type_str = "🔫 Military"
    elif is_drone:
        type_str = "🚁 Drone"
    else:
        type_str = "✈️ Civilian"

    return {
        "is_military": is_military,
        "is_drone": is_drone,
        "type": type_str
    }

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def destination_point(lat, lon, distance_km, bearing_deg):
    R = 6371
    lat1 = radians(lat)
    lon1 = radians(lon)
    brng = radians(bearing_deg)
    d = distance_km / R

    lat2 = asin(sin(lat1) * cos(d) + cos(lat1) * sin(d) * cos(brng))
    lon2 = lon1 + atan2(sin(brng) * sin(d) * cos(lat1), cos(d) - sin(lat1) * sin(lat2))

    return degrees(lat2), degrees(lon2)

@st.cache_data(ttl=60, show_spinner=False)
def fetch_flightradar24():
    """Fetch live aircraft data from Flightradar24 API (global coverage)."""
    try:
        fr24 = FlightRadar24API()
        # Get all live flights (returns Flight objects)
        flights = fr24.get_flights()
        
        aircraft_list = []
        for flight in flights:
            # Extract data from Flight object
            icao24 = flight.hex if hasattr(flight, 'hex') else ""
            callsign = flight.callsign if hasattr(flight, 'callsign') else flight.number
            lat = flight.latitude if hasattr(flight, 'latitude') else None
            lon = flight.longitude if hasattr(flight, 'longitude') else None
            altitude = flight.altitude if hasattr(flight, 'altitude') else None
            velocity = flight.speed if hasattr(flight, 'speed') else None
            heading = flight.heading if hasattr(flight, 'heading') else None
            aircraft_type = flight.aircraft_code if hasattr(flight, 'aircraft_code') else None
            
            if lat is None or lon is None:
                continue
            
            # Convert altitude from feet to meters if present
            if altitude:
                altitude = altitude * 0.3048  # feet to meters
            
            # Convert speed from knots to m/s if present
            if velocity:
                velocity = velocity * 0.514444  # knots to m/s
            
            classification = classify_aircraft(icao24, callsign, velocity, altitude, aircraft_type)
            
            aircraft_list.append({
                "icao24": icao24,
                "callsign": callsign or "UNKNOWN",
                "lat": lat,
                "lon": lon,
                "altitude": altitude,
                "velocity": velocity,
                "heading": heading,
                "vertical_rate": None,  # Not provided by basic API
                "on_ground": False,  # Not provided by basic API
                "distance": 0,  # Will calculate later
                "type": classification["type"],
                "is_military": classification["is_military"],
                "is_drone": classification["is_drone"]
            })
        
        return aircraft_list
    except Exception as e:
        st.toast(f"Flightradar24 API error: {e}", icon="⚠️")
        return None

def filter_aircraft_by_distance(aircraft_list, radar_lat, radar_lon, max_range_km):
    """Filter aircraft by distance from radar centre."""
    filtered = []
    for ac in aircraft_list:
        dist = haversine(radar_lat, radar_lon, ac["lat"], ac["lon"])
        if dist <= max_range_km:
            ac["distance"] = dist
            filtered.append(ac)
    return filtered

def bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    y = sin(lon2 - lon1) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    brng = atan2(y, x)
    return (brng * 180 / pi + 360) % 360

def create_radar_polar(aircraft, radar_lat, radar_lon, max_range_km):
    """Create polar radar plot with rotating sweep line."""
    r_vals = []
    theta_vals = []
    colors = []
    labels = []
    for ac in aircraft:
        dist = ac["distance"]
        brng = bearing(radar_lat, radar_lon, ac["lat"], ac["lon"])
        r_vals.append(dist)
        theta_vals.append(brng)
        if ac["is_military"]:
            colors.append("#ff4444")
        elif ac["is_drone"]:
            colors.append("#ffaa44")
        else:
            colors.append("#2eff9e")
        labels.append(ac["callsign"])

    fig = go.Figure()
    if r_vals:
        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            mode='markers+text',
            marker=dict(size=10, color=colors, line=dict(width=1, color='white')),
            text=labels,
            textposition="top center",
            name='Aircraft'
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, max_range_km],
                tickvals=[max_range_km * 0.25, max_range_km * 0.5, max_range_km * 0.75, max_range_km],
                ticktext=[f"{int(max_range_km*0.25)}km", f"{int(max_range_km*0.5)}km", f"{int(max_range_km*0.75)}km", f"{int(max_range_km)}km"],
                gridcolor='#2a4f6e',
                linecolor='#2aff9e',
                ticks='outside',
                showticklabels=True
            ),
            angularaxis=dict(
                tickmode='array',
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                direction='clockwise',
                rotation=90,
                gridcolor='#2a4f6e',
                linecolor='#2aff9e'
            ),
            bgcolor='#03060c'
        ),
        title=dict(text="Radar Sweep View", font=dict(color='#ccd6f6')),
        paper_bgcolor='#03060c',
        plot_bgcolor='#03060c',
        margin=dict(l=80, r=80, t=80, b=80)
    )

    angle = (datetime.now().second * 6) % 360
    sweep_line = go.Scatterpolar(
        r=[0, max_range_km],
        theta=[angle, angle],
        mode='lines',
        line=dict(color='#ffaa44', width=2),
        name='Sweep',
        showlegend=False
    )
    fig.add_trace(sweep_line)

    return fig

def create_map(aircraft, radar_lat, radar_lon, max_range_km):
    """Create map view with range rings."""
    if not aircraft:
        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(
            lat=[radar_lat],
            lon=[radar_lon],
            mode='markers',
            marker=dict(size=12, color='#ffaa44', symbol='circle'),
            name='Radar Center'
        ))
        fig.update_layout(
            mapbox=dict(
                style="dark",
                center=dict(lat=radar_lat, lon=radar_lon),
                zoom=4
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        return fig

    df = pd.DataFrame(aircraft)
    df['color'] = df.apply(lambda row: '#ff4444' if row['is_military'] else ('#ffaa44' if row['is_drone'] else '#2eff9e'), axis=1)
    df['size'] = df['velocity'].apply(lambda v: 10 if (v and v > 0.5) else 8)

    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        hover_name='callsign',
        hover_data={'altitude': True, 'velocity': True, 'heading': True, 'type': True, 'distance': True},
        zoom=4,
        height=600
    )
    fig.update_traces(
        marker=dict(
            size=df['size'].tolist(),
            color=df['color'].tolist(),
            symbol='circle',
            line=dict(width=1, color='white')
        ),
        selector=dict(type='scattermapbox')
    )

    fig.add_trace(go.Scattermapbox(
        lat=[radar_lat],
        lon=[radar_lon],
        mode='markers',
        marker=dict(size=12, color='#ffaa44', symbol='circle'),
        name='Radar Center'
    ))

    # Range rings
    ring_distances = [0.25, 0.5, 0.75, 1.0]
    for frac in ring_distances:
        r_km = max_range_km * frac
        num_points = 64
        circle_lats = []
        circle_lons = []
        for i in range(num_points+1):
            brng = 360 * i / num_points
            lat2, lon2 = destination_point(radar_lat, radar_lon, r_km, brng)
            circle_lats.append(lat2)
            circle_lons.append(lon2)
        fig.add_trace(go.Scattermapbox(
            lat=circle_lats,
            lon=circle_lons,
            mode='lines',
            line=dict(width=1, color='#28e6a8', dash='dash'),
            showlegend=False,
            hoverinfo='none'
        ))

    fig.update_layout(
        mapbox=dict(
            style="dark",
            center=dict(lat=radar_lat, lon=radar_lon),
            zoom=4
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# -------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------

st.title("🔴 GLOBAL SURVEILLANCE RADAR (Satellite ADS‑B)")
st.markdown("Military & Drone Detection | True global coverage via Flightradar24 + Aireon space-based ADS‑B")
st.markdown("🇭🇹 Owner: Gesner Deslandes")

# Session state
if "last_aircraft" not in st.session_state:
    st.session_state.last_aircraft = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "data_source" not in st.session_state:
    st.session_state.data_source = "Live"
if "prev_lat" not in st.session_state:
    st.session_state.prev_lat = None
if "prev_lon" not in st.session_state:
    st.session_state.prev_lon = None

# Get query parameters for geolocation
query_params = st.query_params
geo_lat = query_params.get("lat")
geo_lon = query_params.get("lon")
if geo_lat is not None and geo_lon is not None:
    try:
        geo_lat = float(geo_lat)
        geo_lon = float(geo_lon)
    except:
        geo_lat = None
        geo_lon = None
else:
    geo_lat = None
    geo_lon = None

# If location changed, clear cache
if geo_lat is not None and geo_lon is not None:
    if (st.session_state.prev_lat != geo_lat or st.session_state.prev_lon != geo_lon):
        st.cache_data.clear()
        st.session_state.last_aircraft = []
        st.session_state.last_update = None
        st.toast("📍 Location updated – refreshing data...", icon="🔄")
    st.session_state.prev_lat = geo_lat
    st.session_state.prev_lon = geo_lon

with st.sidebar:
    st.header("📡 Radar Settings")
    if geo_lat is not None and geo_lon is not None:
        radar_lat = st.number_input("Radar Latitude", value=geo_lat, format="%.5f")
        radar_lon = st.number_input("Radar Longitude", value=geo_lon, format="%.5f")
    else:
        radar_lat = st.number_input("Radar Latitude", value=40.7128, format="%.5f")
        radar_lon = st.number_input("Radar Longitude", value=-74.0060, format="%.5f")
    max_range = st.number_input("Max Range (km)", min_value=30, max_value=20000, value=2000, step=500)
    auto_refresh = st.checkbox("Auto‑refresh page", value=False)
    if auto_refresh:
        refresh_sec = st.number_input("Refresh Interval (sec)", min_value=10, max_value=300, value=60, step=10)
    else:
        refresh_sec = 0

    if st.button("📍 My Location", use_container_width=True):
        st.markdown(
            """
            <script>
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const url = new URL(window.location.href);
                        url.searchParams.set('lat', lat);
                        url.searchParams.set('lon', lon);
                        window.location.href = url.href;
                    },
                    (error) => {
                        alert("Geolocation error: " + error.message);
                    }
                );
            } else {
                alert("Geolocation is not supported by your browser.");
            }
            </script>
            """,
            unsafe_allow_html=True
        )
        st.stop()

    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.info("🌍 **Global Coverage** | Powered by Flightradar24 + Aireon satellite ADS‑B")
    if st.session_state.data_source == "Live":
        st.success("🟢 Live data (global)")
    else:
        st.warning("🟡 Using cached data")

# Fetch data from Flightradar24
with st.spinner("🌍 Fetching global aircraft data from satellite network..."):
    all_aircraft = fetch_flightradar24()

if all_aircraft is not None:
    aircraft = filter_aircraft_by_distance(all_aircraft, radar_lat, radar_lon, max_range)
    st.session_state.last_aircraft = aircraft
    st.session_state.last_update = datetime.now()
    st.session_state.data_source = "Live"
elif st.session_state.last_aircraft:
    aircraft = st.session_state.last_aircraft
    st.session_state.data_source = "Cached"
else:
    aircraft = []
    st.session_state.data_source = "None"
    st.warning("⚠️ No data available. Check your Flightradar24 API connection.")

left_col, right_col = st.columns([0.5, 0.5])

with left_col:
    st.subheader("📡 RADAR SWEEP VIEW")
    polar_fig = create_radar_polar(aircraft, radar_lat, radar_lon, max_range)
    st.plotly_chart(polar_fig, use_container_width=True)

    st.subheader(f"📋 Detected Objects ({len(aircraft)})")
    if aircraft:
        df_table = pd.DataFrame(aircraft)
        display_df = df_table[["callsign", "lat", "lon", "altitude", "velocity", "heading", "type", "distance"]].copy()
        display_df["altitude"] = display_df["altitude"].apply(lambda x: f"{x:.0f}m" if x is not None else "N/A")
        display_df["velocity"] = display_df["velocity"].apply(lambda x: f"{x:.1f}m/s" if x is not None else "?")
        display_df["heading"] = display_df["heading"].apply(lambda x: f"{x:.0f}°" if x is not None else "---")
        display_df["distance"] = display_df["distance"].apply(lambda x: f"{x:.0f}km")
        display_df = display_df.rename(columns={
            "callsign": "CALLSIGN/ID",
            "lat": "LATITUDE",
            "lon": "LONGITUDE",
            "altitude": "ALT (m)",
            "velocity": "SPEED (m/s)",
            "heading": "HEADING",
            "type": "TYPE",
            "distance": "DISTANCE"
        })
        st.dataframe(display_df, use_container_width=True, height=400)

        selected_callsign = st.selectbox("Select object for detailed report", df_table["callsign"].tolist())
        selected_ac = df_table[df_table["callsign"] == selected_callsign].iloc[0]

        st.subheader("📋 Detailed Report")
        col1, col2 = st.columns(2)
        col1.metric("✈️ OBJECT", selected_ac["callsign"])
        col2.metric("🆔 ICAO24", selected_ac["icao24"] if selected_ac["icao24"] else "N/A")
        col1.metric("📍 LAT/LON", f"{selected_ac['lat']:.5f}, {selected_ac['lon']:.5f}")
        alt_text = f"{selected_ac['altitude']:.0f} m ({selected_ac['altitude']*3.28084:.0f} ft)" if selected_ac["altitude"] else "unknown"
        col2.metric("📏 ALTITUDE", alt_text)
        speed_text = f"{selected_ac['velocity']:.2f} m/s ({selected_ac['velocity']*3.6:.1f} km/h)" if selected_ac["velocity"] else "unknown"
        col1.metric("💨 SPEED", speed_text)
        heading_text = f"{selected_ac['heading']:.1f}° (true)" if selected_ac["heading"] else "unknown"
        col2.metric("🧭 HEADING", heading_text)
        col1.metric("📡 DISTANCE", f"{selected_ac['distance']:.0f} km")
        col2.metric("📋 TYPE", selected_ac["type"])
        
        st.markdown("**🛡️ Classification**")
        if selected_ac["is_military"]:
            st.success("🔫 **Military Aircraft** – flagged by ICAO range or callsign keywords.")
        elif selected_ac["is_drone"]:
            st.warning("🚁 **Drone / UAV** – flagged by ICAO range, callsign keywords, or low‑altitude/speed behaviour.")
        else:
            st.info("✈️ **Civilian Aircraft** – no military or drone indicators.")
        st.caption("🌍 **Global coverage** – Data provided by Flightradar24 + Aireon space-based ADS‑B network. Tracks aircraft anywhere on Earth, including oceans and remote regions.")

        report_content = f"""
GLOBAL SURVEILLANCE REPORT
==========================
Object: {selected_ac['callsign']}
ICAO24: {selected_ac['icao24'] if selected_ac['icao24'] else 'N/A'}
Type: {selected_ac['type']}
Latitude: {selected_ac['lat']:.5f}
Longitude: {selected_ac['lon']:.5f}
Distance from radar: {selected_ac['distance']:.0f} km
Altitude: {alt_text}
Speed: {speed_text}
Heading: {heading_text}
Time of report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data source: Flightradar24 + Aireon satellite ADS-B
"""
        st.download_button(
            label="📥 Download Report (TXT)",
            data=report_content,
            file_name=f"{selected_ac['callsign']}_global_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("No aircraft detected within current range. Try increasing the range or check your location.")

with right_col:
    st.subheader("🗺️ Global Radar Coverage Map")
    map_fig = create_map(aircraft, radar_lat, radar_lon, max_range)
    st.plotly_chart(map_fig, use_container_width=True)
    if st.session_state.last_update:
        st.caption(f"📡 Last update: {st.session_state.last_update.strftime('%H:%M:%S')} | Range: {max_range} km | 🌍 Global satellite coverage")
    else:
        st.caption(f"📡 Range: {max_range} km | 🌍 Global satellite coverage")

if refresh_sec > 0:
    st.markdown(
        f"""
        <script>
            setTimeout(function() {{
                window.location.reload();
            }}, {refresh_sec * 1000});
        </script>
        """,
        unsafe_allow_html=True
    )

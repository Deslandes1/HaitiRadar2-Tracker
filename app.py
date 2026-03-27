import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt, atan2, pi, asin, degrees
import time
from datetime import datetime

st.set_page_config(page_title="REAL RADAR - Live Airborne Tracker", layout="wide", page_icon="🔴")

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def destination_point(lat, lon, distance_km, bearing_deg):
    """Calculate destination lat/lon given start, distance (km), bearing (deg)."""
    R = 6371
    lat1 = radians(lat)
    lon1 = radians(lon)
    brng = radians(bearing_deg)
    d = distance_km / R

    lat2 = asin(sin(lat1) * cos(d) + cos(lat1) * sin(d) * cos(brng))
    lon2 = lon1 + atan2(sin(brng) * sin(d) * cos(lat1), cos(d) - sin(lat1) * sin(lat2))

    return degrees(lat2), degrees(lon2)

@st.cache_data(ttl=30)
def fetch_opensky():
    """Get raw states from OpenSky API with retry and longer timeout."""
    url = "https://opensky-network.org/api/states/all"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RadarApp/1.0)"}
    max_retries = 3
    timeout = 20  # seconds

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("states", [])
            elif resp.status_code == 429:
                wait = 30
                st.warning(f"OpenSky rate limit hit. Waiting {wait}s before retry (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                st.warning(f"OpenSky returned status {resp.status_code} (attempt {attempt+1})")
        except requests.exceptions.Timeout:
            st.warning(f"OpenSky connection timeout (attempt {attempt+1}/{max_retries})")
        except Exception as e:
            st.warning(f"OpenSky attempt {attempt+1} failed: {e}")

        if attempt < max_retries - 1 and 'resp' in locals() and resp is not None and resp.status_code != 429:
            wait = 2 ** attempt
            time.sleep(wait)

    st.warning("⚠️ OpenSky API is currently rate‑limiting or unavailable. Using cached data if available.")
    return None

def filter_aircraft(states, radar_lat, radar_lon, max_range_km):
    aircraft_list = []
    for s in states:
        icao24 = s[0]
        callsign = s[1].strip() if s[1] else None
        lon = s[5]
        lat = s[6]
        geo_alt = s[7]
        on_ground = s[8]
        velocity = s[9]
        heading = s[10]
        vert_rate = s[11]

        if lat is None or lon is None:
            continue

        dist = haversine(radar_lat, radar_lon, lat, lon)
        if dist <= max_range_km:
            aircraft_list.append({
                "icao24": icao24,
                "callsign": callsign or f"FLT{icao24[-4:]}",
                "lat": lat,
                "lon": lon,
                "altitude": geo_alt if geo_alt is not None else None,
                "velocity": velocity if velocity is not None else None,
                "heading": heading if heading is not None else None,
                "vertical_rate": vert_rate if vert_rate is not None else None,
                "on_ground": on_ground or False,
                "distance": dist
            })
    seen = set()
    unique = []
    for ac in aircraft_list:
        if ac["icao24"] not in seen:
            seen.add(ac["icao24"])
            unique.append(ac)
    return unique

def bearing(lat1, lon1, lat2, lon2):
    """Bearing from point1 to point2 in degrees (0‑360)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    y = sin(lon2 - lon1) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    brng = atan2(y, x)
    return (brng * 180 / pi + 360) % 360

def create_radar_polar(aircraft, radar_lat, radar_lon, max_range_km):
    """
    Polar radar plot with rotating sweep line (angle based on current second).
    The sweep rotates continuously, independent of aircraft data.
    """
    r_vals = []
    theta_vals = []
    colors = []
    labels = []
    for ac in aircraft:
        dist = ac["distance"]
        if dist <= max_range_km:
            brng = bearing(radar_lat, radar_lon, ac["lat"], ac["lon"])
            r_vals.append(dist)
            theta_vals.append(brng)
            moving = ac["velocity"] is not None and ac["velocity"] > 0.5
            colors.append("#2eff9e" if moving else "#ff5555")
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

    # Base layout
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

    # Rotating sweep line – angle changes every second (6° per second)
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
                zoom=6
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        return fig

    df = pd.DataFrame(aircraft)
    df['color'] = df['velocity'].apply(lambda v: '#2eff9e' if (v and v > 0.5) else '#ff5555')
    df['size'] = df['velocity'].apply(lambda v: 8 if (v and v > 0.5) else 6)

    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        hover_name='callsign',
        hover_data={'altitude': True, 'velocity': True, 'heading': True},
        zoom=8,
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
            zoom=6
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# -------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------

st.title("🔴 GROUND RADAR (ADS‑B)")
st.markdown("Live tracking | Real aircraft & drones with transponders | No simulation")
st.markdown("🇭🇹 Owner: Gesner Deslandes")

# Session state for cached data
if "last_aircraft" not in st.session_state:
    st.session_state.last_aircraft = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None

with st.sidebar:
    st.header("📡 Radar Settings")
    radar_lat = st.number_input("Radar Latitude", value=40.7128, format="%.5f")
    radar_lon = st.number_input("Radar Longitude", value=-74.0060, format="%.5f")
    max_range = st.number_input("Max Range (km)", min_value=30, max_value=300, value=120, step=10)
    refresh_sec = st.number_input("Refresh Interval (sec)", min_value=3, max_value=60, value=60, step=1)

    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("Powered by [OpenSky Network](https://opensky-network.org)")

# Fetch data (cached)
states = fetch_opensky()

# Determine which aircraft to display
if states is not None:
    # New data received
    aircraft = filter_aircraft(states, radar_lat, radar_lon, max_range)
    st.session_state.last_aircraft = aircraft
    st.session_state.last_update = datetime.now()
elif st.session_state.last_aircraft:
    # No new data, but we have cached data
    aircraft = st.session_state.last_aircraft
    st.warning("⚠️ Using cached data from previous successful fetch. OpenSky API is currently rate‑limiting.")
else:
    # No new data and no cached data
    aircraft = []
    st.warning("⚠️ No data available. Radar is searching but no objects detected yet. Try adjusting range or waiting for API availability.")

# Always render the dashboard
left_col, right_col = st.columns([0.5, 0.5])

with left_col:
    st.subheader("📡 RADAR SWEEP VIEW")
    polar_fig = create_radar_polar(aircraft, radar_lat, radar_lon, max_range)
    st.plotly_chart(polar_fig, use_container_width=True)

    st.subheader(f"📋 Detected Objects ({len(aircraft)})")
    if aircraft:
        df_table = pd.DataFrame(aircraft)
        display_df = df_table[["callsign", "lat", "lon", "altitude", "velocity", "heading"]].copy()
        display_df["altitude"] = display_df["altitude"].apply(lambda x: f"{x:.0f}m" if x is not None else "N/A")
        display_df["velocity"] = display_df["velocity"].apply(lambda x: f"{x:.1f}m/s" if x is not None else "?")
        display_df["heading"] = display_df["heading"].apply(lambda x: f"{x:.0f}°" if x is not None else "---")
        status = []
        for _, row in df_table.iterrows():
            if row["velocity"] is not None and row["velocity"] > 0.5:
                status.append("🟢 MOVING")
            else:
                status.append("🔴 STATIC")
        display_df["status"] = status
        display_df = display_df.rename(columns={
            "callsign": "CALLSIGN/ID",
            "lat": "LATITUDE",
            "lon": "LONGITUDE",
            "altitude": "ALT (m)",
            "velocity": "SPEED (m/s)",
            "heading": "HEADING"
        })
        st.dataframe(display_df, use_container_width=True, height=400)

        selected_callsign = st.selectbox("Select object for detailed report", df_table["callsign"].tolist())
        selected_ac = df_table[df_table["callsign"] == selected_callsign].iloc[0]

        st.subheader("📋 Detailed Report")
        col1, col2 = st.columns(2)
        col1.metric("✈️ OBJECT", selected_ac["callsign"])
        col2.metric("🆔 ICAO24", selected_ac["icao24"])
        col1.metric("📍 LAT/LON", f"{selected_ac['lat']:.5f}, {selected_ac['lon']:.5f}")
        alt_text = f"{selected_ac['altitude']:.0f} m ({selected_ac['altitude']*3.28084:.0f} ft)" if selected_ac["altitude"] else "unknown"
        col2.metric("📏 ALTITUDE", alt_text)
        speed_text = f"{selected_ac['velocity']:.2f} m/s ({selected_ac['velocity']*3.6:.1f} km/h)" if selected_ac["velocity"] else "unknown"
        col1.metric("💨 SPEED", speed_text)
        heading_text = f"{selected_ac['heading']:.1f}° (true)" if selected_ac["heading"] else "unknown"
        col2.metric("🧭 HEADING", heading_text)
        vert_rate_text = f"{selected_ac['vertical_rate']:.1f} m/s" if selected_ac["vertical_rate"] else "N/A"
        col1.metric("📈 VERTICAL RATE", vert_rate_text)
        on_ground_text = "YES (on ground)" if selected_ac["on_ground"] else "AIRBORNE"
        col2.metric("🛬 ON GROUND", on_ground_text)
        st.caption("🔍 Real ADS-B data via OpenSky Network. This report corresponds to real-world transponder emissions.")

        # Download button
        report_content = f"""
OBJECT REPORT
=============
Object: {selected_ac['callsign']}
ICAO24: {selected_ac['icao24']}
Latitude: {selected_ac['lat']:.5f}
Longitude: {selected_ac['lon']:.5f}
Altitude: {alt_text}
Speed: {speed_text}
Heading: {heading_text}
Vertical Rate: {vert_rate_text}
On Ground: {on_ground_text}
Time of report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        st.download_button(
            label="📥 Download Report (TXT)",
            data=report_content,
            file_name=f"{selected_ac['callsign']}_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("No aircraft detected within current range.")

with right_col:
    st.subheader("🗺️ Radar Coverage Map")
    map_fig = create_map(aircraft, radar_lat, radar_lon, max_range)
    st.plotly_chart(map_fig, use_container_width=True)
    if st.session_state.last_update:
        st.caption(f"📡 Last update: {st.session_state.last_update.strftime('%H:%M:%S')} | Range: {max_range} km")
    else:
        st.caption(f"📡 Range: {max_range} km")

# Auto-refresh using JavaScript (reloads page every refresh_sec seconds)
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

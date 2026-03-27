import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt, atan2, pi, asin, degrees
import time
from datetime import datetime

st.set_page_config(page_title="SURVEILLANCE RADAR - Military & Drone Detection", layout="wide", page_icon="🔴")

# -------------------------------------------------------------------
# Classification helpers
# -------------------------------------------------------------------

# Known military ICAO hex ranges (prefixes)
# These are common ranges; not exhaustive but a good starting point
MILITARY_ICAO_PREFIXES = [
    "AE",  # US military
    "AD",  # US military (some)
    "AF",  # US Air Force / misc
    "3C",  # Germany
    "3E",  # Germany
    "33",  # Italy
    "34",  # Spain
    "38",  # Turkey
    "39",  # France
    "40",  # UK
    "43",  # UK
    "44",  # UK
    "45",  # Denmark
    "46",  # Sweden
    "48",  # Poland
    "4B",  # Turkey
    "4C",  # Israel
    "4D",  # Israel
    "4E",  # Romania
    "4F",  # Saudi Arabia
    "50",  # Jordan
    "51",  # UAE
    "52",  # Kuwait
    "53",  # Qatar
    "54",  # Australia
    "55",  # Taiwan
    "56",  # Switzerland
    "57",  # Singapore
    "58",  # South Africa
    "59",  # South Korea
    "5A",  # China
    "5B",  # Cyprus
    "5C",  # Malta
    "5D",  # India
    "5E",  # Malaysia
    "5F",  # Indonesia
    "60",  # Pakistan
    "61",  # Sri Lanka
    "62",  # Sudan
    "63",  # Ethiopia
    "64",  # Kenya
    "65",  # Tanzania
    "66",  # Uganda
    "67",  # Zimbabwe
    "68",  # Zambia
    "69",  # Namibia
    "6A",  # Botswana
    "6B",  # Mozambique
    "6C",  # Malawi
    "6D",  # Lesotho
    "6E",  # Swaziland
    "6F",  # Mauritius
    "70",  # Somalia
    "71",  # Djibouti
    "72",  # Eritrea
    "73",  # Rwanda
    "74",  # Burundi
    "75",  # Comoros
    "76",  # Seychelles
    "77",  # Maldives
    "78",  # Singapore
    "79",  # Hong Kong
    "7A",  # Macau
    "7B",  # Mongolia
    "7C",  # North Korea
    "7D",  # South Korea
    "7E",  # Japan
    "7F",  # Philippines
    "80",  # Vietnam
    "81",  # Cambodia
    "82",  # Laos
    "83",  # Myanmar
    "84",  # Thailand
    "85",  # Taiwan
    "86",  # China
    "87",  # China
    "88",  # China
    "89",  # China
    "8A",  # China
    "8B",  # China
    "8C",  # China
    "8D",  # China
    "8E",  # China
    "8F",  # China
    "90",  # China
    "91",  # China
    "92",  # China
    "93",  # China
    "94",  # China
    "95",  # China
    "96",  # China
    "97",  # China
    "98",  # China
    "99",  # China
    "9A",  # China
    "9B",  # China
    "9C",  # China
    "9D",  # China
    "9E",  # China
    "9F",  # China
    "A0",  # Russia
    "A1",  # Russia
    "A2",  # Russia
    "A3",  # Russia
    "A4",  # Russia
    "A5",  # Russia
    "A6",  # Russia
    "A7",  # Russia
    "A8",  # Russia
    "A9",  # Russia
    "AA",  # Russia
    "AB",  # Russia
    "AC",  # Russia
]

# Known drone ICAO prefixes (examples)
DRONE_ICAO_PREFIXES = [
    "4CAA",  # DJI
    "4CAB",  # DJI
    "4CAC",  # DJI
    "4CAD",  # DJI
    "4CAE",  # DJI
    "4CAF",  # DJI
    "4CB0",  # DJI
    "4CB1",  # DJI
    "4CB2",  # DJI
    "4CB3",  # DJI
    "4CB4",  # DJI
    "4CB5",  # DJI
    "4CB6",  # DJI
    "4CB7",  # DJI
    "4CB8",  # DJI
    "4CB9",  # DJI
    "4CBA",  # DJI
    "4CBB",  # DJI
    "4CBC",  # DJI
    "4CBD",  # DJI
    "4CBE",  # DJI
    "4CBF",  # DJI
    "4CC0",  # DJI
    "4CC1",  # DJI
    "4CC2",  # DJI
    "4CC3",  # DJI
    "4CC4",  # DJI
    "4CC5",  # DJI
    "4CC6",  # DJI
    "4CC7",  # DJI
    "4CC8",  # DJI
    "4CC9",  # DJI
    "4CCA",  # DJI
    "4CCB",  # DJI
    "4CCC",  # DJI
    "4CCD",  # DJI
    "4CCE",  # DJI
    "4CCF",  # DJI
    "4CD0",  # DJI
    "4CD1",  # DJI
    "4CD2",  # DJI
    "4CD3",  # DJI
    "4CD4",  # DJI
    "4CD5",  # DJI
    "4CD6",  # DJI
    "4CD7",  # DJI
    "4CD8",  # DJI
    "4CD9",  # DJI
    "4CDA",  # DJI
    "4CDB",  # DJI
    "4CDC",  # DJI
    "4CDD",  # DJI
    "4CDE",  # DJI
    "4CDF",  # DJI
]

def classify_aircraft(icao24, callsign, velocity, altitude):
    """Return dict with classification flags and type string."""
    is_military = False
    is_drone = False
    type_str = "Unknown"

    # Normalise for comparison
    icao_upper = icao24.upper()
    callsign_upper = callsign.upper() if callsign else ""

    # Military by ICAO prefix
    for prefix in MILITARY_ICAO_PREFIXES:
        if icao_upper.startswith(prefix):
            is_military = True
            break

    # Military by callsign keywords
    mil_keywords = ["AF", "NAVY", "ARMY", "AIR FORCE", "MIL", "RAAF", "RAF", "LUFT", "ARMEE", "FAP", "FAB", "FAC", "FAD", "FAE", "FAG", "FAH", "FAI", "FAJ", "FAK", "FAL", "FAM", "FAN", "FAO", "FAP", "FAQ", "FAR", "FAS", "FAT", "FAU", "FAV", "FAW", "FAX", "FAY", "FAZ", "FBA", "FBB", "FBC", "FBD", "FBE", "FBF", "FBG", "FBH", "FBI", "FBJ", "FBK", "FBL", "FBM", "FBN", "FBO", "FBP", "FBQ", "FBR", "FBS", "FBT", "FBU", "FBV", "FBW", "FBX", "FBY", "FBZ", "FCA", "FCB", "FCC", "FCD", "FCE", "FCF", "FCG", "FCH", "FCI", "FCJ", "FCK", "FCL", "FCM", "FCN", "FCO", "FCP", "FCQ", "FCR", "FCS", "FCT", "FCU", "FCV", "FCW", "FCX", "FCY", "FCZ"]
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

    # Heuristic: low altitude, low speed, not a helicopter (we can't know helicopter type, but can still flag)
    if not is_drone and not is_military:
        if altitude is not None and altitude < 500 and velocity is not None and velocity < 30:
            is_drone = True

    # Determine type string
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
# Existing helper functions (unchanged)
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

@st.cache_data(ttl=30)
def fetch_opensky():
    url = "https://opensky-network.org/api/states/all"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RadarApp/1.0)"}
    max_retries = 3
    timeout = 20

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
            classification = classify_aircraft(icao24, callsign, velocity, geo_alt)
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
                "distance": dist,
                "type": classification["type"],
                "is_military": classification["is_military"],
                "is_drone": classification["is_drone"]
            })
    seen = set()
    unique = []
    for ac in aircraft_list:
        if ac["icao24"] not in seen:
            seen.add(ac["icao24"])
            unique.append(ac)
    return unique

def bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    y = sin(lon2 - lon1) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)
    brng = atan2(y, x)
    return (brng * 180 / pi + 360) % 360

def create_radar_polar(aircraft, radar_lat, radar_lon, max_range_km):
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
            # Color by type: military red, drone orange, civilian green
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
    # Color by type
    df['color'] = df.apply(lambda row: '#ff4444' if row['is_military'] else ('#ffaa44' if row['is_drone'] else '#2eff9e'), axis=1)
    df['size'] = df['velocity'].apply(lambda v: 10 if (v and v > 0.5) else 8)

    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        hover_name='callsign',
        hover_data={'altitude': True, 'velocity': True, 'heading': True, 'type': True},
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

st.title("🔴 SURVEILLANCE RADAR (ADS‑B)")
st.markdown("Military & Drone Detection | Real‑time airspace monitoring")
st.markdown("🇭🇹 Owner: Gesner Deslandes")

# Session state for cached data
if "last_aircraft" not in st.session_state:
    st.session_state.last_aircraft = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None

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

with st.sidebar:
    st.header("📡 Radar Settings")
    if geo_lat is not None and geo_lon is not None:
        radar_lat = st.number_input("Radar Latitude", value=geo_lat, format="%.5f")
        radar_lon = st.number_input("Radar Longitude", value=geo_lon, format="%.5f")
    else:
        radar_lat = st.number_input("Radar Latitude", value=40.7128, format="%.5f")
        radar_lon = st.number_input("Radar Longitude", value=-74.0060, format="%.5f")
    max_range = st.number_input("Max Range (km)", min_value=30, max_value=300, value=120, step=10)
    refresh_sec = st.number_input("Refresh Interval (sec)", min_value=3, max_value=60, value=60, step=1)

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
    st.markdown("Powered by [OpenSky Network](https://opensky-network.org)")

states = fetch_opensky()

if states is not None:
    aircraft = filter_aircraft(states, radar_lat, radar_lon, max_range)
    st.session_state.last_aircraft = aircraft
    st.session_state.last_update = datetime.now()
elif st.session_state.last_aircraft:
    aircraft = st.session_state.last_aircraft
    st.warning("⚠️ Using cached data from previous successful fetch. OpenSky API is currently rate‑limiting.")
else:
    aircraft = []
    st.warning("⚠️ No data available. Radar is searching but no objects detected yet. Try adjusting range or waiting for API availability.")

left_col, right_col = st.columns([0.5, 0.5])

with left_col:
    st.subheader("📡 RADAR SWEEP VIEW")
    polar_fig = create_radar_polar(aircraft, radar_lat, radar_lon, max_range)
    st.plotly_chart(polar_fig, use_container_width=True)

    st.subheader(f"📋 Detected Objects ({len(aircraft)})")
    if aircraft:
        df_table = pd.DataFrame(aircraft)
        display_df = df_table[["callsign", "lat", "lon", "altitude", "velocity", "heading", "type"]].copy()
        display_df["altitude"] = display_df["altitude"].apply(lambda x: f"{x:.0f}m" if x is not None else "N/A")
        display_df["velocity"] = display_df["velocity"].apply(lambda x: f"{x:.1f}m/s" if x is not None else "?")
        display_df["heading"] = display_df["heading"].apply(lambda x: f"{x:.0f}°" if x is not None else "---")
        display_df = display_df.rename(columns={
            "callsign": "CALLSIGN/ID",
            "lat": "LATITUDE",
            "lon": "LONGITUDE",
            "altitude": "ALT (m)",
            "velocity": "SPEED (m/s)",
            "heading": "HEADING",
            "type": "TYPE"
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
        # Classification details
        st.markdown("**🛡️ Classification**")
        if selected_ac["is_military"]:
            st.success("🔫 **Military Aircraft** – flagged by ICAO range or callsign keywords.")
        elif selected_ac["is_drone"]:
            st.warning("🚁 **Drone / UAV** – flagged by ICAO range, callsign keywords, or low‑altitude/speed behaviour.")
        else:
            st.info("✈️ **Civilian Aircraft** – no military or drone indicators.")
        st.caption("🔍 Real ADS-B data via OpenSky Network. Military detection based on known ICAO hex ranges and callsign patterns. Drone detection includes manufacturer ICAO prefixes and heuristic low‑altitude/speed behaviour.")

        # Download button
        report_content = f"""
SURVEILLANCE REPORT
===================
Object: {selected_ac['callsign']}
ICAO24: {selected_ac['icao24']}
Type: {selected_ac['type']}
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
            file_name=f"{selected_ac['callsign']}_surveillance_report.txt",
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

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt, atan2, pi, asin, degrees
import time
from datetime import datetime

# -------------------------------------------------------------------
# Language dictionaries (same as before – omitted for brevity, include full translations)
# -------------------------------------------------------------------
# ... (include the full TRANSLATIONS dictionary from previous version)
# To keep the answer manageable, I'll include a placeholder. In your actual app.py, you must include the complete translations.
TRANSLATIONS = {
    'en': { ... },   # add all translations from the previous working version
    'fr': { ... },
    'es': { ... },
    'ht': { ... }
}

def t(key, **kwargs):
    lang = st.session_state.get('language', 'en')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# -------------------------------------------------------------------
# Page config & language selector
# -------------------------------------------------------------------
st.set_page_config(page_title="Surveillance Radar - Global ADS-B", layout="wide", page_icon="🔴")

col_lang1, col_lang2, col_lang3, col_lang4 = st.columns([1,1,1,5])
with col_lang1:
    if st.button("🇺🇸 English"):
        st.session_state.language = 'en'
        st.rerun()
with col_lang2:
    if st.button("🇫🇷 Français"):
        st.session_state.language = 'fr'
        st.rerun()
with col_lang3:
    if st.button("🇪🇸 Español"):
        st.session_state.language = 'es'
        st.rerun()
with col_lang4:
    if st.button("🇭🇹 Kreyòl"):
        st.session_state.language = 'ht'
        st.rerun()

if 'language' not in st.session_state:
    st.session_state.language = 'en'

# -------------------------------------------------------------------
# Enhanced drone detection (same as before)
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
    "4CB5", "4CB6", "4CB7", "4CB8", "4CB9", "4CBA", "4CBB", "4CBC", "4CBD", "4CBE", "4CBF",
    "4CC0", "4CC1", "4CC2", "4CC3", "4CC4", "4CC5", "4CC6", "4CC7", "4CC8", "4CC9", "4CCA",
    "4CCB", "4CCC", "4CCD", "4CCE", "4CCF", "4CD0", "4CD1", "4CD2", "4CD3", "4CD4", "4CD5",
    "4CD6", "4CD7", "4CD8", "4CD9", "4CDA", "4CDB", "4CDC", "4CDD", "4CDE", "4CDF",
    "7C", "7D", "7E", "7F", "A5", "A6", "A7", "A8", "A9", "AA", "AB", "AC", "AD", "AE", "AF",
]

def classify_aircraft(icao24, callsign, velocity, altitude, aircraft_type=None):
    is_military = False
    is_drone = False

    icao_upper = icao24.upper() if icao24 else ""
    callsign_upper = callsign.upper() if callsign else ""

    for prefix in MILITARY_ICAO_PREFIXES:
        if icao_upper.startswith(prefix):
            is_military = True
            break
    mil_keywords = ["AF", "NAVY", "ARMY", "AIR FORCE", "MIL", "RAAF", "RAF", "LUFT", "ARMEE"]
    if any(kw in callsign_upper for kw in mil_keywords):
        is_military = True

    for prefix in DRONE_ICAO_PREFIXES:
        if icao_upper.startswith(prefix):
            is_drone = True
            break
    drone_keywords = ["DRONE", "UAV", "DRON", "QUAD", "HEXA", "OCTO", "RQ", "MQ", "GLOBALHAWK", "PREDATOR", "REAPER"]
    if any(kw in callsign_upper for kw in drone_keywords):
        is_drone = True

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

# ---------- Improved fetch with shorter timeout and fewer retries ----------
def fetch_opensky():
    url = "https://opensky-network.org/api/states/all"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RadarApp/1.0)"}
    max_retries = 2
    timeout = 15  # seconds

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("states", [])
            elif resp.status_code == 429:
                wait = 20
                st.toast(f"OpenSky rate limit. Waiting {wait}s... (attempt {attempt+1}/{max_retries})", icon="⏳")
                time.sleep(wait)
            else:
                st.toast(f"OpenSky returned {resp.status_code}. Retrying... (attempt {attempt+1}/{max_retries})", icon="⚠️")
                time.sleep(2 ** attempt)
        except requests.exceptions.Timeout:
            st.toast(f"OpenSky timeout (attempt {attempt+1}/{max_retries})", icon="⏱️")
            time.sleep(2 ** attempt)
        except Exception as e:
            st.toast(f"OpenSky error: {e}", icon="❌")
            time.sleep(2 ** attempt)

    return None  # No data after retries

def fetch_flightradar24(api_key):
    try:
        from flightradar24 import FlightRadar24API
        fr24 = FlightRadar24API(api_key)
        flights = fr24.get_flights()
        aircraft_list = []
        for f in flights:
            aircraft_list.append({
                "icao24": getattr(f, "hex", ""),
                "callsign": getattr(f, "callsign", getattr(f, "number", "")),
                "lat": getattr(f, "latitude", None),
                "lon": getattr(f, "longitude", None),
                "geo_alt": getattr(f, "altitude", None),
                "velocity": getattr(f, "speed", None),
                "heading": getattr(f, "heading", None),
                "vertical_rate": None,
                "on_ground": False,
            })
        return aircraft_list
    except Exception as e:
        st.warning(f"Flightradar24 API error: {e}")
        return None

def fetch_data(api_key=None):
    if api_key:
        fr_data = fetch_flightradar24(api_key)
        if fr_data is not None:
            return fr_data
        st.info("Flightradar24 not available – falling back to OpenSky (limited range).")
    return fetch_opensky()

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
            if ac.get("is_military", False):
                colors.append("#ff4444")
            elif ac.get("is_drone", False):
                colors.append("#ffaa44")
            else:
                colors.append("#2eff9e")
            labels.append(ac["callsign"])
    fig = go.Figure()
    if r_vals:
        fig.add_trace(go.Scatterpolar(
            r=r_vals, theta=theta_vals, mode='markers+text',
            marker=dict(size=10, color=colors, line=dict(width=1, color='white')),
            text=labels, textposition="top center", name='Aircraft'
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, max_range_km], tickvals=[max_range_km*0.25, max_range_km*0.5, max_range_km*0.75, max_range_km],
                            ticktext=[f"{int(max_range_km*0.25)}km", f"{int(max_range_km*0.5)}km", f"{int(max_range_km*0.75)}km", f"{int(max_range_km)}km"],
                            gridcolor='#2a4f6e', linecolor='#2aff9e', ticks='outside', showticklabels=True),
            angularaxis=dict(tickmode='array', tickvals=[0,45,90,135,180,225,270,315],
                             ticktext=['N','NE','E','SE','S','SW','W','NW'],
                             direction='clockwise', rotation=90, gridcolor='#2a4f6e', linecolor='#2aff9e'),
            bgcolor='#03060c'
        ),
        title=dict(text="Radar Sweep View", font=dict(color='#ccd6f6')),
        paper_bgcolor='#03060c', plot_bgcolor='#03060c', margin=dict(l=80, r=80, t=80, b=80)
    )
    angle = (datetime.now().second * 6) % 360
    sweep_line = go.Scatterpolar(r=[0, max_range_km], theta=[angle, angle], mode='lines',
                                 line=dict(color='#ffaa44', width=2), name='Sweep', showlegend=False)
    fig.add_trace(sweep_line)
    return fig

def create_map(aircraft, radar_lat, radar_lon, max_range_km):
    if not aircraft:
        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(lat=[radar_lat], lon=[radar_lon], mode='markers',
                                        marker=dict(size=12, color='#ffaa44', symbol='circle'), name='Radar Center'))
        fig.update_layout(mapbox=dict(style="dark", center=dict(lat=radar_lat, lon=radar_lon), zoom=4),
                          margin=dict(l=0, r=0, t=0, b=0))
        return fig
    df = pd.DataFrame(aircraft)
    df['color_group'] = df.apply(lambda row: 'military' if row.get('is_military', False) else ('drone' if row.get('is_drone', False) else 'civilian'), axis=1)
    color_map = {'military': '#ff4444', 'drone': '#ffaa44', 'civilian': '#2eff9e'}
    df['size'] = df['velocity'].apply(lambda v: 10 if (v and v > 0.5) else 8)
    fig = px.scatter_mapbox(df, lat='lat', lon='lon', hover_name='callsign',
                            hover_data={'altitude': True, 'velocity': True, 'heading': True, 'type': True, 'distance': True},
                            zoom=4, height=600, color='color_group', color_discrete_map=color_map, size='size', size_max=12, title='')
    fig.add_trace(go.Scattermapbox(lat=[radar_lat], lon=[radar_lon], mode='markers',
                                    marker=dict(size=12, color='#ffaa44', symbol='circle'), name='Radar Center'))
    ring_distances = [0.25, 0.5, 0.75, 1.0]
    for frac in ring_distances:
        r_km = max_range_km * frac
        circle_lats, circle_lons = [], []
        for i in range(65):
            brng = 360 * i / 64
            lat2, lon2 = destination_point(radar_lat, radar_lon, r_km, brng)
            circle_lats.append(lat2)
            circle_lons.append(lon2)
        fig.add_trace(go.Scattermapbox(lat=circle_lats, lon=circle_lons, mode='lines',
                                        line=dict(width=1, color='#28e6a8'), showlegend=False, hoverinfo='none'))
    fig.update_layout(mapbox=dict(style="dark", center=dict(lat=radar_lat, lon=radar_lon), zoom=4),
                      margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

# -------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------
st.title(t('app_title'))
st.markdown(t('subtitle'))
st.markdown(t('owner'))
st.markdown(t('business'))

# Session state
if "last_aircraft" not in st.session_state:
    st.session_state.last_aircraft = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "data_source" not in st.session_state:
    st.session_state.data_source = "OpenSky"
if "prev_lat" not in st.session_state:
    st.session_state.prev_lat = None
if "prev_lon" not in st.session_state:
    st.session_state.prev_lon = None
if "dismiss_error" not in st.session_state:
    st.session_state.dismiss_error = False

# Geolocation
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

if geo_lat is not None and geo_lon is not None:
    if (st.session_state.prev_lat != geo_lat or st.session_state.prev_lon != geo_lon):
        st.cache_data.clear()
        st.session_state.last_aircraft = []
        st.session_state.last_update = None
        st.session_state.dismiss_error = False
        st.toast(t('location_updated'), icon="🔄")
    st.session_state.prev_lat = geo_lat
    st.session_state.prev_lon = geo_lon

with st.sidebar:
    st.header(t('radar_settings'))
    if geo_lat is not None and geo_lon is not None:
        radar_lat = st.number_input(t('radar_latitude'), value=geo_lat, format="%.5f")
        radar_lon = st.number_input(t('radar_longitude'), value=geo_lon, format="%.5f")
    else:
        radar_lat = st.number_input(t('radar_latitude'), value=40.7128, format="%.5f")
        radar_lon = st.number_input(t('radar_longitude'), value=-74.0060, format="%.5f")
    max_range = st.number_input(t('max_range'), min_value=30, max_value=2000, value=500, step=50)

    st.divider()
    st.header(t('data_source'))
    st.markdown(t('global_coverage_info'))
    api_key = st.text_input(t('api_key_label'), type="password", placeholder=t('api_key_placeholder'))
    if api_key:
        st.info(t('global_active'))
    else:
        st.info(t('opensky_info'))

    auto_refresh = st.checkbox(t('auto_refresh'), value=False)
    if auto_refresh:
        refresh_sec = st.number_input(t('refresh_interval'), min_value=10, max_value=300, value=60, step=10)
    else:
        refresh_sec = 0

    if st.button(t('my_location'), use_container_width=True):
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

    if st.button(t('refresh_now'), use_container_width=True):
        st.cache_data.clear()
        st.session_state.dismiss_error = False
        st.rerun()

    st.divider()
    st.markdown(t('license_title'))
    st.markdown(t('license_text'))
    st.markdown(t('contact_phone'))
    st.markdown(t('contact_email'))
    st.caption(t('terms'))

# Fetch data
with st.spinner(t('fetching')):
    raw_data = fetch_data(api_key if api_key else None)

if raw_data is not None:
    aircraft = []
    if api_key:
        for item in raw_data:
            dist = haversine(radar_lat, radar_lon, item["lat"], item["lon"])
            if dist <= max_range:
                classification = classify_aircraft(item["icao24"], item["callsign"], item["velocity"], item["geo_alt"])
                aircraft.append({
                    **item,
                    "distance": dist,
                    "type": classification["type"],
                    "is_military": classification["is_military"],
                    "is_drone": classification["is_drone"]
                })
    else:
        for s in raw_data:
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
            if dist <= max_range:
                classification = classify_aircraft(icao24, callsign, velocity, geo_alt)
                aircraft.append({
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
    st.session_state.last_aircraft = aircraft
    st.session_state.last_update = datetime.now()
    st.session_state.data_source = "Flightradar24" if api_key else "OpenSky"
    st.session_state.dismiss_error = False
else:
    if st.session_state.last_aircraft:
        aircraft = st.session_state.last_aircraft
        st.warning(t('using_cached'))
        st.session_state.dismiss_error = False
    else:
        aircraft = []
        if not st.session_state.dismiss_error:
            error_placeholder = st.empty()
            with error_placeholder.container():
                st.error(t('no_data_error'))
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(t('dismiss'), key="dismiss_error_btn"):
                        st.session_state.dismiss_error = True
                        st.rerun()
                with col2:
                    if st.button(t('retry'), key="retry_btn"):
                        st.cache_data.clear()
                        st.session_state.dismiss_error = False
                        st.rerun()
        else:
            st.info(t('error_dismissed'))

if 'aircraft' in locals():
    left_col, right_col = st.columns([0.5, 0.5])
    with left_col:
        st.subheader(t('radar_sweep'))
        polar_fig = create_radar_polar(aircraft, radar_lat, radar_lon, max_range)
        st.plotly_chart(polar_fig, use_container_width=True)

        st.subheader(t('detected_objects', count=len(aircraft)))
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

            selected_callsign = st.selectbox(t('select_object'), df_table["callsign"].tolist())
            selected_ac = df_table[df_table["callsign"] == selected_callsign].iloc[0]

            st.subheader(t('detailed_report'))
            col1, col2 = st.columns(2)
            col1.metric(t('object'), selected_ac["callsign"])
            col2.metric(t('icao'), selected_ac["icao24"] if selected_ac["icao24"] else "N/A")
            col1.metric(t('lat_lon'), f"{selected_ac['lat']:.5f}, {selected_ac['lon']:.5f}")
            alt_text = f"{selected_ac['altitude']:.0f} m ({selected_ac['altitude']*3.28084:.0f} ft)" if selected_ac["altitude"] else "unknown"
            col2.metric(t('altitude'), alt_text)
            speed_text = f"{selected_ac['velocity']:.2f} m/s ({selected_ac['velocity']*3.6:.1f} km/h)" if selected_ac["velocity"] else "unknown"
            col1.metric(t('speed'), speed_text)
            heading_text = f"{selected_ac['heading']:.1f}° (true)" if selected_ac["heading"] else "unknown"
            col2.metric(t('heading'), heading_text)
            col1.metric(t('distance'), f"{selected_ac['distance']:.0f} km")
            col2.metric(t('type'), selected_ac["type"])
            st.markdown(f"**{t('classification')}**")
            if selected_ac["is_military"]:
                st.success(t('military_msg'))
            elif selected_ac["is_drone"]:
                st.warning(t('drone_msg'))
            else:
                st.info(t('civilian_msg'))
            st.caption(t('data_source_caption') + ("Flightradar24 (global)" if api_key else "OpenSky Network (regional)"))

            report_content = f"""
{t('detailed_report')}
===================
{t('object')}: {selected_ac['callsign']}
{t('icao')}: {selected_ac['icao24'] if selected_ac['icao24'] else 'N/A'}
{t('type')}: {selected_ac['type']}
{t('lat_lon')}: {selected_ac['lat']:.5f}, {selected_ac['lon']:.5f}
{t('distance')}: {selected_ac['distance']:.0f} km
{t('altitude')}: {alt_text}
{t('speed')}: {speed_text}
{t('heading')}: {heading_text}
{t('data_source_caption')}: {st.session_state.data_source}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            st.download_button(
                label=t('download_report'),
                data=report_content,
                file_name=f"{selected_ac['callsign']}_report.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info(t('no_aircraft'))

    with right_col:
        st.subheader("🗺️ Radar Coverage Map")
        map_fig = create_map(aircraft, radar_lat, radar_lon, max_range)
        st.plotly_chart(map_fig, use_container_width=True)
        if st.session_state.last_update:
            st.caption(t('last_update', time=st.session_state.last_update.strftime('%H:%M:%S'), range=max_range, source=st.session_state.data_source))
        else:
            st.caption(t('range_only', range=max_range, source=st.session_state.data_source))

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

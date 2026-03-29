import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from math import radians, sin, cos, sqrt, atan2, pi, asin, degrees
import time
import random
from datetime import datetime, timedelta

# -------------------------------------------------------------------
# Language dictionaries (extended with satellite keys and demo strings)
# -------------------------------------------------------------------
TRANSLATIONS = {
    'en': {
        # Radar keys
        'app_title': '🔴 GLOBAL SURVEILLANCE RADAR',
        'subtitle': 'Military & Drone Detection | Real‑time airspace monitoring',
        'owner': '🇭🇹 Owner: Gesner Deslandes – Licensed Software',
        'business': '🏢 **GlobalInternet.py**',
        'radar_settings': '📡 Radar Settings',
        'radar_latitude': 'Radar Latitude',
        'radar_longitude': 'Radar Longitude',
        'max_range': 'Max Range (km)',
        'data_source': '🔑 Data Source',
        'global_coverage_info': 'For global coverage (oceans & remote areas), enter your Flightradar24 API key.',
        'api_key_label': 'Flightradar24 API Key',
        'api_key_placeholder': 'Enter your API key (optional)',
        'global_active': '🌍 **Global coverage active** – you will see aircraft worldwide.',
        'opensky_info': '📡 Using OpenSky Network (regional coverage, free).',
        'demo_mode': '🎮 Demo Mode (sample data – for testing only)',
        'auto_refresh': 'Auto‑refresh page',
        'refresh_interval': 'Refresh Interval (sec)',
        'my_location': '📍 My Location',
        'refresh_now': '🔄 Refresh Now',
        'license_title': '📜 **Software License**',
        'license_text': '**Proprietary Commercial Software**  \nCopyright © 2025 Gesner Deslandes. All rights reserved.\n\nThis software is **licensed**, not sold.  \nYou may use it only after purchasing a valid license from the author.\n\n**Unauthorized copying, distribution, or resale is strictly prohibited.**\n\nFor licensing, support, or payments:\n',
        'contact_phone': '📞 **Prisme Transfer** (Digicel Moncash): `(509) 4738-5663`',
        'contact_email': '📧 **Email**: `deslandes78@gmail.com`',
        'terms': 'By using this software you agree to the terms above.',
        'radar_sweep': '📡 RADAR SWEEP VIEW',
        'detected_objects': '📋 Detected Objects ({count})',
        'select_object': 'Select object for detailed report',
        'detailed_report': '📋 Detailed Report',
        'object': '✈️ OBJECT',
        'icao': '🆔 ICAO24',
        'lat_lon': '📍 LAT/LON',
        'altitude': '📏 ALTITUDE',
        'speed': '💨 SPEED',
        'heading': '🧭 HEADING',
        'distance': '📡 DISTANCE',
        'type': '📋 TYPE',
        'classification': '🛡️ Classification',
        'military_msg': '🔫 **Military Aircraft** – flagged by ICAO range or callsign keywords.',
        'drone_msg': '🚁 **Drone / UAV** – flagged by ICAO range, callsign keywords, or low‑altitude/speed behaviour.',
        'civilian_msg': '✈️ **Civilian Aircraft** – no military or drone indicators.',
        'data_source_caption': 'Data source: ',
        'download_report': '📥 Download Report (TXT)',
        'no_aircraft': 'No aircraft detected within current range. This is often due to limited OpenSky coverage in your area. Try:\n- Centering the radar on a busier region (e.g., New York).\n- Purchasing a Flightradar24 API key for true global coverage.',
        'last_update': '📡 Last update: {time} | Range: {range} km | Source: {source}',
        'range_only': '📡 Range: {range} km | Source: {source}',
        'fetching': 'Fetching aircraft data...',
        'using_cached': '⚠️ Using cached data (API unavailable)',
        'no_data_error': '❌ No live aircraft data available from OpenSky. For real‑time tracking in your area, please obtain a Flightradar24 API key (paid) or enable Demo Mode to test the interface.',
        'dismiss': 'Dismiss',
        'retry': 'Retry',
        'error_dismissed': 'Error dismissed. Click \'Refresh Now\' to retry.',
        'opensky_rate_limit': 'OpenSky rate limit. Waiting {wait}s... (attempt {attempt}/{max_retries})',
        'opensky_retry': 'OpenSky returned {status}. Retrying... (attempt {attempt}/{max_retries})',
        'opensky_timeout': 'OpenSky timeout (attempt {attempt}/{max_retries})',
        'opensky_error': 'OpenSky error: {error}',
        'using_cached_toast': 'Using cached data (OpenSky unavailable)',
        'location_updated': '📍 Location updated – refreshing data...',
        'demo_active': '🎮 DEMO MODE – sample data (for testing only)',
        'api_status': 'API Status: {status}',
        # Satellite keys
        'satellite_mode': '🛰️ Satellite Tracker',
        'satellite_list': '📋 Satellite Positions',
        'download_all_satellites': '📥 Download All Satellite Data (CSV)',
        'select_satellite': 'Select satellite for detailed view',
        'satellite_report': 'SATELLITE REPORT',
        'current_position': 'Current Position',
        'predicted_track': 'Predicted Ground Track (next 2 hours)',
        'next_passes': '🔭 Next Passes Over Your Location',
        'download_sat_report': '📥 Download Report (TXT)',
        'no_passes': 'No passes predicted in the next 2 days.',
        'fetching_satellites': 'Fetching satellite positions (this may take 30 seconds)...',
        'sat_api_key_label': 'N2YO API Key',
        'sat_api_key_placeholder': 'Enter your N2YO API key (free at n2yo.com)',
        'sat_auto_refresh': 'Auto‑refresh',
        'sat_refresh_interval': 'Refresh interval (seconds)',
        'sat_pass_location': 'Predict passes over:',
        'sat_latitude': 'Latitude',
        'sat_longitude': 'Longitude',
        'sat_demo_mode': '🎮 Demo Mode (sample data – for testing only)',
        'sat_demo_active': '🎮 DEMO MODE – sample satellite data (testing only)',
    },
    'fr': {
        'app_title': '🔴 RADAR DE SURVEILLANCE GLOBAL',
        'subtitle': 'Détection militaire & drones | Surveillance aérienne en temps réel',
        'owner': '🇭🇹 Propriétaire : Gesner Deslandes – Logiciel sous licence',
        'business': '🏢 **GlobalInternet.py**',
        'radar_settings': '📡 Paramètres Radar',
        'radar_latitude': 'Latitude du radar',
        'radar_longitude': 'Longitude du radar',
        'max_range': 'Portée max (km)',
        'data_source': '🔑 Source de données',
        'global_coverage_info': 'Pour une couverture mondiale (océans & zones reculées), entrez votre clé API Flightradar24.',
        'api_key_label': 'Clé API Flightradar24',
        'api_key_placeholder': 'Entrez votre clé API (optionnel)',
        'global_active': '🌍 **Couverture mondiale active** – vous verrez les aéronefs du monde entier.',
        'opensky_info': '📡 Utilisation du réseau OpenSky (couverture régionale, gratuit).',
        'demo_mode': '🎮 Mode démo (données d’exemple – test uniquement)',
        'auto_refresh': 'Actualisation automatique',
        'refresh_interval': 'Intervalle d\'actualisation (s)',
        'my_location': '📍 Ma position',
        'refresh_now': '🔄 Actualiser',
        'license_title': '📜 **Licence du logiciel**',
        'license_text': '**Logiciel commercial propriétaire**  \nCopyright © 2025 Gesner Deslandes. Tous droits réservés.\n\nCe logiciel est **sous licence**, non vendu.  \nVous ne pouvez l\'utiliser qu\'après avoir acheté une licence valide auprès de l\'auteur.\n\n**La copie, distribution ou revente non autorisée est strictement interdite.**\n\nPour les licences, support ou paiements :\n',
        'contact_phone': '📞 **Prisme Transfer** (Digicel Moncash) : `(509) 4738-5663`',
        'contact_email': '📧 **Email** : `deslandes78@gmail.com`',
        'terms': 'En utilisant ce logiciel, vous acceptez les conditions ci-dessus.',
        'radar_sweep': '📡 VUE RADAR (BALAYAGE)',
        'detected_objects': '📋 Objets détectés ({count})',
        'select_object': 'Sélectionnez un objet pour un rapport détaillé',
        'detailed_report': '📋 Rapport détaillé',
        'object': '✈️ OBJET',
        'icao': '🆔 ICAO24',
        'lat_lon': '📍 LAT/LON',
        'altitude': '📏 ALTITUDE',
        'speed': '💨 VITESSE',
        'heading': '🧭 CAP',
        'distance': '📡 DISTANCE',
        'type': '📋 TYPE',
        'classification': '🛡️ Classification',
        'military_msg': '🔫 **Aéronef militaire** – détecté par plage ICAO ou indicatif.',
        'drone_msg': '🚁 **Drone / UAV** – détecté par plage ICAO, indicatif, ou comportement (basse altitude/vitesse).',
        'civilian_msg': '✈️ **Aéronef civil** – aucun indicateur militaire ou drone.',
        'data_source_caption': 'Source de données : ',
        'download_report': '📥 Télécharger le rapport (TXT)',
        'no_aircraft': 'Aucun aéronef détecté dans la portée actuelle. Cela est souvent dû à la couverture limitée d’OpenSky dans votre région. Essayez :\n- Centrer le radar sur une zone plus fréquentée (ex. New York).\n- Acheter une clé API Flightradar24 pour une couverture mondiale.',
        'last_update': '📡 Dernière mise à jour : {time} | Portée : {range} km | Source : {source}',
        'range_only': '📡 Portée : {range} km | Source : {source}',
        'fetching': 'Récupération des données aéronefs...',
        'using_cached': '⚠️ Utilisation des données mises en cache (API indisponible)',
        'no_data_error': '❌ Aucune donnée aéronef en direct disponible via OpenSky. Pour un suivi en temps réel dans votre région, veuillez obtenir une clé API Flightradar24 (payante) ou activer le mode démo pour tester l’interface.',
        'dismiss': 'Ignorer',
        'retry': 'Réessayer',
        'error_dismissed': 'Erreur ignorée. Cliquez sur "Actualiser" pour réessayer.',
        'opensky_rate_limit': 'Limite de débit OpenSky. Attente de {wait}s... (tentative {attempt}/{max_retries})',
        'opensky_retry': 'OpenSky a retourné {status}. Nouvel essai... (tentative {attempt}/{max_retries})',
        'opensky_timeout': 'Délai d\'attente OpenSky dépassé (tentative {attempt}/{max_retries})',
        'opensky_error': 'Erreur OpenSky : {error}',
        'using_cached_toast': 'Utilisation des données mises en cache (OpenSky indisponible)',
        'location_updated': '📍 Position mise à jour – actualisation des données...',
        'demo_active': '🎮 MODE DÉMO – données d’exemple (test uniquement)',
        'api_status': 'État API : {status}',
        # Satellite keys French
        'satellite_mode': '🛰️ Traqueur de satellites',
        'satellite_list': '📋 Positions des satellites',
        'download_all_satellites': '📥 Télécharger toutes les données (CSV)',
        'select_satellite': 'Sélectionner un satellite',
        'satellite_report': 'RAPPORT SATELLITE',
        'current_position': 'Position actuelle',
        'predicted_track': 'Trajectoire prévue (2h)',
        'next_passes': '🔭 Prochains passages',
        'download_sat_report': '📥 Télécharger le rapport (TXT)',
        'no_passes': 'Aucun passage prévu dans les 2 prochains jours.',
        'fetching_satellites': 'Récupération des positions satellites (30 sec)...',
        'sat_api_key_label': 'Clé API N2YO',
        'sat_api_key_placeholder': 'Entrez votre clé N2YO (gratuite sur n2yo.com)',
        'sat_auto_refresh': 'Actualisation auto',
        'sat_refresh_interval': "Intervalle d'actualisation (s)",
        'sat_pass_location': 'Prédire les passages à :',
        'sat_latitude': 'Latitude',
        'sat_longitude': 'Longitude',
        'sat_demo_mode': '🎮 Mode démo (données d’exemple – test uniquement)',
        'sat_demo_active': '🎮 MODE DÉMO – données satellites d’exemple (test uniquement)',
    },
    'es': {
        'app_title': '🔴 RADAR DE VIGILANCIA GLOBAL',
        'subtitle': 'Detección militar y drones | Monitoreo aéreo en tiempo real',
        'owner': '🇭🇹 Propietario: Gesner Deslandes – Software bajo licencia',
        'business': '🏢 **GlobalInternet.py**',
        'radar_settings': '📡 Configuración del Radar',
        'radar_latitude': 'Latitud del radar',
        'radar_longitude': 'Longitud del radar',
        'max_range': 'Alcance máximo (km)',
        'data_source': '🔑 Fuente de datos',
        'global_coverage_info': 'Para cobertura global (océanos y zonas remotas), ingrese su clave API de Flightradar24.',
        'api_key_label': 'Clave API de Flightradar24',
        'api_key_placeholder': 'Ingrese su clave API (opcional)',
        'global_active': '🌍 **Cobertura global activa** – verá aeronaves en todo el mundo.',
        'opensky_info': '📡 Usando OpenSky Network (cobertura regional, gratis).',
        'demo_mode': '🎮 Modo demo (datos de ejemplo – solo pruebas)',
        'auto_refresh': 'Actualización automática',
        'refresh_interval': 'Intervalo de actualización (seg)',
        'my_location': '📍 Mi ubicación',
        'refresh_now': '🔄 Actualizar ahora',
        'license_title': '📜 **Licencia de software**',
        'license_text': '**Software comercial propietario**  \nCopyright © 2025 Gesner Deslandes. Todos los derechos reservados.\n\nEste software está **bajo licencia**, no se vende.  \nSolo puede usarlo después de comprar una licencia válida al autor.\n\n**La copia, distribución o reventa no autorizada está estrictamente prohibida.**\n\nPara licencias, soporte o pagos:\n',
        'contact_phone': '📞 **Prisme Transfer** (Digicel Moncash): `(509) 4738-5663`',
        'contact_email': '📧 **Correo electrónico**: `deslandes78@gmail.com`',
        'terms': 'Al usar este software acepta los términos anteriores.',
        'radar_sweep': '📡 VISTA RADAR (BARRIDO)',
        'detected_objects': '📋 Objetos detectados ({count})',
        'select_object': 'Seleccione un objeto para informe detallado',
        'detailed_report': '📋 Informe detallado',
        'object': '✈️ OBJETO',
        'icao': '🆔 ICAO24',
        'lat_lon': '📍 LAT/LON',
        'altitude': '📏 ALTITUD',
        'speed': '💨 VELOCIDAD',
        'heading': '🧭 RUMBO',
        'distance': '📡 DISTANCIA',
        'type': '📋 TIPO',
        'classification': '🛡️ Clasificación',
        'military_msg': '🔫 **Aeronave militar** – identificada por rango ICAO o indicativo.',
        'drone_msg': '🚁 **Drone / UAV** – identificado por rango ICAO, indicativo o comportamiento (baja altitud/velocidad).',
        'civilian_msg': '✈️ **Aeronave civil** – sin indicadores militares o de dron.',
        'data_source_caption': 'Fuente de datos: ',
        'download_report': '📥 Descargar informe (TXT)',
        'no_aircraft': 'No se detectaron aeronaves en el alcance actual. Esto suele deberse a la cobertura limitada de OpenSky en su área. Pruebe:\n- Centrar el radar en una región con más tráfico (ej. Nueva York).\n- Adquirir una clave API de Flightradar24 para cobertura global.',
        'last_update': '📡 Última actualización: {time} | Alcance: {range} km | Fuente: {source}',
        'range_only': '📡 Alcance: {range} km | Fuente: {source}',
        'fetching': 'Obteniendo datos de aeronaves...',
        'using_cached': '⚠️ Usando datos en caché (API no disponible)',
        'no_data_error': '❌ No hay datos de aeronaves en directo disponibles a través de OpenSky. Para un seguimiento en tiempo real en su área, obtenga una clave API de Flightradar24 (de pago) o active el modo demo para probar la interfaz.',
        'dismiss': 'Descartar',
        'retry': 'Reintentar',
        'error_dismissed': 'Error descartado. Haga clic en "Actualizar ahora" para reintentar.',
        'opensky_rate_limit': 'Límite de tasa de OpenSky. Esperando {wait}s... (intento {attempt}/{max_retries})',
        'opensky_retry': 'OpenSky devolvió {status}. Reintentando... (intento {attempt}/{max_retries})',
        'opensky_timeout': 'Tiempo de espera agotado de OpenSky (intento {attempt}/{max_retries})',
        'opensky_error': 'Error de OpenSky: {error}',
        'using_cached_toast': 'Usando datos en caché (OpenSky no disponible)',
        'location_updated': '📍 Ubicación actualizada – refrescando datos...',
        'demo_active': '🎮 MODO DEMO – datos de ejemplo (solo pruebas)',
        'api_status': 'Estado API: {status}',
        # Satellite keys Spanish
        'satellite_mode': '🛰️ Rastreador de satélites',
        'satellite_list': '📋 Posiciones de satélites',
        'download_all_satellites': '📥 Descargar todos los datos (CSV)',
        'select_satellite': 'Seleccionar satélite',
        'satellite_report': 'INFORME DEL SATÉLITE',
        'current_position': 'Posición actual',
        'predicted_track': 'Trayectoria prevista (2h)',
        'next_passes': '🔭 Próximos pasos',
        'download_sat_report': '📥 Descargar informe (TXT)',
        'no_passes': 'No se prevén pasos en los próximos 2 días.',
        'fetching_satellites': 'Obteniendo posiciones de satélites (30 seg)...',
        'sat_api_key_label': 'Clave API N2YO',
        'sat_api_key_placeholder': 'Ingrese su clave N2YO (gratuita en n2yo.com)',
        'sat_auto_refresh': 'Actualización automática',
        'sat_refresh_interval': 'Intervalo (seg)',
        'sat_pass_location': 'Predecir pasos en:',
        'sat_latitude': 'Latitud',
        'sat_longitude': 'Longitud',
        'sat_demo_mode': '🎮 Modo demo (datos de ejemplo – solo pruebas)',
        'sat_demo_active': '🎮 MODO DEMO – datos de satélite de ejemplo (solo pruebas)',
    },
    'ht': {
        'app_title': '🔴 RADAR SIVEYANS GLOBAL',
        'subtitle': 'Deteksyon militè & dron | Siveyans espas aeryen an tan reyèl',
        'owner': '🇭🇹 Pwopriyetè: Gesner Deslandes – Lojisyèl ki gen lisans',
        'business': '🏢 **GlobalInternet.py**',
        'radar_settings': '📡 Anviwònman Radar',
        'radar_latitude': 'Latitid radar',
        'radar_longitude': 'Longitid radar',
        'max_range': 'Ran maksimòm (km)',
        'data_source': '🔑 Sous done',
        'global_coverage_info': 'Pou kouvèti mondyal (oseyan & zòn lwen), antre kle API Flightradar24 ou a.',
        'api_key_label': 'Kle API Flightradar24',
        'api_key_placeholder': 'Antre kle API ou a (opsyonèl)',
        'global_active': '🌍 **Kouvèti mondyal aktive** – w ap wè avyon atravè lemonn.',
        'opensky_info': '📡 Sèvi ak OpenSky Network (kouvèti rejyonal, gratis).',
        'demo_mode': '🎮 Mòd demonstrasyon (done egzanp – tès sèlman)',
        'auto_refresh': 'Aktualizasyon otomatik',
        'refresh_interval': 'Entèval aktualizasyon (s)',
        'my_location': '📍 Kote mwen ye',
        'refresh_now': '🔄 Aktualize kounye a',
        'license_title': '📜 **Lisans lojisyèl**',
        'license_text': '**Lojisyèl komèsyal pwopriyetè**  \nCopyright © 2025 Gesner Deslandes. Tout dwa rezève.\n\nLojisyèl sa a **gen lisans**, li pa vann.  \nOu ka sèvi ak li sèlman apre w fin achte yon lisans valab nan men otè a.\n\n**Kopi, distribisyon oswa revent san otorizasyon entèdi.**\n\nPou lisans, sipò, oswa peman:\n',
        'contact_phone': '📞 **Prisme Transfer** (Digicel Moncash): `(509) 4738-5663`',
        'contact_email': '📧 **Imèl**: `deslandes78@gmail.com`',
        'terms': 'Lè w sèvi ak lojisyèl sa a, ou dakò ak kondisyon ki anwo yo.',
        'radar_sweep': '📡 VIZUALIZASYON RADAR (BALE)',
        'detected_objects': '📋 Objè detekte ({count})',
        'select_object': 'Chwazi yon objè pou rapò detaye',
        'detailed_report': '📋 Rapò detaye',
        'object': '✈️ OBJÈ',
        'icao': '🆔 ICAO24',
        'lat_lon': '📍 LAT/LON',
        'altitude': '📏 ALTITID',
        'speed': '💨 VITÈS',
        'heading': '🧭 KAP',
        'distance': '📡 DISTANS',
        'type': '📋 TIP',
        'classification': '🛡️ Klasifikasyon',
        'military_msg': '🔫 **Avyon militè** – detekte pa seri ICAO oswa mo kle yo rele.',
        'drone_msg': '🚁 **Dron / UAV** – detekte pa seri ICAO, mo kle yo rele, oswa konpòtman (altitid ba/vitès ba).',
        'civilian_msg': '✈️ **Avyon sivil** – pa gen endikatè militè oswa dron.',
        'data_source_caption': 'Sous done: ',
        'download_report': '📥 Telechaje rapò (TXT)',
        'no_aircraft': 'Pa gen okenn avyon detekte nan ran aktyèl la. Sa souvan rive akòz kouvèti limite OpenSky nan zòn ou a. Eseye:\n- Mete radar nan yon zòn ki gen plis trafik (eg. New York).\n- Achte yon kle API Flightradar24 pou kouvèti mondyal.',
        'last_update': '📡 Dènye mizajou: {time} | Ran: {range} km | Sous: {source}',
        'range_only': '📡 Ran: {range} km | Sous: {source}',
        'fetching': 'Ap chache done avyon...',
        'using_cached': '⚠️ Sèvi ak done ki nan kachèt (API pa disponib)',
        'no_data_error': '❌ Pa gen done avyon an dirèk disponib atravè OpenSky. Pou yon swivi an tan reyèl nan zòn ou a, tanpri jwenn yon kle API Flightradar24 (peye) oswa aktive mòd Demo pou teste koòdone yo.',
        'dismiss': 'Fèmen',
        'retry': 'Eseye ankò',
        'error_dismissed': 'Erè fèmen. Klike sou "Aktualize kounye a" pou eseye ankò.',
        'opensky_rate_limit': 'Limit vitès OpenSky. Ap tann {wait}s... (esey {attempt}/{max_retries})',
        'opensky_retry': 'OpenSky retounen {status}. Ap eseye ankò... (esey {attempt}/{max_retries})',
        'opensky_timeout': 'Tan ekspirasyon OpenSky (esey {attempt}/{max_retries})',
        'opensky_error': 'Erè OpenSky: {error}',
        'using_cached_toast': 'Sèvi ak done kachèt (OpenSky pa disponib)',
        'location_updated': '📍 Kote mete ajou – ap rafrechi done...',
        'demo_active': '🎮 MÒD DEMO – done egzanp (tès sèlman)',
        'api_status': 'Estati API: {status}',
        # Satellite keys Haitian Creole
        'satellite_mode': '🛰️ Swiv satelit',
        'satellite_list': '📋 Pozisyon satelit',
        'download_all_satellites': '📥 Telechaje tout done (CSV)',
        'select_satellite': 'Chwazi yon satelit',
        'satellite_report': 'RAPÒ SATELIT',
        'current_position': 'Pozisyon aktyèl',
        'predicted_track': 'Trase predi (2 èdtan)',
        'next_passes': '🔭 Pase kap vini yo',
        'download_sat_report': '📥 Telechaje rapò (TXT)',
        'no_passes': 'Pa gen pase prevwa nan 2 jou kap vini yo.',
        'fetching_satellites': 'Ap chache pozisyon satelit (30 seg)...',
        'sat_api_key_label': 'Kle API N2YO',
        'sat_api_key_placeholder': 'Antre kle N2YO ou (gratis sou n2yo.com)',
        'sat_auto_refresh': 'Aktualizasyon otomatik',
        'sat_refresh_interval': 'Entèval (s)',
        'sat_pass_location': 'Predi pase sou:',
        'sat_latitude': 'Latitid',
        'sat_longitude': 'Longitid',
        'sat_demo_mode': '🎮 Mòd demonstrasyon (done egzanp – tès sèlman)',
        'sat_demo_active': '🎮 MÒD DEMO – done satelit egzanp (tès sèlman)',
    },
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
    if st.button("🇺🇸 English", width='stretch'):
        st.session_state.language = 'en'
        st.rerun()
with col_lang2:
    if st.button("🇫🇷 Français", width='stretch'):
        st.session_state.language = 'fr'
        st.rerun()
with col_lang3:
    if st.button("🇪🇸 Español", width='stretch'):
        st.session_state.language = 'es'
        st.rerun()
with col_lang4:
    if st.button("🇭🇹 Kreyòl", width='stretch'):
        st.session_state.language = 'ht'
        st.rerun()

if 'language' not in st.session_state:
    st.session_state.language = 'en'

# -------------------------------------------------------------------
# Mode selector
# -------------------------------------------------------------------
mode = st.radio("", ["Aircraft Radar", "Satellite Tracker"], horizontal=True)

# -------------------------------------------------------------------
# Classification arrays (radar)
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
# Radar helper functions
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
                st.toast(t('opensky_rate_limit', wait=wait, attempt=attempt+1, max_retries=max_retries), icon="⏳")
                time.sleep(wait)
            else:
                st.toast(t('opensky_retry', status=resp.status_code, attempt=attempt+1, max_retries=max_retries), icon="⚠️")
                time.sleep(2 ** attempt)
        except requests.exceptions.Timeout:
            st.toast(t('opensky_timeout', attempt=attempt+1, max_retries=max_retries), icon="⏱️")
            time.sleep(2 ** attempt)
        except Exception as e:
            st.toast(t('opensky_error', error=str(e)), icon="❌")
            time.sleep(2 ** attempt)

    return None

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

def generate_demo_aircraft(radar_lat, radar_lon, max_range_km, num_aircraft=15):
    """Create realistic sample aircraft around the given centre (for testing only)."""
    demo_aircraft = []
    callsigns = ["AAL", "DAL", "UAL", "SWA", "JBU", "FDX", "UPS", "BAW", "KLM", "AFR", "DLH", "JAL", "CPA", "QFA"]
    types = ["✈️ Civilian", "🔫 Military", "🚁 Drone"]
    weights = [0.85, 0.10, 0.05]

    for i in range(num_aircraft):
        dist = random.uniform(20, max_range_km)
        brng = random.uniform(0, 360)
        lat2, lon2 = destination_point(radar_lat, radar_lon, dist, brng)
        alt = random.uniform(0, 12000)
        speed = random.uniform(0, 250)
        heading = random.uniform(0, 360)
        type_choice = random.choices(types, weights=weights)[0]
        is_military = (type_choice == "🔫 Military")
        is_drone = (type_choice == "🚁 Drone")
        callsign = f"{random.choice(callsigns)}{random.randint(100, 9999)}"
        icao24 = f"{random.randint(0, 0xFFFFFF):06X}"
        demo_aircraft.append({
            "icao24": icao24,
            "callsign": callsign,
            "lat": lat2,
            "lon": lon2,
            "altitude": alt,
            "velocity": speed,
            "heading": heading,
            "vertical_rate": random.uniform(-10, 10),
            "on_ground": (alt < 500 and speed < 50),
            "distance": dist,
            "type": type_choice,
            "is_military": is_military,
            "is_drone": is_drone,
        })
    return demo_aircraft

def fetch_data(api_key=None):
    return fetch_opensky()  # only real data

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
# Satellite functions (with demo mode)
# -------------------------------------------------------------------
def get_satellite_list():
    return {
        25544: "International Space Station (ISS)",
        27424: "Hubble Space Telescope",
        28654: "NOAA 19 (weather)",
        33591: "NOAA 18 (weather)",
        33590: "NOAA 17 (weather)",
        27607: "FENGYUN 1C (weather)",
        43014: "NOAA 20 (weather)",
        43750: "RADARSAT Constellation",
        45338: "GPS IIF-12",
        42727: "Tiangong-1",
        37820: "GPS IIF-2",
        37765: "GLONASS",
        43072: "LARE",
        40967: "Cubesat",
    }

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all_satellites(api_key, satellite_dict):
    results = []
    for sat_id, sat_name in satellite_dict.items():
        try:
            url = f"https://api.n2yo.com/rest/v1/satellite/positions/{sat_id}/0/0/0/1/&apiKey={api_key}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'positions' in data and data['positions']:
                    pos = data['positions'][0]
                    results.append({
                        "ID": sat_id,
                        "Name": sat_name,
                        "Latitude": pos['satlatitude'],
                        "Longitude": pos['satlongitude'],
                        "Altitude (km)": pos['sataltitude'],
                        "Speed (km/s)": pos['satvelocity'],
                        "Last Update": datetime.fromtimestamp(pos['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    })
                else:
                    results.append({"ID": sat_id, "Name": sat_name, "Error": "No position data"})
            else:
                results.append({"ID": sat_id, "Name": sat_name, "Error": f"HTTP {resp.status_code}"})
        except Exception as e:
            results.append({"ID": sat_id, "Name": sat_name, "Error": str(e)})
        time.sleep(1.5)
    return pd.DataFrame(results)

def generate_demo_satellites(satellite_dict, num_extra=3):
    """Generate demo satellite data for all real satellites plus a few extra random ones."""
    demo_satellites = []
    for sat_id, sat_name in satellite_dict.items():
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        alt = random.uniform(300, 40000)
        speed = random.uniform(0.5, 8)
        demo_satellites.append({
            "ID": sat_id,
            "Name": sat_name,
            "Latitude": lat,
            "Longitude": lon,
            "Altitude (km)": alt,
            "Speed (km/s)": speed,
            "Last Update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    for i in range(num_extra):
        demo_satellites.append({
            "ID": 100000 + i,
            "Name": f"DemoSat-{i+1}",
            "Latitude": random.uniform(-90, 90),
            "Longitude": random.uniform(-180, 180),
            "Altitude (km)": random.uniform(300, 40000),
            "Speed (km/s)": random.uniform(0.5, 8),
            "Last Update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    return pd.DataFrame(demo_satellites)

def generate_demo_track(sat_id, sat_name, seconds=7200):
    """Generate a fake ground track for a demo satellite."""
    start_lat = random.uniform(-80, 80)
    start_lon = random.uniform(-180, 180)
    track = []
    for t in range(0, seconds, 120):  # every 2 minutes
        lat = start_lat + (t / seconds) * random.uniform(-20, 20)
        lon = start_lon + (t / seconds) * random.uniform(-40, 40)
        lat = max(-90, min(90, lat))
        lon = (lon + 180) % 360 - 180
        track.append({
            'satlatitude': lat,
            'satlongitude': lon,
            'sataltitude': random.uniform(300, 40000),
            'satvelocity': random.uniform(0.5, 8),
            'timestamp': datetime.now().timestamp() + t
        })
    return {
        'current': track[0],
        'track': track,
        'satname': sat_name
    }

def generate_demo_passes(sat_id, user_lat, user_lon, days=2):
    """Generate fake pass times."""
    passes = []
    now = datetime.now()
    for i in range(5):
        start = now + timedelta(days=random.uniform(0, days))
        duration = random.randint(300, 1200)
        passes.append({
            'startUTC': start.timestamp(),
            'endUTC': (start + timedelta(seconds=duration)).timestamp(),
            'duration': duration,
            'maxEl': random.randint(10, 90)
        })
    return passes

def fetch_satellite_details(sat_id, api_key, seconds=7200, demo_mode=False):
    if demo_mode:
        sat_name = next((name for sid, name in get_satellite_list().items() if sid == sat_id), "Demo Satellite")
        return generate_demo_track(sat_id, sat_name, seconds)
    else:
        url = f"https://api.n2yo.com/rest/v1/satellite/positions/{sat_id}/0/0/0/{seconds}/&apiKey={api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'info' in data and 'positions' in data:
                    positions = data['positions']
                    if positions:
                        return {
                            'current': positions[0],
                            'track': positions,
                            'satname': data['info']['satname']
                        }
        except Exception as e:
            st.error(f"Error fetching details: {e}")
        return None

def fetch_passes(sat_id, lat, lon, api_key, days=2, demo_mode=False):
    if demo_mode:
        return generate_demo_passes(sat_id, lat, lon, days)
    else:
        url = f"https://api.n2yo.com/rest/v1/satellite/visualpasses/{sat_id}/{lat}/{lon}/{0}/{days}/&apiKey={api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'passes' in data:
                    return data['passes']
        except:
            pass
        return []

# -------------------------------------------------------------------
# Mode selection: Aircraft Radar
# -------------------------------------------------------------------
if mode == "Aircraft Radar":
    # Radar UI (same as original)
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
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False

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

    # Radar sidebar
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

        demo_mode = st.checkbox(t('demo_mode'), value=st.session_state.demo_mode,
                                help="Use sample aircraft data to test the interface – not real traffic.")
        if demo_mode != st.session_state.demo_mode:
            st.session_state.demo_mode = demo_mode
            st.rerun()

        if api_key:
            st.info(t('global_active'))
        elif st.session_state.demo_mode:
            st.info(t('demo_active'))
        else:
            st.info(t('opensky_info'))

        auto_refresh = st.checkbox(t('auto_refresh'), value=False)
        if auto_refresh:
            refresh_sec = st.number_input(t('refresh_interval'), min_value=10, max_value=300, value=60, step=10)
        else:
            refresh_sec = 0

        if st.button(t('my_location'), width='stretch'):
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

        if st.button(t('refresh_now'), width='stretch'):
            st.cache_data.clear()
            st.session_state.dismiss_error = False
            st.rerun()

    # Fetch data
    if st.session_state.demo_mode:
        aircraft = generate_demo_aircraft(radar_lat, radar_lon, max_range, num_aircraft=20)
        st.session_state.last_aircraft = aircraft
        st.session_state.last_update = datetime.now()
        st.session_state.data_source = "Demo"
        st.session_state.dismiss_error = False
    else:
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
                            if st.button(t('dismiss'), key="dismiss_error_btn", width='stretch'):
                                st.session_state.dismiss_error = True
                                st.rerun()
                        with col2:
                            if st.button(t('retry'), key="retry_btn", width='stretch'):
                                st.cache_data.clear()
                                st.session_state.dismiss_error = False
                                st.rerun()
                else:
                    st.info(t('error_dismissed'))

    if 'aircraft' in locals() and aircraft:
        left_col, right_col = st.columns([0.5, 0.5])
        with left_col:
            st.subheader(t('radar_sweep'))
            polar_fig = create_radar_polar(aircraft, radar_lat, radar_lon, max_range)
            st.plotly_chart(polar_fig, width='stretch')

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
                st.dataframe(display_df, width='stretch', height=400)

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
                st.caption(t('data_source_caption') + st.session_state.data_source)

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
                    width='stretch'
                )
            else:
                st.info(t('no_aircraft'))

        with right_col:
            st.subheader("🗺️ Radar Coverage Map")
            map_fig = create_map(aircraft, radar_lat, radar_lon, max_range)
            st.plotly_chart(map_fig, width='stretch')
            if st.session_state.last_update:
                st.caption(t('last_update', time=st.session_state.last_update.strftime('%H:%M:%S'), range=max_range, source=st.session_state.data_source))
            else:
                st.caption(t('range_only', range=max_range, source=st.session_state.data_source))
    else:
        st.info("No aircraft to display. Try adjusting the range, or enable Demo Mode to test the interface.")

    if refresh_sec > 0 and not st.session_state.demo_mode:
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

    # License (already in sidebar)

# -------------------------------------------------------------------
# Mode selection: Satellite Tracker
# -------------------------------------------------------------------
else:
    with st.sidebar:
        st.markdown("### Settings")
        sat_api_key = st.text_input(
            t('sat_api_key_label'),
            type="password",
            value="8TGB9U-SLULC9-N5XN43-5P4U",
            help="Get your free key at n2yo.com"
        )
        sat_demo_mode = st.checkbox(t('sat_demo_mode'), value=False,
                                    help="Use sample satellite data to test the interface – not real positions.")
        if sat_demo_mode:
            st.info(t('sat_demo_active'))
        auto_refresh_sat = st.checkbox(t('sat_auto_refresh'), value=False)
        if auto_refresh_sat:
            refresh_sec_sat = st.number_input(t('sat_refresh_interval'), min_value=10, max_value=300, value=60, step=10)
        else:
            refresh_sec_sat = 0

        st.divider()
        st.subheader(t('sat_pass_location'))
        user_lat = st.number_input(t('sat_latitude'), value=40.7128, format="%.5f")
        user_lon = st.number_input(t('sat_longitude'), value=-74.0060, format="%.5f")

        if st.button("Refresh Data", width='stretch'):
            st.cache_data.clear()
            st.rerun()

    # Satellite main content
    if not sat_demo_mode and not sat_api_key:
        st.warning("Please enter your N2YO API key to use the satellite tracker, or enable Demo Mode.")
        st.stop()

    satellites_dict = get_satellite_list()
    if sat_demo_mode:
        with st.spinner("Generating demo satellite data..."):
            df_satellites = generate_demo_satellites(satellites_dict, num_extra=5)
        st.info(t('sat_demo_active'))
    else:
        with st.spinner(t('fetching_satellites')):
            df_satellites = fetch_all_satellites(sat_api_key, satellites_dict)

        if 'Error' in df_satellites.columns:
            error_rows = df_satellites[df_satellites['Error'].notna()]
            if not error_rows.empty:
                st.warning(f"Could not fetch data for: {', '.join(error_rows['Name'])}")
            df_satellites = df_satellites[df_satellites['Error'].isna()].drop(columns=['Error'], errors='ignore')

    if df_satellites.empty:
        st.error("No satellite data available. Check your API key or try again later.")
        st.stop()

    st.subheader(t('satellite_list'))
    st.dataframe(df_satellites, use_container_width=True)

    csv = df_satellites.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=t('download_all_satellites'),
        data=csv,
        file_name=f"satellites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    selected_name = st.selectbox(t('select_satellite'), df_satellites['Name'].tolist())
    selected_row = df_satellites[df_satellites['Name'] == selected_name].iloc[0]
    selected_id = selected_row['ID']

    with st.spinner(f"Fetching detailed data for {selected_name}..."):
        details = fetch_satellite_details(selected_id, sat_api_key if not sat_demo_mode else None,
                                          seconds=7200, demo_mode=sat_demo_mode)

    if details:
        current = details['current']
        track = details['track']
        sat_name = details['satname']

        lat = current['satlatitude']
        lon = current['satlongitude']
        alt = current['sataltitude']
        vel = current['satvelocity']
        timestamp = datetime.fromtimestamp(current['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Satellite", sat_name)
        col2.metric("Latitude", f"{lat:.4f}°")
        col3.metric("Longitude", f"{lon:.4f}°")
        col4.metric("Altitude", f"{alt:.1f} km")
        col1.metric("Speed", f"{vel:.2f} km/s")
        col2.metric("Last Updated", timestamp)

        st.subheader(t('predicted_track'))
        track_lons = [p['satlongitude'] for p in track]
        track_lats = [p['satlatitude'] for p in track]

        fig = go.Figure()
        fig.add_trace(go.Scattergeo(
            lon=track_lons,
            lat=track_lats,
            mode='lines',
            line=dict(width=1, color='rgba(100, 200, 255, 0.7)'),
            name='Predicted Track'
        ))
        fig.add_trace(go.Scattergeo(
            lon=[lon],
            lat=[lat],
            mode='markers',
            marker=dict(size=10, color='red', symbol='circle'),
            name=sat_name,
            hovertext=f"{sat_name}<br>Lat: {lat:.4f}<br>Lon: {lon:.4f}<br>Alt: {alt:.0f} km"
        ))
        fig.update_layout(
            geo=dict(
                projection_type="natural earth",
                showland=True,
                landcolor="rgb(243, 243, 243)",
                countrycolor="rgb(204, 204, 204)",
            ),
            title=f"{sat_name} – Current Position and Predicted Track"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(t('next_passes'))
        passes = fetch_passes(selected_id, user_lat, user_lon,
                              sat_api_key if not sat_demo_mode else None,
                              days=2, demo_mode=sat_demo_mode)
        if passes:
            df_passes = pd.DataFrame(passes)
            df_passes['startUTC'] = pd.to_datetime(df_passes['startUTC'], unit='s')
            df_passes['endUTC'] = pd.to_datetime(df_passes['endUTC'], unit='s')
            df_passes['duration'] = df_passes['duration'].apply(lambda x: f"{int(x//60)}m {int(x%60)}s")
            display_df = df_passes[['startUTC', 'endUTC', 'duration', 'maxEl']].rename(columns={
                'startUTC': 'Start (UTC)',
                'endUTC': 'End (UTC)',
                'duration': 'Duration',
                'maxEl': 'Max Elevation (°)'
            })
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info(t('no_passes'))

        report_text = f"""
{t('satellite_report')}
================
Name: {sat_name}
ID: {selected_id}
Current position:
  Latitude: {lat:.5f}°
  Longitude: {lon:.5f}°
  Altitude: {alt:.1f} km
  Speed: {vel:.2f} km/s
  Last update: {timestamp}

Ground track: {len(track)} predicted positions over the next 2 hours.
Pass predictions over ({user_lat}, {user_lon}): {'See table above' if passes else 'None in next 2 days.'}
"""
        st.download_button(
            label=t('download_sat_report'),
            data=report_text,
            file_name=f"{sat_name}_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.error(f"Could not retrieve detailed data for {selected_name}.")

    if auto_refresh_sat:
        st.markdown(
            f"""
            <meta http-equiv="refresh" content="{refresh_sec_sat}">
            """,
            unsafe_allow_html=True
        )

    # License section (common)
    with st.sidebar:
        st.divider()
        st.markdown(t('license_title'))
        st.markdown(t('license_text'))
        st.markdown(t('contact_phone'))
        st.markdown(t('contact_email'))
        st.caption(t('terms'))

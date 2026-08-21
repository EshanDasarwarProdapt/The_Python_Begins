import streamlit as st
import pydeck as pdk
import os
import time
from dotenv import load_dotenv

# Load Env
load_dotenv()

from graph import graph

# --- CONFIG & CSS ---
st.set_page_config(
    page_title="Project O.M.N.I. Command Center",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Sci-Fi Theme */
    .stApp {
        background-color: #0A0A0A;
        color: #00FFCC;
        font-family: 'Courier New', Courier, monospace;
    }
    h1, h2, h3 {
        color: #FF0055;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .metric-box {
        background: rgba(0, 255, 204, 0.05);
        border: 1px solid #00FFCC;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 0 10px rgba(0,255,204,0.2);
    }
    .defcon-1 { color: #FF0000; font-weight: bold; font-size: 2em; text-shadow: 0 0 10px #FF0000; }
    .defcon-2 { color: #FF5500; font-weight: bold; font-size: 2em; }
    .defcon-3 { color: #FFFF00; font-weight: bold; font-size: 2em; }
    .defcon-4 { color: #55FF00; font-weight: bold; font-size: 2em; }
    .defcon-5 { color: #00FFCC; font-weight: bold; font-size: 2em; }
    
    .terminal {
        background: #000;
        border: 1px solid #FF0055;
        padding: 15px;
        font-family: 'Courier New', Courier, monospace;
        color: #FF0055;
        height: 300px;
        overflow-y: scroll;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Project O.M.N.I.")
st.subheader("Omni-Intelligence Global Crisis Command Center")

# --- INITIALIZE STATE ---
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/master-ball.png", width=100)
    st.markdown("### SYSTEM CONTROLS")
    if st.button("INITIATE GLOBAL SCAN", type="primary", use_container_width=True):
        st.session_state.is_scanning = True
        st.session_state.scan_results = None
        
    st.markdown("---")
    st.markdown("**Status**: STANDBY")
    st.markdown("**Modules Active**: 11 / 11")

# --- MAIN LOGIC ---
if st.session_state.is_scanning:
    with st.spinner("Executing O.M.N.I. multi-agent orbital sweep..."):
        # Run LangGraph
        initial_state = {}
        try:
            final_state = graph.invoke(initial_state)
            st.session_state.scan_results = final_state
        except Exception as e:
            st.error(f"SYSTEM FAILURE: {e}")
        st.session_state.is_scanning = False
        st.rerun()

if st.session_state.scan_results:
    res = st.session_state.scan_results
    
    # 1. TOP ROW: GLOBE & DEFCON
    col1, col2 = st.columns([2, 1])
    
    target = res.get("target_event", {})
    lat = target.get("latitude", 0)
    lon = target.get("longitude", 0)
    
    with col1:
        st.markdown("### TARGET LOCK")
        if lat and lon:
            # Get Pokemon sprite
            poke_sprite = res.get("tactical_pokemon", {}).get("sprite_url")
            
            layers = []
            
            # Base radar pulse
            radar_layer = pdk.Layer(
                'ScatterplotLayer',
                data=[{'position': [lon, lat], 'radius': 150000}],
                get_position='position',
                get_radius='radius',
                get_fill_color=[255, 0, 85, 100],
                pickable=True
            )
            layers.append(radar_layer)
            
            # Pokemon Icon Layer
            if poke_sprite:
                icon_data = {
                    "url": poke_sprite,
                    "width": 128,
                    "height": 128,
                    "anchorY": 128
                }
                icon_layer = pdk.Layer(
                    type="IconLayer",
                    data=[{"position": [lon, lat], "icon_data": icon_data}],
                    get_icon="icon_data",
                    get_size=4,
                    size_scale=20,
                    get_position="position",
                    pickable=True,
                )
                layers.append(icon_layer)

            view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=4, pitch=50)
            st.pydeck_chart(pdk.Deck(
                layers=layers, 
                initial_view_state=view_state, 
                map_style=pdk.map_styles.CARTO_DARK  # Fixes black screen without Mapbox token
            ))
        else:
            st.warning("No coordinates acquired.")
            
    with col2:
        st.markdown("### THREAT LEVEL")
        defcon = res.get("defcon_level", 5)
        st.markdown(f"<div class='metric-box' style='text-align:center;'><span class='defcon-{defcon}'>DEFCON {defcon}</span></div>", unsafe_allow_html=True)
        
        st.markdown("### SEISMIC ANOMALY")
        mag = target.get("magnitude", "N/A")
        place = target.get("place", "N/A")
        st.markdown(f"<div class='metric-box'><b>Magnitude:</b> {mag}<br><b>Location:</b> {place}</div>", unsafe_allow_html=True)
        
        st.markdown("### WEATHER HAZARDS")
        wx = res.get("weather_intel", {})
        st.markdown(f"<div class='metric-box'><b>Temp:</b> {wx.get('temperature_c', 'N/A')} °C<br><b>Wind:</b> {wx.get('windspeed_kmh', 'N/A')} km/h</div>", unsafe_allow_html=True)

    # 2. MID ROW: CYBER / FINANCIAL & INTEL
    st.markdown("---")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.markdown("### MACRO-FINANCIAL")
        crypto = res.get("macro_cyber_intel", {}).get("crypto", {})
        btc = crypto.get("bitcoin", {}).get("usd", "N/A")
        eth = crypto.get("ethereum", {}).get("usd", "N/A")
        st.markdown(f"<div class='metric-box'><b>BTC/USD:</b> ${btc}<br><b>ETH/USD:</b> ${eth}</div>", unsafe_allow_html=True)
        
    with col4:
        st.markdown("### CYBER & SENTIMENT")
        cyber = res.get("macro_cyber_intel", {}).get("cyber_alerts", {})
        alerts = cyber.get("alerts", [])
        if alerts:
            st.markdown(f"<div class='metric-box'><b>Threats Detected:</b><br>- " + "<br>- ".join(alerts[:3]) + "</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='metric-box'>Network clear. No anomalies detected in top feeds.</div>", unsafe_allow_html=True)
            
    with col5:
        st.markdown("### ORBITAL ASSETS")
        orbit = res.get("macro_cyber_intel", {}).get("orbital_activity", {})
        st.markdown(f"<div class='metric-box'><b>Mission:</b> {orbit.get('mission_name', 'N/A')}<br><b>Status:</b> {'SUCCESS' if orbit.get('success') else 'UNKNOWN'}</div>", unsafe_allow_html=True)

    # 3. BOTTOM ROW: TACTICAL POKEMON & AI SYNTHESIS
    st.markdown("---")
    col6, col7 = st.columns([1, 2])
    
    with col6:
        st.markdown("### INTERVENTION UNIT")
        poke = res.get("tactical_pokemon", {})
        if "error" not in poke:
            sprite = poke.get("sprite_url")
            if sprite:
                st.image(sprite, width=150)
            
            st.markdown(f"**Codename:** {poke.get('name', 'UNKNOWN').upper()}")
            st.markdown(f"**Type:** {', '.join(poke.get('types', []))}")
            st.markdown(f"**Abilities:** {', '.join(poke.get('abilities', []))}")
            
            # Simple bar chart for stats
            stats = poke.get("stats", {})
            for stat, val in stats.items():
                st.progress(min(val / 200.0, 1.0), text=f"{stat.upper()}: {val}")
        else:
            st.error("Deployment Failed.")
            
    with col7:
        st.markdown("### O.M.N.I. SYNTHESIS REPORT")
        summary = res.get("threat_summary", "NO DATA")
        st.markdown(f"<div class='terminal'>{summary}</div>", unsafe_allow_html=True)

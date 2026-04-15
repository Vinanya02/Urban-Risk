import streamlit as st
import folium
import sys
import requests
from datetime import datetime
import pytz
from gtts import gTTS
import base64
import os
import pandas as pd

missing_dependencies = []

# Optional imports with safe fallback
try:
    from pyngrok import ngrok
except ImportError:
    ngrok = None
    missing_dependencies.append("pyngrok")

st.set_page_config(page_title="Global Sentinel: AI Monitor", layout="wide")

try:
    from streamlit_folium import st_folium
except ImportError:
    st_folium = None
    missing_dependencies.append("streamlit-folium")

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None
    missing_dependencies.append("streamlit-geolocation")

try:
    from langchain_community.vectorstores import FAISS
except ImportError:
    FAISS = None
    missing_dependencies.append("langchain-community")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None
    missing_dependencies.append("langchain-huggingface")


def show_dependency_error():
    if not missing_dependencies:
        return
    st.set_page_config(page_title="Global Sentinel: AI Monitor", layout="wide")
    st.title("🛡️ Global Sentinel: Intelligent Prediction System")
    st.error(
        "The app is missing required Python packages in the active environment.\n"
        "Install them in the same virtual environment that runs Streamlit."
    )
    st.write("### Missing packages")
    for dep in missing_dependencies:
        st.write(f"- `{dep}`")
    st.write("### Run this inside your venv")
    st.code(
        "d:\\urban-risk\\venv_new\\Scripts\\python.exe -m pip install streamlit-folium streamlit-geolocation langchain-community langchain-huggingface"
    )
    st.write("### Then start the app with")
    st.code("d:\\urban-risk\\venv_new\\Scripts\\python.exe -m streamlit run dashboard/app.py")
    st.stop()


# --- NEW: INITIALIZE VECTOR DATABASE (THE KNOWLEDGE BASE) ---
@st.cache_resource
def load_knowledge_base():
    if HuggingFaceEmbeddings is None or FAISS is None:
        return None
    # 1. We define our official emergency protocols (In the future, we will let users upload PDFs here!)
    emergency_protocols = [
        "FLASH FLOOD & CYCLONE PROTOCOL: Move immediately to higher ground. Do not walk, swim, or drive through standing water. Six inches of fast-moving water can knock you off your feet. Disconnect all major electrical appliances.",
        "EXTREME HEAT & FIRE PROTOCOL: Stay indoors in an air-conditioned location. Drink plenty of fluids even if you don't feel thirsty. Monitor engine temperature if driving. If fire is detected, evacuate immediately and stay low to avoid smoke.",
        "NIGHTTIME CRIME & SECURITY PROTOCOL: You are in a high-vulnerability zone with low visibility. Stay in well-lit public areas. Avoid walking alone. Keep all valuables concealed. Request a verified rideshare directly to your door.",
        "EARTHQUAKE SEISMIC PROTOCOL: DROP to your hands and knees. COVER your head and neck under a sturdy table or desk. HOLD ON to your shelter until the shaking stops. Stay away from glass and outside walls.",
        "SEVERE AVIATION PROTOCOL: Severe weather and high winds detected. Check flight status immediately. Expect severe turbulence and grounding. Secure all loose baggage.",
        "RAILWAY HAZARD PROTOCOL: Heavy rain and track flooding detected. Expect severe train delays or derailration hazards. Avoid underground subway stations that may flood."
    ]
    # 2. We load a lightweight AI model to turn these English sentences into Math (Vectors)
    # This downloads a tiny ~80MB model on the first run to act as the "Smart Detective"
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # 3. We create the FAISS Vector Database and store the knowledge!
    vector_db = FAISS.from_texts(emergency_protocols, embeddings)
    return vector_db

show_dependency_error()

# Load the brain into memory
vector_database = load_knowledge_base()

# --- MEMORY CACHE: Load Crime Data safely ---
@st.cache_data
def load_crime_data():
    try:
        df = pd.read_csv("data/Chicago_Crimes_2012_to_2017.csv", nrows=50000)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        return None

crime_dataframe = load_crime_data()

st.set_page_config(page_title="Global Sentinel: AI Monitor", layout="wide")

# --- 1. AUTO-CONNECT SECURE TUNNEL ---
def init_ngrok():
    if ngrok is None:
        return None, "pyngrok not installed"
    try:
        tunnels = ngrok.get_tunnels()
        if tunnels:
            # If tunnels exist, use the first one
            return tunnels[0].public_url, None
        else:
            # Don't start new tunnel automatically to avoid session limits
            return None, "No active tunnels. Start ngrok manually if needed."
    except Exception as e:
        return None, str(e)

secure_url, ngrok_error = init_ngrok()
if secure_url:
    st.success(f"✅ **SECURE LINK ACTIVE:** [Click here to open the Live App]({secure_url})")

st.title("🛡️ Global Sentinel: Intelligent Prediction System")
st.write("Real-time Risk Analysis: Live vs. Home Base")

# --- SYSTEM STATUS (RAG & AI ENGINE) ---
col_rag1, col_rag2, col_rag3 = st.columns(3)
with col_rag1:
    if vector_database is not None:
        st.success("✅ RAG Vector Database: ACTIVE")
    else:
        st.error("❌ RAG Vector Database: FAILED")
        
with col_rag2:
    if HuggingFaceEmbeddings is not None and FAISS is not None:
        st.success("✅ AI Models: Loaded")
    else:
        st.error("❌ AI Models: Not Available")

with col_rag3:
    st.info("🔍 RAG Status: MONITORING (Will activate on red alerts)")

# --- 2. VOICE AI ENGINE ---
def play_voice_alert(text):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("alert.mp3")
        st.write("🔊 **AI Voice Alert Generated:**")
        st.audio("alert.mp3", format="audio/mp3", autoplay=True)
    except Exception as e:
        st.error(f"Audio Engine Error: {e}")

# --- 3. SETUP HOME LOCATION ---
if 'home_lat' not in st.session_state:
    st.session_state.home_lat = 12.9716  
if 'home_lon' not in st.session_state:
    st.session_state.home_lon = 77.5946

with st.sidebar:
    st.header("🏠 Set Home Base")
    new_home_lat = st.number_input("Home Latitude", value=st.session_state.home_lat, format="%.4f")
    new_home_lon = st.number_input("Home Longitude", value=st.session_state.home_lon, format="%.4f")
    
    if st.button("💾 Save Home Location"):
        st.session_state.home_lat = new_home_lat
        st.session_state.home_lon = new_home_lon
        st.success("Home Location Locked!")
        
    st.write("---")
    enable_audio = st.checkbox("🔊 Enable AI Voice Alerts", value=True)

st.sidebar.header("📍 Live Tracker")
location = streamlit_geolocation()

live_lat = st.session_state.home_lat
live_lon = st.session_state.home_lon

if location['latitude'] is not None:
    live_lat = location['latitude']
    live_lon = location['longitude']
    st.sidebar.success("Signal: LIVE GPS LOCKED")
else:
    st.sidebar.warning("Signal: WEAK (Open the Secure Link above!)")

# --- 4. THE "OMNI-BRAIN" (Weather + Earthquakes + Live Crime + Visibility) ---
def predict_risk(lat, lon):
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    current_hour = current_time.hour
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,rain,wind_speed_10m,is_day,visibility"
    try:
        response = requests.get(url).json()['current']
        temp = response['temperature_2m']
        rain = response['rain']
        wind = response['wind_speed_10m']
        is_day = response.get('is_day', 1) 
        visibility = response.get('visibility', 10000) 
    except:
        temp, rain, wind, is_day, visibility = 25, 0, 10, 1, 10000
        
    status = "SAFE"
    predictions = []
    voice_warning = "" 
    
    try:
        url_eq = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        eq_data = requests.get(url_eq).json()
        for feature in eq_data['features']:
            eq_lat = feature['geometry']['coordinates'][1]
            eq_lon = feature['geometry']['coordinates'][0]
            mag = feature['properties']['mag']
            
            if abs(lat - eq_lat) < 2.0 and abs(lon - eq_lon) < 2.0:
                predictions.append(f"🌋 SEISMIC ALERT: Magnitude {mag} Earthquake Nearby!")
                status = "DANGER"
                voice_warning += f" Geological Danger. A magnitude {mag} earthquake has been detected near this location."
                break 
    except:
        pass 

    is_late_night = current_hour >= 23 or current_hour < 4
    
    if crime_dataframe is not None:
        nearby_crimes = crime_dataframe[
            (crime_dataframe['Latitude'] > lat - 0.02) & (crime_dataframe['Latitude'] < lat + 0.02) &
            (crime_dataframe['Longitude'] > lon - 0.02) & (crime_dataframe['Longitude'] < lon + 0.02)
        ]
        crime_count = len(nearby_crimes)
        
        if crime_count > 500:
            if is_late_night:
                predictions.append(f"🦹🔴 RED ALERT: Severe Live Crime Risk! (Late night in historical hotspot)")
                status = "DANGER"
                voice_warning += " Red Alert. You are in a known crime hotspot during high-risk hours. Extreme caution advised."
            else:
                predictions.append(f"🦹🟡 YELLOW ALERT: Known Crime Area (Daytime - Moderate Risk)")
                if status == "SAFE": status = "CAUTION"
                
        elif crime_count > 100:
            if is_late_night:
                predictions.append(f"🦹🟠 ORANGE ALERT: Elevated Nighttime Risk ({crime_count} incidents)")
                if status == "SAFE": status = "CAUTION"
                if not voice_warning: voice_warning = " Orange Alert. Elevated crime probability detected due to late hours."
    else:
        if is_late_night:
            predictions.append("🟡 YELLOW ALERT: Late Night Suspicious Activity Risk")
            if status == "SAFE": status = "CAUTION"
            if not voice_warning: voice_warning = " Caution. It is late at night. Suspicious activity, cyber threats, and theft risk are elevated."

    if is_day == 0 and visibility < 2000 and is_late_night:
        predictions.append("🦹🔴 RED ALERT: Extreme Live Vulnerability (Dead of night + Low Visibility)")
        status = "DANGER"
        if not voice_warning: voice_warning += " Red Alert. Poor visibility and darkness detected. Severe risk of ambush or theft."

    if rain > 5.0 or wind > 60:
        predictions.append("🔴🌊 RED ALERT: Severe Cyclone / Flash Flood Warning!")
        status = "DANGER"
        voice_warning += f" Red alert. Heavy rainfall of {rain} millimeters detected. Flash flooding risk is extreme."
    elif rain > 1.0 or wind > 40:
        predictions.append("🟠 ORANGE ALERT: Heavy Rainfall Expected.")
        if status == "SAFE": status = "CAUTION"

    if temp >= 40: 
        predictions.append("🔴🔥 RED ALERT: Extreme Heatwave / Severe Fire Hazard!")
        status = "DANGER"
        if not voice_warning: voice_warning += f" Red alert. Extreme heatwave of {temp} degrees. Severe fire danger."
    elif temp >= 35:
        predictions.append("🟠 ORANGE ALERT: High Fire Risk (Extreme Heat)")
        if status == "SAFE": status = "CAUTION"

    is_rush_hour = current_hour in [8, 9, 10, 17, 18, 19] 
    
    if is_rush_hour:
        if temp >= 32:
            predictions.append("🔥🚌 YELLOW ALERT: High Transit Fire / Engine Overheating Risk")
            if status == "SAFE": status = "CAUTION"
            if not voice_warning: voice_warning += " Caution. Rush hour traffic combined with high heat. Risk of vehicle overheating."
        if rain > 0.5:
            predictions.append("🚗⚠️ ORANGE ALERT: Road Accident Hotspot / Traffic Gridlock")
            if status in ["SAFE", "CAUTION"]: status = "CAUTION"
            
    if wind > 45:
        predictions.append("✈️🔴 RED ALERT: Severe Aviation Risk (Turbulence / Grounded Flights)")
        status = "DANGER"
        if not voice_warning: voice_warning += " Severe aviation risk detected due to high winds. Flights may be grounded."
        
    if wind > 35:
        predictions.append("🚢🟠 ORANGE ALERT: High Maritime & Boating Risk (Rough Seas)")
        if status == "SAFE": status = "CAUTION"
        
    if rain > 3.0:
        predictions.append("🚆🟠 ORANGE ALERT: Railway Risk (Track Flooding / Derailment Hazard)")
        if status == "SAFE": status = "CAUTION"

    if not predictions:
        predictions.append("✅ Low Risk Zone - All Clear")
        
    return temp, status, predictions, voice_warning

# --- 5. NEW: RAG PREDICTIVE ACTION ENGINE ---
def generate_action_plan(predictions):
    """Uses the Vector Database (FAISS) to semantically find the correct survival protocol."""
    plan = []
    for p in predictions:
        if "Low Risk" in p:
            continue
            
        # 1. The AI takes the live threat string (e.g., "🔴🌊 RED ALERT: Severe Cyclone / Flash Flood Warning!")
        threat_query = p 
        
        # 2. It searches the Vector DB for the closest matching emergency manual!
        # k=1 means "Find the top 1 most mathematically relevant protocol"
        docs = vector_database.similarity_search(threat_query, k=1)
        
        # 3. We extract the exact text from the matched document
        best_protocol = docs[0].page_content
        plan.append(f"**📖 RAG Retrieved Protocol:** {best_protocol}")
        
    return list(set(plan)) 

# --- 6. DUAL MONITOR DISPLAY ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Live Location")
    temp_live, status_live, preds_live, voice_live = predict_risk(live_lat, live_lon)
    st.metric("Temperature", f"{temp_live}°C")
    st.metric("Risk Status", status_live, delta_color="inverse")
    
    for p in preds_live:
        if "Low" in p: st.success(p)
        else: st.error(p)
        
    # Inject the Gen-AI Action Plan into the UI if there is danger
    if status_live != "SAFE":
        with st.expander("📖 View AI Survival & Action Guide (RAG-Powered)", expanded=True):
            st.markdown("**Powered by LangChain HuggingFace RAG** - Semantic matching to survival protocols")
            actions = generate_action_plan(preds_live)
            for action in actions:
                st.error(action)
        
    if enable_audio and voice_live and status_live != "SAFE":
        play_voice_alert(voice_live)

with col2:
    st.subheader("🏠 Home Base")
    temp_home, status_home, preds_home, voice_home = predict_risk(st.session_state.home_lat, st.session_state.home_lon)
    st.metric("Temperature", f"{temp_home}°C")
    st.metric("Risk Status", status_home, delta_color="inverse")
    
    for p in preds_home:
        if "Low" in p: st.success(p)
        else: st.error(p)
        
    # Inject the Gen-AI Action Plan into the UI if there is danger
    if status_home != "SAFE":
        with st.expander("📖 View AI Survival & Action Guide (RAG-Powered)", expanded=True):
            st.markdown("**Powered by LangChain HuggingFace RAG** - Semantic matching to survival protocols")
            actions = generate_action_plan(preds_home)
            for action in actions:
                st.error(action)
        
    if enable_audio and voice_home and status_home != "SAFE" and status_live == "SAFE":
        play_voice_alert(f"Home Base Alert: {voice_home}")

# --- 7. MAP ---
st.write("---")
m = folium.Map(location=[live_lat, live_lon], zoom_start=12)
folium.Marker([live_lat, live_lon], popup="YOU", icon=folium.Icon(color="green")).add_to(m)
folium.Marker([st.session_state.home_lat, st.session_state.home_lon], popup="HOME", icon=folium.Icon(color="blue")).add_to(m)
folium.PolyLine([[live_lat, live_lon], [st.session_state.home_lat, st.session_state.home_lon]], color="gray", opacity=0.5, dash_array='5, 5').add_to(m)

st_folium(m, width="100%", height=500)
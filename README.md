import streamlit as st
import time

# =====================================================================
# 1. PAGE CONFIGURATION & LAYOUT SETTINGS
# =====================================================================
st.set_page_config(
    page_title="Smart EV Charging System",
    page_icon="⚡",
    layout="wide"
)

# =====================================================================
# 2. APPLICATION MEMORY & STATE INITIALIZATION
# =====================================================================
# This mock database holds the current status of all 6 parking slots
if 'parking_lots' not in st.session_state:
    st.session_state.parking_lots = {
        "Slot 1": {"type": "EV", "status": "Available", "vehicle_no": "", "is_ev": False, "soc": 100, "violation": False},
        "Slot 2": {"type": "EV", "status": "Available", "vehicle_no": "", "is_ev": False, "soc": 100, "violation": False},
        "Slot 3": {"type": "EV", "status": "Available", "vehicle_no": "", "is_ev": False, "soc": 100, "violation": False},
        "Slot 4": {"type": "Regular", "status": "Available", "vehicle_no": "", "is_ev": False, "soc": 100, "violation": False},
        "Slot 5": {"type": "Regular", "status": "Available", "vehicle_no": "", "is_ev": False, "soc": 100, "violation": False},
        "Slot 6": {"type": "Regular", "status": "Available", "vehicle_no": "", "is_ev": False, "soc": 100, "violation": False},
    }

if 'logs' not in st.session_state:
    st.session_state.logs = ["🤖 System Engine Initialized. CSP Allocation Constraints Active."]

def log_event(message):
    st.session_state.logs.insert(0, f"[{time.strftime('%X')}] {message}")

# =====================================================================
# 3. AI CORE LOGIC ENGINE: CONSTRAINT SATISFACTION PROBLEM (CSP) SOLVER
# =====================================================================
def allocate_parking_slot_csp(vehicle_no, is_ev, current_soc):
    lots = st.session_state.parking_lots
    
    # -----------------------------------------------------------------
    # CONDITION A: INCOMING VEHICLE IS A NORMAL CAR (NON-EV)
    # -----------------------------------------------------------------
    if not is_ev:
        # Constraint Rule 1: Attempt to fill regular slots first
        for slot, details in lots.items():
            if details["type"] == "Regular" and details["status"] == "Available":
                return slot
        # Constraint Rule 2: Spillover to EV slot if regular spots are full (Triggers ICE-ing violation)
        for slot, details in lots.items():
            if details["type"] == "EV" and details["status"] == "Available":
                return slot
        return None

    # -----------------------------------------------------------------
    # CONDITION B: INCOMING VEHICLE IS AN ELECTRIC VEHICLE (EV)
    # -----------------------------------------------------------------
    # Filter for dedicated EV charging terminals
    ev_slots = {k: v for k, v in lots.items() if v["type"] == "EV"}
    
    # Constraint Rule 3: Map to any immediately open EV terminal
    for slot, details in ev_slots.items():
        if details["status"] == "Available":
            return slot
            
    # Constraint Rule 4: Dynamic Heuristic Deadlock Resolution
    # If all EV slots are full, check if any parked EV has finished charging (100% SoC)
    if current_soc < 50:  # Only prioritize vehicles in critical need of energy
        for slot, details in ev_slots.items():
            if details["status"] == "Occupied" and details["is_ev"] and details["soc"] == 100:
                log_event(f"⚠️ CSP Deadlock Resolved: Eviction notice issued to {details['vehicle_no']} at {slot} for critical vehicle {vehicle_no}.")
                lots[slot]["status"] = "Available"  # Free slot programmatically
                return slot

    # Constraint Rule 5: Spillover to Regular slot if EV terminals are deadlocked
    for slot, details in lots.items():
        if details["type"] == "Regular" and details["status"] == "Available":
            return slot

    return None

# =====================================================================
# 4. WEB INTERFACE VIEW (STREAMLIT FRONTEND)
# =====================================================================
st.markdown("<h1 style='text-align: center;'>⚡ Smart EV Parking Management System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Automated slot allocation using Constraint Satisfaction Problem (CSP) frameworks.</p>", unsafe_allow_html=True)
st.write("---")

left_panel, right_panel = st.columns([2, 1])

# Left Side Dashboard Display
with left_panel:
    st.subheader("📍 Layout Grid & Infrastructure Status")
    
    # Render layout tiles dynamically using conditional styling
    grid = st.columns(3)
    for index, (slot_name, data) in enumerate(st.session_state.parking_lots.items()):
        with grid[index % 3]:
            if data["status"] == "Available":
                bg, border, title, desc = "#e8f5e9", "#2e7d32", "🟢 Available", f"Type: {data['type']}"
            else:
                if data["violation"]:
                    bg, border, title, desc = "#ffebee", "#c62828", "🚨 ICE-ing VIOLATION", f"Vehicle: {data['vehicle_no']}"
                elif data["soc"] == 100:
                    bg, border, title, desc = "#fff3e0", "#ef6c00", "🔋 Fully Charged (Deadlock Risk)", f"Vehicle: {data['vehicle_no']}"
                else:
                    bg, border, title, desc = "#e3f2fd", "#1565c0", f"⚡ Active Charge ({data['soc']}% SoC)", f"Vehicle: {data['vehicle_no']}"
            
            st.markdown(f"""
                <div style="background-color: {bg}; border: 2px solid {border}; padding: 18px; border-radius: 10px; text-align: center; margin-bottom: 15px;">
                    <b style="font-size: 1.1rem; color: #222;">{slot_name}</b><br/>
                    <small style="color: #555;">{desc}</small><br/>
                    <span style="font-weight: bold; font-size: 0.9rem; display: block; margin-top: 8px;">{title}</span>
                </div>
            """, unsafe_allow_html=True)
            
    st.write("---")
    
    # Interactive Arrival Gateway Form
    st.subheader("📥 Entry Management Gate")
    c1, c2, c3 = st.columns(3)
    with c1:
        input_plate = st.text_input("License Plate Number", placeholder="TS-09-AB-1234")
    with c2:
        check_ev = st.checkbox("Is Electric Vehicle (EV)?", value=True)
    with c3:
        input_soc = st.slider("Current Battery (%)", 0, 100, 40, disabled=not check_ev)
        
    if st.button("Evaluate Allocation Optimization", type="primary", use_container_width=True):
        if input_plate:
            target_slot = allocate_parking_slot_csp(input_plate, check_ev, input_soc)
            if target_slot:
                slot_ref = st.session_state.parking_lots[target_slot]
                slot_ref["status"] = "Occupied"
                slot_ref["vehicle_no"] = input_plate
                slot_ref["is_ev"] = check_ev
                slot_ref["soc"] = input_soc
                
                # Check for structural violations (Non-EV vehicle using an EV slot)
                if not check_ev and slot_ref["type"] == "EV":
                    slot_ref["violation"] = True
                    log_event(f"🚨 Sensor Alert: Non-EV vehicle {input_plate} blocked Charging Node {target_slot}!")
                else:
                    slot_ref["violation"] = False
                    log_event(f"✅ CSP Solved: Directed vehicle {input_plate} to terminal {target_slot}.")
                st.rerun()
            else:
                st.error("❌ Allocation Failed: Grid capacity optimization bounds exceeded.")
        else:
            st.warning("Please type a valid license plate string.")

# Right Side Telemetry Logs & Process Simulator
with right_panel:
    st.subheader("🤖 Algorithmic System Logs")
    for event in st.session_state.logs[:8]:
        st.caption(event)
        
    st.write("---")
    st.subheader("⚙️ System Operations Simulator")
    
    # Button to fast forward charging metrics
    st.markdown("**Simulate Power Delivery Progress:**")
    if st.button("⚡ Fast Forward Clock (+25% SoC)", use_container_width=True):
        for slot, configuration in st.session_state.parking_lots.items():
            if configuration["status"] == "Occupied" and configuration["is_ev"] and configuration["soc"] < 100:
                updated_charge = min(100, configuration["soc"] + 25)
                st.session_state.parking_lots[slot]["soc"] = updated_charge
                if updated_charge == 100:
                    log_event(f"📱 User Alert: Vehicle {configuration['vehicle_no']} at terminal {slot} completed charging cycles.")
        st.rerun()
        
    # Module to release a car manually
    st.markdown("**Manual Release Gateway:**")
    target_clear = st.selectbox("Select terminal to disconnect", [""] + list(st.session_state.parking_lots.keys()))
    if st.button("Clear Terminal Session", use_container_width=True):
        if target_clear:
            record = st.session_state.parking_lots[target_clear]
            if record["status"] == "Occupied":
                log_event(f"🚪 Departure Event: Vehicle {record['vehicle_no']} cleared terminal node {target_clear}.")
                record["status"] = "Available"
                record["vehicle_no"] = ""
                record["violation"] = False
                st.rerun()

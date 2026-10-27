import streamlit as st
import pandas as pd
import time

# 1. Page Configuration
st.set_page_config(
    page_title="EV Smart Parking & CSP Allocation",
    page_icon="⚡",
    layout="wide"
)

# 2. Session State Initialization (Persistent Storage Simulation)
if 'parking_lots' not in st.session_state:
    # Initialize 6 slots: 3 EV slots, 3 Regular slots
    st.session_state.parking_lots = {
        f"Slot {i}": {
            "type": "EV" if i <= 3 else "Regular",
            "status": "Available",
            "vehicle_no": "",
            "is_ev": False,
            "battery_soc": 100,
            "violation": False
        } for i in range(1, 7)
    }
if 'logs' not in st.session_state:
    st.session_state.logs = ["System initialized. CSP Solver online."]

def add_log(message):
    st.session_state.logs.insert(0, f"[{time.strftime('%X')}] {message}")

# 3. Core AI Engine: CSP Slot Allocator
def allocate_slot_csp(vehicle_no, is_ev, current_soc):
    lots = st.session_state.parking_lots
    
    # Rule 1: If it's a Non-EV, strictly look at Regular spots first
    if not is_ev:
        for slot, details in lots.items():
            if details["type"] == "Regular" and details["status"] == "Available":
                return slot
        # Hard Constraint: Only allow Non-EV into EV spot if absolutely no regular spots exist
        for slot, details in lots.items():
            if details["type"] == "EV" and details["status"] == "Available":
                return slot
        return None

    # Rule 2: If it is an EV, prioritize EV spots based on lowest battery state of charge (SoC)
    # If an EV spot is occupied by a FULLY CHARGED EV (100%), the CSP engine marks it as "Kickable"
    ev_slots = {k: v for k, v in lots.items() if v["type"] == "EV"}
    
    # Look for a clean, empty EV slot first
    for slot, details in ev_slots.items():
        if details["status"] == "Available":
            return slot
            
    # Dynamic Optimization: If all EV slots are full, check if any parked EV is at 100% SoC
    if current_soc < 50: # Only trigger kick-out logic for critical vehicles needing charge
        for slot, details in ev_slots.items():
            if details["status"] == "Occupied" and details["is_ev"] and details["battery_soc"] == 100:
                add_log(f"⚠️ CSP Deadlock Alert: Discharging vehicle {details['vehicle_no']} requested to vacate {slot} for critical EV {vehicle_no}.")
                # Free the slot up programmatically
                lots[slot]["status"] = "Available"
                return slot

    # Rule 3: Spillover - If EV spots are totally deadlocked, assign to a regular spot for now
    for slot, details in lots.items():
        if details["type"] == "Regular" and details["status"] == "Available":
            return slot

    return None

# 4. Header Layout
st.markdown("<h1 style='text-align: center;'>⚡ Smart EV Parking Management System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Resolving the EV Charging Deadlock Problem using Constraint Satisfaction Logic</p>", unsafe_allow_html=True)
st.write("---")

# 5. Main Dashboard View
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Layout Visualizer & Real-time Sensor Status")
    
    # Render parking grid layout
    grid_cols = st.columns(3)
    idx = 0
    for slot_name, details in st.session_state.parking_lots.items():
        with grid_cols[idx % 3]:
            # Styling based on state
            if details["status"] == "Available":
                bg_color = "#e8f5e9" # light green
                border_color = "#2e7d32"
                text_content = "🟢 Available"
                sub_text = f"Type: {details['type']}"
            else:
                if details["violation"]:
                    bg_color = "#ffebee" # light red
                    border_color = "#c62828"
                    text_content = "🚨 VIOLATION (ICE-ed)"
                    sub_text = f"Vehicle: {details['vehicle_no']}"
                elif details["battery_soc"] == 100:
                    bg_color = "#fff3e0" # light orange
                    border_color = "#ef6c00"
                    text_content = "🔋 Fully Charged (Deadlock Risk)"
                    sub_text = f"Vehicle: {details['vehicle_no']}"
                else:
                    bg_color = "#e3f2fd" # light blue
                    border_color = "#1565c0"
                    text_content = f"⚡ Charging ({details['battery_soc']}% SoC)"
                    sub_text = f"Vehicle: {details['vehicle_no']}"
            
            st.markdown(f"""
                <div style="background-color: {bg_color}; border: 2px solid {border_color}; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                    <b style="font-size: 1.1rem; color: #333;">{slot_name}</b><br/>
                    <small style="color: #666;">{sub_text}</small><br/>
                    <span style="font-weight: bold; font-size: 0.9rem;">{text_content}</span>
                </div>
            """, unsafe_allow_html=True)
        idx += 1

    st.write("---")
    
    # 6. Action Forms: Manage incoming vehicles
    st.subheader("📥 Vehicle Arrival Gate")
    form_col1, form_col2, form_col3 = st.columns(3)
    
    with form_col1:
        v_num = st.text_input("Vehicle Number", placeholder="KA-01-MG-1234")
    with form_col2:
        v_type = st.checkbox("Is Electric Vehicle (EV)?", value=True)
    with form_col3:
        v_soc = st.slider("Current Battery (%)", 0, 100, 35, disabled=not v_type)

    if st.button("Calculate & Allocate Slot", type="primary", use_container_width=True):
        if v_num:
            allocated = allocate_slot_csp(v_num, v_type, v_soc)
            if allocated:
                st.session_state.parking_lots[allocated]["status"] = "Occupied"
                st.session_state.parking_lots[allocated]["vehicle_no"] = v_num
                st.session_state.parking_lots[allocated]["is_ev"] = v_type
                st.session_state.parking_lots[allocated]["battery_soc"] = v_soc
                
                # Mock Computer Vision Check: If non-EV parks in an EV spot
                if not v_type and st.session_state.parking_lots[allocated]["type"] == "EV":
                    st.session_state.parking_lots[allocated]["violation"] = True
                    add_log(f"🚨 Computer Vision Alert: Non-EV {v_num} detected illegally occupying EV space {allocated}!")
                else:
                    st.session_state.parking_lots[allocated]["violation"] = False
                    add_log(f"✅ CSP Assignment: Allocated {v_num} to {allocated} successfully.")
                st.rerun()
            else:
                st.error("❌ Allocation Failed: Parking lot fully optimized, no slots matching criteria available.")
        else:
            st.warning("Please type a valid license plate number.")

with col_right:
    # 7. AI Control Logs & System Simulation
    st.subheader("🤖 AI System Logs")
    for log in st.session_state.logs[:8]:
        st.caption(log)
        
    st.write("---")
    st.subheader("⚙️ Simulation Operations")
    
    # Manual trigger to simulate passage of time / vehicle departure
    st.markdown("**Simulate Charging Progress:**")
    if st.button("⚡ Fast Forward Charging (+25% SoC)"):
        for slot, details in st.session_state.parking_lots.items():
            if details["status"] == "Occupied" and details["is_ev"] and details["battery_soc"] < 100:
                new_soc = min(100, details["battery_soc"] + 25)
                st.session_state.parking_lots[slot]["battery_soc"] = new_soc
                if new_soc == 100:
                    add_log(f"📱 Notification Sent: {details['vehicle_no']} in {slot} is fully charged. Alerted driver to vacate.")
        st.rerun()
        
    st.markdown("**Release & Departure:**")
    release_slot = st.selectbox("Select slot to manually clear", [""] + list(st.session_state.parking_lots.keys()))
    if st.button("Clear Selected Slot"):
        if release_slot:
            v = st.session_state.parking_lots[release_slot]["vehicle_no"]
            st.session_state.parking_lots[release_slot]["status"] = "Available"
            st.session_state.parking_lots[release_slot]["vehicle_no"] = ""
            st.session_state.parking_lots[release_slot]["violation"] = False
            add_log(f"🚪 Departure: Vehicle {v} vacated {release_slot}.")
            st.rerun()
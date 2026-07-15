import streamlit as st
from database import run_query
from datetime import date


def create_default_location_if_missing(user_id):
    """Checks if the user has any pantry locations, and if not, prompts to create one."""
    locations = run_query("SELECT location_id, location_name FROM pantry_locations WHERE user_id = %s", (user_id,))
    
    if not locations:
        st.warning("⚠️ Setup incomplete. You need at least one pantry location to add items.")
        
        # Form to add a quick default location
        with st.form("create_location_form"):
            st.markdown("### Create Your First Pantry Location")
            
            # Use columns for a cleaner input
            col1, col2 = st.columns(2)
            with col1:
                location_name = st.text_input("Location Name", value="Main Fridge")
            with col2:
                storage_type = st.selectbox("Storage Type", ['Cool', 'Frozen', 'Dry'])
            
            submitted = st.form_submit_button("Create Default Location")

            if submitted:
                today = date.today().isoformat()
                location_query = """
                INSERT INTO pantry_locations (user_id, location_name, storage_type, date_added)
                VALUES (%s, %s, %s, %s)
                """
                if run_query(location_query, (user_id, location_name, storage_type, today), fetch=False):
                    st.success(f"Location '{location_name}' created successfully! You can now add items.")
                    st.rerun() 
                else:
                    st.error("Failed to create location.")
        return False
    return True

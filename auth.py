import streamlit as st
from database import run_query
from datetime import date

def authenticate(email, password):
    """Checks credentials against the database."""
    query = "SELECT user_id, full_name, password_hash FROM users WHERE email = %s"
    user_data = run_query(query, (email,))
    
    if user_data and user_data[0]['password_hash'] == password: 
        # NOTE: In a production app, use bcrypt for secure password hashing!
        return user_data[0]['user_id'], user_data[0]['full_name']
    return None, None

def signup(name, email, password):
    """Registers a new user and creates their default pantry location."""
    today = date.today().isoformat()
    
    try:
        # 1. Insert new user (returns new user_id)
        user_query = """
        INSERT INTO users (full_name, email, password_hash, join_date) 
        VALUES (%s, %s, %s, %s)
        """
        new_user_id = run_query(user_query, (name, email, password, today), fetch=False)
        
        if new_user_id:
            # 2. Add Default Pantry Location using the new user_id
            location_query = """
            INSERT INTO pantry_locations (user_id, location_name, storage_type, date_added)
            VALUES (%s, 'Main Fridge', 'Cool', %s)
            """
            run_query(location_query, (new_user_id, today), fetch=False)
            
            st.success(f"Account created for {name}! Default location added. Please Log In.")
            st.rerun() # ADDED FOR CLEANER UX: Force rerun after signup to clear form
            return True
        
        return False
        
    except Exception as e:
        if "Duplicate entry" in str(e):
            st.error("That email is already registered.")
        else:
            st.error(f"An error occurred during sign up: {e}")
        return False
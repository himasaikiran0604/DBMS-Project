import os
import streamlit as st
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "raise_on_warnings": False
}

@st.cache_resource
def get_db_connection():
    """Establishes and returns a cached database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}. Please check credentials in database.py.")
        return None

def run_query(query, params=None, fetch=True):
    """Utility function to execute a query."""
    conn = get_db_connection()
    if not conn:
        return [] if fetch else False

    cursor = conn.cursor(dictionary=True, buffered=True)
    
    try:
        cursor.execute(query, params)
        
        if not fetch:
            conn.commit()
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            return True
        
        results = cursor.fetchall()
        return results

    except mysql.connector.Error as err:
        import sys
        st.error("A critical database error occurred. See console for details.")
        print(f"\n--- CRITICAL SQL ERROR ---", file=sys.stderr)
        print(f"QUERY: {query}", file=sys.stderr)
        print(f"PARAMS: {params}", file=sys.stderr)
        print(f"ERROR: {err}", file=sys.stderr)
        print(f"--------------------------\n", file=sys.stderr)
        # --- END DEBUGGING LINE ---
        
        conn.rollback()
        return [] if fetch else False
    
    finally:
        cursor.close()


def fetch_pantry_data(user_id):
    """Fetches all pantry items for the user."""
    query = """
    SELECT 
        i.ingredient_name, 
        pi.quantity_available, 
        pi.unit_name,                 /* EXPLICITLY SELECT UNIT_NAME */
        pi.expiry_date,
        pl.location_name              /* EXPLICITLY SELECT LOCATION_NAME */
    FROM pantry_items pi
    JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
    JOIN pantry_locations pl ON pi.location_id = pl.location_id
    WHERE pi.user_id = %s
    ORDER BY pi.expiry_date ASC
    """
    return run_query(query, (user_id,))

def fetch_user_recipes(user_id):
    """Fetches all recipes created by the user."""
    query = """
    SELECT recipe_id, recipe_name, cuisine, servings, prep_time_minutes, cook_time_minutes, instructions
    FROM recipes
    WHERE created_by_user_id = %s
    ORDER BY recipe_name
    """
    return run_query(query, (user_id,))
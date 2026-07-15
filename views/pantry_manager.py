import streamlit as st
from database import run_query
from utils import create_default_location_if_missing
from datetime import date
from decimal import Decimal

## ci 2. Add Pantry Items
def show_pantry_manager(user_id):
    """Allows user to add new items to their pantry, checking for and merging duplicates."""
    st.markdown("---")
    st.image("https://placehold.co/800x80/A69722/ffffff?text=Add+Items+To+Your+Pantry", use_container_width=True)

    if not create_default_location_if_missing(user_id):
        return

    # Fetch available ingredients and locations
    ingredients = run_query("SELECT ingredient_id, ingredient_name, unit_name FROM ingredients")
    locations = run_query("SELECT location_id, location_name FROM pantry_locations WHERE user_id = %s", (user_id,))

    if not ingredients or not locations:
        st.error("Ingredient catalog or locations not available. Please check database configuration.")
        return

    ingredient_map = {item['ingredient_name']: item['ingredient_id'] for item in ingredients} if ingredients else {}
    location_map = {item['location_name']: item['location_id'] for item in locations} if locations else {}

    with st.form("add_pantry_item"):
        st.markdown("### Item Details")
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.selectbox("Ingredient Name", list(ingredient_map.keys()))
            item_location = st.selectbox("Storage Location", list(location_map.keys()))

        with col2:
            qty = st.number_input("Quantity Available", min_value=0.01, step=0.1)
            # Find default unit for the selected ingredient
            try:
                unit_default = next((i['unit_name'] for i in ingredients if i['ingredient_name'] == item_name), "units")
            except Exception:
                unit_default = "units" # Fallback if initial fetch fails
            
            unit = st.text_input("Unit", value=unit_default)

        purchase_date = st.date_input("Purchase Date", value=date.today())
        expiry_date = st.date_input("Expiry Date (Optional)", value=date.today())

        submitted = st.form_submit_button("Add Item to Pantry")

        if submitted:
            ing_id = ingredient_map[item_name]
            loc_id = location_map[item_location]

            # --- Duplication Check ---
            check_query = """
            SELECT pantry_item_id, quantity_available 
            FROM pantry_items 
            WHERE user_id = %s AND ingredient_id = %s AND location_id = %s
            """
            existing_item = run_query(check_query, (user_id, ing_id, loc_id))

            if existing_item:
                # UPDATE existing item (Merge quantities)
                existing_id = existing_item[0]['pantry_item_id']
                old_qty = existing_item[0]['quantity_available']
                new_qty = Decimal(str(old_qty)) + Decimal(str(qty))

                update_query = "UPDATE pantry_items SET quantity_available = %s, purchase_date = %s, expiry_date = %s WHERE pantry_item_id = %s"
                run_query(update_query, (new_qty, purchase_date, expiry_date, existing_id), fetch=False)
                st.success(f"Merged! {item_name} inventory updated. New quantity: {new_qty:.2f} {unit}.")
            else:
                # INSERT new item
                insert_query = """
                INSERT INTO pantry_items (user_id, ingredient_id, quantity_available, unit_name, purchase_date, expiry_date, location_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                run_query(insert_query, (user_id, ing_id, Decimal(str(qty)), unit, purchase_date, expiry_date, loc_id), fetch=False)
                st.success(f"Added {qty} {unit} of {item_name} to your pantry!")


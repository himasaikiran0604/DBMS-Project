import streamlit as st
import pandas as pd
from database import run_query, fetch_pantry_data
from datetime import date
from decimal import Decimal
import time

## 1. Dashboard (Read & Consume)
def show_pantry_dashboard(user_id, user_name):
    """Displays the user's main pantry inventory, expiry alerts, and item consumption."""
    st.markdown("---")
    st.image("https://placehold.co/800x80/F5A623/ffffff?text=Your+Personalised+Pantry", use_container_width=True)
    st.header(f" Welcome back, {user_name}!")

    # Fetch Pantry Data using the function from database.py
    pantry_data = fetch_pantry_data(user_id)
    
    if not pantry_data:
        st.info("Your pantry is empty! Use '➕ Add Pantry Items' to stock up.")
        return

    # Convert to DataFrame for processing alerts
    df = pd.DataFrame(pantry_data)
    
    # CRITICAL FIX: Convert object to datetime/date types for vectorized subtraction
    df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
    today = date.today()
    
    # Calculate days difference and filter for items expiring in <= 7 days
    # CRITICAL FIX: Ensure 'today' is converted to Pandas Timestamp for correct vectorized subtraction
    expiry_diff = df['expiry_date'] - pd.Timestamp(today).date()
    df['days_until_expiry'] = expiry_diff.apply(lambda x: x.days)
    
    expiring_soon = df[(df['days_until_expiry'] <= 7) & (df['days_until_expiry'] >= 0)].sort_values(by='days_until_expiry')

    # Expiry Alert Widget
    st.markdown("## Expiring items")
    if not expiring_soon.empty:
        st.warning(f"🚨 **{len(expiring_soon)} items** are expiring soon! Please use them.")
        # Use simple dictionary for dataframe display to avoid complex object issues
        st.dataframe(expiring_soon[['ingredient_name', 'quantity_available', 'unit_name', 'days_until_expiry']], width=900)
    else:
        st.success("✅ No ingredients are expiring soon. Good job!")
    st.markdown("---")
    
    # Main Pantry View
    st.markdown("## Current Stock ")
    # show core columns — width numeric to avoid Streamlit TypeError
    display_cols = [c for c in df.columns if c not in ['days_until_expiry']]
    st.dataframe(df[display_cols], width=900)
    
    # --- Item Consumption Form (Consume/Delete Logic) ---
    st.markdown("---")
    st.markdown("## Consume Items")
    
    # Prepare list for selectbox
    # Ensure location_name column exists (fallback to empty string if missing)
    if 'location_name' not in df.columns:
        df['location_name'] = ''

    df['display_name'] = df['ingredient_name'] + ' (' + df['location_name'] + ')'
    item_options = df['display_name'].tolist()
    
    # CRITICAL FIX: Only render the consumption form if items exist
    if not item_options:
        st.info("No items available to consume.")
        return
    
    if item_options:
        with st.form("consume_item_form"):
            selected_display_name = st.selectbox("Select Item to Use Up:", item_options, key="consume_item_select")
            
            # Filter the DataFrame to get the selected item's data
            selected_row_df = df[df['display_name'] == selected_display_name]
            
            # CRITICAL FIX: Check if DataFrame is not empty before proceeding
            if not selected_row_df.empty:
                selected_row = selected_row_df.iloc[0]
                
                # CRITICAL FIX: Convert Decimal to float for st.number_input max_value
                try:
                    max_qty = float(selected_row['quantity_available'])
                except Exception:
                    # Fallback — if conversion fails, set a high max
                    max_qty = 99999.0
                
                consume_qty = st.number_input(
                    f"Quantity to Remove ({selected_row.get('unit_name', '')})",
                    min_value=0.01,
                    max_value=max_qty,
                    step=0.1,
                    key="consume_qty_input"
                )
                
                submitted = st.form_submit_button("Consume Item & Update Inventory")

                if submitted:
                    
                    # --- START STABILITY BLOCK ---
                    with st.status("Processing Consumption...", expanded=True) as status:
                        
                        # Find the corresponding pantry_item_id
                        ing_id_query = """
                        SELECT pi.pantry_item_id
                        FROM pantry_items pi
                        JOIN ingredients i ON pi.ingredient_id = i.ingredient_id
                        WHERE pi.user_id = %s 
                        AND i.ingredient_name = %s 
                        AND pi.unit_name = %s
                        """
                        status.update(label="1. Retrieving item ID...", state="running")
                        item_details = run_query(ing_id_query, (user_id, selected_row['ingredient_name'], selected_row.get('unit_name', '')))
                        
                        if item_details:
                            pantry_item_id = item_details[0]['pantry_item_id']
                            
                            current_qty = Decimal(str(selected_row['quantity_available']))
                            consumed_qty = Decimal(str(consume_qty))
                            new_qty = current_qty - consumed_qty
                            
                            status.update(label="2. Updating database quantity...", state="running")

                            if new_qty > 0:
                                update_query = "UPDATE pantry_items SET quantity_available = %s WHERE pantry_item_id = %s"
                                run_query(update_query, (new_qty, pantry_item_id), fetch=False)
                                final_message = f"✅ Consumed {consumed_qty:.2f} {selected_row.get('unit_name', '')} of {selected_row['ingredient_name']}. Remaining: {new_qty:.2f}"
                            else:
                                delete_query = "DELETE FROM pantry_items WHERE pantry_item_id = %s"
                                run_query(delete_query, (pantry_item_id,), fetch=False)
                                final_message = f"✅ Consumed all of {selected_row['ingredient_name']}. Item removed from pantry."
                            
                            status.update(label=final_message, state="complete")
                            time.sleep(1) # Visual pause
                            st.rerun() 
                        
                        else:
                            status.update(label="Failed to find item in pantry.", state="error")
                            st.error("Error finding item details for update. Check if unit name is correctly stored.")

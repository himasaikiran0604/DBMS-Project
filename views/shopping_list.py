import streamlit as st
import pandas as pd
from database import run_query, fetch_user_recipes
from decimal import Decimal
from datetime import date


## 5. Shopping List View
def show_shopping_list(user_id):
    """Displays the user's pending shopping lists and allows interactive updating."""
    st.markdown("---")
    st.image("https://placehold.co/800x80/F14A03/ffffff?text=Shopping+List", use_container_width=True)
    list_query = "SELECT list_id, created_date, total_items, status FROM shopping_lists WHERE user_id = %s ORDER BY created_date DESC"
    user_lists = run_query(list_query, (user_id,))
    
    if not user_lists:
        st.info("You have no active shopping lists. Generate one from the '🍳 My Recipes' page!")
        return

    # Filter to only show Active/Pending lists in the selection box
    active_lists = [l for l in user_lists if l['status'] != 'Completed']
    
    if not active_lists:
        st.success("All your shopping lists are completed! Start a new one.")
        return

    st.markdown("### Active Lists")
    df_lists = pd.DataFrame(active_lists)
    st.dataframe(df_lists.drop(columns=['list_id']), width=900)
    
    list_options = {f"List created {row['created_date']} ({row['total_items']} items) - {row['status']}": row['list_id'] for index, row in df_lists.iterrows()}
    
    selected_list_name = st.selectbox("Select List to Edit:", list(list_options.keys()), key='list_select')
    selected_list_id = list_options[selected_list_name]

    # Fetch items for the selected list
    item_query = """
    SELECT 
        i.ingredient_name, 
        sli.quantity_needed, 
        sli.unit_name,
        sli.purchased_flag,
        sli.ingredient_id,
        sli.list_id
    FROM shopping_list_items sli
    JOIN ingredients i ON sli.ingredient_id = i.ingredient_id
    WHERE sli.list_id = %s
    ORDER BY sli.purchased_flag ASC, i.ingredient_name ASC
    """
    list_items = run_query(item_query, (selected_list_id,))

    if list_items:
        st.markdown("#### Items to Purchase")
        df_items = pd.DataFrame(list_items)
        
        # Prepare DataFrame for editing: rename purchased_flag column for display
        df_edit = df_items.rename(columns={'purchased_flag': 'Purchased?'})
        
        # Hide internal IDs but keep them for updating the database
        df_display = df_edit.drop(columns=['ingredient_id', 'list_id'])
        
        # --- Interactive Data Editor ---
        edited_df = st.data_editor(
            df_display,
            column_config={
                "Purchased?": st.column_config.CheckboxColumn(
                    "Purchased?",
                    help="Mark item as bought.",
                    default=False,
                ),
                "quantity_needed": st.column_config.NumberColumn("Quantity Needed", format="%.2f"),
            },
            hide_index=True,
            width=900,
            key='shopping_list_editor'
        )

        # --- Update Logic Form ---
        col_update, col_complete = st.columns(2)
        
        with col_update:
            if st.button("Update Purchased Items"):
                # Track changes made in the data editor
                updated_count = 0
                for index, row in edited_df.iterrows():
                    # Find the original row in the static df_items using the index
                    original_row = df_items.iloc[index]
                    
                    # Check if the purchased flag changed
                    if original_row['purchased_flag'] != row['Purchased?']:
                        update_query = """
                        UPDATE shopping_list_items SET purchased_flag = %s 
                        WHERE list_id = %s AND ingredient_id = %s
                        """
                        run_query(update_query, (row['Purchased?'], selected_list_id, original_row['ingredient_id']), fetch=False)
                        updated_count += 1
                
                if updated_count > 0:
                    st.success(f"{updated_count} items updated!")
                    st.rerun() 
                else:
                    st.info("No changes were made to the list.")

        # --- Complete List Logic ---
        with col_complete:
            if st.button("✅ Mark List as Completed", type="secondary"):
                # 1. Mark all remaining items as purchased (optional step)
                update_all_query = """
                UPDATE shopping_list_items SET purchased_flag = TRUE 
                WHERE list_id = %s
                """
                run_query(update_all_query, (selected_list_id,), fetch=False)
                
                # 2. Update the list status
                complete_list_query = """
                UPDATE shopping_lists SET status = 'Completed' 
                WHERE list_id = %s
                """
                run_query(complete_list_query, (selected_list_id,), fetch=False)
                
                st.success(f"Shopping List '{selected_list_name}' has been marked as Completed!")
                st.rerun()
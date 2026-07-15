import streamlit as st
import pandas as pd
from database import run_query, fetch_user_recipes
from decimal import Decimal
from datetime import date

## 4. My Recipes (Read & Delete & Shopping List Generator)
def show_recipes(user_id):
    """Shows user's recipes, allows deletion, and includes shopping list generation."""
    st.markdown("---")
    st.image("https://placehold.co/800x80/CF03F1/ffffff?text=My+Recipes", use_container_width=True)
    user_recipes = fetch_user_recipes(user_id)
    
    if not user_recipes:
        st.info("You haven't added any recipes yet! Use '✍️ Add Recipe' to create one.")
        return

    df = pd.DataFrame(user_recipes)
    recipe_map = {row['recipe_name']: row['recipe_id'] for index, row in df.iterrows()}
    recipe_options = list(recipe_map.keys())

    # --- Display Recipes ---
    st.markdown("### Your Recipe Collection")
    
    # 1. ADD NEW INDEX COLUMN STARTING AT 1
    df.insert(0, 'No.', range(1, 1 + len(df)))
    
    # Hide the recipe_id column in the main display
    display_cols = [c for c in df.columns if c not in ['recipe_id']]
    # 2. HIDE PANDAS INDEX (index=False) AND SET NEW INDEX AS FIRST COLUMN
    st.dataframe(df[display_cols], width=900, hide_index=True)
    
    # --- Recipe Details & Actions ---
    st.markdown("---")
    st.markdown("### Recipe Details and Actions")

    selected_recipe_name = st.selectbox("Select a Recipe for Actions:", recipe_options, key='recipe_select_action')
    
    # Find the selected recipe ID using the map (reliable integer lookup)
    selected_recipe_id = recipe_map.get(selected_recipe_name)

    if selected_recipe_id is None:
        st.error("Error: Could not find selected recipe ID.")
        return
        
    # Get the full recipe details (guaranteed to find the row)
    selected_recipe = df[df['recipe_id'] == selected_recipe_id].iloc[0]


    # Show Instructions
    with st.expander("View Instructions"):
        st.markdown(selected_recipe.get('instructions', 'No instructions provided.'))
    
    # --- Ingredient Requirements ---
    st.markdown("#### Required Ingredients")
    # Primary query used previously (qualified column names to avoid ambiguity)
    req_query = """
    SELECT i.ingredient_name, ri.qty_required, ri.unit_name,  ri.notes
    FROM recipe_ingredients ri
    JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
    WHERE ri.recipe_id = %s
    """

    requirements = run_query(req_query, (selected_recipe_id,))
    
    # If query returned nothing, but there is a recorded SQL error, show it (helpful for debugging)
    last_sql_error = st.session_state.get('last_sql_error') if 'last_sql_error' in st.session_state else None
    if (not requirements or len(requirements) == 0) and last_sql_error:
        with st.expander("A critical database error occurred (click to view details)"):
            st.code(last_sql_error)

    # If still empty, show the friendly message (no crash)
    if not requirements:
        st.warning("This recipe has no ingredients defined.")
    else:
        # Normalize results into a DataFrame and display (this handles either qty_required or quantity_required)
        req_df = pd.DataFrame(requirements)

        # Defensive: ensure columns exist for display
        display_cols = [c for c in [ 'ingredient_name','qty_required', 'unit_name','notes'] if c in req_df.columns]
        if display_cols:
            st.dataframe(req_df[display_cols], hide_index=True, width=900)
        else:
            st.warning("Recipe ingredient records exist but expected columns are missing. See console for details.")

    col1, col2 = st.columns(2)

    # --- ACTION 1: Generate Shopping List ---
    with col1:
        if st.button("🛒 Generate Shopping List"):
            generate_shopping_list(user_id, selected_recipe_id, selected_recipe.get('recipe_name', selected_recipe_name))

    # --- ACTION 2: Delete Recipe ---
    with col2:
        if st.button("🗑️ Delete Recipe", type="primary"):
            # Cascading Delete: Delete ingredients first, then the recipe
            delete_ri_query = "DELETE FROM recipe_ingredients WHERE recipe_id = %s"
            run_query(delete_ri_query, (selected_recipe_id,), fetch=False)
            
            delete_recipe_query = "DELETE FROM recipes WHERE recipe_id = %s"
            run_query(delete_recipe_query, (selected_recipe_id,), fetch=False)
            
            st.success(f"Recipe '{selected_recipe_name}' and its ingredients have been deleted.")
            st.rerun() 


def generate_shopping_list(user_id, recipe_id, recipe_name):
    """Compares recipe needs against pantry stock and adds shortfall to shopping list."""
    
    # 1. Fetch Recipe Requirements
    req_query = "SELECT ingredient_id, qty_required, unit_name FROM recipe_ingredients WHERE recipe_id = %s"
    requirements = run_query(req_query, (recipe_id,))

    # Fallback if different column name used
    if not requirements:
        req_query_alt = "SELECT ingredient_id, quantity_required AS qty_required, unit_name FROM recipe_ingredients WHERE recipe_id = %s"
        requirements = run_query(req_query_alt, (recipe_id,))

    if not requirements:
        st.error(f"Cannot generate list: Recipe '{recipe_name}' has no ingredients defined.")
        return

    # 2. Fetch User's Pantry Stock
    stock_query = "SELECT ingredient_id, quantity_available FROM pantry_items WHERE user_id = %s"
    pantry_stock = run_query(stock_query, (user_id,))

    stock_map = {item['ingredient_id']: item['quantity_available'] for item in pantry_stock} if pantry_stock else {}

    shortfall_items = []

    for req in requirements:
        ing_id = req.get('ingredient_id')
        required_val = req.get('qty_required') if req.get('qty_required') is not None else req.get('quantity_required', 0)
        try:
            required = Decimal(str(required_val))
        except Exception:
            required = Decimal('0')

        available = Decimal(str(stock_map.get(ing_id, 0)))

        # Calculate Shortfall
        shortfall = required - available

        if shortfall > Decimal(0):
            # Find ingredient name for display and insertion
            name_query = "SELECT ingredient_name FROM ingredients WHERE ingredient_id = %s"
            name_res = run_query(name_query, (ing_id,))
            ingredient_name = name_res[0]['ingredient_name'] if name_res else "Unknown"

            shortfall_items.append({
                'ingredient_id': ing_id,
                'ingredient_name': ingredient_name,
                'quantity_needed': shortfall,
                'unit_name': req.get('unit_name', '')
            })

    if not shortfall_items:
        st.success(f"🎉 Great News! You have all ingredients needed for '{recipe_name}'!")
        return

    # 3. Create New Shopping List Header
    list_query = """
    INSERT INTO shopping_lists (user_id, created_date, total_items, estimated_cost, status)
    VALUES (%s, %s, %s, %s, 'Pending')
    """
    new_list_id = run_query(list_query, (user_id, date.today(), len(shortfall_items), Decimal('0.00')), fetch=False)

    # 4. Insert Shortfall Items
    if new_list_id:
        item_insert_query = """
        INSERT INTO shopping_list_items (list_id, ingredient_id, quantity_needed, unit_name, purchased_flag)
        VALUES (%s, %s, %s, %s, FALSE)
        """
        for item in shortfall_items:
            run_query(item_insert_query, (new_list_id, item['ingredient_id'], item['quantity_needed'], item['unit_name']), fetch=False)
        
        st.success(f"🛒 Shopping List Generated! {len(shortfall_items)} items added for '{recipe_name}'.")
        st.subheader("Items to Buy:")
        
        # Prepare list for clean display
        display_df = pd.DataFrame(shortfall_items)
        st.dataframe(display_df[['ingredient_name', 'quantity_needed', 'unit_name']], width=900)


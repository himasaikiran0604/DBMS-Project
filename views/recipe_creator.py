import streamlit as st
from database import run_query
from utils import create_default_location_if_missing # Not needed here, but good practice
from decimal import Decimal

## 3. Recipe Creator
def show_recipe_creator(user_id):
    """Allows user to add a new recipe and its ingredients in a multi-step process."""
    st.markdown("---")
    st.image("https://placehold.co/800x80/31794B/ffffff?text=Add+a+New+Recipe", use_container_width=True)
    
    # Initialize recipe state if not present
    if 'temp_recipe' not in st.session_state:
        st.session_state['temp_recipe'] = {'id': None, 'name': None, 'ingredients': []}

    # Fetch diet types and ingredients for the forms
    diet_types = run_query("SELECT diet_type_id, diet_name FROM diet_types")
    diet_map = {item['diet_name']: item['diet_type_id'] for item in diet_types} if diet_types else {}
    ingredients = run_query("SELECT ingredient_id, ingredient_name, unit_name FROM ingredients")
    ingredient_map = {item['ingredient_name']: item['ingredient_id'] for item in ingredients} if ingredients else {}

    
    # --- Step 1: Recipe Header ---
    if st.session_state['temp_recipe']['id'] is None:
        with st.form("recipe_header"):
            st.markdown("### 1. Recipe Details")
            name = st.text_input("Recipe Name")
            
            # Duplication Check
            existing_recipes = run_query("SELECT recipe_name FROM recipes WHERE created_by_user_id = %s AND recipe_name = %s", (user_id, name))
            if existing_recipes and name:
                st.error("You already have a recipe with this name. Please choose a unique name.")
                header_submitted = st.form_submit_button("Save Recipe Header (Disabled)")
            else:
                col1, col2, col3, col4 = st.columns(4)
                with col1: servings = st.number_input("Servings", min_value=1)
                with col2: prep_time = st.number_input("Prep Time (min)", min_value=0)
                with col3: cook_time = st.number_input("Cook Time (min)", min_value=0)
                with col4:
                    diet_name = st.selectbox("Diet Type", list(diet_map.keys())) if diet_map else None
                cuisine = st.text_input("Cuisine (e.g., Indian, Italian)")
                instructions = st.text_area("Cooking Instructions")
                
                header_submitted = st.form_submit_button("Save Recipe Header")

            if header_submitted and name and not existing_recipes:
                diet_id = diet_map.get(diet_name) if diet_name else None
                
                # Insert recipe header
                insert_recipe_query = """
                INSERT INTO recipes (created_by_user_id, diet_type_id, recipe_name, cuisine, servings, prep_time_minutes, cook_time_minutes, instructions)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                new_recipe_id = run_query(insert_recipe_query, (user_id, diet_id, name, cuisine, servings, prep_time, cook_time, instructions), fetch=False)
                
                if new_recipe_id:
                    st.session_state['temp_recipe']['id'] = new_recipe_id
                    st.session_state['temp_recipe']['name'] = name
                    st.success(f"Recipe '{name}' saved! Proceed to add ingredients.")
                    st.rerun() 
                else:
                    st.error("Failed to save recipe header to the database.")
    
    # --- Step 2: Ingredient Adder (only shows after header is saved) ---
    if st.session_state['temp_recipe']['id'] is not None:
        recipe_name = st.session_state['temp_recipe']['name']
        recipe_id = st.session_state['temp_recipe']['id']
        
        st.markdown(f"### 2. Add Ingredients to: **{recipe_name}**")
        
        with st.form("recipe_ingredients_adder", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: ingredient_name = st.selectbox("Ingredient", list(ingredient_map.keys()), key="ri_name") if ingredient_map else None
            with col2: qty_required = st.number_input("Quantity Required", min_value=0.01, step=0.01, key="ri_qty")
            with col3: 
                # Find default unit for the selected ingredient
                try:
                    unit_default = next((i['unit_name'] for i in ingredients if i['ingredient_name'] == ingredient_name), "grams")
                except Exception:
                    unit_default = "grams"

                unit_name = st.text_input("Unit", value=unit_default, key="ri_unit")

            notes = st.text_input("Notes (e.g., diced, boiled)", key="ri_notes")
            
            ingredient_submitted = st.form_submit_button("Add Ingredient to Recipe")

            if ingredient_submitted:
                
                # --- CAPTURE VARIABLES DEFENSIELY ---
                ing_id = ingredient_map.get(ingredient_name)
                # Ensure the final values are pulled from the session state keys after submission
                final_unit_name = st.session_state.get("ri_unit", unit_name) 
                final_qty_required = st.session_state.get("ri_qty", qty_required)
                
                if not ing_id:
                    st.error("Invalid ingredient selected.")
                else:
                    # --- START STABILITY BLOCK ---
                    with st.status("Adding Ingredient to Recipe...", expanded=True) as status:
                        
                        # --- DUPLICATE CHECK ---
                        duplicate_check_query = """
                        SELECT 1 FROM recipe_ingredients 
                        WHERE recipe_id = %s AND ingredient_id = %s
                        """
                        if run_query(duplicate_check_query, (recipe_id, ing_id)):
                            status.update(label=f"'{ingredient_name}' is already added.", state="error")
                            st.error(f"'{ingredient_name}' is already added to this recipe. Please choose a different ingredient or finish.")
                        else:
                            insert_ri_query = """
                            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty_required, unit_name, notes)
                            VALUES (%s, %s, %s, %s, %s)
                            """
                            status.update(label="Attempting insertion...", state="running")
                            # Ensure qty is Decimal for SQL insertion consistency
                            if run_query(insert_ri_query, (recipe_id, ing_id, Decimal(str(final_qty_required)), final_unit_name, notes), fetch=False):
                                
                                # --- SUCCESS PATH ---
                                st.session_state['temp_recipe']['ingredients'].append(
                                    f"{final_qty_required} {final_unit_name} of {ingredient_name}"
                                )
                                status.update(label="✅ Ingredient Added Successfully!", state="complete")
                                
                                # SUCCESS MESSAGE ONLY!
                                st.success(f"Added {final_qty_required} {final_unit_name} of {ingredient_name}")
                            else:
                               st.success(f"Added {qty_required} {unit_name} of {ingredient_name}")
                                
        if st.button("✅ Finish Recipe"):
            st.session_state['temp_recipe'] = {'id': None, 'name': None, 'ingredients': []}
            st.success(f"Recipe '{recipe_name}' successfully finalized!")
            st.rerun() 

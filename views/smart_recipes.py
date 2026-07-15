import streamlit as st
import pandas as pd
from database import run_query
from decimal import Decimal

def show_smart_recipes(user_id):
    """
    Suggests recipes by comparing all available recipes against the user's pantry items.
    Displays recipes sorted by the percentage of required ingredients currently available.
    """
    st.markdown("---")
    st.image("https://placehold.co/800x80/FF4B4B/ffffff?text=Instant+Recipes", use_container_width=True)

    # 1. Fetch ALL Recipe Requirements
    # Note: We join recipes and recipe_ingredients to get all requirements at once
    recipes_query = """
    SELECT 
        r.recipe_id, r.recipe_name, r.cuisine, r.servings,
        ri.ingredient_id
    FROM recipes r
    JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id;
    """
    all_requirements = run_query(recipes_query)

    # 2. Fetch User's Pantry Stock
    stock_query = "SELECT ingredient_id FROM pantry_items WHERE user_id = %s AND quantity_available > 0"
    pantry_stock = run_query(stock_query, (user_id,))
    
    if not all_requirements:
        st.info("No recipes found in the system to suggest. Please add some recipes first.")
        return
    
    if not pantry_stock:
        st.warning("Your pantry is empty! Add some items to get smart suggestions.")
        return

    # Create a set of ingredients the user owns for fast lookup
    user_ingredient_ids = {item['ingredient_id'] for item in pantry_stock}

    # 3. Calculate Match Percentage for Each Recipe
    recipe_scores = {}
    
    # Group requirements by recipe
    df_req = pd.DataFrame(all_requirements)

    for recipe_id, group in df_req.groupby('recipe_id'):
        recipe_name = group.iloc[0]['recipe_name']
        cuisine = group.iloc[0]['cuisine']
        servings = group.iloc[0]['servings']
        
        required_ingredients = set(group['ingredient_id'])
        total_required = len(required_ingredients)
        
        # Calculate how many required ingredients the user possesses
        ingredients_available = required_ingredients.intersection(user_ingredient_ids)
        available_count = len(ingredients_available)
        
        # Calculate scores
        match_percentage = (available_count / total_required) * 100
        missing_count = total_required - available_count
        
        recipe_scores[recipe_id] = {
            'Recipe': recipe_name,
            'Cuisine': cuisine,
            'Servings': servings,
            'Match %': int(match_percentage),
            'Missing Items': missing_count,
            'Status': 'Cookable!' if missing_count == 0 else f'{missing_count} missing'
        }

    # 4. Display Results
    df_scores = pd.DataFrame(recipe_scores.values())
    
    # Sort by highest match percentage
    df_scores = df_scores.sort_values(by=['Match %', 'Missing Items'], ascending=[False, True])
    
    st.markdown("---")
    st.info("Recipes below are sorted by how many ingredients you currently have in stock.")
    
    st.dataframe(
        df_scores,
        column_config={
            'Match %': st.column_config.ProgressColumn(
                "Match Percentage",
                help="Percentage of required ingredients you currently own",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True,
        width=900
    )
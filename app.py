import streamlit as st
import pandas as pd
from auth import authenticate, signup
from views.dashboard import show_pantry_dashboard
from views.pantry_manager import show_pantry_manager
from views.recipes import show_recipes
from views.recipe_creator import show_recipe_creator
from views.shopping_list import show_shopping_list
from views.smart_recipes import show_smart_recipes 
import sys

# --- 1. Navigation Options (Matching the requested labels) ---
NAV_OPTIONS = {
    "🏠 My Pantry": "show_pantry_dashboard",     # Home / Inventory
    "➕ Add Pantry Items": "show_pantry_manager",  # Addition symbol
    "🥘 My Recipes": "show_recipes",             # Frying pan / Food
    "✨ Instant Recipes":"show_smart_recipes",
    "📝 Add Recipe": "show_recipe_creator",      # Pencil / Writing
    "🛒 Shopping List": "show_shopping_list"      # Cart / Shopping
}

# --- 2. State Management Callback ---

def navigate_to(page_key):
    """Callback function to change the application state and force a rerun."""
    st.session_state['app_mode'] = page_key

def custom_sidebar_nav():
    """Renders the sidebar navigation using buttons and checks the current state."""
    
    # Initialize app_mode to the first option if it's not set
    if 'app_mode' not in st.session_state:
        st.session_state['app_mode'] = list(NAV_OPTIONS.keys())[0]

    st.sidebar.header("Navigation")

    for label, function_name in NAV_OPTIONS.items():
        is_active = st.session_state['app_mode'] == label
        
        # Use st.button with specific styling (type="primary" or default) and a callback
        st.sidebar.button(
            label,
            on_click=navigate_to,
            args=[label], # Pass the label to the callback function
            key=f"nav_btn_{label.replace(' ', '_')}",
            use_container_width=True,
            # Use type="primary" to apply the theme's accent color to the active button
            type="primary" if is_active else "secondary"
        )
    st.sidebar.markdown("---") # Visual separator

# --- CSS Injection for Margin Cleanup (Simplified) ---
def add_custom_css(is_dashboard_active):
    """Injects minimal CSS for top margin cleanup."""
    
    css = """
    <style>
    /* Global fixes for layout */
    .stApp > header {
        display: none; /* Hide Streamlit's default header (hamburger menu) */
    }
    
    /* FIX 1: Eliminate default padding/margin from the top of the entire app container */
    .css-1d3f8my, .block-container { 
        padding-top: 30px !important;
        margin-top: 0px !important;
    }

    /* FIX 2: Style for the centered login card background */
    .centered-card-bg {
        background-color: #1E1E1E; /* Dark background for card effect */
        border-radius: 10px;
        padding: 0px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        /* CRITICAL FIX: Aggressively remove top margin from internal Streamlit elements */
        margin-top: 0px !important;
    }
    
    /* Target the container wrapping the central columns to reduce its top margin */
    /* This targets the column that holds the centered content */
    [data-testid="stColumn"] > div {
        margin-top: -10px; /* Reduce margin on login/signup columns */
    }
    
    /* Ensure content padding is standard when no fixed banner is present */
    .block-container {
        padding-top: 2rem; 
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- 3. MAIN APPLICATION FLOW ---

def main():
    # Set wide layout for better dashboard visibility
    st.set_page_config(
        page_title="Pantry Chef App", 
        layout="wide"
    )
    
    # 3.1 AUTHENTICATION CHECK & STATE INITIALIZATION
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
    
    if 'access_mode' not in st.session_state:
        st.session_state['access_mode'] = 'Login'
        
    dashboard_active = st.session_state.get('app_mode') == "🏠 My Pantry" and st.session_state.logged_in

    # --- Inject custom CSS based on active page ---
    add_custom_css(dashboard_active)
    
    if st.session_state.logged_in:
        # --- LOGGED IN VIEW (SIDEBAR) ---
        
        # 1. Logo
        st.sidebar.image("https://i.pinimg.com/originals/cd/8f/1c/cd8f1c818f7412d7b4fa8e6dcaad35f3.jpg") 
        
        st.sidebar.success(f"Logged in as {st.session_state.user_name}")
        
        # 2. Navigation
        custom_sidebar_nav()
        
        # 3. DISPATCHER 
        current_page_label = st.session_state['app_mode']
        function_name = NAV_OPTIONS.get(current_page_label, 'show_pantry_dashboard')
        
        # Mapping the string name back to the actual callable function
        if function_name == "show_pantry_dashboard":
            show_pantry_dashboard(st.session_state.user_id, st.session_state.user_name)
        elif function_name == "show_pantry_manager":
            show_pantry_manager(st.session_state.user_id)
        elif function_name == "show_recipes":
            show_recipes(st.session_state.user_id)
        elif function_name == "show_smart_recipes":
            show_smart_recipes(st.session_state.user_id)
        elif function_name == "show_recipe_creator":
            show_recipe_creator(st.session_state.user_id)
        elif function_name == "show_shopping_list":
            show_shopping_list(st.session_state.user_id)
        # Note: All functions must be imported from pages.py

        if st.sidebar.button("Log Out"):
            # Clear session state and rerun the app
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun() 

    else:
        # --- LOGOUT VIEW (LOGIN/SIGNUP) ---
        st.markdown("---")
        # Image and Title Header (Full width, top-level elements)
        st.image("https://placehold.co/800x80/F5A623/ffffff?text=Pantry+Chef+-+Smart+Kitchen+Manager", use_container_width=True)
        
        # Change tags to <h4> and <p> and reduce margins for compactness
        st.markdown("<h4 style='text-align: center; color: #F5A623; margin-top: 5px; margin-bottom: 5px;'>The Smart Way to Cook</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #DDDDDD; margin-top: 0px; margin-bottom: 10px;'>Link your pantry to your recipes and stop wasting food.</p>", unsafe_allow_html=True)
        st.markdown("---")
        # --- START RELIABLE CENTERED LOGIN BOX ---
        
        # Create columns: Col 1 (Spacer), Col 2 (Content 500px wide), Col 3 (Spacer)
        # Ratio of 1:3:1 creates a nicely centered block on a wide layout
        col_left, col_center, col_right = st.columns([1, 3, 1])
        
        with col_center:
            # Apply the dark background styling to the centered column
            st.markdown("<div class='centered-card-bg'>", unsafe_allow_html=True)
            
            # --- LOGIN/SIGNUP BUTTONS ---
            col_login, col_signup = st.columns(2)
            
            with col_login:
                if st.button("Login", use_container_width=True, type="primary" if st.session_state['access_mode'] == 'Login' else "secondary"):
                    st.session_state['access_mode'] = 'Login'
                    st.rerun()
                    
            with col_signup:
                if st.button("Sign Up", use_container_width=True, type="primary" if st.session_state['access_mode'] == 'Sign Up' else "secondary"):
                    st.session_state['access_mode'] = 'Sign Up'
                    st.rerun()
                    
            # --- REMOVED: st.markdown("---") divider line ---
            
            # --- FORM RENDERING BASED ON ACCESS MODE ---
            if st.session_state['access_mode'] == "Login":
                st.markdown("### Login to Access Your Pantry")
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                
                if st.button("Log In"):
                    user_id, user_name = authenticate(email, password)
                    if user_id:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.user_name = user_name
                        st.rerun() 
                    else:
                        st.error("Invalid Email or Password")
                        
            elif st.session_state['access_mode'] == "Sign Up":
                st.markdown("### Create Your Account")
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                
                if st.button("Create Account"):
                    if new_name and new_email and new_password:
                        # signup function will handle its own rerun if successful
                        signup(new_name, new_email, new_password) 
                    else:
                        st.error("Please fill in all fields.")

            st.markdown("</div>", unsafe_allow_html=True)
            # --- END RELIABLE CENTERED LOGIN BOX ---

if __name__ == "__main__":
    main()
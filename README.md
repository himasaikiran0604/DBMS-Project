# 🍳 Recipe & Pantry Manager

A **Recipe & Pantry Manager** built using **Python, Streamlit, and MySQL** that helps users organize pantry items, manage recipes, generate shopping lists, and reduce food waste through expiry tracking.

---

# 📖 Overview

The application allows users to:

- Manage pantry inventory
- Track ingredient expiry dates
- Create and manage recipes
- Generate shopping lists automatically
- Maintain multiple pantry locations
- Authenticate securely with login/signup

---

# ✨ Features

## 🔐 Authentication

- User Registration
- User Login
- Session Management
- Logout

---

## 🏠 Pantry Management

- Add pantry ingredients
- Update ingredient quantities
- Consume ingredients
- Automatic quantity merging
- Delete empty pantry items
- Pantry locations
- Expiry date tracking
- Expiry alerts

---

## 🍳 Recipe Management

- Create recipes
- Add cooking instructions
- Add cuisine
- Add diet type
- Add preparation & cooking time
- Add servings
- Add recipe ingredients
- Prevent duplicate ingredients
- Delete recipes

---

## 🤖 Smart Recipes

- AI-assisted recipe recommendations
- Pantry-based recipe suggestions
- Smart ingredient matching

---

## 🛒 Shopping List

- Automatic shopping list generation
- Compare pantry stock with recipe ingredients
- Add only missing ingredients
- Mark items as purchased
- Complete shopping lists

---

## 📊 Dashboard

- Pantry overview
- Inventory status
- Expiry notifications
- Ingredient consumption

---

# 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend |
| Streamlit | Web Interface |
| MySQL | Database |
| Pandas | Data Processing |
| mysql-connector-python | Database Connectivity |
| Python Decimal | Accurate Quantity Calculations |

---

# 📁 Project Structure

```text
Recipe-Pantry-Manager/
│
├── views/
│   ├── dashboard.py
│   ├── pantry_manager.py
│   ├── recipe_creator.py
│   ├── recipes.py
│   ├── shopping_list.py
│   └── smart_recipes.py
│
├── app.py
├── auth.py
├── database.py
├── utils.py
├── .env
├── .gitignore
└── README.md
```

---

# 🗄 Database Tables

The project uses the following MySQL tables:

- users
- ingredients
- pantry_locations
- pantry_items
- recipes
- recipe_ingredients
- shopping_lists
- shopping_list_items
- diet_types

---

# ⚙ Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/recipe-pantry-manager.git
```

```bash
cd recipe-pantry-manager
```

---

## 2. Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install streamlit pandas mysql-connector-python python-dotenv
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=recipe_pantry_manager_app
```

---

## 5. Create Database

```sql
CREATE DATABASE recipe_pantry_manager_app;
```

Import your SQL file:

```bash
mysql -u root -p recipe_pantry_manager_app < database.sql
```

---

## 6. Run the Application

```bash
streamlit run app.py
```

---

# 🚀 Application Workflow

```
Login / Signup
       │
       ▼
Dashboard
       │
 ┌─────┼──────────┐
 ▼     ▼          ▼
Pantry Recipes Shopping
       │
       ▼
Generate Shopping List
       │
       ▼
Complete Shopping
```

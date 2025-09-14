import json
import os
import random
import sys
import logging

FOOD_DB = []
logger = logging.getLogger(__name__)

def load_food_database():
    """Loads the food database from the JSON file."""
    global FOOD_DB
    if not FOOD_DB:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'food_database.json')
        try:
            with open(db_path, 'r') as f:
                FOOD_DB = json.load(f)
        except FileNotFoundError:
            print(f"FATAL ERROR: The food database file was not found at {db_path}")
            print("Please ensure the file is named correctly and is in the main project directory.")
            sys.exit(1)


def generate_meal_plan(targets, preferences):
    """
    Generates a 7-day meal plan based on nutritional targets and user preferences.
    """
    load_food_database()
    
    diet_pref = preferences.get('dietary_preference', 'Non_Veg')
    
    filtered_foods = [food for food in FOOD_DB if diet_pref in food['diet']]
    
    if not filtered_foods:
        logger.warning(f"No food items for preference: {diet_pref}. Using entire database.")
        filtered_foods = FOOD_DB

    meal_structure = {
        'Breakfast': {'Protein': 1, 'Grain': 1},
        'Lunch': {'Protein': 1, 'Vegetable': 2, 'Grain': 1},
        'Dinner': {'Protein': 1, 'Vegetable': 2, 'Fat': 1}
    }
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    full_plan = {}

    for day in days:
        daily_meals = {}
        for meal_name, structure in meal_structure.items():
            meal_components = []
            for food_type, count in structure.items():
                options = [f for f in filtered_foods if f['type'] == food_type]
                if options:
                    # **FIX**: Append the full 'name' field which includes the quantity.
                    for _ in range(count):
                        chosen_food = random.choice(options)
                        meal_components.append(chosen_food['name'])
                else:
                    logger.warning(f"No options for type '{food_type}'. Skipping for {meal_name}.")

            if meal_components:
                daily_meals[meal_name] = ", ".join(meal_components)
            else:
                daily_meals[meal_name] = "No suitable items found for this meal."

        full_plan[day] = daily_meals
        
    return full_plan
import json
import os
import random
import sys

EXERCISE_DB = []

def load_exercise_database():
    """Loads the exercise database from the JSON file."""
    global EXERCISE_DB
    if not EXERCISE_DB:
        # Corrected filename to match your upload: 'exercise_databse.json'
        db_path = os.path.join(os.path.dirname(__file__), '..', 'exercise_database.json')
        try:
            with open(db_path, 'r') as f:
                EXERCISE_DB = json.load(f)
        except FileNotFoundError:
            print(f"FATAL ERROR: The exercise database file was not found at {db_path}")
            print("Please ensure the file is named correctly and is in the main project directory.")
            # Exiting because the module cannot function without its data
            sys.exit(1)


def generate_exercise_plan(condition_str, has_limitations):
    """
    Generates a 7-day exercise plan based on the predicted condition(s) and limitations.
    """
    load_exercise_database()
    
    # Define a standard weekly template
    weekly_template = {
        "Monday": "Cardio",
        "Tuesday": "Strength",
        "Wednesday": "Cardio",
        "Thursday": "Flexibility",
        "Friday": "Cardio",
        "Saturday": "Strength",
        "Sunday": "Rest"
    }
    
    # Split the predicted condition string into individual conditions
    conditions = condition_str.split('_and_')

    # Filter exercises based on limitations
    if has_limitations:
        # If user has limitations, only choose low-impact exercises
        suitable_exercises = [e for e in EXERCISE_DB if e['impact'] == 'Low']
    else:
        suitable_exercises = EXERCISE_DB

    # Further filter based on the primary health condition(s)
    final_exercise_pool = []
    for exercise in suitable_exercises:
        # An exercise is suitable if 'All' is in its suitability list
        if 'All' in exercise['suitability']:
            final_exercise_pool.append(exercise)
            continue
        # Or if ANY of the user's predicted conditions are in the suitability list
        if any(cond in exercise['suitability'] for cond in conditions):
            final_exercise_pool.append(exercise)
    
    # Ensure the pool is not empty; if it is, use all suitable exercises
    if not final_exercise_pool:
        final_exercise_pool = suitable_exercises

    full_plan = {}
    for day, exercise_type in weekly_template.items():
        if day == "Sunday":
            full_plan[day] = "Rest Day. Focus on recovery and light stretching if you feel up to it."
            continue

        # Find exercises matching the day's type from the filtered pool
        options = [e for e in final_exercise_pool if e['type'] == exercise_type]
        
        if options:
            # Pick a random exercise from the suitable options
            choice = random.choice(options)
            details = choice.get('duration') or choice.get('reps', 'Follow standard procedure.')
            full_plan[day] = f"{choice['name']} ({details})"
        else:
            # Fallback if no specific exercise is found (e.g., no flexibility exercises for a condition)
            # Find any low-intensity exercise as a safe default
            fallback_options = [e for e in final_exercise_pool if e['intensity'] == 'Low']
            if fallback_options:
                choice = random.choice(fallback_options)
                details = choice.get('duration') or choice.get('reps', 'Follow standard procedure.')
                full_plan[day] = f"{choice['name']} ({details})"
            else:
                 full_plan[day] = f"Light activity like gentle walking for 20-30 minutes."

    return full_plan
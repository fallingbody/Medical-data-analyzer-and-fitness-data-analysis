import pandas as pd
import json
import os
import sys
import logging
import sqlite3
import threading
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
import numpy as np
from .health_metrics import HealthMetrics
from . import meal_planner_module
from . import exercise_planner_module

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODEL_PIPELINE = None
MODEL_LOCK = threading.Lock()
IS_TRAINING_FLAG = False
TRAINING_COLUMNS = [] # Global variable to store column order
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_FILE = os.path.join(BASE_DIR, 'health_dataset.csv')
DB_FILE = os.path.join(BASE_DIR, 'users.db')

def train_model():
    """Trains the health prediction model using a robust data pipeline."""
    global MODEL_PIPELINE, IS_TRAINING_FLAG, TRAINING_COLUMNS
    
    with MODEL_LOCK:
        IS_TRAINING_FLAG = True
    
    try:
        logger.info("Starting model training with robust imputation and RandomForest...")
        df = pd.read_csv(DATASET_FILE)

        if 'Condition' not in df.columns or df.empty:
            logger.critical("'Condition' column not found or dataset is empty. Aborting training.")
            return

        df.dropna(subset=['Condition'], inplace=True)
        if len(df) < 10:
             logger.warning(f"Dataset has only {len(df)} rows. Model accuracy may be low.")

        X = df.drop('Condition', axis=1)
        y = df['Condition']
        
        # **FIX**: Store the column order from the training data
        TRAINING_COLUMNS = X.columns.tolist()

        numeric_features = X.select_dtypes(include=np.number).columns.tolist()
        categorical_features = X.select_dtypes(exclude=np.number).columns.tolist()
        
        logger.info(f"Identified {len(numeric_features)} numeric features and {len(categorical_features)} categorical features.")

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ], remainder='passthrough')

        with MODEL_LOCK:
            MODEL_PIPELINE = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
            MODEL_PIPELINE.fit(X, y)
            logger.info("AI Model trained successfully.")

    except FileNotFoundError:
        logger.critical(f"FATAL ERROR: health_dataset.csv not found at {DATASET_FILE}.")
    except Exception as e:
        logger.error(f"An error occurred during model training: {e}", exc_info=True)
    finally:
        with MODEL_LOCK:
            IS_TRAINING_FLAG = False


def get_recommendations(parameters, health_statuses, personal_profile):
    """Generate personalized recommendations using the robust pipeline."""
    with MODEL_LOCK:
        if MODEL_PIPELINE is None:
            logger.error("Model is not available for predictions.")
            return None, "Model_Unavailable"

    try:
        # **FIX**: Create the DataFrame and ensure it has all training columns in the correct order.
        input_df = pd.DataFrame([parameters])
        for col in TRAINING_COLUMNS:
            if col not in input_df.columns:
                input_df[col] = np.nan # Add missing columns as NaN, the imputer will handle them
        input_df = input_df[TRAINING_COLUMNS] # Enforce the correct column order

        predicted_condition = MODEL_PIPELINE.predict(input_df)[0]
        logger.info(f"AI Predicted condition: {predicted_condition}")

        metrics = HealthMetrics()
        weight = float(parameters.get('Weight_kg') or 70)
        height = float(parameters.get('Height_cm') or 170)
        age = int(parameters.get('Age') or 30)
        gender = parameters.get('Gender') or 'Male'
        
        activity_level = personal_profile.get('activity_level', 'Moderate').lower()
        daily_calories = metrics.calculate_daily_calories(weight, height, age, gender, activity_level)
        daily_protein = metrics.calculate_protein_requirement(weight, activity_level)
        carbs_grams = round(daily_calories * 0.5 / 4)
        fats_grams = round(daily_calories * 0.3 / 9)
        
        # **FIX**: Ensure personalized numerical values are formatted into the final output.
        nutritional_targets = {
            'daily_calories': f"{daily_calories} kcal",
            'daily_protein': f"{daily_protein} g",
            'carbs_grams': f"{carbs_grams} g",
            'fats_grams': f"{fats_grams} g"
        }
        
        diet_plan = meal_planner_module.generate_meal_plan(nutritional_targets, personal_profile)
        has_limitations = 'Yes' in personal_profile.get('limitations', 'No')
        exercise_plan = exercise_planner_module.generate_exercise_plan(predicted_condition, has_limitations)
        
        plans = {
            'diet_plan': diet_plan,
            'exercise_plan': exercise_plan,
            'nutritional_requirements': nutritional_targets,
            'health_analysis': metrics.compare_with_normal(parameters)
        }

        logger.info("Successfully generated personalized recommendations.")
        return plans, predicted_condition

    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}", exc_info=True)
        return None, "Analysis_Inconclusive"

def get_general_recommendations():
    """Provides a safe, general-purpose health plan as a fallback."""
    logger.info("Generating general fallback recommendations because personalized plan failed.")
    general_diet = {
        "Monday": {"Breakfast": "Oatmeal (1 cup) with fruits", "Lunch": "Mixed vegetable salad with Chickpeas (1 cup)", "Dinner": "Lentil soup (1 bowl) with a slice of whole wheat bread"},
        "Tuesday": {"Breakfast": "Scrambled eggs (2) or Tofu scramble (150g)", "Lunch": "Leftover lentil soup", "Dinner": "Grilled chicken (100g) or Paneer (100g) with quinoa and steamed vegetables"},
        "Wednesday": {"Breakfast": "Greek yogurt (1 cup) with berries and a sprinkle of nuts", "Lunch": "Chicken or Chickpea salad wrap (1)", "Dinner": "Baked fish (100g) or a Black bean burger with a side salad"},
        "Thursday": {"Breakfast": "Oatmeal (1 cup) with fruits", "Lunch": "Leftover fish or bean burger", "Dinner": "Vegetable stir-fry with brown rice (1 cup)"},
        "Friday": {"Breakfast": "Smoothie with spinach, banana, and protein powder", "Lunch": "Quinoa salad with mixed greens", "Dinner": "Whole wheat pasta with a tomato-based vegetable sauce"},
        "Saturday": {"Breakfast": "Whole wheat toast (2 slices) with avocado and a boiled egg", "Lunch": "A large colorful salad with a variety of vegetables and seeds", "Dinner": "Healthy homemade pizza on a whole wheat base (2 slices)"},
        "Sunday": {"Breakfast": "Whole wheat pancakes with fresh fruit", "Lunch": "Leftovers from the week", "Dinner": "Roast chicken or a hearty Vegetable and bean roast"}
    }
    general_exercise = {
        "Monday": "30 minutes of brisk walking in a park or on a treadmill.",
        "Tuesday": "20 minutes of bodyweight exercises: 2 sets of 10 squats, 10 push-ups (on knees if needed), and a 30-second plank.",
        "Wednesday": "30 minutes of an enjoyable cardio activity like cycling or swimming.",
        "Thursday": "Active Rest Day: 15-20 minutes of gentle stretching, focusing on major muscle groups.",
        "Friday": "30 minutes of brisk walking, perhaps trying to include some small hills.",
        "Saturday": "20 minutes of bodyweight exercises: 2 sets of 12 lunges (each leg), 10 glute bridges, and 15 crunches.",
        "Sunday": "Active Recovery: A long, leisurely walk to relax and recover."
    }
    plans = {
        'diet_plan': general_diet,
        'exercise_plan': general_exercise,
        'nutritional_requirements': {
            'daily_calories': "Approx. 1800-2200 kcal",
            'daily_protein': "Approx. 70-90 g",
            'carbs_grams': "Focus on complex carbs",
            'fats_grams': "Focus on healthy fats"
        },
        'health_analysis': {}
    }
    return plans

def is_model_training():
    """Checks if the model training process is active."""
    global IS_TRAINING_FLAG
    return IS_TRAINING_FLAG

def fetch_verified_reports_for_retraining():
    """Fetches verified reports from the database for retraining."""
    logger.info("Fetching verified reports from the database for retraining...")
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        query = "SELECT parameters, feedback_condition FROM reports WHERE is_verified = 1 AND feedback_condition IS NOT NULL"
        reports = conn.execute(query).fetchall()
        conn.close()
        logger.info(f"Found {len(reports)} verified reports to add to the dataset.")
        return reports
    except Exception as e:
        logger.error(f"Failed to fetch reports from DB: {e}")
        return []

def append_to_dataset(reports):
    """Appends new data to the health_dataset.csv file."""
    if not reports:
        logger.info("No new reports to append.")
        return False
    
    new_data = []
    for report in reports:
        try:
            params = json.loads(report['parameters'])
            params['Condition'] = report['feedback_condition']
            new_data.append(params)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping a report due to error: {e}")
            continue
    
    if not new_data:
        logger.warning("No valid data to append after processing.")
        return False

    try:
        df_new = pd.DataFrame(new_data)
        df_new.to_csv(DATASET_FILE, mode='a', header=not os.path.exists(DATASET_FILE), index=False)
        logger.info(f"Successfully appended {len(df_new)} new records to {DATASET_FILE}.")
        return True
    except Exception as e:
        logger.error(f"Failed to write to dataset CSV: {e}")
        return False

def retrain_and_load_model():
    """The complete pipeline for fetching data, updating dataset, and retraining."""
    logger.info("--- Starting automatic retraining pipeline ---")
    verified_reports = fetch_verified_reports_for_retraining()
    if append_to_dataset(verified_reports):
        train_model()
        logger.info("--- Automatic retraining pipeline finished ---")
    else:
        logger.info("--- Retraining not needed: No new data found ---")


# --- Initial model training on application start ---
train_model()
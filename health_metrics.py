import pandas as pd

class HealthMetrics:
    # Normal ranges for various health parameters
    NORMAL_RANGES = {
        'Systolic_BP': (90, 120),
        'Diastolic_BP': (60, 80),
        'Sugar': (70, 100),
        'Cholesterol': (125, 200),
        'Hb': {'Male': (13.5, 17.5), 'Female': (12.0, 15.5)},
        'BMI': (18.5, 24.9),
        'Urea': (7, 20),
        'Creatinine': (0.7, 1.3)
    }

    @staticmethod
    def calculate_bmi(weight_kg, height_cm):
        """Calculate BMI from weight and height."""
        if not all(isinstance(i, (int, float)) for i in [weight_kg, height_cm]) or height_cm == 0:
            return 0
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)

    @staticmethod
    def calculate_daily_calories(weight_kg, height_cm, age, gender, activity_level):
        """Calculate daily calorie requirements using Harris-Benedict equation."""
        if not all(isinstance(i, (int, float)) for i in [weight_kg, height_cm, age]) or not gender or gender == 'N/A':
             return 2000 # Return a safe default if data is missing

        # Basic Metabolic Rate (BMR)
        if gender.lower() == 'male':
            bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

        # Activity multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'moderate': 1.55,
            'active': 1.725
        }
        
        return round(bmr * activity_multipliers.get(activity_level.lower(), 1.55))

    @staticmethod
    def calculate_protein_requirement(weight_kg, activity_level):
        """Calculate daily protein requirement in grams."""
        if not isinstance(weight_kg, (int, float)) or not activity_level:
            return 75 # Return a safe default

        # Base requirement: 0.8g per kg for sedentary, more for active
        multipliers = {
            'sedentary': 0.8,
            'moderate': 1.2,
            'active': 1.6
        }
        return round(weight_kg * multipliers.get(activity_level.lower(), 1.2))

    @staticmethod
    def compare_with_normal(parameters):
        """Compare parameters with normal ranges and return analysis."""
        analysis = {}
        
        for param, value in parameters.items():
            # **FIX**: Ensure the value is a valid number before attempting comparison.
            if param in HealthMetrics.NORMAL_RANGES and isinstance(value, (int, float)):
                normal_range_data = HealthMetrics.NORMAL_RANGES[param]
                
                actual_range = None
                # **FIX**: Correctly handle gender-specific ranges like Hb.
                if isinstance(normal_range_data, dict):
                    gender = parameters.get('Gender')
                    if gender and gender != 'N/A':
                        actual_range = normal_range_data.get(gender.title())
                else:
                    actual_range = normal_range_data

                if not actual_range:
                    continue

                if isinstance(actual_range, tuple):
                    status = 'Normal'
                    difference = 0
                    if value < actual_range[0]:
                        status = 'Low'
                        difference = value - actual_range[0]
                    elif value > actual_range[1]:
                        status = 'High'
                        difference = value - actual_range[1]
                    
                    analysis[param] = {
                        'value': value,
                        'normal_range': actual_range,
                        'status': status,
                        'difference': difference
                    }
        return analysis
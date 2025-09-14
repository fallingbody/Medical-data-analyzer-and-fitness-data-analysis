import re
from .health_metrics import HealthMetrics

def find_first_match(text, patterns, cast_type=float):
    """
    Searches for the first matching pattern in the text and returns the extracted value.
    """
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                value_str = match.group(1)
                # Remove any non-numeric characters except for the decimal point
                cleaned_str = re.sub(r'[^\d.]', '', value_str)
                if cleaned_str:
                    return cast_type(cleaned_str)
            except (ValueError, IndexError):
                continue
    return None


def extract_medical_parameters(text):
    """
    Extracts a comprehensive set of medical parameters using flexible regex patterns
    that can handle various phrasings found in medical reports. It now gracefully
    handles missing values by assigning None.
    """
    params = {}

    # --- Vital Signs (Improved Regex) ---
    bp_match = re.search(r'(?:Blood\s*Pressure|BP)\s*[:\s-]*\s*(?:is|reading\s*is)?\s*(\d{2,3}\s*[/]\s*\d{2,3})', text, re.IGNORECASE)
    if bp_match:
        try:
            bp_values = bp_match.group(1).replace(' ', '').split('/')
            params['Systolic_BP'] = int(bp_values[0])
            params['Diastolic_BP'] = int(bp_values[1])
        except (IndexError, ValueError):
            params['Systolic_BP'] = None
            params['Diastolic_BP'] = None
    else:
        params['Systolic_BP'] = None
        params['Diastolic_BP'] = None

    # --- Personal Info ---
    params['Age'] = find_first_match(text, [r'Age\s*[:\s-]*\s*(\d{1,3})', r'\((\d+)\s*years\)', r'(\d{1,3})\s*years\s*old'], cast_type=int)
    gender_match = re.search(r'(?:Gender|Sex)\s*[:\s-]*\s*(Male|Female|[MF])(?!\w)', text, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).upper()
        params['Gender'] = 'Male' if gender in ['M', 'MALE'] else 'Female'
    else:
        # Fallback to searching for the words "male" or "female" in the text
        if re.search(r'\bmale\b', text, re.IGNORECASE):
            params['Gender'] = 'Male'
        elif re.search(r'\bfemale\b', text, re.IGNORECASE):
            params['Gender'] = 'Female'
        else:
            params['Gender'] = None
    
    # --- Biometrics ---
    params['Weight_kg'] = find_first_match(text, [r'Weight\s*(?:is|:)?(?: \s*recorded\s*as)?\s*(\d+\.?\d*)\s*kg'])
    params['Height_cm'] = find_first_match(text, [r'Height\s*[:\s-]*\s*(\d+\.?\d*)\s*cm'])

    # --- Hematology ---
    params['Hb'] = find_first_match(text, [r'Hemoglobin\s*[:\s-]*\s*([\d.]+)'])
    params['Hematocrit'] = find_first_match(text, [r'Hematocrit\s*[:\s-]*\s*([\d.]+)'])

    # --- Biochemistry ---
    params['Sugar'] = find_first_match(text, [r'(?:Fasting\s*Glucose|Sugar)\s*(?:level)?[-:\s]*\s*([\d.]+)'])
    params['Cholesterol'] = find_first_match(text, [r'(?:Total\s*)?Cholesterol\s*[:\s-]*\s*([\d.]+)'])
    params['Urea'] = find_first_match(text, [r'Urea\s*[:\s-]*\s*([\d.]+)'])
    params['Creatinine'] = find_first_match(text, [r'(?:Serum\s*)?Creatinine\s*[:\s-]*\s*([\d.]+)'])

    # --- Lifestyle Info ---
    params['Cigarettes_Per_Day'] = find_first_match(text, [r'(\d+)\s*cigarettes\s*per\s*day'], cast_type=int)
    
    # --- Calculated Metrics ---
    if params.get('Weight_kg') and params.get('Height_cm'):
        params['BMI'] = HealthMetrics.calculate_bmi(params['Weight_kg'], params['Height_cm'])
    else:
        params['BMI'] = None

    return params
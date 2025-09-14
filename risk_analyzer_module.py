def analyze_risks(parameters):
    """
    Analyzes extracted medical parameters to identify potential future health risks
    based on a set of predefined rules. This is a rule-based expert system.
    """
    risks = []
    
    # Ensure parameters are not None to avoid errors
    age = parameters.get('Age')
    bmi = parameters.get('BMI')
    systolic_bp = parameters.get('Systolic_BP')
    diastolic_bp = parameters.get('Diastolic_BP')
    cholesterol = parameters.get('Cholesterol')
    sugar = parameters.get('Sugar')
    cigarettes = parameters.get('Cigarettes_Per_Day')
    hb = parameters.get('Hb')
    urea = parameters.get('Urea')
    creatinine = parameters.get('Creatinine')
    gender = parameters.get('Gender')

    # 1. Cardiovascular Disease Risk
    if (systolic_bp and systolic_bp > 140) or (diastolic_bp and diastolic_bp > 90):
        if (cholesterol and cholesterol > 240) or (bmi and bmi > 30):
            risks.append({
                "name": "High Cardiovascular Risk",
                "reason": "High blood pressure combined with high cholesterol or obesity significantly increases the risk of heart attack and stroke."
            })

    # 2. Type 2 Diabetes Mellitus Risk
    if sugar and sugar > 125:
         if bmi and bmi > 25:
            risks.append({
                "name": "High Diabetes Risk",
                "reason": "Elevated blood sugar (pre-diabetic or diabetic range) combined with being overweight is a primary indicator for Type 2 Diabetes."
            })

    # 3. Chronic Kidney Disease (CKD) Progression Risk
    if (urea and urea > 50) or (creatinine and creatinine > 1.2):
        if (systolic_bp and systolic_bp > 130) or (sugar and sugar > 150):
             risks.append({
                "name": "Chronic Kidney Disease Progression",
                "reason": "Elevated urea or creatinine suggests existing kidney strain. Co-existing high blood pressure or high sugar can accelerate kidney damage."
            })

    # 4. Metabolic Syndrome Risk
    conditions_met = 0
    if (systolic_bp and systolic_bp > 130) or (diastolic_bp and diastolic_bp > 85): conditions_met += 1
    if sugar and sugar > 100: conditions_met += 1
    if cholesterol and cholesterol > 200: conditions_met += 1 # Simplified for general cholesterol
    if bmi and bmi > 30: conditions_met += 1
    if conditions_met >= 3:
        risks.append({
            "name": "Metabolic Syndrome",
            "reason": "Presence of three or more risk factors (high BP, high blood sugar, high cholesterol, obesity) indicates Metabolic Syndrome, a precursor to many serious health issues."
        })

    # 5. Lung Disease / COPD Risk
    if cigarettes and cigarettes > 10:
        if age and age > 45:
            risks.append({
                "name": "High Lung Disease Risk (COPD/Cancer)",
                "reason": "Long-term smoking, especially over the age of 45, is the leading cause of Chronic Obstructive Pulmonary Disease (COPD) and lung cancer."
            })

    # 6. Anemia Complication Risk
    if hb and hb < 11.0:
        if (urea and urea > 60) or (age and age > 65):
             risks.append({
                "name": "Anemia Complication Risk",
                "reason": "Anemia in older adults or those with kidney issues can lead to significant fatigue, cardiac stress, and worsened overall health."
            })

    # 7. Liver Disease (Fatty Liver) Risk
    if bmi and bmi > 30:
        if (cholesterol and cholesterol > 200) or (sugar and sugar > 110):
            risks.append({
                "name": "Non-Alcoholic Fatty Liver Disease (NAFLD) Risk",
                "reason": "Obesity, combined with high cholesterol or blood sugar, is a major risk factor for fat accumulation in the liver, which can lead to serious liver damage."
            })

    # 8. Osteoporosis Risk
    if gender and gender == 'Female' and age and age > 60:
         risks.append({
            "name": "Osteoporosis Risk",
            "reason": "Post-menopausal women over 60 are at a significantly higher risk for bone density loss, leading to fractures."
        })

    # 9. Gout / Hyperuricemia Risk
    if urea and urea > 50: # High urea can be linked to high uric acid
        if bmi and bmi > 28:
            risks.append({
                "name": "Gout Risk",
                "reason": "High urea levels can be associated with hyperuricemia, and obesity is a strong risk factor for developing painful gout."
            })

    # 10. Peripheral Artery Disease (PAD) Risk
    if cigarettes and cigarettes > 5:
        if (sugar and sugar > 125) or (cholesterol and cholesterol > 220):
             risks.append({
                "name": "Peripheral Artery Disease Risk",
                "reason": "Smoking combined with diabetes or high cholesterol dramatically increases the risk of plaque buildup in the arteries of the legs and feet."
            })
            
    # 11. Stroke Risk
    if (systolic_bp and systolic_bp > 160) or (diastolic_bp and diastolic_bp > 100):
        if (age and age > 55) or (cigarettes and cigarettes > 0):
            risks.append({
                "name": "Elevated Stroke Risk",
                "reason": "Significantly high blood pressure (Stage 2 Hypertension), especially when combined with age or smoking, is a critical risk factor for stroke."
            })
            
    # 12. Dehydration and Acute Kidney Injury Risk
    if (urea and urea > 60) and (creatinine and creatinine > 1.4):
        fluid = parameters.get('Fluid_Intake_ml')
        if fluid and fluid < 1000:
            risks.append({
                "name": "Dehydration / Acute Kidney Injury Risk",
                "reason": "High kidney markers (Urea, Creatinine) coupled with very low fluid intake can precipitate acute kidney injury. Proper hydration is critical."
            })
            
    # 13. Iron-Deficiency Anemia Specific Risk
    if hb and hb < 12.0:
        diet = parameters.get('Dietary_Preference')
        if diet and 'Veg' in diet:
            risks.append({
                "name": "Iron-Deficiency Anemia Concern",
                "reason": "Low hemoglobin in individuals on a vegetarian diet requires careful planning to ensure adequate intake of iron-rich plant-based foods and Vitamin C for absorption."
            })
            
    # 14. High-Risk Pregnancy Consultation Recommended
    if parameters.get('is_pregnant'): # Assuming a flag could be set
        if (sugar and sugar > 100) or (systolic_bp and systolic_bp > 130) or (bmi and bmi > 30):
            risks.append({
                "name": "High-Risk Pregnancy Factors",
                "reason": "Pre-existing high blood sugar, high blood pressure, or obesity can lead to complications like gestational diabetes or preeclampsia. Close monitoring with a doctor is essential."
            })
            
    # 15. Gallstone Formation Risk
    if (cholesterol and cholesterol > 240) and (bmi and bmi > 30):
        if gender and gender == 'Female':
            risks.append({
                "name": "Gallstone Formation Risk",
                "reason": "High cholesterol, obesity, and female gender are all significant risk factors for the formation of cholesterol-based gallstones."
            })

    # 16. Sleep Apnea Risk
    if (bmi and bmi > 35) and (systolic_bp and systolic_bp > 130):
        risks.append({
                "name": "Sleep Apnea Risk",
                "reason": "Significant obesity combined with hypertension strongly suggests a risk for obstructive sleep apnea, which can impact heart health. A sleep study may be warranted."
            })
            
    # 17. Macular Degeneration Risk
    if (age and age > 60) and (cigarettes and cigarettes > 0):
        risks.append({
                "name": "Age-Related Macular Degeneration (AMD) Risk",
                "reason": "Age is the primary risk factor for AMD, a leading cause of vision loss. Smoking significantly accelerates this risk."
            })
            
    # 18. Cognitive Decline / Dementia Risk
    if (age and age > 65) and (systolic_bp and systolic_bp > 140) and (sugar and sugar > 125):
        risks.append({
                "name": "Cognitive Decline / Vascular Dementia Risk",
                "reason": "Chronic high blood pressure and high blood sugar in older adults can damage blood vessels in the brain, increasing the long-term risk of cognitive decline."
            })
            
    # 19. Pancreatitis Risk
    alcohol = parameters.get('Alcohol_Consumption')
    if alcohol and alcohol.lower() == 'high':
         if (cholesterol and cholesterol > 250): # Triglycerides are better, but cholesterol is a proxy
            risks.append({
                "name": "Pancreatitis Risk",
                "reason": "High alcohol consumption is a primary cause of acute pancreatitis. This risk is exacerbated by very high levels of lipids (fats) in the blood."
            })
            
    # 20. General Frailty and Fall Risk
    if (age and age > 75) and (hb and hb < 12.0) and (bmi and bmi < 20):
        risks.append({
                "name": "Frailty and Fall Risk",
                "reason": "A combination of advanced age, anemia (leading to weakness), and being underweight suggests a higher risk of frailty, which can lead to dangerous falls."
            })

    if not risks:
        risks.append({
            "name": "General Health Advisory",
            "reason": "No specific high-risk conditions were identified based on the provided data. However, maintaining a healthy lifestyle, including a balanced diet, regular exercise, and routine check-ups, is crucial for long-term well-being. Please consult a healthcare professional for a comprehensive evaluation."
        })
    return risks
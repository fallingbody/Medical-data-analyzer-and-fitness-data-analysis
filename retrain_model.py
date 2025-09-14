import pandas as pd
import sqlite3
import json
import os
from modules.fitness_module import train_model

DB_FILE = os.path.join(os.path.dirname(__file__), 'users.db')
DATASET_FILE = os.path.join(os.path.dirname(__file__), 'health_dataset.csv')

def fetch_verified_reports():
    """Fetches reports from the DB that have been verified for retraining."""
    print("Fetching verified reports from the database...")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # In a real system, you'd have an admin interface to set is_verified=1
    # For now, we assume feedback_condition is the correct label
    query = "SELECT parameters, feedback_condition FROM reports WHERE is_verified = 1 AND feedback_condition IS NOT NULL"
    reports = conn.execute(query).fetchall()
    conn.close()
    print(f"Found {len(reports)} verified reports to add to the dataset.")
    return reports

def append_to_dataset(reports):
    """Appends new data to the health_dataset.csv file."""
    if not reports:
        print("No new reports to append. Exiting.")
        return False

    new_data = []
    for report in reports:
        try:
            params = json.loads(report['parameters'])
            params['Condition'] = report['feedback_condition']
            new_data.append(params)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Skipping a report due to error: {e}")
            continue
            
    if not new_data:
        print("No valid data to append after processing. Exiting.")
        return False

    df_new = pd.DataFrame(new_data)
    
    # Append to CSV without writing the header if the file already exists
    df_new.to_csv(DATASET_FILE, mode='a', header=not os.path.exists(DATASET_FILE), index=False)
    print(f"Successfully appended {len(df_new)} new records to {DATASET_FILE}.")
    return True

def main():
    """Main function to run the retraining pipeline."""
    verified_reports = fetch_verified_reports()
    
    if append_to_dataset(verified_reports):
        print("\nDataset updated. Now retraining the model...")
        # This will reload the updated dataset and retrain the pipeline
        train_model()
        print("Model retraining complete!")
    else:
        print("Model retraining not needed as there was no new data.")

if __name__ == '__main__':
    main()
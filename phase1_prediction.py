# scripts/phase1_prediction.py

# 1. Import necessary libraries
import pandas as pd
import os

# 2. Define file paths
input_file_path = os.path.join('data', 'Chicago_Crimes_2012_to_2017.csv')
output_file_path = os.path.join('data', 'community_predictions.csv')

# 3. A function to load the data
def load_data(path):
    print(f"Loading data from: {path}")
    try:
        # We only need two columns for this task, so we'll load just those.
        df = pd.read_csv(path, on_bad_lines='skip', usecols=['Primary Type', 'Community Area'])
        print("Data loaded successfully!")
        return df
    except FileNotFoundError:
        print(f"Error: The file was not found at {path}")
        return None

# 4. A function to process data and create predictions
def process_and_save_predictions(df, output_path):
    print("\nStarting data processing...")
    
    # Drop rows where 'Community Area' is empty
    df.dropna(subset=['Community Area'], inplace=True)
    
    # Convert community area to integer
    df['Community Area'] = df['Community Area'].astype(int)
    
    # For this phase, our "prediction" will be a simple count of total crimes
    # This gives us a basic risk score for each area.
    # We group by 'Community Area' and count the number of crimes in each.
    community_risk = df.groupby('Community Area').size().reset_index(name='CrimeCount')
    
    # Save the results to a new CSV file
    community_risk.to_csv(output_path, index=False)
    
    print(f"Processing complete!")
    print(f"Risk data has been saved to: {output_path}")
    
    return community_risk

# 5. Main part of our script
if __name__ == "__main__":
    crime_df = load_data(input_file_path)

    if crime_df is not None:
        predictions = process_and_save_predictions(crime_df, output_file_path)
        
        print("\nHere's a sample of the saved risk data:")
        print(predictions.head())
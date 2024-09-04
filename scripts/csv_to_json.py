import pandas as pd
import os
import json
import random

# Path to input csv and output json files
input_csv_dir = 'output/csv'
output_json_dir = 'output/json'

# Function to convert CSV to JSON with selected fields and additional fields
def convert_csv_to_json(csv_file_path, limit=None, fields=None):
    df = pd.read_csv(csv_file_path)
    df = df.fillna("")  # Replace NaN values with empty string
    
    # Rename columns to all lower case
    df.columns = [col.lower() for col in df.columns]
    
    # Select only the specified fields (excluding the new fields to be added)
    if fields:
        df = df[[field for field in fields if field in df.columns]]
    
    # Convert DataFrame to list of dictionaries
    json_data = df.to_dict(orient='records')
    
    # Apply limit if provided
    if limit is not None:
        json_data = json_data[:limit]
    
    return json_data

# Path to the specific CSV file
patients_csv_file = 'patients.csv'
file_path = os.path.join(input_csv_dir, patients_csv_file)

# Specify the fields to include, including new fields
fields = [
    '_id', 'birthdate', 'ssn', 'prefix', 'firstName', 'lastName', 'gender',
    'address', 'city', 'state', 'county', 'zip'
]

# Convert CSV to JSON with a limit of 50 objects and specified fields
json_data = convert_csv_to_json(file_path, limit=50, fields=fields)

# List of diseases and allergies for random data generation
diseases = [
    'Hypertension', 'Diabetes', 'Asthma', 'Cancer', 'Heart Disease', 'Chronic Obstructive Pulmonary Disease (COPD)',
    'Arthritis', 'Stroke', 'Kidney Disease', 'Alzheimer\'s Disease', 'Obesity', 'Liver Disease'
]

allergies = [
    'Penicillin', 'Peanuts', 'Shellfish', 'Pollen', 'Dust Mites', 'Insect Stings', 'Latex', 'Mold', 'Pet Dander',
    'Food Additives', 'Eggs', 'Milk', 'Soy', 'Wheat'
]

# Add dummy data that was not available in dataset, but need for database
def add_dummy_data(records, diseases, allergies):
    for record in records:
        record['diseases'] = random.sample(diseases, 2)  # Select 2 random diseases
        record['allergies'] = random.sample(allergies, 2)  # Select 2 random allergies
        # Generate email using the first name
        first_name = record['first'].lower()
        record['email'] = f"{first_name}@example.com"
        record['digitalConsent'] = True  # Assuming consent is given

    return records

# Add dummy data to specific fields
json_data = add_dummy_data(json_data, diseases, allergies)

# Save JSON file
json_file_path = os.path.join(output_json_dir, 'patients.json')
with open(json_file_path, 'w') as json_file:
    json.dump(json_data, json_file, indent=4)

print(f"Converted and saved {json_file_path} with {len(json_data)} records.")
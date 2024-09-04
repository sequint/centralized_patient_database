#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 13:19:01 2024

@author: stevenquintana
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps

# Create the Flask server app
app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['health-records']
patients_collection = db['patients']
doctors_collection = db['doctors']

# Home route to HTML file
@app.route('/')
def home():
    return render_template('index.html')

# Doctor login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    doctor = doctors_collection.find_one({'email': email, 'password': password})
    
    if doctor:
        return jsonify({'success': True, 'message': 'Login successful', 'user': dumps(doctor)}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid login credentials'}), 404

# Create a doctor
@app.route('/doctors', methods=['POST'])
def create_doctor():
    new_doctor = request.json

    try:
        result = doctors_collection.insert_one(new_doctor)
        new_doctor_id = str(result.inserted_id)
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to create doctor', 'error': str(e)}), 500
    
    return jsonify({'success': True, 'message': 'Doctor record created', 'patient_id': new_doctor_id}), 201

# Create a patient
@app.route('/patients/<doctor_id>', methods=['POST'])
def create_patient(doctor_id):
    # Extract patient data from the request
    new_patient = request.json
    
    # Insert new patient into the patients collection
    try:
        result = patients_collection.insert_one(new_patient)
        new_patient_id = str(result.inserted_id)  # Get the MongoDB generated ID
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to create patient', 'error': str(e)}), 500
    
    # Update the doctor's patient list
    try:
        update_result = doctors_collection.update_one(
            {'_id': ObjectId(doctor_id)},
            {'$push': {'patients': new_patient_id}}  # Use $push to add the patient ID to the array
        )
        
        if update_result.matched_count == 0:
            return jsonify({'success': False, 'message': 'Doctor not found'}), 404
        if update_result.modified_count == 0:
            return jsonify({'success': False, 'message': 'Doctor record was not updated'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to update doctor record', 'error': str(e)}), 500
    
    # Return success response
    return jsonify({'success': True, 'message': 'Patient record created', 'patient_id': new_patient_id}), 201

# Convert a MongoDB document to a JSON serializable format
def convert_to_json_serializable(document):
    if isinstance(document, list):
        return [convert_to_json_serializable(item) for item in document]
    elif isinstance(document, dict):
        return {k: convert_to_json_serializable(v) for k, v in document.items()}
    elif isinstance(document, ObjectId):
        return str(document)
    else:
        return document

# Get all patients for a doctor
@app.route('/patients/<doctor_id>', methods=['GET'])
def get_patients(doctor_id):
    doctor = doctors_collection.find_one({'_id': ObjectId(doctor_id)})

    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    patientIds = doctor.get('patients', [])
    
    if not patientIds:
        return jsonify({'error': 'No patients associated with this doctor'}), 404

    patient_object_ids = [ObjectId(pid) for pid in patientIds]
    query = {'_id': {'$in': patient_object_ids}}

    patients = list(patients_collection.find(query))

    # Convert each patient document to a JSON serializable format
    patients_serializable = convert_to_json_serializable(patients)

    return jsonify(patients_serializable), 200

# Get one patient
@app.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = patients_collection.find_one({'_id': ObjectId(patient_id)})
    if patient:
        return jsonify(patient), 200
    else:
        return jsonify({'error': 'Patient record not found'}), 404

# Update one patient record
@app.route('/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    updated_patient = request.json
    result = patients_collection.update_one(
        {'_id': ObjectId(patient_id)},
        {'$set': updated_patient}
    )
    if result.matched_count:
        return jsonify({'message': 'Patient record updated'}), 200
    else:
        return jsonify({'message': 'Patient record not found'}), 404

# Delete one patient record
@app.route('/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    # Convert patient_id to ObjectId
    patient_obj_id = ObjectId(patient_id)
    
    # Find the patient document
    patient = patients_collection.find_one({'_id': patient_obj_id})
    
    if not patient:
        return jsonify({'message': 'Patient record not found'}), 404
    
    # Delete the patient record
    result = patients_collection.delete_one({'_id': patient_obj_id})
    
    if result.deleted_count:
        # Remove the patient ID from the doctor's patient list
        doctors_collection.update_one(
            {'patients': patient_id},
            {'$pull': {'patients': patient_id}}
        )
        return jsonify({'message': 'Patient record deleted and removed from doctor\'s list'}), 200
    else:
        return jsonify({'message': 'Patient record not found'}), 404


# Delete all patient records
@app.route('/patients', methods=['DELETE'])
def delete_patients():
    data = request.json
    patient_ids = data.get('patient_ids', [])
    
    if not patient_ids:
        return jsonify({'message': 'No patient IDs provided'}), 400

    # Convert patient IDs to ObjectId
    patient_object_ids = [ObjectId(pid) for pid in patient_ids]
    
    # Delete multiple patient records
    result = patients_collection.delete_many({'_id': {'$in': patient_object_ids}})
    print('Result', result, flush=True)
    print('Result length:', result.deleted_count, flush=True)
    
    if result.deleted_count > 0:
        # Remove the deleted patient IDs from all doctors' patient lists
        doctors_collection.update_many(
            {'patients': {'$in': patient_ids}},
            {'$pullAll': {'patients': patient_ids}}
        )
        return jsonify({'message': 'Patient records deleted and removed from doctors\' list'}), 200
    else:
        return jsonify({'message': 'No patient records found to delete'}), 404


if __name__ == '__main__':
    app.run(debug=True)
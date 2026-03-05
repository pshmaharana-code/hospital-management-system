import requests
import json

# 1. Login as DOCTOR
login_url = 'http://127.0.0.1:5000/api/login'
login_data = {
    "username": "bkmaharana", # <--- UPDATE THIS
    "password": "1234"  # <--- UPDATE THIS
}

response = requests.post(login_url, json=login_data)
print("--- DOCTOR LOGIN ---")
print("Status:", response.status_code)

# Only proceed if login was successful
if response.status_code == 200:
    token = response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Doctor Dashboard
    doctor_url = 'http://127.0.0.1:5000/api/doctor/dashboard'
    doctor_response = requests.get(doctor_url, headers=headers)
    
    print("\n--- DOCTOR DASHBOARD DATA ---")
    print("Status:", doctor_response.status_code)
    
    # Pretty-print the JSON output so it's readable
    if doctor_response.status_code == 200:
        parsed_json = doctor_response.json()
        print(json.dumps(parsed_json, indent=4))
    else:
        print("Error Data:", doctor_response.json())
        
else:
    print("Login failed! Check your credentials.")
    print("Data:", response.json())
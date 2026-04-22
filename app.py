import os
import secrets
from werkzeug.utils import secure_filename
from extension import db
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy import func
from flask_bcrypt import Bcrypt
from datetime import datetime, date, time, timedelta
import io
from flask import send_file
import matplotlib
import matplotlib.pyplot as plt
# This is a crucial line for running Matplotlib in a web server
matplotlib.use('Agg')
from werkzeug.security import generate_password_hash


from dotenv import load_dotenv
import razorpay

# Load the environment variables from the .env file
load_dotenv()

# Securely fetch the keys
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Initialize the client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))



#initialize the flask application
app = Flask(__name__)

#---Media upload configuration---
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jepg', 'webp'}

#create folder if it doesnot exits
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file, prefix):
    # """
    # Takes an uploaded file and a prefix (e.g., 'patient_1' or 'doctor_5').
    # Saves the file safely and returns the database-ready URL string.
    # """
    if file and allowed_file(file.filename):
        from werkzeug.utils import secure_filename
        import os

        filename = secure_filename(file.filename)
        unique_filename = f"{prefix}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        file.save(filepath)
        return f"/static/uploads/{unique_filename}"
    return None

def generate_secure_otp():
    """Generates a cryptographically secure 6-digit OTP."""
    #create a string of 6 random digit(0-9)
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))

def simulate_email_delivery(username, otp):
    """
    Simulates sending an email by printing it clearly in the terminal.
    In production, this is where you'd put your smtplib/SendGrid logic.
    """
    print(f"\n{'='*50}")
    print(f"📧 MOCK EMAIL INTERCEPTED (DEV MODE)")
    print(f"To: {username}")
    print(f"Subject: Hospital Portal - Password Reset Code")
    print(f"Message: You requested a password reset. Your secure code is:")
    print(f"         >>> {otp} <<<")
    print(f"This code will expire in 15 minutes.")
    print(f"{'='*50}\n")

#allow the vue SPA to communicate with the flask api 
CORS(app)

# configure the jwt for secure token-based authentication
#(we will move this secrete-key to .env file later before production)
app.config["JWT_SECRET_KEY"] = "super-secrete-hms-key-change-later"
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

#Initialize extention
db.init_app(app)
bcrypt = Bcrypt(app)

from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirect to login page if the user is not logged in.

@login_manager.user_loader #The user_loader function is required by Flask-Login. 
#It's used to retrieve a user from the database based on the ID that Flask-Login stores in the session.
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/api/payments/create-order', methods=['POST', 'OPTIONS'])
def create_payment_order():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS OK"}), 200
        
    verify_jwt_in_request()
    
    try:
        data = request.get_json()
        amount = data.get('amount') # Amount in Rupees
        
        # Razorpay expects amounts in PAISA (1 Rupee = 100 Paisa)
        # So ₹500 must be sent as 50000
        order_amount = int(amount) * 100 
        order_currency = 'INR'
        order_receipt = f"receipt_order_{secrets.token_hex(4)}"

        # Create the order in Razorpay's system
        razorpay_order = client.order.create({
            "amount": order_amount,
            "currency": order_currency,
            "receipt": order_receipt,
            "payment_capture": 1 # Auto-capture payment
        })

        return jsonify({
            "order_id": razorpay_order['id'],
            "amount": order_amount,
            "key_id": RAZORPAY_KEY_ID
        }), 200

    except Exception as e:
        print(f"Razorpay Error: {e}")
        return jsonify({"msg": "Failed to create payment order"}), 500




@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    # 1. Handle Vue's CORS Preflight check
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON data"}), 400

    # 2. Extract credentials. We look for 'email' first, but fallback to 'username'
    # This means the frontend input can handle either one!
    login_identifier = data.get('email') or data.get('username')
    password = data.get('password')

    if not login_identifier or not password:
        return jsonify({"msg": "Missing credentials"}), 400

    # 3. Look for the user by matching EITHER the email or the username
    user = User.query.filter((User.email == login_identifier) | (User.username == login_identifier)).first()

    # 4. Check if user exists and password is correct
    if user and bcrypt.check_password_hash(user.password, password):
        
        # 5. Handle Blacklisted Users (The Security Gate)
        if user.status == 'blacklisted':
            return jsonify({"msg": "Access Denied. Your account has been suspended by administration."}), 403
        
        # 6. Handle Active Users & Generate Token
        if user.status == 'active':
            access_token = create_access_token(
                identity=str(user.id), 
                additional_claims={"role": user.role}
            )
            
            return jsonify({
                "msg": "Login Successful!",
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "email": user.email, # Included email in the response payload
                    "username": user.username,
                    "role": user.role
                }
            }), 200

    # 7. If we get here, credentials failed
    return jsonify({"msg": "Invalid credentials. Please try again."}), 401



@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def api_register():
    # 1. CORS Preflight
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    try:
        data = request.get_json()

        username = data.get('username')
        email = data.get('email') # <-- NEW: Extract the email
        password = data.get('password')
        name = data.get('name')
        contact = data.get('contact')

        # 2. Update validation to include email
        if not username or not email or not password or not name or not contact:
            return jsonify({"msg": "Missing required fields"}), 400
        
        # 3. The Security Gate: Block duplicate/blacklisted emails
        if User.query.filter_by(email=email).first():
            return jsonify({"msg": "This email is already registered."}), 409
            
        if User.query.filter_by(username=username).first():
            return jsonify({"msg": "Username already exists"}), 409
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 4. Save the email to the User model
        new_user = User(username=username, email=email, password=hashed_password, role='patient', status='active')
        db.session.add(new_user)
        db.session.flush()

        new_patient = Patient(name=name, contact=contact, user_id=new_user.id)
        db.session.add(new_patient)

        db.session.commit()

        return jsonify({"msg": "Registration successful! You can now log in."}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback() # If something crashes, undo the database changes
        return jsonify({"msg": "Failed to register user"}), 500

@app.route('/api/auth/forgot-password', methods=['POST', 'OPTIONS'])
def api_forgot_password():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({"msg": "Please provide a username."}), 400
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"msg": "If that account exists, a recovery code has been sent."}), 200
        
        otp = generate_secure_otp()
        expiry_time = datetime.now() + timedelta(minutes=15)

        user.reset_otp = otp
        user.reset_otp_expiry = expiry_time
        db.session.commit()

        simulate_email_delivery(user.username, otp)

        return jsonify({"msg": "If that account exists, a recovery code has been sent."}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "An error occurred while processing your request."}), 500


@app.route('/api/auth/verify-otp', methods=['POST', 'OPTIONS'])
def api_verify_otp():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200

    try:
        data = request.get_json()
        username = data.get('username')
        otp = data.get('otp')

        if not username or not otp:
            return jsonify({"msg": "Missing username or OTP."}), 400

        user = User.query.filter_by(username=username).first()

        # 1. Check if user exists and OTP matches
        if not user or user.reset_otp != otp:
            return jsonify({"msg": "Invalid or incorrect reset code."}), 401

        # 2. Check if the OTP has expired
        if not user.reset_otp_expiry or datetime.now() > user.reset_otp_expiry:
            return jsonify({"msg": "This reset code has expired. Please request a new one."}), 401

        # SUCCESS! But notice we DO NOT delete the OTP here yet. 
        # We need it to stay alive for 1 more minute so the final reset route can use it.
        return jsonify({"msg": "Code verified! Please enter your new password."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while verifying the code."}), 500


@app.route('/api/auth/reset-password', methods=['POST','OPTIONS'])
def api_reset_password():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    try:
        data = request.get_json()
        username = data.get('username')
        otp = data.get('otp')
        new_password = data.get('password')

        if not all([username, otp, new_password]):
            return jsonify({"msg": "Missing required fields."}), 400
        
        user = User.query.filter_by(username=username).first()

        if not user or user.reset_otp != otp:
            return jsonify({"msg": "Invalid or incorrect reset code."}), 401
        
        if not user.reset_otp_expiry or datetime.now() > user.reset_otp_expiry:
            return jsonify({"msg": "This reset code has expired. Please request a new one."}), 401
        
        # We use your app's bcrypt instance, and decode it to a string for the database
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        user.reset_otp = None
        user.reset_otp_expiry = None

        db.session.commit()

        return jsonify({"msg": "Password reset successfully! You can now log in."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "An error occurred while resetting your password."}), 500

@app.route('/api/admin/dashboard', methods=['GET', 'OPTIONS'])
def api_admin_dashboard():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    #Authorization check : only admin can access this page
    claims = get_jwt()

    if claims.get("role") != 'admin':
        return jsonify({"msg": "Unauthorizes access. Admin only."}), 403

    try:
        #fetch statistic from database
        total_doctors = Doctor.query.count()
        total_patients = Patient.query.count()
        total_appointments = Appointment.query.count()

        # fetch the live feed of 5 most recent appointments
        # fetch the live feed of 5 most recent appointments
        recent_appts = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
        recent_list = [{
            "id": a.id,
            "doctor": a.doctor.name if a.doctor else "Unknown",
            "patient": a.patient.name if a.patient else "Unknown", # <-- ADD THIS LINE BACK
            "date": a.date,
            "status": a.status
        } for a in recent_appts]

        # Chart 1: Doctors by Department (Pie Chart)
        departments = Department.query.all()
        dept_labels = []
        dept_data = []
        for dept in departments:
            count = Doctor.query.filter_by(department_id=dept.id).count()
            if count > 0: # Only show departments that actually have doctors
                dept_labels.append(dept.name)
                dept_data.append(count)
        
        # Chart 2: Appointment Status Breakdown (Doughnut Chart)
        statuses = ['Booked', 'Completed', 'Cancelled']
        status_data = []
        for status in statuses:
            count = Appointment.query.filter_by(status=status).count()
            status_data.append(count)

        return jsonify({
            "total_doctors": total_doctors,
            "total_patients": total_patients,
            "total_appointments": total_appointments,
            "recent_activity": recent_list,
            "charts": {
                "departments": {
                    "labels": dept_labels,
                    "data": dept_data
                },
                "appointments": {
                    "labels": statuses,
                    "data": status_data
                }
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to fetch admin analytics."}), 500
    
@app.route('/api/admin/doctors', methods=['POST', 'OPTIONS'])
def api_admin_create_doctor():
    # 1. CORS Preflight
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. Manual VIP Bouncer Check
    verify_jwt_in_request()
    
    claims = get_jwt()
    if claims.get("role") != 'admin':
        return jsonify({"msg": "Unauthorized access. Admin only."}), 403
    
    #Extract doctors data
    data = request.get_json()
    name = data.get('name')
    email = data.get('email') # <-- NEW
    username = data.get('username')
    password = data.get('password')
    department_id = data.get('department_id')
    experience = data.get('experience')

    # Update validation checks
    if not all([name, email, username, password, department_id]):
        return jsonify({"msg": "Missing required fields."}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "This username is already taken."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "This email is already registered to an account."}), 400
    
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(email=email, username=username, password=hashed_password, role='doctor')
        db.session.add(new_user)
        db.session.flush()

        # FIXED: Pass the clean integer directly to the Doctor model! No searching required.
        new_doctor = Doctor(user_id=new_user.id, name=name, department_id=department_id, experience=experience)
        db.session.add(new_doctor)

        db.session.commit()
        return jsonify({"msg": f"Dr. {name} has been successfully registered!"}), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Database error while registering doctor."}),500
    
@app.route('/api/admin/departments', methods=['GET', 'POST', 'OPTIONS'])
def api_admin_departments():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    if get_jwt().get("role") != 'admin':
        return jsonify({"msg": "Unauthorized access. Admin only."}), 403

    # GET: Fetch all departments (for the UI table and the Doctor dropdown)
    if request.method == 'GET':
        try:
            departments = Department.query.all()
            result = []
            for dept in departments:
                # Count how many doctors are currently in this department
                doctor_count = Doctor.query.filter_by(department_id=dept.id).count()
                result.append({
                    "id": dept.id,
                    "name": dept.name,
                    "description": dept.description,
                    "doctor_count": doctor_count
                })
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"msg": "Failed to fetch departments."}), 500

    # POST: Create a brand new department
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({"msg": "Department name is required."}), 400
        
        if Department.query.filter_by(name=name).first():
            return jsonify({"msg": "A department with this name already exists."}), 400
        
        try:
            new_dept = Department(name=name, description=description)
            db.session.add(new_dept)
            db.session.commit()
            return jsonify({"msg": f"Department '{name}' created successfully!"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Database error while creating department."}), 500


@app.route('/api/admin/departments/<int:dept_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def api_admin_department_detail(dept_id):
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    if get_jwt().get("role") != 'admin':
        return jsonify({"msg": "Unauthorized access."}), 403

    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"msg": "Department not found."}), 404

    # PUT: Update the department name/description
    if request.method == 'PUT':
        data = request.get_json()
        dept.name = data.get('name', dept.name)
        dept.description = data.get('description', dept.description)
        try:
            db.session.commit()
            return jsonify({"msg": "Department updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Failed to update department."}), 500

    # DELETE: Remove the department (Safety check enforced!)
    if request.method == 'DELETE':
        doctor_count = Doctor.query.filter_by(department_id=dept.id).count()
        if doctor_count > 0:
            return jsonify({"msg": f"Cannot delete. {doctor_count} doctors are currently assigned to this department."}), 400
        
        try:
            db.session.delete(dept)
            db.session.commit()
            return jsonify({"msg": "Department deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Failed to delete department."}), 500
        
@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['PATCH', 'OPTIONS'])
def api_admin_toggle_user_status(user_id):
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    if get_jwt().get("role") != 'admin':
        return jsonify({"msg": "Unauthorized. Admin only."}), 403

    # 1. Find the user
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"msg": "User not found."}), 404

    # 2. SAFETY CHECK: Only applies to Doctors
    if target_user.role == 'doctor':
        doctor_profile = Doctor.query.filter_by(user_id=target_user.id).first()
        
        if doctor_profile and target_user.status == 'active':
            upcoming_appts = Appointment.query.filter(
                Appointment.doctor_id == doctor_profile.id,
                Appointment.date >= date.today(),
                Appointment.status == 'Booked' 
            ).count()

            if upcoming_appts > 0:
                return jsonify({"msg": f"Cannot blacklist. Dr. {doctor_profile.name} has {upcoming_appts} upcoming appointments. Please reassign or cancel them first."}), 400

    # 3. TOGGLE THE STATUS (CRITICAL: Notice how this is aligned with the 'if' statements above!)
    new_status = 'blacklisted' if target_user.status == 'active' else 'active'
    target_user.status = new_status
    
    try:
        db.session.commit()
        action = "suspended" if new_status == 'blacklisted' else "reactivated"
        return jsonify({"msg": f"Account successfully {action}."}), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Database error while updating status."}), 500
    
@app.route('/api/admin/system-users', methods=['GET', 'OPTIONS'])
def api_admin_get_system_users():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    if get_jwt().get("role") != 'admin':
        return jsonify({"msg": "Unauthorized."}), 403

    try:
        # Fetch all doctors with their user status
        doctors = Doctor.query.all()
        doc_list = [{
            "id": d.id,
            "user_id": d.user.id,
            "name": d.name,
            "department": d.department.name,
            "email": d.user.email,
            "status": d.user.status
        } for d in doctors if d.user] # Ensure user exists

        # Fetch all patients with their user status
        patients = Patient.query.all()
        pat_list = [{
            "id": p.id,
            "user_id": p.user.id,
            "name": p.name,
            "contact": p.contact,
            "email": p.user.email,
            "status": p.user.status
        } for p in patients if p.user]

        return jsonify({
            "doctors": doc_list,
            "patients": pat_list
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to fetch system users."}), 500

@app.route('/api/doctor/dashboard', methods=['GET'])
def api_doctor_dashboard():
    # 1. CORS Preflight
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. Manual VIP Bouncer Check
    verify_jwt_in_request()
    
    # 3. Security Check: Doctors only
    claims = get_jwt()
    if claims.get("role") != 'doctor':
        return jsonify({"msg": "Unauthorized access. Doctors only."}), 403
    
    # 4. Find the doctor profile
    current_user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()

    if not doctor:
        return jsonify({"msg": "Doctor profile not found."}), 404

    today = date.today()

    # 5. Fetch Upcoming Appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'Booked',
        Appointment.date >= today
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    # Flatten appointments for JSON
    appointments_list = []
    for appt in upcoming_appointments:
        appointments_list.append({
            "id": appt.id,
            "patient_id": appt.patient.id,
            "date": appt.date.strftime('%Y-%m-%d'),
            "time": appt.time.strftime('%H:%M'),
            "patient_name": appt.patient.name,
            "patient_contact": appt.patient.contact
        })

    # 6. Fetch 7-Day Availability Schedule
    availability_schedule = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id
    ).order_by(DoctorAvailability.day_of_week.asc()).all()

    # Flatten the schedule for JSON (handling None values carefully)
    schedule_list = []
    for slot in availability_schedule:
        schedule_list.append({
            "day_of_week": slot.day_of_week,
            "morning_start_time": slot.morning_start_time.strftime('%H:%M') if slot.morning_start_time else None,
            "morning_end_time": slot.morning_end_time.strftime('%H:%M') if slot.morning_end_time else None,
            "evening_start_time": slot.evening_start_time.strftime('%H:%M') if slot.evening_start_time else None,
            "evening_end_time": slot.evening_end_time.strftime('%H:%M') if slot.evening_end_time else None
        })

    # 7. Generate 7-Day Date List for the Vue calendar
    # this list will contain (date_obj, date_name and day_of_week)
    days_list = []
    for i in range(7):
        day = today + timedelta(days=i)
        days_list.append({
            "date": day.strftime('%Y-%m-%d'),
            "day_name": day.strftime('%A'),
            "day_of_week": day.weekday()
        })

    # 8. Send the massive data payload to Vue
    return jsonify({
        "doctor_name": doctor.name,
        "department": doctor.department.name if doctor.department else None,
        "upcoming_appointments": appointments_list,
        "availability_schedule": schedule_list,
        "days_list": days_list
    }), 200

# ==========================================
# DOCTOR PROFILE MANAGEMENT
# ==========================================

@app.route('/api/doctor/profile', methods=['GET', 'PUT', 'OPTIONS'])
def api_doctor_profile():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200

    verify_jwt_in_request()
    
    try:
        user_id = get_jwt_identity()
        doctor = Doctor.query.filter_by(user_id=user_id).first()

        if not doctor:
            return jsonify({"msg": "Doctor profile not found."}), 404

        if request.method == 'GET':
            return jsonify({
                "name": doctor.name,
                "contact": getattr(doctor, 'contact', ''),
                "qualification": getattr(doctor, 'qualification', ''),
                "experience": getattr(doctor, 'experience', ''),
                "bio": getattr(doctor, 'bio', ''),
                "consultation_fee": getattr(doctor, 'consultation_fee', 500),
                "profile_picture": getattr(doctor, 'profile_picture', None)
            }), 200

        if request.method == 'PUT':
            data = request.get_json()
            # Update the fields based on your exact schema
            doctor.name = data.get('name', doctor.name)
            doctor.contact = data.get('contact', doctor.contact)
            doctor.qualification = data.get('qualification', doctor.qualification)
            doctor.experience = data.get('experience', doctor.experience)
            doctor.bio = data.get('bio', doctor.bio)
            if 'consultation_fee' in data:
                doctor.consultation_fee = int(data.get('consultation_fee', 500))
            
            db.session.commit()
            return jsonify({"msg": "Professional profile updated successfully."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to handle profile."}), 500


@app.route('/api/doctor/profile/picture', methods=['POST', 'OPTIONS'])
def api_upload_doctor_picture():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200

    verify_jwt_in_request()
    
    try:
        user_id = get_jwt_identity()
        doctor = Doctor.query.filter_by(user_id=user_id).first()

        if not doctor:
            return jsonify({"msg": "Doctor not found."}), 404

        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({"msg": "No file selected."}), 400

        # --- USING OUR REUSABLE ENGINE ---
        picture_url = save_uploaded_image(file, f"doctor_{doctor.id}")
        
        if picture_url:
            doctor.profile_picture = picture_url
            db.session.commit()
            return jsonify({
                "msg": "Profile picture updated successfully!",
                "picture_url": picture_url
            }), 200
            
        return jsonify({"msg": "Invalid file type."}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to upload image."}), 500

@app.route('/api/doctor/schedule', methods=['POST','OPTIONS'])
def api_update_doctor_schedule():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("role") != 'doctor':
        return jsonify({"msg": "Unaluthorised access. Doctors only."}), 403
    
    current_user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    if not doctor:
        return jsonify({"msg": "Doctor profile not found."}), 404
    
    try:
        schedule_data = request.get_json() # Expecting a list of 7 days

        # Helper function to convert "09:00" text into Python time objects
        def parse_time(time_str):
            if not time_str or time_str == "":
                return None
            return datetime.strptime(time_str, '%H:%M').time()
        
        # 3. Loop through the 7 days Vue sends us
        for day_data in schedule_data:
            day_of_week = day_data.get('day_of_week')

            # Check if an entry already exists for this day
            availability = DoctorAvailability.query.filter_by(
                doctor_id = doctor.id,
                day_of_week = day_of_week
            ).first()

            # If not, create a blank one
            if not availability:
                availability = DoctorAvailability(doctor_id=doctor.id, day_of_week=day_of_week)
                db.session.add(availability)

            # update the shift time
            availability.morning_start_time = parse_time(day_data.get('morning_start_time'))
            availability.morning_end_time = parse_time(day_data.get('morning_end_time'))
            availability.evening_start_time = parse_time(day_data.get('evening_start_time'))
            availability.evening_end_time = parse_time(day_data.get('evening_end_time'))

            # save the whole week to the database

        db.session.commit()
        return jsonify({"msg": "Weekly schedule successfully updated!"}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to update schedule"}), 500
    
@app.route('/api/doctor/leaves', methods=['GET', 'POST', 'OPTIONS'])
def api_doctor_leaves():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get('role') != 'doctor':
        return jsonify({"msg": "Unauthorized. Doctors only"}), 403
    
    current_user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()

    # GET: fetch all the upcoming leaves
    if request.method == 'GET':
        leaves = DoctorLeave.query.filter_by(doctor_id=doctor.id).order_by(DoctorLeave.date).all()
        leave_list = [{"id": l.id, "date": l.date.strftime('%Y-%m-%d')} for l in leaves]
        return jsonify(leave_list), 200
    
    # POST : add a new leave date
    if request.method == 'POST':
        data = request.get_json()
        leaves_date_str = data.get('date')

        if not leaves_date_str:
            return jsonify({"msg": "Date is required."}), 400
        
        try:
            leave_date = datetime.strptime(leaves_date_str, '%Y-%m-%d').date()

            # Prevent duplicate leave entry for the same day.
            existing_leave = DoctorLeave.query.filter_by(doctor_id=doctor.id, date=leave_date).first()
            if existing_leave:
                return jsonify({"msg": "You already have timeoff schedule for this date."}), 400
            
            new_leave = DoctorLeave(doctor_id=doctor.id, date=leave_date)
            db.session.add(new_leave)
            db.session.commit()

            return jsonify({"msg": "Time off scheduled successfully"}), 201
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Failed to schedule time off."}), 500



@app.route('/api/doctor/appointment/<int:appointment_id>/consult', methods=['POST', 'OPTIONS'])
def api_submit_consultation(appointment_id):
    # 1. CORS Preflight
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. Security Check: Doctors Only
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("role") != 'doctor':
        return jsonify({"msg": "Unauthorized. Doctors only."}), 403

    current_user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()

    # Find the specific appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # 3. Double-Check Permissions
    if appointment.doctor_id != doctor.id:
        return jsonify({"msg": "Permission denied. This is not your patient."}), 403

    try:
        # Grab the form data Vue sends us
        data = request.get_json()
        diagnosis = data.get('diagnosis')
        prescription = data.get('prescription')
        notes = data.get('notes')

        if not diagnosis or not prescription:
            return jsonify({"msg": "Diagnosis and Prescription are required."}), 400

        # 4. Create the Treatment Record
        new_treatment = Treatment(
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
            appointment_id=appointment.id
        )
        db.session.add(new_treatment)

        # 5. Flip the Status!
        appointment.status = 'Completed'

        # Commit both changes at the exact same time
        db.session.commit()
        return jsonify({"msg": "Consultation complete! Patient record updated."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to submit consultation."}), 500

@app.route('/api/doctor/patient/<int:patient_id>/history', methods=['GET', 'OPTIONS'])
def api_doctor_patient_history(patient_id):
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("role") != 'doctor':
        return jsonify({"msg": "Unauthorized."}), 403
    
    current_user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    patient = Patient.query.get_or_404(patient_id)

    link_exist = Appointment.query.filter_by(doctor_id=doctor.id, patient_id=patient.id).first()
    if not link_exist:
        return jsonify({"msg": "Permission denied. You are not assigned to this patient."}), 403
    
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='Completed'
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    history_list = []
    for appt in completed_appointments:
        history_list.append({
            "date": appt.date.strftime('%b %d, %Y'),
            "consulting_doctor": appt.doctor.name,
            "diagnosis": appt.treatment.diagnosis if appt.treatment else "Pending",
            "prescription": appt.treatment.prescription if appt.treatment else "Pending",
            "notes": appt.treatment.notes if appt.treatment else "N/A"
        })

    return jsonify({
        "patient_name": patient.name,
        "patient_age": patient.age or "N/A",
        "patient_gender": patient.gender or "N/A",
        "blood_group": patient.blood_group or "N/A",
        "history": history_list
    }), 200


@app.route('/api/patient/dashboard', methods=['GET'])
@jwt_required()
def api_patient_dashboard():
    #Authorization check : only admin can access this page
    claims = get_jwt()
    if claims.get("role") != 'patient':
        return jsonify({"msg": "Unauthorized access. Patients only."}), 403

    # get the user id hidden inside the token
    current_user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(user_id=current_user_id).first()
    
    if not patient:
        return jsonify({"msg": "Patient profile not found."}), 404
    
    # fetch upcomming appointment
    upcoming_appointments = Appointment.query.filter(
        and_(
            Appointment.patient_id == patient.id,
            Appointment.status == 'Booked'
        )
    ).order_by(Appointment.date.asc()).all()
    
    # we cannot send SQLAlchemy object directly to json.
    # we must format them to clean dictionary first.
    appointments_list = []
    for appt in upcoming_appointments:
        appointments_list.append({
            "id": appt.id,
            "date": appt.date.strftime('%Y-%m-%d'),
            "time": appt.time.strftime('%H:%M'),
            "doctor_name": appt.doctor.name,
            "department": appt.doctor.department.name
        })

    # send the clean data back to the Vue frontend
    return jsonify({"patient_name": patient.name,
                    "upcoming_appointments": appointments_list
                }), 200


@app.route('/api/patient/doctor/<int:doctor_id>/slots', methods=['GET', 'OPTIONS'])
def api_get_doctor_slots(doctor_id):
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    verify_jwt_in_request()

    target_data_str = request.args.get('date')
    if not target_data_str:
        return jsonify({"msg": "Date parameter is required"}), 400
    
    try:
        target_date = datetime.strptime(target_data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid date format."}), 400
    
    # FIX 1: Removed quotes around doctor_id
    doctor = Doctor.query.get(doctor_id) 
    if not doctor:
        return jsonify({"msg": "Doctor not found"}), 404
    
    # === LAYER 1: THE EXCEPTION LAYER (Vacations/Leaves) ===
    leave = DoctorLeave.query.filter_by(doctor_id=doctor_id, date=target_date).first()
    if leave: # FIX 2: If leave EXISTS, return empty array. (You had 'if not leave')
        return jsonify([]), 200

    # === LAYER 2: THE MASTER ROSTER ===
    day_of_week = target_date.weekday()
    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=day_of_week
    ).first()

    # If they don't have a schedule for this day, or it's turned off
    if not availability:
        return jsonify([]), 200
    
    # === LAYER 3: THE MATH ENGINE ===
    slot_duration = timedelta(minutes=doctor.slot_duration)
    generated_slot = []

    def generate_shift_slot(start_time, end_time):
        if not start_time or not end_time:
            return
            
        # FIX 3: Use combine() instead of strptime() to merge a Date and a Time!
        current_dt = datetime.combine(target_date, start_time)
        end_dt = datetime.combine(target_date, end_time)

        # keep adding slots until the next slot would push past quitting time
        while current_dt + slot_duration <= end_dt:
            generated_slot.append(current_dt.time().strftime('%H:%M'))
            current_dt += slot_duration

    # Slice up both the morning and evening shifts!
    generate_shift_slot(availability.morning_start_time, availability.morning_end_time)
    generate_shift_slot(availability.evening_start_time, availability.evening_end_time)

    # === LAYER 4: THE FILTER (Remove booked appointments) ===
    booked_appointment = Appointment.query.filter_by(
        doctor_id = doctor_id,
        date = target_date,
        status = 'Booked'
    ).all()

    booked_times = [appt.time.strftime('%H:%M') for appt in booked_appointment]

    available_slots = [slot for slot in generated_slot if slot not in booked_times]

    return jsonify(available_slots), 200

@app.route('/api/doctors', methods=['GET'])
def api_get_all_doctor():
    doctors = Doctor.query.all()
    doc_list = []
    for doc in doctors:
        doc_list.append({
            "id": doc.id,
            "name": doc.name,
            "department": doc.department.name if doc.department else "General",
            "experience": doc.experience,
            "consultation_fee": doc.consultation_fee
        })

    return jsonify(doc_list), 200


@app.route('/api/departments', methods=['GET'])
@jwt_required()
def api_get_departments():
    try:
        #fetch the depatmetn from the database
        departments = Department.query.all()

        # package them in to a single JSON list
        dept_list = []
        for dept in departments:
            dept_list.append({
                "id": dept.id,
                "name": dept.name,
                "description": dept.description
            })
        return jsonify(dept_list), 200
    except Exception as e:
        print(f"Error fetching departments: {e}")
        return jsonify({"msg": "Failed to load departments"}), 500

@app.route('/api/departments/<int:department_id>/doctors', methods=['GET'])
@jwt_required()
def api_get_doctors_by_dept(department_id):
    try:
        # Find all active doctors in this specific department
        doctors = Doctor.query.join(User).filter(
            Doctor.department_id == department_id,
            User.status == 'active'
        ).all()

        doc_list = []
        for doc in doctors:
            doc_list.append({
                "id": doc.id,
                "name": doc.name,
                "experience": doc.experience,
                "qualification": doc.qualification
            })
            
        return jsonify(doc_list), 200
        
    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return jsonify({"msg": "Failed to load doctors"}), 500
    
    

@app.route('/api/patient/appointment', methods=['POST', 'OPTIONS'])
def api_book_appointment():
    # 1. CORS Preflight
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. Security Check: Patients Only
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("role") != 'patient':
        return jsonify({"msg": "Unauthorized. Only patients can book appointments."}), 403

    try:
        user_id = get_jwt_identity()
        patient = Patient.query.filter_by(user_id=user_id).first()

        if not patient:
            return jsonify({"msg": "Patient profile not found"}), 404
        
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        date = data.get('date')
        time = data.get('time')

        # fetch the family member
        family_member_id = data.get('family_member_id')

        if not all([doctor_id, date, time]):
            return jsonify({"msg": "Missing required booking details."}), 400
        
        try:
            booking_date = datetime.strptime(date, '%Y-%m-%d').date()
            booking_time = datetime.strptime(time, '%H:%M').time() # <-- ADD THIS LINE
        except ValueError:
            return jsonify({"msg": "Invalid date or time format."}), 400
        
        # If an ID was provided, verify this family member actually belongs to this patient!
        member_name_for_msg = patient.name
        if family_member_id:
            member = FamilyMember.query.filter_by(id=family_member_id, patient_id=patient.id, ).first()
            if not member:
                return jsonify({"msg": "Security Error: Invalid family member selected."}), 403
            member_name_for_msg = member.name

        new_appt = Appointment(
            patient_id = patient.id,
            doctor_id = doctor_id,
            date = booking_date,
            time = booking_time,
            family_member_id = family_member_id,
            status = 'Booked',
            payment_id=data.get('payment_id')
        )

        db.session.add(new_appt)
        db.session.commit()

        # Dynamic success message!
        return jsonify({"msg": f"Appointment successfully booked for {member_name_for_msg}!"}), 201
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to book appointment."}), 500
    


@app.route('/api/patient/appointment/<int:appointment_id>/cancel', methods=['POST', 'OPTIONS'])
def api_patient_cancel_appointment(appointment_id):
    # 1. Handle the CORS Preflight request so the browser doesn't panic
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. Security Check: Ensure the user is logged in as a Patient
    verify_jwt_in_request()
    claims = get_jwt()
    if claims.get("role") != 'patient':
        return jsonify({"msg": "Unauthorized. Patients only."}), 403

    current_user_id = int(get_jwt_identity())
    patient = Patient.query.filter_by(user_id=current_user_id).first()

    # 3. Find the specific appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # 4. Strict Permissions Check: Ensure this patient owns this appointment
    if appointment.patient_id != patient.id:
        return jsonify({"msg": "Permission denied. You cannot cancel someone else's appointment."}), 403

    # 5. Execute the Cancellation
    try:
        appointment.status = 'Cancelled'
        db.session.commit()
        return jsonify({"msg": "Appointment cancelled successfully."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to cancel appointment."}), 500




    
@app.route('/api/patient/history', methods=['GET', 'OPTIONS'])
def api_patient_history():
    # 1. THE PREFLIGHT CHECK (Let the browser's security check pass)
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. THE BOUNCER (Manually check the VIP badge)
    verify_jwt_in_request()

    try:
        current_user_id = int(get_jwt_identity())

        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if not patient:
            return jsonify({"msg": "Patient profile not found."}), 404
        
        past_appointments = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.status.in_(['Completed', 'Cancelled'])
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

        history_list = []
        for appt in past_appointments:
            # Safely extract treatment details if the doctor has filled them out
            diagnosis = appt.treatment.diagnosis if appt.treatment else "Pending"
            prescription = appt.treatment.prescription if appt.treatment else "Pending"
            notes = appt.treatment.notes if appt.treatment else "No notes provided."

            history_list.append({
                "id": appt.id,
                "date": appt.date.strftime('%b %d, %Y'), 
                "time": appt.time.strftime('%H:%M'),
                "doctor_name": appt.doctor.name,
                "department": appt.doctor.department.name,
                "status": appt.status,
                # Add our new treatment data!
                "diagnosis": diagnosis,
                "prescription": prescription,
                "notes": notes
            })

        return jsonify(history_list), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to load patient history"}), 500

@app.route('/api/patient/profile', methods=['GET', 'PUT', 'OPTIONS'])
def api_patient_profile():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200

    verify_jwt_in_request()
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        patient = Patient.query.filter_by(user_id=user_id).first()

        if not patient or not user:
            return jsonify({"msg": "Profile not found."}), 404

        # --- THE GET ROUTE: Sending data to Vue on refresh ---
        if request.method == 'GET':
            return jsonify({
                "name": patient.name,
                "username": user.username,
                "contact": patient.contact,          # FIXED: Ensure this is mapped correctly!
                "age": getattr(patient, 'age', ''), 
                "gender": getattr(patient, 'gender', ''),
                "blood_group": getattr(patient, 'blood_group', ''),
                "address": getattr(patient, 'address', ''),
                "profile_picture": patient.profile_picture  # FIXED: Send the image URL to Vue!
            }), 200

        # --- THE PUT ROUTE: Saving data when you click "Save Changes" ---
        if request.method == 'PUT':
            data = request.get_json()
            
            # Update the User table (Username)
            new_username = data.get('username')
            if new_username and new_username != user.username:
                # Check if username is already taken by someone else
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    return jsonify({"msg": "Username is already taken."}), 400
                user.username = new_username

            # Update the Patient table
            patient.name = data.get('name', patient.name)
            patient.contact = data.get('contact', patient.contact) # FIXED: Save the phone number!
            
            # If you have these extra fields in your models.py, we save them here:
            if hasattr(patient, 'age'): patient.age = data.get('age')
            if hasattr(patient, 'gender'): patient.gender = data.get('gender')
            if hasattr(patient, 'blood_group'): patient.blood_group = data.get('blood_group')
            if hasattr(patient, 'address'): patient.address = data.get('address')

            db.session.commit()
            return jsonify({"msg": "Profile updated successfully."}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to load or update profile."}), 500
    
@app.route('/api/patient/profile/picture', methods=['POST', 'OPTIONS'])
def api_upload_profile_picture():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    verify_jwt_in_request()
    
    try:
        user_id = get_jwt_identity()
        patient = Patient.query.filter_by(user_id=user_id).first()

        if not patient:
            return jsonify({"msg": "Patient not found."}), 404
        
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({"msg": "No file selected."}), 400
        
        picture_url = save_uploaded_image(file, f"patient_{patient.id}")

        if picture_url:
            patient.profile_picture = picture_url
            db.session.commit()
            return jsonify({
                "msg": "Profile picture updated successfully!",
                "picture_url": picture_url
            }), 200
        return jsonify({"msg": "Invalid file type. Only JPG, PNG, and WEBP are allowed."}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to upload image."}), 500



    
# ----- PATIENT PROFILE AND FAMILY MANAGEMENT -------
@app.route('/api/patient/family', methods=['POST', 'OPTIONS'])
def api_add_family_member():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    if get_jwt().get("role") != 'patient':
        return jsonify({"msg": "Unauthorized. Only patients can add family members."}), 403
    
    try:
        #identify the patient
        user_id = get_jwt_identity()
        patient = Patient.query.filter_by(user_id=user_id).first()

        if not patient:
            return jsonify({"msg": "Patient profile not found."}), 404
        
        # Extract the data vue sends us
        data = request.get_json()
        name = data.get('name')
        relation = data.get('relation')
        gender = data.get('gender')
        date_of_birth = data.get('date_of_birth')

        if not all([name, relation, gender, date_of_birth]):
            return jsonify({"msg": "Missing required family member details."}), 400
        
        new_member = FamilyMember(
            patient_id=patient.id, 
            name=name,
            relation=relation,
            gender=gender,
            date_of_birth=date_of_birth
        )

        db.session.add(new_member)
        db.session.commit()

        return jsonify({"msg": f"{name} has been added to your family profile!"}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"msg": "Failed to add family member."}), 500
    
@app.route('/api/patient/family', methods=['GET', 'OPTIONS'])
def api_get_family_members():
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS preflight OK"}), 200
    
    verify_jwt_in_request()
    if get_jwt().get("role") != 'patient':
        return jsonify({"msg": "Unauthorized."}), 403
    
    try:
        user_id = get_jwt_identity()
        patient = Patient.query.filter_by(user_id=user_id).first()

        if not patient:
            return jsonify({"msg": "Patient profile not found."}), 404
        
        family_list = [{
            "id": member.id,
            "name": member.name,
            "relation": member.relation,
            "gender": member.gender,
            "date_of_birth": member.date_of_birth
        } for member in patient.family_member]

        return jsonify(family_list), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc() # <-- This tells Python to print the exact crash report!
        return jsonify({"msg": "Failed to fetch family members."}), 500



from models import User, Doctor, Patient, FamilyMember, Appointment, Treatment, Department, DoctorAvailability, DoctorLeave

if __name__ == '__main__':
    app.run(debug=True)

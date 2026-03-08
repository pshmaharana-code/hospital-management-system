from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy import and_
from flask_bcrypt import Bcrypt
from datetime import datetime, date, time, timedelta
import io
from flask import send_file
import matplotlib
import matplotlib.pyplot as plt
# This is a crucial line for running Matplotlib in a web server
matplotlib.use('Agg')

#initialize the flask application
app = Flask(__name__)

#allow the vue SPA to communicate with the flask api 
CORS(app)

# configure the jwt for secure token-based authentication
#(we will move this secrete-key to .env file later before production)
app.config["JWT_SECRET_KEY"] = "super-secrete-hms-key-change-later"
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

#Initialize extention
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirect to login page if the user is not logged in.

@login_manager.user_loader #The user_loader function is required by Flask-Login. 
#It's used to retrieve a user from the database based on the ID that Flask-Login stores in the session.
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    # 1. Vue will send JSON data, so we grab it using get_json() instead of request.form
    data = request.get_json()
    
    if not data:
        return jsonify({"msg": "Missing JSON data"}), 400

    username = data.get('username')
    password = data.get('password')

    # 2. Look for user in database (Same as your old logic!)
    user = User.query.filter_by(username=username).first()

    # 3. Check if user exists and password is correct
    if user and bcrypt.check_password_hash(user.password, password):
        
        # 4. Handle Blacklisted Users
        if user.status == 'blacklisted':
            return jsonify({"msg": "This account has been blacklisted. Please contact support."}), 403
        
        # 5. Handle Active Users & Generate Token
        if user.status == 'active':
            
            # Create the JWT Token. We use the user's ID as their "identity"
            # We also attach the role so the Vue frontend knows where to redirect them!
            access_token = create_access_token(
                identity=str(user.id), 
                additional_claims={"role": user.role}
            )
            
            # Return the token and user info as JSON
            return jsonify({
                "msg": "Login Successful!",
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                }
            }), 200

    # 6. If we get here, credentials failed
    return jsonify({"msg": "Invalid username or password. Please try again."}), 401

# @app.route('/logout')
# def logout():
#     logout_user() #Logs the user out
#     flash('You have been logged out.', 'info')
#     return redirect(url_for('login'))

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def api_register():
    # 1. CORS Preflight
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        contact = data.get('contact')

        if not username or not password or not name or not contact:
            return jsonify({"msg": "Missing required fields"}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({"msg": "Username already exists"}), 409
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, password = hashed_password, role = 'patient', status='active')
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


@app.route('/api/admin/dashboard', methods=['GET'])
@jwt_required()
def api_admin_dashboard():
    #Authorization check : only admin can access this page
    claims = get_jwt()

    if claims.get("role") != 'admin':
        return jsonify({"msg": "Unauthorizes access. Admin only."}), 403

    #fetch statistic from database
    doctor_count = Doctor.query.count()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()

    return jsonify({"msg": "Welcome to admin dashboard.",
                    "stats": {
                        "doctors": doctor_count,
                        "patients": patient_count,
                        "appointments": appointment_count
                    }}), 200

@app.route('/api/doctor/dashboard', methods=['GET'])
@jwt_required()
def api_doctor_dashboard():
    # 1. Security Check: Doctors only
    claims = get_jwt()
    if claims.get("role") != 'doctor':
        return jsonify({"msg": "Unauthorized access. Doctors only."}), 403
    
    # 2. Find the doctor profile
    current_user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()

    if not doctor:
        return jsonify({"msg": "Doctor profile not found."}), 404

    today = date.today()

    # 3. Fetch Upcoming Appointments
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
            "date": appt.date.strftime('%Y-%m-%d'),
            "time": appt.time.strftime('%H:%M'),
            "patient_name": appt.patient.name,
            "patient_contact": appt.patient.contact
        })

    # 4. Fetch 7-Day Availability Schedule
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

    # 5. Generate 7-Day Date List for the Vue calendar
    # this list will contain (date_obj, date_name and day_of_week)
    days_list = []
    for i in range(7):
        day = today + timedelta(days=i)
        days_list.append({
            "date": day.strftime('%Y-%m-%d'),
            "day_name": day.strftime('%A'),
            "day_of_week": day.weekday()
        })

    # 6. Send the massive data payload to Vue
    return jsonify({
        "doctor_name": doctor.name,
        "department": doctor.department.name if doctor.department else None,
        "upcoming_appointments": appointments_list,
        "availability_schedule": schedule_list,
        "days_list": days_list
    }), 200
@app.route('/doctor/update_schedule', methods = ['POST'])
@login_required
def update_schedule():
    if current_user.role != 'doctor':
        abort(403)

    doctor = Doctor.query.filter_by(user_id = current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    try:
        # We will loop 7 times (for day 0 to 6)
        for day_index in range(7):
            # Find the correct availability record for this doctor and day
            availability = DoctorAvailability.query.filter_by(
                doctor_id=doctor.id,
                day_of_week=day_index
            ).first()

            if availability:
                # Get the 4 time strings from the form for this day
                m_start_str = request.form.get(f"{day_index}_morning_start")
                m_end_str = request.form.get(f"{day_index}_morning_end")
                e_start_str = request.form.get(f"{day_index}_evening_start")
                e_end_str = request.form.get(f"{day_index}_evening_end")

                def to_time(time_str):
                    if time_str:
                        return datetime.strptime(time_str, '%H:%M').time()
                    return None
                
                availability.morning_start_time = to_time(m_start_str)
                availability.morning_end_time = to_time(m_end_str)
                availability.evening_start_time = to_time(e_start_str)
                availability.evening_end_time = to_time(e_end_str)

        db.session.commit()
        flash('Your schedule has been updated successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating your schedule: {e}', 'danger')

    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/mark_complete/<int:appointment_id>', methods = ['GET', 'POST'])
@login_required
def mark_complete(appointment_id):
    if current_user.role != 'doctor':
        abort(403)

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.doctor.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')

        new_treatment = Treatment(diagnosis=diagnosis, prescription=prescription, notes=notes, appointment_id=appointment.id)

        appointment.status = 'Completed'

        db.session.add(new_treatment)
        db.session.commit()

        flash('Appointment marked as completed and treatment details saved.','success')
        return redirect(url_for('doctor_dashboard'))
    
    return render_template('mark_complete.html', appointment=appointment)

@app.route('/doctor/patient_history/<int:patient_id>')
@login_required
def doctor_patient_history(patient_id):
    if current_user.role != 'doctor':
        abort(403)

    patient = Patient.query.get_or_404(patient_id)

    # Security check: Ensure the doctor is actually linked to this patient
    # via at least one appointment (even if not completed)
    link_exist = Appointment.query.filter_by(doctor_id=current_user.doctor.id, patient_id=patient.id).first()

    if not link_exist and current_user.role != 'admin':
        flash('You do not have permission to view this patient\'s history.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='Completed'
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template('doctor_patient_history.html', patient=patient, appointments=completed_appointments)


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
                    "upcomming_appointments": appointments_list
                }), 200


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
    
@app.route('/api/doctors/<int:doctor_id>/slots', methods=['GET'])
@jwt_required()
def api_get_doctor_slots(doctor_id):
    try:
        doctor = Doctor.query.get_or_404(doctor_id)
        SLOT_DURATION = timedelta(minutes=30)

        # 1. Get the doctor's weekly schedule
        schedule_query = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
        schedule_dict = {s.day_of_week: s for s in schedule_query}

        # 2. Get existing bookings to know what is taken
        today = date.today()
        existing_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date >= today,
            Appointment.status == 'Booked'
        ).all()
        
        # Super fast lookup set
        booked_slots = set((appt.date, appt.time) for appt in existing_appointments)

        # 3. Generate the 7 days of slots
        days_to_show = []
        for i in range(7):
            current_date = today + timedelta(days=i)
            day_of_week = current_date.weekday()
            default_schedule = schedule_dict.get(day_of_week)
            
            day_slots = []
            if default_schedule:
                # Calculate Morning Slots
                if default_schedule.morning_start_time and default_schedule.morning_end_time:
                    current_time = datetime.combine(current_date, default_schedule.morning_start_time)
                    end_time = datetime.combine(current_date, default_schedule.morning_end_time)
                    while current_time < end_time:
                        slot_time_obj = current_time.time()
                        status = 'Booked' if (current_date, slot_time_obj) in booked_slots else 'Available'
                        day_slots.append({'time': slot_time_obj.strftime('%H:%M'), 'status': status})
                        current_time += SLOT_DURATION
                
                # Calculate Evening Slots
                if default_schedule.evening_start_time and default_schedule.evening_end_time:
                    current_time = datetime.combine(current_date, default_schedule.evening_start_time)
                    end_time = datetime.combine(current_date, default_schedule.evening_end_time)
                    while current_time < end_time:
                        slot_time_obj = current_time.time()
                        status = 'Booked' if (current_date, slot_time_obj) in booked_slots else 'Available'
                        day_slots.append({'time': slot_time_obj.strftime('%H:%M'), 'status': status})
                        current_time += SLOT_DURATION
            
            # Add this day's calculated data to our massive list
            days_to_show.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'display_date': current_date.strftime('%b %d, %Y'), 
                'day_name': current_date.strftime('%A'),            
                'slots': day_slots
            })

        return jsonify(days_to_show), 200

    except Exception as e:
        import traceback
        traceback.print_exc() # This will print the exact line error in your Flask terminal
        return jsonify({"msg": "Failed to load time slots"}), 500
    

@app.route('/api/patient/appointment/book', methods=['POST', 'OPTIONS'])
def api_book_appointment():
    # 1. THE PREFLIGHT CHECK (CORS)
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    # THE BOUNCER
    verify_jwt_in_request()
    current_user_id = int(get_jwt_identity())

    try:
        # Grab the data Vue just sent us
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        date_str = data.get('date') # Format: 'YYYY-MM-DD'
        time_str = data.get('time') # Format: 'HH:MM'
        
        # Convert the string text into actual Python Date/Time objects
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appt_time = datetime.strptime(time_str, '%H:%M').time()

        #Find the patient
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        if not patient:
            return jsonify({"msg": "Patient profile not found."}), 404
        
        # Check if ANY appointment exists for this doctor, on this date, at this time, that is 'Booked'
        existing_booking = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=appt_date,
            time=appt_time,
            status='Booked'
        ).first()

        if existing_booking:
            # If a booking is found, immediately reject the request!
            return jsonify({"msg": "Sorry, this slot was just booked by someone else!"}), 409

        # create the new appointment
        new_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            date=appt_date,
            time=appt_time,
            status='Booked'
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        return jsonify({"msg": "Appointment successfully booked!"}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to book appointment"}), 500
    


# @app.route('/patient/book_appointment')
# @login_required
# def book_appointment():
#     if current_user.role != 'patient':
#         abort(403)

#     #get all the department
#     departments = Department.query.all()

#     return render_template('select_department.html', departments=departments)


@app.route('/api/patient/appointment/cancel/<int:appointment_id>', methods=['POST', 'OPTIONS'])
def api_cancel_appointment(appointment_id):
    # 1. THE PREFLIGHT CHECK: Let the browser's invisible OPTIONS request pass!
    if request.method == "OPTIONS":
        return jsonify({"msg": "CORS Preflight OK"}), 200

    # 2. THE BOUNCER: Now we manually check the VIP badge for the real POST request
    verify_jwt_in_request() 
    current_user_id = int(get_jwt_identity())
    
    # 3. Find the patient profile
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    if not patient:
        return jsonify({"msg": "Patient profile not found."}), 404

    # 4. Find the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # 5. Security Check: Does this appointment belong to THIS patient?
    if appointment.patient_id != patient.id:
        return jsonify({"msg": "You do not have permission to cancel this appointment."}), 403 
        
    # 6. Cancel it and save!
    appointment.status = 'Cancelled'
    db.session.commit()
    
    return jsonify({"msg": "Appointment successfully cancelled."}), 200

# @app.route('/patient/select_doctor/<int:department_id>')
# @login_required
# def select_doctor(department_id):
#     if current_user.role != 'patient':
#         abort(403)

#     #find the department the user clicked on or return 404 
#     department = Department.query.get_or_404(department_id)

#     #find all the doctor who belongs to this department and have a 'active' status not 'blacklisted'

#     doctors = Doctor.query.join(User).filter(
#         Doctor.department_id == department_id,
#         User.status == 'active'
#     ).all()

#     return render_template('select_doctor.html', department=department, doctors=doctors)

@app.route('/patient/doctor_profile/<int:doctor_id>')
@login_required
def doctor_profile(doctor_id):
    if current_user.role != 'patient':
        abort(403)
        
    # Find the doctor by their ID
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Render a new template, passing the doctor's info
    return render_template('doctor_profile.html', doctor=doctor)



# @app.route('/patient/confirm_booking/<int:doctor_id>/<string:date>/<string:time>')
# @login_required
# def confirm_booking(doctor_id, date, time):
#     if current_user.role != 'patient':
#         abort(403)
        
#     doctor = Doctor.query.get_or_404(doctor_id)
    
#     # Convert the date and time strings back into objects for display
#     try:
#         booking_date = datetime.strptime(date, '%Y-%m-%d').date()
#         booking_time = datetime.strptime(time, '%H:%M').time()
#     except ValueError:
#         flash('Invalid booking slot.', 'danger')
#         return redirect(url_for('patient_dashboard'))
    
#     return render_template('confirm_booking.html', doctor=doctor, booking_date=booking_date, booking_time=booking_time)


    
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

@app.route('/api/patient/profile', methods = ['GET', 'PUT', 'OPTIONS'])
def api_patient_profile():
    
    if request.method == 'OPTIONS':
        return jsonify({"msg": "CORS Preflight OK"}), 200
    
    verify_jwt_in_request()

    try:
        current_user_id = int(get_jwt_identity())
        patient = Patient.query.filter_by(user_id=current_user_id).first()

        if not patient:
            return jsonify({"msg": "Patient profile not found."}), 404
        
        if request.method == 'GET':
            return jsonify({
                "name": patient.name,
                "concat": patient.contact,
                "age": patient.age,
                "gender": patient.gender,
                "blood_group": patient.blood_group,
                "address": patient.address,
                "username": patient.user.username # Pulling from the linked User table!
            })
        # 4. IF PUT: Save the updated data from Vue
        if request.method == 'PUT':
            data = request.get_json()
            
            # Update basic text fields safely
            patient.name = data.get('name', patient.name)
            patient.contact = data.get('contact', patient.contact)
            patient.gender = data.get('gender', patient.gender)
            patient.blood_group = data.get('blood_group', patient.blood_group)
            patient.address = data.get('address', patient.address)
            
            # SAFE AGE CHECK: Prevent crashes if the age box is left empty
            age_input = data.get('age')
            if age_input == "" or age_input is None:
                patient.age = None
            else:
                patient.age = int(age_input)
            
            # SMART USERNAME CHECK: Only update if they actually typed a NEW username
            new_username = data.get('username')
            if new_username and new_username != patient.user.username:
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    return jsonify({"msg": "Username already taken by another user."}), 409
                patient.user.username = new_username
                
            db.session.commit()
            return jsonify({"msg": "Profile updated successfully!"}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Failed to process profile request"}), 500


@app.route('/admin/doctors')
@login_required
def manage_doctors():
    if current_user.role != 'admin':
        abort(403)

    #get the search query from the URL argument
    search_query = request.args.get('search_query', '')
    #base query
    doctors_query = Doctor.query

    #if there is a search query, filter the results
    if search_query:
        doctors_query = doctors_query.join(Department).filter(
            or_(
                Doctor.name.contains(search_query),
                #Doctor.specialization.contains(search_query)
                Department.name.contains(search_query)
            )
        )
    #query all doctors from the database
    doctors = doctors_query.all()
    return render_template('manage_doctors.html', doctors=doctors)

@app.route('/admin/doctors/add', methods = ['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        #get data from the form
        name = request.form.get('name')
        #specialization = request.form.get('specialization')
        department_id = request.form.get('department_id')
        username = request.form.get('username')
        password = request.form.get('password')
        contact = request.form.get('contact')
        experience = request.form.get('experience')
        qualification = request.form.get('qualification')

        #check if username already exist
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exist. Please choose another.', 'danger')
            departments = Department.query.all()
            #return redirect(url_for('add_doctor'))
            return render_template('add_doctor.html', departments=departments)
        
        #create the new user with doctor role
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, role='doctor')
        db.session.add(new_user)
        db.session.commit()

        #create the corresponding doctor record
        new_doctor = Doctor(name=name, department_id=department_id, user_id=new_user.id, contact=contact, experience=experience, qualification=qualification)
        db.session.add(new_doctor)
        db.session.commit()

        #We've just created a new_doctor. Now, get their new ID.
        doctor_id = new_doctor.id
        
        # Create a default 7-day availability schedule for this doctor
        # We use 0=Monday, 1=Tuesday,and so on 6=Sunday
        default_availability = []
        for day in range(7):
            default_availability.append(
                DoctorAvailability(
                    day_of_week=day,
                    doctor_id=doctor_id,
                    morning_start_time=None,
                    morning_end_time=None,
                    evening_start_time=None,
                    evening_end_time=None
                )
            )
        

        db.session.bulk_save_objects(default_availability)
        db.session.commit()

        flash('Doctor added successfully! A default 7-day schedule was created.', 'success')
        return redirect(url_for('manage_doctors'))

    # Fetch all departments to pass to the dropdown menu
    departments = Department.query.all()
    return render_template('add_doctor.html', departments=departments)

@app.route('/admin/departments/add', methods=['GET', 'POST'])
@login_required
def add_departments():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        department = request.form.get('name')
        description = request.form.get('description')

        exist_dept = Department.query.filter_by(name=department).first()
        if exist_dept:
                flash('Department already exist.', 'danger')
                return render_template('add_departments.html')

        new_dept = Department(name=department, description=description)
        db.session.add(new_dept)
        db.session.commit()

        flash('Department created successfully.', 'success')
        return redirect(url_for('add_departments'))

    return render_template('add_departments.html')


@app.route('/admin/doctors/edit/<int:doctor_id>', methods = ['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if current_user.role != 'admin':
        abort(403)

    #Find the doctor by ID, return 404 if not found
    doctor = Doctor.query.get_or_404(doctor_id)

    # Get all departments for the dropdown
    departments = Department.query.all()
    
    if request.method == 'POST':
        doctor.name = request.form.get('name')
        #doctor.specialization = request.form.get('specialization')
        doctor.department_id = request.form.get('department_id')
        doctor.contact = request.form.get('contact')
        doctor.experience = request.form.get('experience')
        doctor.qualification = request.form.get('qualification')
        #commit the changes to the database
        db.session.commit()

        flash('Doctor details updated successfully!', 'success')
        return redirect(url_for('manage_doctors'))

    return render_template('edit_doctor.html', doctor=doctor, departments=departments)

@app.route('/admin/doctor/delete/<int:doctor_id>', methods = ['GET', 'POST'])
@login_required
def delete_doctor(doctor_id):
    if current_user.role != 'admin':
        abort(403)

    #find the doctor and their associated user account
    doctor_to_delete = Doctor.query.get_or_404(doctor_id)
    user_to_delete = User.query.get_or_404(doctor_to_delete.user_id)

    #delete both the record from database
    db.session.delete(doctor_to_delete)
    db.session.delete(user_to_delete)
    db.session.commit()

    flash('Doctor has been removed from the system.', 'success')
    return redirect(url_for('manage_doctors'))

@app.route('/admin/doctor/blacklist/<int:doctor_id>', methods = ['POST', 'GET'])
@login_required
def blacklist_doctor(doctor_id):
    if current_user.role != 'admin':
        abort(403)

    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)

    user.status = 'blacklisted'
    db.session.commit()

    flash('Doctor has been blacklisted and can no longer log in.', 'warning')
    return redirect(url_for('manage_doctors'))

@app.route('/admin/doctors/activate/<int:doctor_id>', methods=['POST', 'GET'])
@login_required
def activate_doctor(doctor_id):
    if current_user.role != 'admin':
        abort(403)
    
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)
    
    # Update the user's status
    user.status = 'active'
    db.session.commit()
    
    flash('Doctor has been re-activated.', 'success')
    return redirect(url_for('manage_doctors'))

@app.route('/admin/patients')
@login_required
def manage_patients():
    if current_user.role != 'admin':
        abort(403)

    #get the search query from the URL argument
    search_query = request.args.get('search_query', '')

    #base query for patients
    patients_query = Patient.query

    #if there is a search query, filter the result
    if search_query:
        patients_query = patients_query.join(User).filter(
            or_(
                Patient.name.contains(search_query),
                Patient.contact.contains(search_query),
                User.username.contains(search_query)
            )
        )

    patients = patients_query.all()

    return render_template('manage_patients.html', patients=patients)

@app.route('/admin/patient/edit/<int:patient_id>', methods = ['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if current_user.role != 'admin':
        abort(403)

    #find the patient by id
    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':
        #get new data from the form
        patient.name = request.form.get('name')
        patient.contact = request.form.get('contact')

        db.session.commit()

        flash('Patient details updated successfully!', 'success')
        return redirect(url_for('manage_patients'))
    
    return render_template('edit_patient.html', patient=patient)

@app.route('/admin/patient/delete/<int:patient_id>', methods=['POST', 'GET'])
@login_required
def delete_patient(patient_id):
    if current_user.role != 'admin':
        abort(403)

    #find the patient and their associate user account
    patient_to_delete = Patient.query.get_or_404(patient_id)
    user_to_delete = User.query.get_or_404(patient_to_delete.user_id)

    #delete both the records
    db.session.delete(patient_to_delete)
    db.session.delete(user_to_delete)
    db.session.commit()

    flash('Patient has been removed from the system.', 'success')
    return redirect(url_for('manage_patients'))

@app.route('/admin/patient/blacklist/<int:patient_id>', methods = ['GET', 'POST'])
@login_required
def blacklist_patient(patient_id):
    if current_user.role != 'admin':
        abort(403)

    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)

    user.status = 'blacklisted'
    db.session.commit()

    flash('Patient has been blacklisted and can no longer log in.', 'warning')
    return redirect(url_for('manage_patients'))

@app.route('/admin/patients/activate/<int:patient_id>', methods=['POST', 'GET'])
@login_required
def activate_patient(patient_id):
    if current_user.role != 'admin':
        abort(403)
    
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    
    # Update the user's status
    user.status = 'active'
    db.session.commit()
    
    flash('Patient has been re-activated.', 'success')
    return redirect(url_for('manage_patients'))

@app.route('/admin/appointments')
@login_required
def manage_appointments():
    if current_user.role != 'admin':
        abort(403)

    all_appointments = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template('manage_appointments.html', appointments=all_appointments)

@app.route('/admin/patient_history/<int:patient_id>')
@login_required
def admin_patient_history(patient_id):
    # Only admins can access this page
    if current_user.role != 'admin':
        abort(403)
        
    # Find the patient
    patient = Patient.query.get_or_404(patient_id)
    
    # Find all 'Completed' appointments for this patient
    completed_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='Completed'
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    return render_template('admin_patient_history.html', patient=patient, appointments=completed_appointments)

@app.route('/admin_chart.png')
@login_required
def admin_chart():
    if current_user.role != 'admin':
        abort(403)

    docto_count = Doctor.query.count()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()

    labels = ['Doctors', 'Patients', 'Appointments']
    data = [docto_count, patient_count, appointment_count]

    fig, ax = plt.subplots(figsize=(8, 4))

    colors = ['#28a745', '#17a2b8', '#ffc107']
    ax.bar(labels, data, color=colors)

    ax.set_title('System Overview', fontsize=16)
    ax.set_ylabel('Total Count', fontsize=12)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close(fig) # Close the figure to free up memory
    img.seek(0)

    return send_file(img, mimetype='image/png')


from models import User, Doctor, Patient, Appointment, Treatment, Department, DoctorAvailability

if __name__ == '__main__':
    app.run(debug=True)

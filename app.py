from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
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
    return "Database Configured"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        #look for user in database
        user = User.query.filter_by(username=username).first()

        #check if user exist and password is correct, AND User is Active
        if user and bcrypt.check_password_hash(user.password, password) and user.status == 'active':
            login_user(user) #Logs the user in
            #for now we'll just show a massage
            #later we'll redirect it to correct dashboard.
            flash('Login Successful!', 'success')
            
            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            elif user.role == "doctor":
                return redirect(url_for('doctor_dashboard'))
            elif user.role == "patient":
                return redirect(url_for('patient_dashboard'))
            
        elif user and user.status == 'blacklisted':
            flash('This account has been blacklisted. Please contact support.', 'danger')     
        else:
            flash('Invalid username or password, Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user() #Logs the user out
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        contact = request.form.get('contact')
        username = request.form.get('username')
        password = request.form.get('password')

        #check if username already exits in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if existing_user.status == 'blacklisted':
                flash('This username is blacklisted and cannot be registered.', 'danger')
            else:
                flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        #If username is new , hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        #create new user with patient role
        new_user = User(username=username, password=hashed_password, role='patient')

        #add and commit new user to get an id
        db.session.add(new_user)
        db.session.commit()

        #Create corresponding patient record
        new_patient = Patient(name=name, contact=contact, user_id=new_user.id)
        db.session.add(new_patient)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    #Authorization check : only admin can access this page
    if current_user.role != 'admin':
        abort(403)

    #fetch statistic from database
    doctor_count = Doctor.query.count()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()

    #pass the count to the templates
    return render_template('admin_dashboard.html', doctor_count=doctor_count, patient_count=patient_count, appointment_count=appointment_count)

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        abort(403)
    
    #find the doctor profile linked to logged-in-user
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    if not doctor:
        flash('Doctor profile not found.', 'Danger')
        return redirect(url_for('logout'))

    #get today's date
    today = date.today()

    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'Booked',
        Appointment.date >= today
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    # --- NEW: Fetch 7-Day Availability Schedule ---
    # We fetch all 7 days for this doctor, ordered by the day (0=Mon, 1=Tue...)
    availability_schedule = DoctorAvailability.query.filter_by(
        doctor_id=doctor.id
    ).order_by(DoctorAvailability.day_of_week.asc()).all()

    # --- NEW: Generate 7-Day Date List ---
    # This list will contain (date_obj, day_name, day_of_week) for the next 7 days
    days_list = []
    for i in range(7):
        day = today + timedelta(days=i)
        days_list.append({
            'date': day,
            'day_name': day.strftime('%A'), # e.g., "Tuesday"
            'day_of_week': day.weekday()    # e.g., 1 (for Tuesday)
        })

    return render_template('doctor_dashboard.html', doctor=doctor, appointments=upcoming_appointments, schedule=availability_schedule, days_list=days_list) # Pass the new list

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

    except:
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


@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        abort(403)

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    upcoming_appointments = Appointment.query.filter(
        and_(
            Appointment.patient_id == patient.id,
            Appointment.status == 'Booked'
        )
    ).order_by(Appointment.date.asc()).all()
    return render_template('patient_dashboard.html', appointments=upcoming_appointments)

@app.route('/patient/book_appointment')
@login_required
def book_appointment():
    if current_user.role != 'patient':
        abort(403)

    #get all the department
    departments = Department.query.all()

    return render_template('select_department.html', departments=departments)

@app.route('/patient/appointment/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    # Only patients can access this
    if current_user.role != 'patient':
        abort(403)
        
    # Find the patient record for the current user
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('logout'))

    # Find the appointment to be cancelled
    appointment = Appointment.query.get_or_404(appointment_id)

    # Check if this appointment actually belongs to this patient
    if appointment.patient_id != patient.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        abort(403) # Forbidden
        
    # Update the status to 'Cancelled'
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment has been successfully cancelled.', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/select_doctor/<int:department_id>')
@login_required
def select_doctor(department_id):
    if current_user.role != 'patient':
        abort(403)

    #find the department the user clicked on or return 404 
    department = Department.query.get_or_404(department_id)

    #find all the doctor who belongs to this department and have a 'active' status not 'blacklisted'

    doctors = Doctor.query.join(User).filter(
        Doctor.department_id == department_id,
        User.status == 'active'
    ).all()

    return render_template('select_doctor.html', department=department, doctors=doctors)

@app.route('/patient/doctor_profile/<int:doctor_id>')
@login_required
def doctor_profile(doctor_id):
    if current_user.role != 'patient':
        abort(403)
        
    # Find the doctor by their ID
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Render a new template, passing the doctor's info
    return render_template('doctor_profile.html', doctor=doctor)

@app.route('/patient/select_solt/<int:doctor_id>')
@login_required
def select_slot(doctor_id):
    if current_user.role != 'patient':
        abort(403)

    doctor = Doctor.query.get_or_404(doctor_id)
    #define the duration of each slot
    SLOT_DURATION = timedelta(minutes=30)

    #get doctors 7 days default schedule
    #put it in a dictionary for easy lookup
    schedule_query = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    schedule_dict = {s.day_of_week: s for s in schedule_query}

    today = date.today()
    existing_appointments_query = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= today,
        Appointment.status == 'Booked'
    ).all()

    # A set is much faster than a list for checking "if X in Y"
    booked_slots = set( (appt.date, appt.time) for appt in existing_appointments_query )

    #Generate the 7-day schedule to show the patient
    days_to_show = []
    for i in range(7):
        current_date = today + timedelta(days=i)
        day_of_week = current_date.weekday() # 0=Monday, 1=Tuesday...
        
        # Get the doctor's default schedule for this day
        default_schedule = schedule_dict.get(day_of_week)
        
        day_slots = [] # Holds all generated slots for this day
        
        if default_schedule:
            #Generate slots for MORNING shift
            if default_schedule.morning_start_time:
                current_time = datetime.combine(current_date, default_schedule.morning_start_time)
                end_time = datetime.combine(current_date, default_schedule.morning_end_time)
                
                while current_time < end_time:
                    slot_time_obj = current_time.time()
                    # Check if this slot (date, time) is already in the 'booked_slots' set
                    if (current_date, slot_time_obj) in booked_slots:
                        day_slots.append({'time': slot_time_obj, 'status': 'Booked'})
                    else:
                        day_slots.append({'time': slot_time_obj, 'status': 'Available'})
                    current_time += SLOT_DURATION
            
            #Generate slots for EVENING shift
            if default_schedule.evening_start_time:
                current_time = datetime.combine(current_date, default_schedule.evening_start_time)
                end_time = datetime.combine(current_date, default_schedule.evening_end_time)

                while current_time < end_time:
                    slot_time_obj = current_time.time()
                    if (current_date, slot_time_obj) in booked_slots:
                        day_slots.append({'time': slot_time_obj, 'status': 'Booked'})
                    else:
                        day_slots.append({'time': slot_time_obj, 'status': 'Available'})
                    current_time += SLOT_DURATION
        
        # Add this day's data to our main list
        days_to_show.append({
            'date': current_date,
            'slots': day_slots # This is the list of {'time': '...', 'status': '...'}
        })
    
    # 5. Render the template
    return render_template('select_slot.html', doctor=doctor, days_to_show=days_to_show)

@app.route('/patient/confirm_booking/<int:doctor_id>/<string:date>/<string:time>')
@login_required
def confirm_booking(doctor_id, date, time):
    if current_user.role != 'patient':
        abort(403)
        
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Convert the date and time strings back into objects for display
    try:
        booking_date = datetime.strptime(date, '%Y-%m-%d').date()
        booking_time = datetime.strptime(time, '%H:%M').time()
    except ValueError:
        flash('Invalid booking slot.', 'danger')
        return redirect(url_for('patient_dashboard'))
    
    return render_template('confirm_booking.html', doctor=doctor, booking_date=booking_date, booking_time=booking_time)

@app.route('/patient/book_final', methods=['POST'])
@login_required
def book_final():
    if current_user.role != 'patient':
        abort(403)
        
    try:
        #Get all the data from the hidden form fields
        doctor_id = request.form.get('doctor_id')
        booking_date_str = request.form.get('booking_date')
        booking_time_str = request.form.get('booking_time')
        
        #Convert date/time strings back into objects
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        booking_time = datetime.strptime(booking_time_str, '%H:%M').time()
        
        #Find the patient
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if not patient:
            flash('Patient profile not found.', 'danger')
            return redirect(url_for('logout'))

        # This is CRUCIAL. We must check if another patient booked this
        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=booking_date,
            time=booking_time,
            status='Booked'
        ).first()

        if existing_appointment:
            # The slot was taken! Send the user back to the slot selection page.
            flash('Sorry, that time slot was just booked by another patient. Please select a new time.', 'danger')
            return redirect(url_for('select_slot', doctor_id=doctor_id))

        # If we get here, the slot is free.
        new_appointment = Appointment(
            date=booking_date,
            time=booking_time,
            status='Booked',
            doctor_id=doctor_id,
            patient_id=patient.id
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        flash('Appointment successfully booked! We look forward to seeing you.', 'success')
        return redirect(url_for('patient_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while booking: {e}', 'danger')
        return redirect(url_for('patient_dashboard'))
    
@app.route('/patient/history')
@login_required
def patient_history():
    if current_user.role != 'patient':
        abort(403)

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('logout'))
    
    completed_appointments = Appointment.query.filter_by(patient_id=patient.id, status='Completed').order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template('patient_history.html', appointments=completed_appointments)

@app.route('/patient/edit_profile', methods = ['GET', 'POST'])
@login_required
def patient_edit_profile():
    if current_user.role != 'patient':
        abort(403)

    patient = Patient.query.filter_by(user_id=current_user.id).first()

    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.contact = request.form.get('contact')

        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('patient_dashboard'))
    
    return render_template('patient_edit_profile.html', patient=patient)


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
        # We use 0=Monday, 1=Tuesday, ... 6=Sunday
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
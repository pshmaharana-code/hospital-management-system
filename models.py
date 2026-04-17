from extension import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False) # <-- NEW: Strict unique identifier
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active') # active / blacklisted

class Department(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), unique = True, nullable = False)
    description = db.Column(db.Text, nullable = True)
    doctors = db.relationship('Doctor', backref='department', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    #specialization = db.Column(db.String(100), nullable = False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable = False)
    contact = db.Column(db.String(100), nullable = True)
    experience = db.Column(db.Integer, nullable = True)
    qualification = db.Column(db.String(200), nullable = True)

    profile_picture = db.Column(db.String(255), nullable=True, default=None)
    bio = db.Column(db.Text, nullable=True)

    # --- NEW: Variable Slot Duration (in minutes) ---
    slot_duration = db.Column(db.Integer, default=30, nullable = False)
    #Link to user model for login credentials
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref=db.backref('doctor', uselist = False))

# --- NEW MODEL: The Exception Layer (Vacations/Days Off) ---
class DoctorLeave(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200), nullable=True)

    # Link to the doctor
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable = False)
    doctor = db.relationship('Doctor', backref=db.backref('leaves', cascade="all, delete-orphan"))

    # A doctor can only have one leave entry per specific date
    __table_args__ = (db.UniqueConstraint('doctor_id', 'date', name='_doctor_date_leave_uc'),)

    def __repr__(self):
        return f'<Leave {self.doctor.name} on {self.date}>'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    contact = db.Column(db.String(100), nullable = False)
    # --- NEW MEDICAL PROFILE FIELDS ---
    age = db.Column(db.Integer, nullable = True)
    gender = db.Column(db.String(20), nullable = True)
    blood_group = db.Column(db.String(10), nullable = True)
    address = db.Column(db.Text, nullable = True)
    # ----------------------------------
    #Link to user model for login credentials
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref=db.backref('patient', uselist = False))

    profile_picture = db.Column(db.String(255), nullable=True, default=None) # we default it to none, if its none , vue will show the initial (e.g., "P")

    #Link to familymember model
    family_member = db.relationship('FamilyMember', backref=db.backref('primary_patient'), lazy = True, cascade="all, delete-orphan")
    # this create a virtual list of familymember belonging to this patient
    # 'backref' allow the familymember to instantly know who their primary patient is
    # 'cascade="all delete-orphan" means if the main patient deletes their account ,
    # all their family sub-accounts are automatically deleted too (keeps the DB clean).

class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    #this line links the family member specifically to the primary parent's ID
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable = False)

    name = db.Column(db.String(100), nullable = False)
    relation = db.Column(db.String(50), nullable = False)
    gender = db.Column(db.String(20), nullable = False)
    date_of_birth = db.Column(db.String(20), nullable = False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    date = db.Column(db.Date, nullable = False)
    time = db.Column(db.Time, nullable = False)
    status = db.Column(db.String(80), default = 'Booked')
    #"many" appointments can link to "one" doctor (one-to-many), "ForeignKey goes to many side (here appointment)"
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable = False)
    #"many" appointments can link to "one" doctor (one-to-many), "ForeignKey goes to many side (here appointment)"
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable = False)

    family_member_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable = True)

    doctor = db.relationship('Doctor', backref=db.backref('appointments', cascade="all, delete-orphan"))
    patient = db.relationship('Patient', backref=db.backref('appointments'))
    family_member = db.relationship('FamilyMember', backref='appointments', lazy=True)

# This model stores the doctor's *default weekly schedule*
class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # We use 0 for Monday, 1 for Tuesday, ..., 6 for Sunday
    day_of_week = db.Column(db.Integer, nullable=False) 
    
    # Morning Shift
    morning_start_time = db.Column(db.Time, nullable=True)
    morning_end_time = db.Column(db.Time, nullable=True)
    
    # Evening Shift
    evening_start_time = db.Column(db.Time, nullable=True)
    evening_end_time = db.Column(db.Time, nullable=True)
    
    # Link to the doctor
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    doctor = db.relationship('Doctor', backref=db.backref('availability', cascade="all, delete-orphan"))

    # A doctor can only have one entry per day of the week
    __table_args__ = (db.UniqueConstraint('doctor_id', 'day_of_week', name='_doctor_day_uc'),)

    def __repr__(self):
        return f'<Availability {self.doctor.name} - Day {self.day_of_week}>'


class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    diagnosis = db.Column(db.Text, nullable = False)
    prescription = db.Column(db.Text, nullable = False)
    notes = db.Column(db.Text, nullable = False)
    #"one" treatment for one appointment
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable = False)

    appointment = db.relationship('Appointment', backref=db.backref('treatment', uselist = False))


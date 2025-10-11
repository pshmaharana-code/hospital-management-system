from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    role = db.Column(db.String(50), nullable = False)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    specialization = db.Column(db.String(100), nullable = False)
    #Link to user model for login credentials
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref=db.backref('doctor', uselist = False))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    contact = db.Column(db.String(100), nullable = False)
    #Link to user model for login credentials
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    user = db.relationship('User', backref=db.backref('patient', uselist = False))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    date = db.Column(db.Date, nullable = False)
    time = db.Column(db.Time, nullable = False)
    status = db.Column(db.String(80), default = 'Booked')
    #"many" appointments can link to "one" doctor (one-to-many), "ForeignKey goes to many side (here appointment)"
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable = False)
    #"many" appointments can link to "one" doctor (one-to-many), "ForeignKey goes to many side (here appointment)"
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable = False)

    doctor = db.relationship('Doctor', backref=db.backref('appointments'))
    patient = db.relationship('Patient', backref=db.backref('appointments'))


class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    diagnosis = db.Column(db.Text, nullable = False)
    prescription = db.Column(db.Text, nullable = False)
    notes = db.Column(db.Text, nullable = False)
    #"one" treatment for one appointment
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable = False)

    appointment = db.relationship('Appointment', backref=db.backref('treatment', uselist = False))


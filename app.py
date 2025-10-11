from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

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

        #check if user exist and password is correct
        if user and bcrypt.check_password_hash(user.password, password):
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
    return render_template('admin_dashboard.html')

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        abort(403)
    return render_template('doctor_dashboard.html')

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        abort(403)
    return render_template('patient_dashboard.html')





from models import User, Doctor, Patient, Appointment, Treatment

if __name__ == '__main__':
    app.run(debug=True)
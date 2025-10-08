from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

#initialize the flask application
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

#Initialize extention
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)



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
            #for now we'll just show a massage
            #later we'll redirect it to correct dashboard.
            flash('Login Successful!', 'success')
            return redirect (url_for('home')) #redirect to home on success
        else:
            flash('Invalid username or password, Please try again.', 'danger')

    return render_template('login.html')

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




from models import User, Doctor, Patient, Appointment, Treatment

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

#initialize the flask application
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

#Initialize extention
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


from models import User, Doctor, Patient, Appointment, Treatment


@app.route('/')
def home():
    return "Database Configured"

if __name__ == '__main__':
    app.run(debug=True)
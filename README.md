# Hospital Management System (HMS)

A robust, role-based web application designed to streamline hospital operations. This system manages patients, doctors, appointments, and medical history in a centralized, secure environment.

## 🚀 Features
## 🏥 Current Features

**God-Mode Admin Panel (In Progress)**
* Secure Role-Based Access Control (RBAC) restricted to `admin` JWTs.
* Real-time hospital analytics aggregation (Total Doctors, Patients, Appointments).
* Live feed of recent hospital-wide scheduling activity.

### 1. Admin Role
* **Dashboard:** View system statistics (Total Doctors, Patients, Appointments) with a server-side generated graphical chart.
* **Manage Staff:** Full CRUD (Create, Read, Update, Delete) capabilities for Doctors.
* **Manage Departments:** Dynamically create new medical departments/specializations.
* **Manage Patients:** View and manage patient accounts (Edit, Blacklist/Activate, Delete).
* **Appointments:** View a master list of all appointments (Booked, Completed, Cancelled).
* **Patient History:** Access the complete medical history of any patient.

### 2. Doctor Role
* **Dashboard:** View personal upcoming appointments.
* **Smart Scheduling:** Manage a **7-Day Repeating Schedule** (Morning/Evening shifts). The system automatically generates bookable slots based on this schedule.
* **Treatment:** Mark appointments as "Completed" and record Diagnosis, Prescription, and Notes.
* **History:** View the medical history of patients they are treating.

### 3. Patient Role
* **User Account:** Secure Registration, Login, and Profile Management (Edit Name/Contact).
* **Booking System:** * Browse Doctors by Department.
    * Check real-time availability (slots are generated based on the doctor's schedule and existing bookings).
    * Prevent double-booking conflicts.
* **Dashboard:** View upcoming appointments and status.
* **History:** View complete past medical history, including prescriptions and diagnoses from previous visits.

---

## 🛠️ Technology Stack

* **Backend:** Python (Flask)
* **Database:** SQLite (Managed via Flask-SQLAlchemy)
* **Frontend:** HTML5, CSS3, Bootstrap 5 (Jinja2 Templating)
* **Authentication:** Flask-Login, Flask-Bcrypt
* **Visualization:** Matplotlib (Server-side chart generation)
* **Constraint:** Zero client-side JavaScript logic (Project Requirement)

---

## 📂 Project Structure

/hospital-management-system
│
├── venv/
│
├── instance/                   
│   └── database.db
│
├── static/ 
│   ├── css/
│   │   ├── style.css
│   │   ├── login_style.css
│   │   └── landing.css
│   │
│   └── img/
│       ├── hero_image.jpg
│       └── doctor_login_image.png
│
├── templates/
│   │   # --- Base & Public ---
│   ├── layout.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   │
│   │   # --- Admin Pages ---
│   ├── admin_dashboard.html
│   ├── manage_doctors.html
│   ├── add_doctor.html
│   ├── edit_doctor.html
│   ├── manage_patients.html
│   ├── edit_patient.html
│   ├── manage_appointments.html
│   ├── add_departments.html
│   ├── admin_patient_history.html
│   │
│   │   # --- Doctor Pages ---
│   ├── doctor_dashboard.html
│   ├── mark_complete.html
│   ├── doctor_patient_history.html
│   │
│   │   # --- Patient Pages ---
│   ├── patient_dashboard.html
│   ├── patient_edit_profile.html  
│   ├── patient_history.html       
│   │
│   │   # --- Booking Flow (Patient) ---
│   ├── select_deaprtment.html   
│   ├── select_doctor.html         
│   ├── doctor_profile.html       
│   ├── select_slot.html           
│   └── confirm_booking.html        
│
├── app.py                      
├── models.py                   
├── init_db.py                  
├── requirements.txt            
└── README.md                   

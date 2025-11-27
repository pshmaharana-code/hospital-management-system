import os
from app import app, db, bcrypt
from models import User, Department, Doctor, Patient, Appointment, Treatment, DoctorAvailability
from datetime import date, time

# --- DATABASE AND APP CONTEXT ---
with app.app_context():

    # Find the instance folder path
    instance_path = app.instance_path
    db_path = os.path.join(instance_path, 'database.db')
    
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Created instance folder at: {instance_path}")
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Old database file removed from: {db_path}")

    db.create_all()
    print(f"New database file created at: {db_path} (with DoctorAvailability)")


    admin_username = 'admin'
    admin_password = 'admin' 
    
    if not User.query.filter_by(username=admin_username).first():
        hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
        admin_user = User(
            username=admin_username, 
            password=hashed_password, 
            role='admin',
            status='active'
        )
        db.session.add(admin_user)
        print(f"Admin user '{admin_username}' created.")
    
    
    #CREATE THE DEPARTMENTS (WITH DESCRIPTIONS) ---
    departments_to_add = [
        Department(
            name='Cardiology', 
            description='Specializes in heart-related issues, including diagnosis and treatment of heart diseases and conditions.'
        ),
        Department(
            name='Orthopedics', 
            description='Focuses on conditions involving the musculoskeletal system, including bones, joints, ligaments, tendons, and muscles.'
        ),
        Department(
            name='Neurology', 
            description='Deals with disorders of the nervous system, including the brain, spinal cord, peripheral nerves, and muscles.'
        ),
        Department(
            name='Dermatology', 
            description='Concerned with the diagnosis and treatment of diseases of the skin, hair, and nails.'
        ),
        Department(
            name='Pediatrics', 
            description='Provides medical care for infants, children, and adolescents, focusing on growth, development, and general health.'
        )
    ]
    
    db.session.bulk_save_objects(departments_to_add)
    print(f"Added {len(departments_to_add)} departments.")

    # Commit all changes to the database
    db.session.commit()
    print("All changes saved to the database. Initialization complete!")
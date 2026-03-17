from app import app, db, bcrypt
from models import User, Doctor, Department

with app.app_context():
    cardio = Department.query.filter_by(name='Cardiology').first()
    neuro = Department.query.filter_by(name='Neurology').first()
    
    if not cardio or not neuro:
        print("Wait! Your departments are missing. Run python init.py first!")
    else:
        # --- DOCTOR 1: Dr. Smith (30 min slots) ---
        hashed_pw1 = bcrypt.generate_password_hash('doctor123').decode('utf-8')
        user1 = User(username='dr_smith', password=hashed_pw1, role='doctor', status='active')
        db.session.add(user1)
        db.session.flush() 
        
        doc1 = Doctor(name='Dr. Smith', department_id=cardio.id, user_id=user1.id, slot_duration=30, contact='9876543210')
        db.session.add(doc1)

        # --- DOCTOR 2: Dr. Jones (15 min slots) ---
        hashed_pw2 = bcrypt.generate_password_hash('doctor123').decode('utf-8')
        user2 = User(username='dr_jones', password=hashed_pw2, role='doctor', status='active')
        db.session.add(user2)
        db.session.flush() 
        
        doc2 = Doctor(name='Dr. Jones', department_id=neuro.id, user_id=user2.id, slot_duration=15, contact='1234567890')
        db.session.add(doc2)

        # Commit everything to the database
        db.session.commit()
        print("SUCCESS: Dr. Smith (30min) and Dr. Jones (15min) have been added!")
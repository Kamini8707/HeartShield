import os
import re
import cv2
import joblib
import numpy as np
import pandas as pd
import pytesseract
import random
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from pdf2image import convert_from_path
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- App Initialization ---
app = Flask(__name__)
app.secret_key = 'heartshield_super_secret_key' 

# --- Database Configuration ---
# !! IMPORTANT: Update 'root:password' with your actual MySQL credentials !!
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:PASSWORD@localhost/heartshield_db'
# local dev: use SQLite file DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://kamini:1234@localhost/heartshield_db'


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Load Model ---
try:
    model = joblib.load('best_xgboost_model.pkl')
    print("Model loaded successfully.")
except Exception as e:
    print(f"Warning: Model file not found. {e}")
    model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Database Models ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile Details
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)
    weight = db.Column(db.Float) # Weight included
    blood_group = db.Column(db.String(5))
    profile_pic = db.Column(db.String(150), default='default.jpg')
    
    analyses = db.relationship('Analysis', backref='user', lazy=True)

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Inputs
    age = db.Column(db.Integer); gender = db.Column(db.String(10))
    height = db.Column(db.Float); weight = db.Column(db.Float)
    ap_hi = db.Column(db.Integer); ap_lo = db.Column(db.Integer)
    cholesterol = db.Column(db.Integer); glucose = db.Column(db.Integer)
    smoke = db.Column(db.String(5)); alco = db.Column(db.String(5)); active = db.Column(db.String(5))
    
    # Outputs
    prediction = db.Column(db.Integer); probability = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

# --- OCR & Preprocessing Logic ---
EXPECTED_FEATURES = ['Age ', 'Gender', 'Height', 'Weight', 'ap_hi', 'ap_lo', 'Cholesterol', 'Gluc', 'Smoke', 'Alco', 'Active']

def extract_text_from_image(img_path):
    try:
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # !! WINDOWS USERS: Uncomment if Tesseract is not in PATH !!
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        text = pytesseract.image_to_string(gray, lang='eng', config='--psm 6')
        return text
    except Exception as e:
        print(f"OCR Error: {e}"); return ""

def is_valid_medical_range(key, value):
    try:
        val = float(value)
        if key == 'ap_hi': return 60 <= val <= 300   
        if key == 'ap_lo': return 30 <= val <= 200
        if key == 'cholesterol': return 80 <= val <= 900 
        if key == 'glucose': return 40 <= val <= 700
        if key == 'age': return 1 <= val <= 120
        if key == 'weight': return 20 <= val <= 300
        if key == 'height': return 50 <= val <= 250
    except:
        return False
    return True

def extract_key_values(text):
    text = text.lower()
    patterns = {
        "age": r"\b(?:age|years)\b[^\d\n]{0,25}(\d{1,3})",
        "height": r"\b(?:height|ht)\b[^\d\n]{0,25}(\d{2,3})", 
        "weight": r"\b(?:weight|wt)\b[^\d\n]{0,25}(\d{2,3}(?:\.\d{1,2})?)",
        "cholesterol": r"\b(?:total\s+)?(?:cholesterol|chol)\b[^\d\n]{0,25}(\d{2,3})",
        "glucose": r"\b(?:glucose|gluc|fasting\s+sugar|fbs)\b[^\d\n]{0,25}(\d{2,3})",
        "systolic": r"\b(?:systolic|sys\.?)\s*(?:bp|blood\s*pressure)?\b[^\d\n]{0,25}(\d{2,3})",
        "diastolic": r"\b(?:diastolic|dia\.?)\s*(?:bp|blood\s*pressure)?\b[^\d\n]{0,25}(\d{2,3})",
        "bp_combined": r"\b(?:bp|blood\s*pressure)\b[^\d\n]{0,25}(\d{2,3})\s*[:/-]\s*(\d{2,3})",
        "gender": r"\b(?:gender|sex)\b[^\w\n]{0,25}(male|female|m|f)",
        "smoke": r"\b(?:smoke|smoking|tobacco)\b[^\w\n]{0,25}(yes|no)",
        "alco": r"\b(?:alcohol|liquor)\b[^\w\n]{0,25}(yes|no)",
        "active": r"\b(?:active|exercise)\b[^\w\n]{0,25}(yes|no)"
    }
    
    results = {}
    for key, pattern in patterns.items():
        matches = re.search(pattern, text)
        if matches:
            if key == "systolic":
                val = matches.group(1)
                if is_valid_medical_range('ap_hi', val): results['ap_hi'] = val
            elif key == "diastolic":
                val = matches.group(1)
                if is_valid_medical_range('ap_lo', val): results['ap_lo'] = val
            elif key == "bp_combined":
                sys_val, dia_val = matches.group(1), matches.group(2)
                if 'ap_hi' not in results and is_valid_medical_range('ap_hi', sys_val): results['ap_hi'] = sys_val
                if 'ap_lo' not in results and is_valid_medical_range('ap_lo', dia_val): results['ap_lo'] = dia_val
            elif key == "gender":
                val = matches.group(1).lower()
                results['gender'] = 'Male' if val.startswith('m') else 'Female'
            elif key in ["smoke", "alco", "active"]:
                val = matches.group(1).lower()
                results[key] = 'yes' if val in ['yes', 'active', 'smoker', 'drinker'] else 'no'
            else:
                val = matches.group(1)
                if is_valid_medical_range(key, val): results[key] = val
    return results

def calculate_clinical_risk(data):
    """
    SAFETY NET: Overrides ML Model for extreme/dangerous values.
    Returns (Prediction, Probability) if risk is critical.
    Otherwise returns None (letting AI decide).
    """
    try:
        # 1. Get Values
        chol = int(data.get('cholesterol', 0))
        gluc = int(data.get('glucose', 0))
        ap_hi = int(data.get('ap_hi', 0))
        ap_lo = int(data.get('ap_lo', 0))
        weight = float(data.get('weight', 0))
        height = int(data.get('height', 0))

        # 2. Calculate BMI (Body Mass Index)
        bmi = 0
        if height > 0:
            height_m = height / 100
            bmi = weight / (height_m * height_m)

        # --- CRITICAL THRESHOLDS ---

        # Condition A: Hypertensive Crisis (High BP)
        # Systolic > 180 OR Diastolic > 120
        if ap_hi > 180 or ap_lo > 120:
            return 1, 99.0 # Critical High Risk

        # Condition B: Diabetes / High Sugar
        if gluc > 220:
            return 1, 98.0 

        # Condition C: Very High Cholesterol
        if chol > 300:
            return 1, 97.0

        # Condition D: Morbid Obesity (BMI > 40)
        if bmi > 40:
            return 1, 85.0 # High probability due to obesity risk

    except Exception as e:
        print(f"Clinical Check Error: {e}")
        pass
    
    # If none of the above are true, return None (Use AI Model)
    return None

def preprocess_input(data):
    """Converts raw data to model categories."""
    data_copy = data.copy()
    
    # 1. Categorize Cholesterol
    chol = int(data_copy.get('cholesterol', 0))
    if chol < 200: data_copy['Cholesterol'] = 1
    elif 200 <= chol < 240: data_copy['Cholesterol'] = 2
    else: data_copy['Cholesterol'] = 3
    
    # 2. Categorize Glucose
    gluc = int(data_copy.get('glucose', 0))
    if gluc < 100: data_copy['Gluc'] = 1
    elif 100 <= gluc < 126: data_copy['Gluc'] = 2
    else: data_copy['Gluc'] = 3

    # 3. Map Dropdowns
    data_copy['Gender'] = 2 if str(data_copy.get('gender')).lower() == 'female' else 1
    data_copy['Smoke'] = 1 if str(data_copy.get('smoke')).lower() == 'yes' else 0
    data_copy['Alco'] = 1 if str(data_copy.get('alco')).lower() == 'yes' else 0
    data_copy['Active'] = 1 if str(data_copy.get('active')).lower() == 'yes' else 0

    # 4. Build DataFrame
    input_data = {
        'Age ': [int(data_copy.get('age', 0))], 'Gender': [data_copy['Gender']],
        'Height': [int(data_copy.get('height', 0))], 'Weight': [float(data_copy.get('weight', 0))],
        'ap_hi': [int(data_copy.get('ap_hi', 0))], 'ap_lo': [int(data_copy.get('ap_lo', 0))],
        'Cholesterol': [data_copy['Cholesterol']], 'Gluc': [data_copy['Gluc']],
        'Smoke': [data_copy['Smoke']], 'Alco': [data_copy['Alco']], 'Active': [data_copy['Active']]
    }
    return pd.DataFrame(input_data, columns=EXPECTED_FEATURES)

# --- Routes ---

@app.route('/')
def home():
    feedbacks = []; quotes = ["Healthy heart, happy life.", "Prevention is better than cure.", "Listen to your heart."]
    if os.path.exists('feedback.txt'):
        with open('feedback.txt', 'r') as f:
            content = f.read().split('--------------------')
            feedbacks = [c.strip() for c in content if len(c.strip()) > 10]
            feedbacks = random.sample(feedbacks, min(4, len(feedbacks))) if feedbacks else []
    return render_template('index.html', feedbacks=feedbacks, quotes=quotes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user); return redirect(url_for('home'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Email already exists.', 'error')
        else:
            new_user = User(
                username=request.form.get('username'), email=request.form.get('email'), name=request.form.get('name'), 
                age=request.form.get('age'), gender=request.form.get('gender'), height=request.form.get('height'),
                weight=request.form.get('weight'), blood_group=request.form.get('blood_group')
            )
            new_user.set_password(request.form.get('password')); db.session.add(new_user); db.session.commit()
            flash('Account created! Please login.', 'success'); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('home'))

@app.route('/guest_analyser')
def guest_analyser(): return redirect(url_for('analyser'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Fetch History
    history = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.date_posted.desc()).limit(5).all()
    
    if request.method == 'POST':
        current_user.name = request.form.get('name'); current_user.age = request.form.get('age')
        current_user.gender = request.form.get('gender'); current_user.height = request.form.get('height')
        current_user.weight = request.form.get('weight'); current_user.blood_group = request.form.get('blood_group')
        
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{uuid.uuid4().hex[:8]}.jpg")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename

        try: db.session.commit(); flash('Profile updated!', 'success')
        except: db.session.rollback(); flash('Error saving.', 'error')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user, history=history)

@app.route('/analyser')
def analyser():
    user_data = {}
    if current_user.is_authenticated:
        user_data = {
            'age': current_user.age or '', 'gender': current_user.gender or '', 
            'height': int(current_user.height) if current_user.height else '', 
            'weight': current_user.weight or ''
        }
    return render_template('analyser.html', user_data=user_data)

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/contact')
def contact():
    if not current_user.is_authenticated: return redirect(url_for('login'))
    return render_template('contact.html')

@app.route('/extract', methods=['POST'])
def handle_extraction():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400

    temp_dir = 'temp_files'; os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename); file.save(file_path); full_text = ""
    
    try:
        if file.filename.lower().endswith('.pdf'):
            # !! CONFIG: Check Poppler Path !!
            # poppler_path = r"C:\Program Files\poppler-25.07.0\Library\bin"
            poppler_path = r"C:\Users\Kamini\Downloads\poppler-24.02.0-0\poppler-24.02.0\Library\bin"

            pages = convert_from_path(file_path, dpi=200, poppler_path=poppler_path)
            for i, page in enumerate(pages):
                p_path = os.path.join(temp_dir, f'page_{i}.jpg'); page.save(p_path, 'JPEG')
                full_text += extract_text_from_image(p_path) + "\n"
        else: full_text = extract_text_from_image(file_path)
    except Exception as e: return jsonify({'error': f'OCR Failed: {e}'}), 500

    for f in os.listdir(temp_dir):
        try: os.remove(os.path.join(temp_dir, f)); 
        except: pass

    return jsonify(extract_key_values(full_text))

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    # Validation
    required_fields = ['age', 'height', 'weight', 'ap_hi', 'ap_lo', 'cholesterol', 'glucose', 'smoke', 'alco', 'active']
    for f in required_fields:
        if not data.get(f): return jsonify({'error': f'Missing {f}. Please fill all fields.'}), 400

    try:
        # 1. Strict Type Casting
        data['age'] = int(data['age']); data['height'] = int(data['height']); data['weight'] = float(data['weight'])
        data['ap_hi'] = int(data['ap_hi']); data['ap_lo'] = int(data['ap_lo'])
        data['cholesterol'] = int(data['cholesterol']); data['glucose'] = int(data['glucose'])

        # 2. Clinical Safety Net (Checks for BP > 120 Dia, BMI > 40, etc.)
        clinical_result = calculate_clinical_risk(data)
        
        if clinical_result:
            pred, prob = clinical_result # Force High Risk
        else:
            # 3. AI Prediction (Normal cases)
            processed = preprocess_input(data)
            pred = int(model.predict(processed)[0])
            prob = float(round(model.predict_proba(processed)[0][1] * 100, 2))

        # 4. Save History
        if current_user.is_authenticated:
            rec = Analysis(
                user_id=current_user.id, age=data['age'], gender=data['gender'], height=data['height'],
                weight=data['weight'], ap_hi=data['ap_hi'], ap_lo=data['ap_lo'], 
                cholesterol=data['cholesterol'], glucose=data['glucose'], smoke=data['smoke'], 
                alco=data['alco'], active=data['active'], prediction=pred, probability=prob
            )
            db.session.add(rec); db.session.commit()
            
        return jsonify({'prediction': pred, 'probability': prob})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
@login_required
def handle_feedback():
    data = request.get_json()
    with open('feedback.txt', 'a') as f:
        f.write(f"Name: {data.get('name') or current_user.username}\nReview: {data.get('review')}\n--------------------\n")
    return jsonify({'success': 'Saved'})

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    os.makedirs('static/profile_pics', exist_ok=True)
    os.makedirs('temp_files', exist_ok=True)

    app.run(debug=True)
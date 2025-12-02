# HeartShield – Heart Disease Prediction Web App

HeartShield is a Flask-based web application that predicts the risk of heart disease using an XGBoost machine-learning model.  
Users can create an account, manage their profile, upload medical reports (PDF / image) for OCR extraction, and view their past prediction history.

---

## 1. Features

### 1.1 User & Profile

- User registration and login (Flask-Login)
- Secure password hashing (Werkzeug)
- Profile fields: name, age, gender, height, weight, blood group
- Upload profile picture  
- If no picture is uploaded, the navbar shows the **first letter** of the username as a fallback avatar (handled in templates/CSS)

### 1.2 Heart Disease Prediction

- Uses a trained **XGBoost** model (`best_xgboost_model.pkl`)
- Inputs:
  - Age, Gender, Height, Weight
  - Systolic BP (`ap_hi`)
  - Diastolic BP (`ap_lo`)
  - Cholesterol
  - Glucose
  - Smoking, Alcohol, Physical Activity
- Outputs:
  - Binary prediction (0 – low risk, 1 – high risk)
  - Probability score in percentage

### 1.3 Clinical Safety Net

Before using the ML model, HeartShield applies rule-based checks:

- Very high blood pressure (e.g., `ap_hi > 180` or `ap_lo > 120`)
- Very high glucose (`glucose > 220`)
- Very high cholesterol (`cholesterol > 300`)
- Morbid obesity (BMI > 40)

If any of these are triggered, the app forces a **high-risk** prediction with a high probability, even if the model disagrees.

### 1.4 OCR-Based Extraction from Reports

- Upload **PDF or image** of a medical report
- Uses:
  - **Tesseract OCR**
  - **Poppler** (`pdf2image`)
  - **OpenCV** for preprocessing
- Extracts values like:
  - Age, Height, Weight
  - BP (systolic / diastolic, including `120/80` pattern)
  - Cholesterol, Glucose
  - Lifestyle flags: Smoke, Alcohol, Active (Yes/No)

### 1.5 Analysis History

- Every prediction (for a logged-in user) is stored in the `analysis` table
- Profile page shows the **last 5 analyses**
- Duplicate protection:
  - If the same user submits the **exact same inputs** within a few seconds, a new row is **not** inserted.  
    Instead, the previous prediction is reused.

---

## 2. Tech Stack

### Backend

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- PyMySQL

### Machine Learning

- XGBoost
- pandas
- NumPy
- joblib

### OCR & Image Processing

- Tesseract OCR
- Poppler (`pdf2image`)
- OpenCV

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2 templates

---

## 3. Project Structure

```text
HeartShield/
│
├── app.py
├── best_xgboost_model.pkl
├── requirements.txt
├── feedback.txt
├── README.md
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   ├── images/
│   │   └── heartshield-logo.jpg
│   └── profile_pics/
│       └── (uploaded profile images)
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── analyser.html
│   ├── profile.html
│   ├── contact.html
│   └── about.html
│
└── temp_files/
    └── (temporary OCR images, auto-cleaned)
```
4. Installation & Setup
4.1 Clone the project
git clone https://github.com/<your-username>/HeartShield.git
cd HeartShield

4.2 Create and activate virtual environment
python -m venv venv


On Windows:

venv\Scripts\activate


(Use source venv/bin/activate on Linux/macOS.)

4.3 Install dependencies
pip install -r requirements.txt

4.4 Set up MySQL database and user

Open MySQL Workbench and run:

CREATE DATABASE IF NOT EXISTS heartshield;

CREATE USER IF NOT EXISTS 'heartshield_user'@'localhost'
IDENTIFIED BY 'hs1234';

GRANT ALL PRIVILEGES ON heartshield.* TO 'heartshield_user'@'localhost';
FLUSH PRIVILEGES;

4.5 Configure database URI in app.py

In app.py:

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://heartshield_user:hs1234@localhost/heartshield'
)

4.6 Create tables and run the app
python app.py


The app will start at:

http://127.0.0.1:5000

5. Usage Guide

Register a new account.

Login using your email and password.

Optionally update your profile and upload a profile picture.

Go to Analyser:

Fill in the required medical details, or

Use Upload Report to extract values via OCR.

Click Predict to see:

Heart disease risk (0/1)

Probability in %

Check your recent analyses in the Profile page.

6. Screenshots (placeholders)

You can add actual images in a screenshots/ folder and reference them here:

![Home Page](screenshots/home.png)
![Analyser Page](screenshots/analyser.png)
![Profile Page](screenshots/profile.png)
![Prediction Result](screenshots/result.png)

7. Future Improvements

Doctor / admin panel

Downloadable PDF health report

Email alerts for high-risk predictions

Multi-language OCR support

Deployment on cloud (Render / Railway / AWS)

8. Contributing

Fork the repository

Create a new branch: git checkout -b feature-name

Commit your changes: git commit -m "Add feature"

Push to the branch: git push origin feature-name

Open a Pull Request

9. License

This project is intended for educational and demonstration purposes.
It does not provide a medical diagnosis. Always consult a doctor for medical decisions.

10. Author

Kamini Prajapati
HeartShield – Using AI to support early heart disease risk awareness.

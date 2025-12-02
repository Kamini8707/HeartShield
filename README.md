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

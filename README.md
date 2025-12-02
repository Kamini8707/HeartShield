# HeartShield
❤️ HeartShield – Intelligent Heart Disease Prediction System

HeartShield is an AI-powered Flask web application that predicts the risk of heart disease using medical parameters.
It supports login, profile management, OCR-based medical report extraction, duplicate prevention, and personal analysis history.

⭐ Features
🔐 User Authentication

User registration & login

Password encryption (Werkzeug)

Profile management (name, age, height, weight, blood group)

Upload profile photo OR auto-generate initial avatar

🤖 AI Prediction

XGBoost ML model (best_xgboost_model.pkl)

Predicts heart disease risk (0/1)

Probability score (%)

Clinical safety checks override AI for extreme conditions

Duplicate prevention: prevents back-to-back identical entries

🩺 Medical Data Extraction (OCR)

Upload PDF or image medical reports

Extracts:

Age

Height

Weight

Blood pressure (systolic/diastolic)

Cholesterol

Glucose

Smoking / Alcohol / Activity

Uses Tesseract OCR + Poppler + OpenCV

📊 User Dashboard

View last 5 predictions

Update profile & picture

Auto-fill analyser page with saved profile info

🗃️ MySQL Database

Tables:

user

analysis

🛠️ Tech Stack
Backend

Python

Flask (auth + routing)

Flask-SQLAlchemy

Flask-Login

PyMySQL

Machine Learning

XGBoost

Pandas / NumPy

Joblib

OCR

Tesseract

Poppler

OpenCV

Frontend

HTML
CSS
JavaScript

📂 Project Structure
HeartShield/
│── app.py
│── best_xgboost_model.pkl
│── requirements.txt
│── feedback.txt
│── README.md
│
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   ├── profile_pics/
│   └── images/
│       └── heartshield-logo.jpg
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

⚙️ Installation & Setup
1️⃣ Clone the project
git clone https://github.com/yourusername/HeartShield.git
cd HeartShield
2️⃣ Create virtual environment
python -m venv venv


Activate:

venv\Scripts\activate  (Windows)

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Setup MySQL Database

Login to MySQL Workbench and run:

CREATE DATABASE IF NOT EXISTS heartshield;

CREATE USER IF NOT EXISTS 'heartshield_user'@'localhost' IDENTIFIED BY 'hs1234';

GRANT ALL PRIVILEGES ON heartshield.* TO 'heartshield_user'@'localhost';
FLUSH PRIVILEGES;

5️⃣ Update Database URI in app.py
app.config['SQLALCHEMY_DATABASE_URI'] = \
"mysql+pymysql://heartshield_user:hs1234@localhost/heartshield"

6️⃣ Run the app
python app.py


App will run at:
📌 http://127.0.0.1:5000

🧪 Prediction Flow

User enters medical data manually

OR uploads PDF/image

OCR extracts data

Model predicts

Clinical checks override extreme cases

Result saved into history 

🤝 Contributing

Pull requests are welcome!
For major changes, please open an issue first.

📜 License

This project is for educational purposes.
Free to use and modify.

💙 Author

Kamini Prajapati
HeartShield – Taking Care of Your Heart with AI ❤️

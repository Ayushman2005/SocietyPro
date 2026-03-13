<div align="center">
  <img src="https://img.icons8.com/color/96/000000/city-buildings.png" alt="SocietyPro Logo" width="100"/>
  <h1>🏙️ SocietyPro</h1>
  <p><strong>Smart Residential Management System</strong></p>

  <p>
    <a href="#-about-the-project">About The Project</a> •
    <a href="#-key-features">Key Features</a> •
    <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> •
    <a href="#-installation--setup">Setup</a> •
    <a href="#-future-roadmap">Future Roadmap</a>
  </p>

  <p>
    <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
    <img alt="Flask" src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
    <img alt="MySQL" src="https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white" />
    <img alt="HTML5" src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
    <img alt="CSS3" src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" />
    <img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
  </p>
</div>

---

## 📖 About The Project

**SocietyPro** is a comprehensive web-based application designed to streamline the daily operations of residential societies and apartments. Built with **Python (Flask)** and **MySQL**, it provides a seamless interface for administrators to manage funds, tenants, and bills, while offering residents a digital dashboard to track payments, lodge complaints, and participate in community activities.

Whether you're managing a single building or a large complex, SocietyPro digitizes the manual workload and fosters a better living environment through smart features.

---

## 👥 Meet The Team
This project was designed and developed by a dedicated team of Full Stack Developers:
* **Ayushman Kar** 
* **Satwik Barik** 
* **Nilamani Kundu** 

---

## 🚀 Key Features

### 🔐 For Administrators
- **Dashboard Overview:** Real-time metrics of total society funds, pending dues, and active complaints.
- **Tenant Management:** Easily onboard, edit, or remove residents/tenants from the system.
- **Automated Billing:** Create monthly maintenance bills for residents.
- **Professional PDF Exports:** Automatically generate and download PDF invoices for record-keeping.
- **Fund Management:** Manually log, update, and track the central society fund.
- **Complaint Resolution:** View resident complaints, manage workflows, and mark them as "Resolved" with color-coded status indicators.
- **Community Polls & Bookings:** Manage facility bookings and create polls to gather resident feedback.
- **Secure Authentication:** Captcha protection and OTP verification for admin login and password resets.

### 👤 For Residents (Users)
- **Personal Dashboard:** View outstanding dues, payment history, and account status at a glance.
- **Bill Payments:** Securely track "Paid" vs "Unpaid" status for monthly maintenance. *(Stripe integration ready)*
- **Helpdesk & Complaints:** Lodge complaints (e.g., Water, Electricity) directly to the admin and monitor resolution status.
- **Community Engagement:** Vote on active society polls and book shared facilities.
- **Gateway & Visitor Management:** Pre-approve visitors for enhanced gate security.
- **Profile Management:** Update personal contact details and secure passwords.

### 🌐 System-Wide Features
- **Responsive & Modern UI:** Optimized for all devices with Dark/Light theme support (Vibrant Orange & Dark aesthetics).
- **Asynchronous Email Notifications:** Automated, responsive HTML email alerts for contact inquiries, user boarding, and password resets via SMTP (using background threads for performance).
- **Cloud Database Support:** Seamlessly connect to remote cloud databases (e.g., Aiven) using SSL, with a graceful fallback to Local MySQL.
- **Security First:** Role-based access control (Admin vs. User), CSRF protection, and secure session management.

---

## 🛠️ Tech Stack

**Backend Engine:**
- Python (3.12 compatible)
- Flask Web Framework

**Database:**
- MySQL (Local or Cloud via Aiven)
- `mysql-connector-python`

**Frontend Integration:**
- HTML5, CSS3, & Vanilla JavaScript
- Jinja2 Templating Engine

**Key Libraries & APIs:**
- `reportlab` (Dynamic PDF Invoice Generation)
- `smtplib` & `email` (Automated Threaded HTML Emails)
- `stripe` (Payment Gateway Integration)
- `captcha` (Image Captcha generation)
- `werkzeug.security` (Password Hashing)

---

## ⚙️ Installation & Setup

Follow these simple steps to run the SocietyPro project locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/Ayushman2005/SocietyPro.git
cd SocietyPro
```

### 2. Set Up the Database
- Open MySQL Workbench or your preferred SQL client.
- Create a database named `society_db`.
- Import the provided `society_db.sql` file to scaffold the necessary tables (`users`, `admins`, `bills`, `complaints`, etc.).

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your credentials:
```env
# Local Database Config
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=society_db

# Cloud Database Config (Optional, e.g., Aiven)
CLOUD_DB_HOST=your_cloud_db_host
CLOUD_DB_PORT=your_cloud_db_port
CLOUD_DB_USER=your_cloud_db_user
CLOUD_DB_PASSWORD=your_cloud_db_password
CLOUD_DB_NAME=your_cloud_db_name
SSL_CA_PATH=ca.pem

# App Secrets
SECRET_KEY=your_super_secret_key

# Email Config
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# 3rd Party APIs
STRIPE_SECRET_KEY=your_stripe_secret_key
WEATHER_API_KEY=your_weather_api_key
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Application
```bash
python app.py
```
Open your web browser and visit: **http://127.0.0.1:5000** 🚀

---

## 🔮 Future Roadmap (Machine Learning)
We are actively working on integrating Machine Learning models to make SocietyPro even smarter:
- 🧠 **Smart Complaint Classifier:** Leveraging NLP to automatically categorize and route complaints (e.g., "Plumbing", "Electrical", "Security").
- 📊 **Late Payment Predictor:** A regression model to identify accounts at risk of defaulting on their dues based on payment history.

---

## 📄 License
This project was conceptualized and created for educational purposes. All rights reserved by the development team.
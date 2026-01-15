# 🏙️ SocietyPro - Smart Residential Management System

**SocietyPro** is a comprehensive web-based application designed to streamline the daily operations of residential societies. Built with **Python (Flask)** and **MySQL**, it provides a seamless interface for administrators to manage funds, tenants, and bills, while offering residents a digital dashboard to track payments and lodge complaints.

---

## 👥 Team Members
This project was designed and developed by:
* **Ayushman Kar** (Full Stack Developer)
* **Satwik Barik** (Full Stack Developer)
* **Nilamani Kundu** (Full Stack Developer)

---

## 🚀 Key Features

### 🔐 For Administrators
* **Dashboard Overview:** Real-time view of total society funds, pending dues, and active complaints.
* **Tenant Management:** Add, edit, or remove residents/tenants from the system.
* **Invoice Generation:** Create monthly maintenance bills for residents.
* **PDF Exports:** Automatically generate and download professional PDF invoices for record-keeping.
* **Fund Management:** Manually update and track the central society fund.
* **Complaint Resolution:** View resident complaints and mark them as "Resolved" with color-coded status indicators.

### 👤 For Residents (Users)
* **Personal Dashboard:** View outstanding dues, payment history, and account status.
* **Bill Payment:** Track "Paid" vs "Unpaid" status for monthly maintenance.
* **Complaint Portal:** Lodge complaints (e.g., Water, Electricity) directly to the admin.
* **Profile Management:** Update personal contact details and password.

### 🌐 General Features
* **Responsive Design:** Dark/Light theme support (Orange & Black UI).
* **Email Notifications:** Automated email alerts for contact inquiries via SMTP.
* **Secure Authentication:** Role-based login (Admin vs. User) with session management.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Flask Framework
* **Database:** MySQL
* **Frontend:** HTML5, CSS3, JavaScript, Jinja2 Templates
* **Libraries:**
    * `mysql-connector-python` (Database Connection)
    * `reportlab` (PDF Generation)
    * `smtplib` (Email Services)

---

## ⚙️ Installation & Setup

Follow these steps to run the project locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/Ayushman2005/SocietyPro.git](https://github.com/Ayushman2005/SocietyPro.git)
cd SocietyPro
```

### 2. Set Up the Database
* Open MySQL Workbench or your preferred SQL client.
* Create a database named society_db.
* Import the provided database.sql file to create the tables (users, admins, bills, complaints).
* Optional: Insert an admin user manually if not included in the SQL script:
```bash
INSERT INTO admins (email, password) VALUES ('admin@gmail.com', 'Admin@1234');
```

### 3. Configure Environment Variables
* Create a .env file in the root directory and add your credentials:
```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=society_db
SECRET_KEY=your_secret_key

# Email Config (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

### 4. Install Dependencies:
```bash
pip install -r requirements.txt
```
### 5. Run the Application
```bash
python app.py
```
Visit http://127.0.0.1:5000 in your browser.

---

### 🔮 Future Enhancements (Machine Learning)
We are actively working on integrating ML models to make SocietyPro smarter:
* Smart Complaint Classifier: Using NLP to automatically tag complaints (e.g., "Plumbing", "Electrical").
* Late Payment Predictor: A regression model to identify accounts at risk of defaulting on dues.

---

### 📄 License
* This project is created for educational purposes. All rights reserved by the team members listed above.

---
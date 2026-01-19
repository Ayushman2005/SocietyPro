from flask import (
    Flask, render_template, request, redirect,
    session, url_for, send_file
)
import mysql.connector
import os
import io
import smtplib
import random
from datetime import date
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "society_secret_key")

csrf = CSRFProtect(app)

db_config = {
    "host": os.getenv("DB_HOST", ""),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "")
}

# ======================================================
# DATABASE CONNECTION
# ======================================================


def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"❌ Database Connection Error: {err}")
        return None

# ======================================================
# HOME PAGES
# ======================================================


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/login")
def login_page():
    return render_template("page.html")

# ======================================================
# ADMIN REGISTER
# ======================================================


@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        society_name = request.form["society_name"]  # <--- Get the Society Name
        password = generate_password_hash(request.form["password"])

        db = get_db_connection()
        cur = db.cursor()

        cur.execute("SELECT id FROM admins WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            db.close()
            return "Admin already exists ❌"

        # <--- Update INSERT query to include society_name
        cur.execute(
            "INSERT INTO admins (name, email, password, society_name) VALUES (%s, %s, %s, %s)",
            (name, email, password, society_name)
        )
        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/login")

    return render_template("admin_register.html")

# ======================================================
# ADMIN LOGIN
# ======================================================


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("SELECT id, password FROM admins WHERE email=%s", (email,))
        admin = cur.fetchone()
        cur.close()
        db.close()

        if admin and check_password_hash(admin[1], password):
            session.clear()
            session["admin"] = admin[0]
            return redirect("/admin/dashboard")

        return "Invalid Admin Credentials ❌"

    return render_template("admin_login.html")

# ======================================================
# USER REGISTER
# ======================================================


@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db_connection()
        cur = db.cursor()

        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return "Email already registered ❌"

        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, password)
        )

        user_id = cur.lastrowid
        cur.execute(
            "INSERT INTO bills (user_id, amount, status) VALUES (%s, 0, 'Paid')",
            (user_id,)
        )

        db.commit()
        cur.close()
        db.close()

        return redirect("/user/login")

    return render_template("user_register.html")

# ======================================================
# USER LOGIN
# ======================================================


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        db.close()

        if user and check_password_hash(user[1], password):
            session.clear()
            session["user"] = user[0]
            return redirect("/user/dashboard")

        return "Invalid User Credentials ❌"

    return render_template("user_login.html")

# ======================================================
# FORGOT PASSWORD
# ======================================================


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    msg = ""
    if request.method == "POST":
        email = request.form["email"]
        
        db = get_db_connection()
        cur = db.cursor()
        
        # Check if email exists in EITHER Admin or User table
        cur.execute("SELECT id FROM admins WHERE email=%s", (email,))
        admin = cur.fetchone()
        
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        
        if admin or user:
            # Generate 6-Digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Save OTP to DB (Update if exists, Insert if new)
            cur.execute("REPLACE INTO password_resets (email, otp) VALUES (%s, %s)", (email, otp))
            db.commit()
            
            # --- SECURITY LOG (Simulating Email Sending) ---
            print(f"\n[EMAIL SIMULATION] 📧 To: {email} | Subject: Password Reset | Body: Your OTP is {otp}\n")
            
            cur.close()
            db.close()
            
            # Send user to Step 2
            return render_template("verify_otp.html", email=email, msg="✅ OTP sent! Check your email (or terminal).")
        
        else:
            msg = "❌ Email not found in our records."
            cur.close()
            db.close()

    return render_template("forgot_password.html", msg=msg)

# ======================================================
# 2. VERIFY & RESET ROUTE (Step 2)
# ======================================================
@app.route("/reset_password", methods=["POST"])
def reset_password():
    email = request.form["email"]
    otp_input = request.form["otp"]
    new_password = request.form["new_password"]
    
    db = get_db_connection()
    cur = db.cursor()
    
    # Verify OTP
    cur.execute("SELECT otp FROM password_resets WHERE email=%s", (email,))
    record = cur.fetchone()
    
    if record and record[0] == otp_input:
        # OTP Valid: Hash new password
        hashed_pw = generate_password_hash(new_password)
        
        # Update Password (Try updating both tables)
        cur.execute("UPDATE admins SET password=%s WHERE email=%s", (hashed_pw, email))
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
        
        # Cleanup: Delete used OTP
        cur.execute("DELETE FROM password_resets WHERE email=%s", (email,))
        db.commit()
        
        cur.close()
        db.close()
        return render_template("page.html") # Redirect to Role Selection
    
    else:
        cur.close()
        db.close()
        return render_template("verify_otp.html", email=email, msg="❌ Invalid or Expired OTP")
# ======================================================
# PROFILE UPDATE
# ======================================================


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "admin" not in session and "user" not in session:
        return redirect("/")

    role = "admin" if "admin" in session else "user"
    user_id = session[role]
    table = "admins" if role == "admin" else "users"

    db = get_db_connection()
    cur = db.cursor()
    msg = ""

    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        cur.execute(
            f"UPDATE {table} SET email=%s, password=%s WHERE id=%s",
            (email, password, user_id)
        )
        db.commit()
        msg = "✅ Profile updated"

    cur.execute(f"SELECT email FROM {table} WHERE id=%s", (user_id,))
    data = cur.fetchone()

    cur.close()
    db.close()

    return render_template("profile.html", user=data, role=role, msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- ADMIN DASHBOARD (Modified) ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()

    # 1. Fetch Fund SPECIFIC to this Admin
    cur.execute("SELECT amount FROM society_fund WHERE admin_id = %s", (admin_id,))
    fund_row = cur.fetchone()
    
    if fund_row:
        total_fund = fund_row[0]
    else:
        # Create a wallet for this admin if it doesn't exist
        cur.execute("INSERT INTO society_fund (admin_id, amount) VALUES (%s, 0)", (admin_id,))
        db.commit()
        total_fund = 0

    # 2. Fetch Bills (Only for users belonging to this Admin)
    # We join tables and filter by u.admin_id
    query_bills = """
        SELECT b.id, u.email, b.amount, b.status 
        FROM bills b 
        JOIN users u ON b.user_id = u.id 
        WHERE u.admin_id = %s
    """
    cur.execute(query_bills, (admin_id,))
    bills = cur.fetchall()

    # 3. Fetch Users (Only this Admin's tenants) for the "Create Bill" dropdown
    cur.execute("SELECT id, name FROM users WHERE admin_id = %s", (admin_id,))
    users = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin_dashboard.html", bills=bills, users=users, total_fund=total_fund)
# ---------- ADMIN: VISITOR LOGS ----------

@app.route("/admin/visitors")
def admin_visitors():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()

    # SECURE QUERY: Join users to filter by admin_id
    query = """
        SELECT v.id, v.name, v.phone, v.visit_date, v.visit_time, v.status, u.email 
        FROM visitors v 
        JOIN users u ON v.user_id = u.id 
        WHERE u.admin_id = %s  -- <--- THE FIX
        ORDER BY v.visit_date DESC
    """
    cur.execute(query, (admin_id,))
    visitors = cur.fetchall()
    
    cur.close()
    db.close()
    return render_template("admin_visitors.html", visitors=visitors)
# ---------- ADMIN: MANAGE POLLS ----------
@app.route("/admin/polls", methods=["GET", "POST"])
def admin_polls():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()

    # Create Poll (Save with admin_id)
    if request.method == "POST":
        question = request.form["question"]
        opt1 = request.form["option1"]
        opt2 = request.form["option2"]
        
        cur.execute(
            "INSERT INTO polls (question, option1, option2, admin_id) VALUES (%s, %s, %s, %s)", 
            (question, opt1, opt2, admin_id)
        )
        db.commit()

    # Fetch Polls (Only for this Admin)
    query = """
        SELECT p.id, p.question, p.option1, p.option2, p.status,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.choice = 'option1') as vote1,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.choice = 'option2') as vote2
        FROM polls p 
        WHERE p.admin_id = %s -- <--- THE FIX
        ORDER BY p.id DESC
    """
    cur.execute(query, (admin_id,))
    polls = cur.fetchall()

    cur.close()
    db.close()
    return render_template("admin_polls.html", polls=polls)

# ---------- ADMIN: BOOKING REQUESTS ----------


@app.route("/admin/bookings")
def admin_bookings():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()

    # SECURE QUERY: Filter bookings by the admin's residents
    query = """
        SELECT b.id, b.facility_name, b.booking_date, b.time_slot, b.status, u.email 
        FROM bookings b 
        JOIN users u ON b.user_id = u.id 
        WHERE u.admin_id = %s -- <--- THE FIX
        ORDER BY b.booking_date DESC
    """
    cur.execute(query, (admin_id,))
    bookings = cur.fetchall()
    
    cur.close()
    db.close()
    return render_template("admin_bookings.html", bookings=bookings)
# ---------- UPDATE FUND ROUTE (New) ----------
@app.route("/admin/update_fund", methods=["POST"])
def update_fund():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    new_amount = request.form["amount"]

    db = get_db_connection()
    cur = db.cursor()
    
    # Update only THIS admin's fund
    cur.execute("UPDATE society_fund SET amount = %s WHERE admin_id = %s", (new_amount, admin_id))
    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")
@app.route("/admin/delete_bill/<int:bill_id>", methods=["POST"]) 
def delete_bill(bill_id):
    if "admin" not in session:
        return redirect("/admin/login")

    try:
        db = get_db_connection()
        cur = db.cursor()

        # SQL Command to delete the specific bill
        cur.execute("DELETE FROM bills WHERE id = %s", (bill_id,))

        db.commit()
        cur.close()
        db.close()
    except Exception as e:
        print(f"Error deleting bill: {e}")

    return redirect("/admin/dashboard")
# ---------- ADMIN: TENANTS ----------
@app.route("/admin/tenants", methods=["GET", "POST"])
def admin_tenants():
    if "admin" not in session:
        return redirect("/admin/login")
    
    admin_id = session["admin"] # <--- Get Current Admin ID
    db = get_db_connection()
    
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        
        try:
            cur = db.cursor()
            # SAVE WITH ADMIN ID
            cur.execute(
                "INSERT INTO users (name, email, password, admin_id) VALUES (%s, %s, %s, %s)", 
                (name, email, password, admin_id)
            )
            
            # Create default bill
            user_id = cur.lastrowid
            cur.execute("INSERT INTO bills (user_id, amount, status) VALUES (%s, 0, 'Paid')", (user_id,))
            
            db.commit()
            cur.close()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    # FILTER TENANTS BY ADMIN ID
    cur = db.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE admin_id = %s ORDER BY id DESC", (admin_id,))
    tenants = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin_tenants.html", tenants=tenants)
# ---------- ADMIN: DELETE TENANT ----------


@app.route("/admin/delete_tenant/<int:user_id>", methods=["POST"])
def delete_tenant(user_id):
    if "admin" not in session:
        return redirect("/admin/login")

    try:
        db = get_db_connection()
        cur = db.cursor()

        # 1. First delete all bills associated with this user (to prevent errors)
        cur.execute("DELETE FROM bills WHERE user_id = %s", (user_id,))

        # 2. Then delete the user
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

        db.commit()
        cur.close()
        db.close()
    except Exception as e:
        print(f"Error deleting tenant: {e}")

    return redirect("/admin/tenants")

# ---------- ADMIN: EDIT TENANT ----------
@app.route("/admin/edit_tenant", methods=["POST"])
def edit_tenant():
    if "admin" not in session:
        return redirect("/admin/login")

    user_id = request.form["user_id"]
    name = request.form["name"]
    email = request.form["email"]
    password_input = request.form["password"]

    db = get_db_connection()
    cur = db.cursor()

    if password_input.strip():
        # If admin entered a new password, hash it and update everything
        hashed_pw = generate_password_hash(password_input)
        cur.execute(
            "UPDATE users SET name=%s, email=%s, password=%s WHERE id=%s",
            (name, email, hashed_pw, user_id)
        )
    else:
        # If password field left blank, only update details
        cur.execute(
            "UPDATE users SET name=%s, email=%s WHERE id=%s",
            (name, email, user_id)
        )

    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/tenants")
# ---------- ADMIN: INVOICES ----------
@app.route("/admin/invoices")
def admin_invoices():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()
    
    # Filter bills by joining users and checking admin_id
    query = """
        SELECT bills.id, users.email, bills.amount, bills.status 
        FROM bills 
        JOIN users ON bills.user_id = users.id
        WHERE users.admin_id = %s
        ORDER BY bills.id DESC
    """
    cur.execute(query, (admin_id,))
    invoices = cur.fetchall()
    
    cur.close()
    db.close()
    return render_template("admin_invoices.html", invoices=invoices)

# ---------- ADMIN: SETTINGS ----------


@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if "admin" not in session:
        return redirect("/admin/login")

    msg = ""
    if request.method == "POST":
        new_password = request.form["new_password"]
        admin_id = session["admin"]

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("UPDATE admins SET password=%s WHERE id=%s",
                    (new_password, admin_id))
        db.commit()
        cur.close()
        db.close()
        msg = "Password updated successfully!"

    return render_template("admin_settings.html", msg=msg)

# ---------- ADD BILL ----------


@app.route("/admin/add_bill", methods=["POST"])
def add_bill():
    if "admin" not in session:
        return redirect("/admin/login")

    user_id = request.form["user_id"]
    amount = request.form["amount"]

    db = get_db_connection()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO bills (user_id, amount, status) VALUES (%s, %s, 'Unpaid')", (user_id, amount))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/dashboard")

# ---------- USER DASHBOARD ----------


@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect("/user/login")

    user_id = session["user"]
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT amount, status FROM bills WHERE user_id=%s", (user_id,))
    bills = cur.fetchall()
    cur.close()
    db.close()

    return render_template("user_dashboard.html", bills=bills)
# ---------- ADMIN: MANAGE NOTICES ----------


@app.route("/admin/notices", methods=["GET", "POST"])
def admin_notices():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        # Save with Admin ID
        cur.execute("INSERT INTO notices (title, content, admin_id) VALUES (%s, %s, %s)", 
                    (title, content, admin_id))
        db.commit()

    # Fetch only this Admin's notices
    cur.execute("SELECT id, title, content, DATE_FORMAT(created_at, '%d %b %Y') FROM notices WHERE admin_id = %s ORDER BY id DESC", (admin_id,))
    notices = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin_notices.html", notices=notices)

@app.route("/admin/edit_notice", methods=["POST"])
def edit_notice():
    if "admin" not in session:
        return redirect("/admin/login")

    notice_id = request.form["notice_id"]
    title = request.form["title"]
    content = request.form["content"]

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE notices SET title=%s, content=%s WHERE id=%s",
                (title, content, notice_id))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/notices")


@app.route("/admin/delete_notice/<int:id>")
def delete_notice(id):
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("DELETE FROM notices WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/notices")

# ---------- USER: VIEW NOTICES ----------


@app.route("/user/notices")
def user_notices():
    if "user" not in session:
        return redirect("/user/login")

    db = get_db_connection()
    cur = db.cursor()
    cur.execute(
        "SELECT title, content, DATE_FORMAT(created_at, '%d %b %Y') as date FROM notices ORDER BY id DESC")
    notices = cur.fetchall()
    cur.close()
    db.close()

    return render_template("user_notices.html", notices=notices)
# ---------- DOWNLOAD INVOICE PDF ----------


@app.route("/admin/download_invoice/<int:bill_id>")
def download_invoice(bill_id):
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()
    query = """
        SELECT bills.id, bills.amount, bills.status, users.email 
        FROM bills JOIN users ON bills.user_id = users.id 
        WHERE bills.id = %s
    """
    cur.execute(query, (bill_id,))
    bill = cur.fetchone()
    cur.close()
    db.close()

    if not bill:
        return "Invoice not found", 404

    invoice_id, amount, status, user_email = bill
    today_date = date.today().strftime("%B %d, %Y")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFillColor(colors.HexColor("#ff8c00"))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 60, "Society Management System")

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "Sector 62, Noida, India - 201309")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(width - 50, height - 140, "INVOICE")

    c.setFont("Helvetica", 12)
    c.drawRightString(width - 50, height - 160, f"#{invoice_id:04d}")
    c.drawRightString(width - 50, height - 175, f"Date: {today_date}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 160, "Bill To:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 175, user_email)

    data = [
        ["Description", "Amount (INR)"],
        ["Monthly Society Maintenance", f"Rs. {amount:,.2f}"],
        ["Late Fees", "Rs. 0.00"],
        ["TOTAL", f"Rs. {amount:,.2f}"]
    ]

    table = Table(data, colWidths=[400, 100])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor(
            "#333333")),  # Header Dark Gray
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Description Align Left
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1),
         colors.HexColor("#ff8c00")),  # Total Row Orange
        ('GRID', (0, 0), (-1, -2), 1, colors.black)
    ])
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 350)

    if status == "Paid":
        c.saveState()
        c.translate(width/2, height/2)
        c.rotate(45)
        c.setFillColorRGB(0, 1, 0, 0.3)
        c.setFont("Helvetica-Bold", 80)
        c.drawCentredString(0, 0, "PAID")
        c.restoreState()
    else:
        c.saveState()
        c.translate(width/2, height/2)
        c.rotate(45)
        c.setFillColorRGB(1, 0, 0, 0.1)
        c.setFont("Helvetica-Bold", 80)
        c.drawCentredString(0, 0, "UNPAID")
        c.restoreState()

    c.showPage()
    c.save()

    buffer.seek(0)
    from flask import send_file
    return send_file(buffer, as_attachment=True, download_name=f"Invoice_{invoice_id}.pdf", mimetype='application/pdf')


# 2. USER: COMPLAINTS
@app.route("/user/complaints", methods=["GET", "POST"])
def user_complaints():
    if "user" not in session:
        return redirect("/user/login")

    user_id = session["user"]
    db = get_db_connection()
    cur = db.cursor()

    # Handle New Complaint Submission
    if request.method == "POST":
        subject = request.form["subject"]
        description = request.form["description"]
        cur.execute("INSERT INTO complaints (user_id, subject, description) VALUES (%s, %s, %s)",
                    (user_id, subject, description))
        db.commit()

    # Fetch User's Complaints
    cur.execute(
        "SELECT subject, description, status, created_at FROM complaints WHERE user_id = %s ORDER BY id DESC", (user_id,))
    my_complaints = cur.fetchall()

    cur.close()
    db.close()
    return render_template("user_complaints.html", complaints=my_complaints)


# ---------- ADMIN: COMPLAINTS ----------
@app.route("/admin/complaints", methods=["GET", "POST"])
def admin_complaints():
    if "admin" not in session:
        return redirect("/admin/login")

    admin_id = session["admin"]
    db = get_db_connection()
    cur = db.cursor()

    # Handle "Mark Resolved"
    if request.method == "POST":
        complaint_id = request.form["complaint_id"]
        status = request.form["status"]
        cur.execute("UPDATE complaints SET status=%s WHERE id=%s", (status, complaint_id))
        db.commit()
        return redirect("/admin/complaints")

    # Fetch Complaints (Filtered)
    query = """
        SELECT c.id, u.email, c.subject, c.description, c.status, 
               DATE_FORMAT(c.created_at, '%d %b %Y') as date
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE u.admin_id = %s -- <--- THE FIX
        ORDER BY c.status ASC, c.created_at DESC
    """
    cur.execute(query, (admin_id,))
    complaints = cur.fetchall()

    cur.close()
    db.close()
    return render_template("admin_complaints.html", complaints=complaints)
@app.route('/dashboard')
def dashboard():
    # 1. Connect to database using your existing function
    db = get_db_connection()
    if not db:
        return "Database Error"

    cur = db.cursor()

    # 2. Use Raw SQL to sum the 'amount' column from the 'bills' table
    cur.execute("SELECT SUM(amount) FROM bills")
    result = cur.fetchone()

    cur.close()
    db.close()

    # 3. Handle the result (result[0] will be None if table is empty)
    total_fund = result[0] if result[0] else 0

    return render_template('dashboard.html', total_fund=total_fund)
# ---------- VISITOR GATE PASS ----------


@app.route("/user/visitors", methods=["GET", "POST"])
def user_visitors():
    if "user" not in session:
        return redirect("/user/login")
    user_id = session["user"]
    db = get_db_connection()
    cur = db.cursor()

    # Handle New Visitor Submission
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        date = request.form["date"]
        time = request.form["time"]
        cur.execute("INSERT INTO visitors (user_id, name, phone, visit_date, visit_time) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, name, phone, date, time))
        db.commit()

    # Fetch My Visitors
    cur.execute(
        "SELECT name, phone, visit_date, visit_time, status FROM visitors WHERE user_id=%s ORDER BY id DESC", (user_id,))
    visitors = cur.fetchall()

    cur.close()
    db.close()
    return render_template("user_visitors.html", visitors=visitors)
# ---------- POLLS & VOTING ----------


@app.route("/user/polls", methods=["GET", "POST"])
def user_polls():
    if "user" not in session:
        return redirect("/user/login")
    user_id = session["user"]
    db = get_db_connection()
    cur = db.cursor()

    # Handle Voting
    if request.method == "POST":
        poll_id = request.form["poll_id"]
        choice = request.form["choice"]  # 'option1' or 'option2'

        # Check if already voted
        cur.execute(
            "SELECT id FROM poll_votes WHERE user_id=%s AND poll_id=%s", (user_id, poll_id))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO poll_votes (user_id, poll_id, choice) VALUES (%s, %s, %s)", (user_id, poll_id, choice))
            db.commit()

    # Fetch Polls and Calculate Results
    # This complex query counts votes for option1 and option2 for each poll
    query = """
        SELECT p.id, p.question, p.option1, p.option2, p.status,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.choice = 'option1') as vote1,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.choice = 'option2') as vote2,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.user_id = %s) as has_voted
        FROM polls p ORDER BY p.id DESC
    """
    cur.execute(query, (user_id,))
    polls = cur.fetchall()

    cur.close()
    db.close()
    return render_template("user_polls.html", polls=polls)
# ---------- AMENITY BOOKING ----------


@app.route("/user/bookings", methods=["GET", "POST"])
def user_bookings():
    if "user" not in session:
        return redirect("/user/login")
    user_id = session["user"]

    # Define available facilities and slots
    facilities = ["Community Hall", "Clubhouse",
                  "Tennis Court", "Swimming Pool Area"]
    slots = ["Morning (9 AM - 1 PM)", "Afternoon (2 PM - 6 PM)",
             "Evening (7 PM - 11 PM)"]

    error = None
    success = None

    db = get_db_connection()
    cur = db.cursor()

    # Handle New Booking Submission
    if request.method == "POST":
        facility = request.form["facility"]
        date = request.form["date"]
        slot = request.form["slot"]

        # 1. Check if slot is already taken
        check_query = "SELECT id FROM bookings WHERE facility_name=%s AND booking_date=%s AND time_slot=%s AND status='Confirmed'"
        cur.execute(check_query, (facility, date, slot))
        existing_booking = cur.fetchone()

        if existing_booking:
            error = f"Sorry! The {facility} is already booked for that slot."
        else:
            # 2. Book it if free
            insert_query = "INSERT INTO bookings (user_id, facility_name, booking_date, time_slot, status) VALUES (%s, %s, %s, %s, 'Pending')"
            cur.execute(insert_query, (user_id, facility, date, slot))
            db.commit()
            success = "Booking Request Sent! Awaiting Admin Approval."

    # Fetch My Bookings (To show history)
    cur.execute("SELECT facility_name, booking_date, time_slot, status FROM bookings WHERE user_id=%s ORDER BY booking_date DESC", (user_id,))
    my_bookings = cur.fetchall()

    cur.close()
    db.close()

    return render_template("user_bookings.html",
                           facilities=facilities,
                           slots=slots,
                           my_bookings=my_bookings,
                           error=error,
                           success=success)

# ---------- ADMIN: HANDLE BOOKING ACTIONS ----------


@app.route("/admin/booking_action", methods=["POST"])
def booking_action():
    if "admin" not in session:
        return redirect("/admin/login")

    # Get data from the form body, not the URL
    booking_id = request.form.get("id")
    action = request.form.get("action")

    new_status = "Confirmed" if action == "approve" else "Rejected"

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE bookings SET status = %s WHERE id = %s", (new_status, booking_id))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/bookings")
# ---------- USER: EMERGENCY CONTACTS ----------


@app.route("/user/emergency")
def user_emergency():
    if "user" not in session:
        return redirect("/user/login")

    contacts = [
        # Red = Critical Emergency
        {"name": "Police Station", "role": "Emergency", "phone": "100",
            "icon": "ri-alarm-warning-fill", "theme": "red"},
        {"name": "Fire Brigade", "role": "Emergency",
            "phone": "101", "icon": "ri-fire-fill", "theme": "red"},
        {"name": "Ambulance", "role": "Medical", "phone": "102",
            "icon": "ri-first-aid-kit-fill", "theme": "red"},

        # Green = Security
        {"name": "Main Gate Security", "role": "Security", "phone": "+91 98765 43210",
            "icon": "ri-shield-star-fill", "theme": "green"},

        # Blue = Admin/Office
        {"name": "Society Office", "role": "Admin", "phone": "0120-456-7890",
            "icon": "ri-building-2-fill", "theme": "blue"},

        # Orange = Maintenance
        {"name": "Electrician", "role": "Maintenance", "phone": "+91 91234 56789",
            "icon": "ri-lightbulb-flash-fill", "theme": "orange"},
        {"name": "Plumber", "role": "Maintenance", "phone": "+91 99887 76655",
            "icon": "ri-drop-fill", "theme": "orange"},
    ]

    return render_template("user_emergency.html", contacts=contacts)
# ---------- LOGOUT ----------



@app.route("/submit_contact", methods=["POST"])
def submit_contact():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    try:
        db = get_db_connection()
        if db:
            cur = db.cursor()
            query = "INSERT INTO contact_inquiries (name, email, message) VALUES (%s, %s, %s)"
            cur.execute(query, (name, email, message))
            db.commit()
            cur.close()
            db.close()
    except Exception as e:
        print(f"Database Error: {e}")

    # 2. Send Email Notification
    try:
        # Email Credentials
        smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        sender_email = os.getenv("MAIL_USERNAME")
        password = os.getenv("MAIL_PASSWORD")
        receiver_email = sender_email  # Sending to yourself

        # Create Message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = f"New Inquiry from {name}"

        body = f"""
        New Inquiry Received!
        ---------------------
        Name: {name}
        Email: {email}
        
        Message:
        {message}
        """
        msg.attach(MIMEText(body, "plain"))

        # Connect to Server and Send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()

        print("✅ Email notification sent successfully!")

    except Exception as e:
        print(f"❌ Email Error: {e}")

    # Redirect back to home
    return redirect("/#contact")


if __name__ == "__main__":
    app.run(debug=True)

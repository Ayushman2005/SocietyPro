from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "")

db_config = {
    "host": os.getenv("DB_HOST", ""),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "")
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"❌ Database Connection Error: {err}")
        return None

# ---------- HOME ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("page.html")

# ---------- ADMIN LOGIN ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        if not db: return "Database Error"
        
        cur = db.cursor()
        cur.execute("SELECT id FROM admins WHERE email=%s AND password=%s", (email, password))
        admin = cur.fetchone()
        cur.close()
        db.close()

        if admin:
            session.clear()  # <--- ADD THIS LINE HERE
            session["admin"] = admin[0]
            return redirect("/admin/dashboard")
        return "Invalid Admin Credentials ❌"

    return render_template("admin_login.html")
# ---------- USER LOGIN (FIXED) ----------
@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        if not db: return "Database Error"

        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()
        db.close()

        if user:
            session.clear()
            session["user"] = user[0]
            return redirect("/user/dashboard")
        return "Invalid User Credentials ❌"

    return render_template("user_login.html")

# ---------- REGISTER PAGE (MODIFIED FOR SECURITY) ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # SECURITY FIX: Force role to always be 'user'
        # Do not let the form decide the role!
        role = "user" 

        try:
            db = get_db_connection()
            cur = db.cursor()

            # We only check/insert into the 'users' table now
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return "Error: Email already registered!"

            cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            
            # Create the initial bill for the new user
            new_user_id = cur.lastrowid
            cur.execute("INSERT INTO bills (user_id, amount, status) VALUES (%s, 0, 'Paid')", (new_user_id,))
            
            db.commit()
            cur.close()
            db.close()

            return redirect("/user/login")

        except mysql.connector.Error as err:
            return f"Database Error: {err}"

    return render_template("register.html")
# ---------- ADMIN DASHBOARD (Modified) ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session: return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()
    
    # 1. Fetch the Manual Fund Amount
    cur.execute("SELECT amount FROM society_fund WHERE id = 1")
    fund_row = cur.fetchone()
    total_fund = fund_row[0] if fund_row else 0

    # 2. Fetch Bills & Users (Your existing code)
    cur.execute("SELECT bills.id, users.email, bills.amount, bills.status FROM bills JOIN users ON bills.user_id = users.id")
    bills = cur.fetchall()

    cur.execute("SELECT id, email FROM users")
    users = cur.fetchall()

    cur.close()
    db.close()

    # Pass 'total_fund' to the template
    return render_template("admin_dashboard.html", bills=bills, users=users, total_fund=total_fund)

# ---------- UPDATE FUND ROUTE (New) ----------
@app.route("/admin/update_fund", methods=["POST"])
def update_fund():
    if "admin" not in session: return redirect("/admin/login")
    
    new_amount = request.form["amount"]
    
    db = get_db_connection()
    cur = db.cursor()
    
    # Update the fund value in the database
    cur.execute("UPDATE society_fund SET amount = %s WHERE id = 1", (new_amount,))
    db.commit()
    
    cur.close()
    db.close()
    
    return redirect("/admin/dashboard")
@app.route("/admin/delete_bill/<int:bill_id>")
def delete_bill(bill_id):
    if "admin" not in session: return redirect("/admin/login")

    try:
        db = get_db_connection()
        cur = db.cursor()
        
        # SQL Command to delete the specific bill from the database
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
    if "admin" not in session: return redirect("/admin/login")
    
    db = get_db_connection()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            cur = db.cursor()
            cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            db.commit()
            cur.close()
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    cur = db.cursor()
    cur.execute("SELECT id, email FROM users")
    tenants = cur.fetchall()
    cur.close()
    db.close()
    
    return render_template("admin_tenants.html", tenants=tenants)
# ---------- ADMIN: DELETE TENANT ----------
@app.route("/admin/delete_tenant/<int:user_id>")
def delete_tenant(user_id):
    if "admin" not in session: return redirect("/admin/login")
    
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
    if "admin" not in session: return redirect("/admin/login")
    
    user_id = request.form["user_id"]
    email = request.form["email"]
    password = request.form["password"]
    
    db = get_db_connection()
    cur = db.cursor()
    
    # Update email and password
    cur.execute("UPDATE users SET email=%s, password=%s WHERE id=%s", (email, password, user_id))
    
    db.commit()
    cur.close()
    db.close()
    
    return redirect("/admin/tenants")
# ---------- ADMIN: INVOICES ----------
@app.route("/admin/invoices")
def admin_invoices():
    if "admin" not in session: return redirect("/admin/login")
    
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT bills.id, users.email, bills.amount, bills.status 
        FROM bills JOIN users ON bills.user_id = users.id
        ORDER BY bills.id DESC
    """)
    invoices = cur.fetchall()
    cur.close()
    db.close()
    
    return render_template("admin_invoices.html", invoices=invoices)

# ---------- ADMIN: SETTINGS ----------
@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if "admin" not in session: return redirect("/admin/login")
    
    msg = ""
    if request.method == "POST":
        new_password = request.form["new_password"]
        admin_id = session["admin"]
        
        db = get_db_connection()
        cur = db.cursor()
        cur.execute("UPDATE admins SET password=%s WHERE id=%s", (new_password, admin_id))
        db.commit()
        cur.close()
        db.close()
        msg = "Password updated successfully!"
        
    return render_template("admin_settings.html", msg=msg)

# ---------- ADD BILL ----------
@app.route("/admin/add_bill", methods=["POST"])
def add_bill():
    if "admin" not in session: return redirect("/admin/login")

    user_id = request.form["user_id"]
    amount = request.form["amount"]

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("INSERT INTO bills (user_id, amount, status) VALUES (%s, %s, 'Unpaid')", (user_id, amount))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/dashboard")

# ---------- USER DASHBOARD ----------
@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session: return redirect("/user/login")

    user_id = session["user"]
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT amount, status FROM bills WHERE user_id=%s", (user_id,))
    bills = cur.fetchall()
    cur.close()
    db.close()

    return render_template("user_dashboard.html", bills=bills)

# ---------- DOWNLOAD INVOICE PDF ----------
@app.route("/admin/download_invoice/<int:bill_id>")
def download_invoice(bill_id):
    if "admin" not in session: return redirect("/admin/login")

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

    if not bill: return "Invoice not found", 404

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
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#333333")), # Header Dark Gray
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'), # Description Align Left
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#ff8c00")), # Total Row Orange
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
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    msg = ""
    if request.method == "POST":
        email = request.form["email"]
        new_pass = request.form["new_password"]
        role = request.form["role"] # 'user' or 'admin'
        
        table = "admins" if role == "admin" else "users"
        
        db = get_db_connection()
        cur = db.cursor()
        
        # Check if email exists
        cur.execute(f"SELECT id FROM {table} WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user:
            # Update Password
            cur.execute(f"UPDATE {table} SET password = %s WHERE email = %s", (new_pass, email))
            db.commit()
            msg = "✅ Password reset successful! You can login now."
        else:
            msg = "❌ Email not found in our records."
            
        cur.close()
        db.close()
        
    return render_template("forgot_password.html", msg=msg)


# 2. USER: COMPLAINTS
@app.route("/user/complaints", methods=["GET", "POST"])
def user_complaints():
    if "user" not in session: return redirect("/user/login")
    
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
    cur.execute("SELECT subject, description, status, created_at FROM complaints WHERE user_id = %s ORDER BY id DESC", (user_id,))
    my_complaints = cur.fetchall()
    
    cur.close()
    db.close()
    return render_template("user_complaints.html", complaints=my_complaints)


# 3. ADMIN: COMPLAINTS MANAGEMENT
@app.route("/admin/complaints", methods=["GET", "POST"])
def admin_complaints():
    if "admin" not in session: return redirect("/admin/login")
    
    db = get_db_connection()
    cur = db.cursor()
    
    # Handle Status Update (Resolve)
    if request.method == "POST":
        complaint_id = request.form["complaint_id"]
        status = request.form["status"]
        cur.execute("UPDATE complaints SET status = %s WHERE id = %s", (status, complaint_id))
        db.commit()
    
    # Fetch All Complaints with User Info
    cur.execute("""
        SELECT complaints.id, users.email, complaints.subject, complaints.description, complaints.status, complaints.created_at 
        FROM complaints 
        JOIN users ON complaints.user_id = users.id 
        ORDER BY complaints.id DESC
    """)
    all_complaints = cur.fetchall()
    
    cur.close()
    db.close()
    return render_template("admin_complaints.html", complaints=all_complaints)


# 4. PROFILE EDITING (Both User & Admin)
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session and "admin" not in session:
        return redirect("/")
        
    role = "admin" if "admin" in session else "user"
    user_id = session[role]
    table = "admins" if role == "admin" else "users"
    
    db = get_db_connection()
    cur = db.cursor()
    
    msg = ""
    
    if request.method == "POST":
        new_email = request.form["email"]
        new_pass = request.form["password"]
        
        try:
            cur.execute(f"UPDATE {table} SET email=%s, password=%s WHERE id=%s", (new_email, new_pass, user_id))
            db.commit()
            msg = "✅ Profile updated successfully!"
        except mysql.connector.Error:
            msg = "❌ Error: Email might already be taken."
            
    # Fetch current details
    cur.execute(f"SELECT email, password FROM {table} WHERE id=%s", (user_id,))
    data = cur.fetchone()
    
    cur.close()
    db.close()
    
    return render_template("profile.html", user=data, role=role, msg=msg)
@app.route('/dashboard')
def dashboard():
    # 1. Connect to database using your existing function
    db = get_db_connection()
    if not db: return "Database Error"

    cur = db.cursor()
    
    # 2. Use Raw SQL to sum the 'amount' column from the 'bills' table
    cur.execute("SELECT SUM(amount) FROM bills")
    result = cur.fetchone()
    
    cur.close()
    db.close()

    # 3. Handle the result (result[0] will be None if table is empty)
    total_fund = result[0] if result[0] else 0

    return render_template('dashboard.html', total_fund=total_fund)
# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
# ---------- CONTACT FORM SUBMISSION (WITH EMAIL) ----------
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
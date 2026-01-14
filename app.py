from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io
from datetime import date
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "society_secret_key")

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
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
            session["admin"] = admin[0]
            return redirect("/admin/dashboard")
        return "Invalid Admin Credentials ❌"

    return render_template("admin_login.html")

# ---------- USER LOGIN ----------
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
            session["user"] = user[0]
            return redirect("/user/dashboard")
        return "Invalid User Credentials ❌"

    return render_template("user_login.html")

# ---------- REGISTER PAGE ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        try:
            db = get_db_connection()
            cur = db.cursor()

            table = "admins" if role == "admin" else "users"

            cur.execute(f"SELECT id FROM {table} WHERE email = %s", (email,))
            if cur.fetchone():
                return f"Error: Email already registered as {role}!"

            cur.execute(f"INSERT INTO {table} (email, password) VALUES (%s, %s)", (email, password))
            
            if role == "user":
                new_user_id = cur.lastrowid
                cur.execute("INSERT INTO bills (user_id, amount, status) VALUES (%s, 0, 'Paid')", (new_user_id,))
            
            db.commit()
            cur.close()
            db.close()

            target = "/admin/login" if role == "admin" else "/user/login"
            return redirect(target)

        except mysql.connector.Error as err:
            return f"Database Error: {err}"

    return render_template("register.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session: return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor()
    
    cur.execute("SELECT bills.id, users.email, bills.amount, bills.status FROM bills JOIN users ON bills.user_id = users.id")
    bills = cur.fetchall()

    cur.execute("SELECT id, email FROM users")
    users = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin_dashboard.html", bills=bills, users=users)

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

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
from flask import (
    Flask,
    flash,
    render_template,
    request,
    redirect,
    session,
    url_for,
    send_file,
    Response,
)
import mysql.connector
import os
import io
import smtplib
from captcha.image import ImageCaptcha
import string
import random
import stripe
import threading
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

base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(base_dir), 'frontend')

app = Flask(__name__, 
            template_folder=os.path.join(frontend_dir, 'templates'), 
            static_folder=os.path.join(frontend_dir, 'static'))
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key")

csrf = CSRFProtect(app)

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "society_db"),
}

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def get_db_connection():
    try:
        ssl_path = os.getenv("SSL_CA_PATH", "ca.pem")
        if not os.path.isabs(ssl_path):
            ssl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ssl_path)

        cloud_conn = mysql.connector.connect(
            host=os.getenv("CLOUD_DB_HOST"),
            port=os.getenv("CLOUD_DB_PORT"),
            user=os.getenv("CLOUD_DB_USER"),
            password=os.getenv("CLOUD_DB_PASSWORD"),
            database=os.getenv("CLOUD_DB_NAME"),
            ssl_ca=ssl_path,
            connection_timeout=10,
        )
        if cloud_conn.is_connected():
            print("✅ Connected to Cloud Database (Aiven)")
            return cloud_conn
    except mysql.connector.Error as err:
        print(f"⚠️ Cloud connection failed: {err}. Switching to Local...")

    try:
        local_conn = mysql.connector.connect(**db_config)
        print("🏠 Connected to Local MySQL Database")
        return local_conn
    except mysql.connector.Error as err:
        print(f"❌ Local connection also failed: {err}")
        return None


def generate_captcha_text():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


@app.route("/captcha")
def captcha():
    captcha_text = generate_captcha_text()
    session["captcha"] = captcha_text
    image = ImageCaptcha(width=150, height=50)
    data = image.generate(captcha_text)
    return Response(data, mimetype="image/png")


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


@app.route("/contact")
def contact():
    return render_template("contact.html")


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def send_welcome_email_thread(user_email, user_name, society_name="Society"):
    try:
        print(
            f"DEBUG: Preparing to send Welcome Email to {user_email} ({user_name})"
        )
        msg = MIMEMultipart()
        msg["From"] = os.getenv("MAIL_USERNAME")
        msg["To"] = user_email
        msg["Subject"] = (
            f"Welcome to {society_name} - Your Digital Home Awaits!"
        )

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .button {{
                    background-color: #ff8c00;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    display: inline-block;
                }}
                .container {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 600px;
                    margin: 0 auto;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .header {{
                    background-color: #1f2937;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                    background-color: #ffffff;
                    color: #333333;
                    line-height: 1.6;
                }}
                .footer {{
                    background-color: #f3f4f6;
                    padding: 15px;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">🏠 {society_name}</h1>
                </div>
                <div class="content">
                    <h2>Hello, {user_name}! 👋</h2>
                    <p>Welcome to the family! The admin has successfully added you to the <strong>{society_name}</strong> digital management system.</p>
                    <p>You can now say goodbye to manual registers and paperwork. Your new resident dashboard allows you to:</p>
                    <ul>
                        <li>✅ Pay Maintenance Bills instantly online.</li>
                        <li>✅ Pre-approve Visitors for gate security.</li>
                        <li>✅ Lodge Complaints and track resolution.</li>
                        <li>✅ Vote in community polls.</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>Sent automatically by the <strong>SocietyPro System</strong>.</p>
                    <p>&copy; 2026 {society_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(
            os.getenv("MAIL_SERVER", ""), int(os.getenv("MAIL_PORT"))
        )
        server.starttls()
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.sendmail(
            os.getenv("MAIL_USERNAME"), user_email, msg.as_string()
        )
        server.quit()
        print(f"✅ Impressive Welcome email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def send_welcome_email(user_email, user_name, society_name="Society"):
    thread = threading.Thread(
        target=send_welcome_email_thread, args=(user_email, user_name, society_name)
    )
    thread.start()


@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        society_name = request.form["society_name"]

        db = get_db_connection()
        if db is None:
            return (
                "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
                500,
            )

        cur = db.cursor()
        cur.execute("SELECT id FROM admins WHERE email = %s", (email,))
        existing_admin = cur.fetchone()
        cur.close()
        db.close()

        if existing_admin:
            return "Email already registered! Please login."

        otp = str(random.randint(100000, 999999))

        session["temp_admin"] = {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "society_name": society_name,
        }
        session["temp_otp"] = otp

        send_email(
            to_email=email,
            otp=otp,
            subject="SocietyPro: Verify Your Account",
            heading="Welcome Aboard!",
            message_text="Thank you for registering. Please use the code below to verify your admin account:",
        )
        return redirect("/admin/verify_registration")

    return render_template("auth/admin_register.html")


@app.route("/admin/verify_registration", methods=["GET", "POST"])
def admin_verify_registration():
    if "temp_admin" not in session or "temp_otp" not in session:
        return redirect("/admin/register")

    if request.method == "POST":
        user_otp = request.form["otp"]

        if user_otp == session["temp_otp"]:
            data = session["temp_admin"]

            try:
                db = get_db_connection()
                if db is None:
                    return render_template(
                        "auth/admin_verify_otp.html",
                        error="Database is offline.",
                    )

                cur = db.cursor()
                cur.execute(
                    "INSERT INTO admins (name, email, password, society_name) VALUES (%s, %s, %s, %s)",
                    (
                        data["name"],
                        data["email"],
                        data["password"],
                        data["society_name"],
                    ),
                )
                db.commit()
                cur.close()
                db.close()

                session.pop("temp_admin", None)
                session.pop("temp_otp", None)

                return redirect("/admin/login")

            except Exception as e:
                return f"Database Error: {e}"
        else:
            return render_template(
                "auth/admin_verify_otp.html",
                error="Invalid OTP! Please try again.",
            )

    return render_template("auth/admin_verify_otp.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_captcha = request.form["captcha"]

        if user_captcha != session.get("captcha"):
            return render_template(
                "auth/admin_login.html", error="Invalid CAPTCHA"
            )

        db = get_db_connection()
        if db is None:
            return render_template(
                "auth/admin_login.html",
                error="System maintenance: Database is currently offline.",
            )

        cur = db.cursor()
        cur.execute("SELECT * FROM admins WHERE email=%s", (email,))
        admin = cur.fetchone()

        if admin and check_password_hash(admin[3], password):
            session.pop("captcha", None)
            session["admin_id"] = admin[0]

            cur.close()
            db.close()

            return redirect(url_for("admin_dashboard"))

        cur.close()
        db.close()

        return render_template(
            "auth/admin_login.html", error="Invalid email or password"
        )

    return render_template("auth/admin_login.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db_connection()
        if db is None:
            return render_template(
                "auth/user_login.html",
                error="System maintenance: Database is currently offline.",
            )

        cur = db.cursor()
        cur.execute("SELECT id, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        db.close()

        if user and check_password_hash(user[1], password):
            session.clear()
            session["user"] = user[0]
            return redirect("/user/dashboard")

        return render_template(
            "auth/user_login.html", error="Invalid Credentials"
        )

    return render_template("auth/user_login.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        db = get_db_connection()
        if db is None:
            return render_template(
                "auth/forgot_password.html",
                error="Database offline. Try again later.",
            )

        cur = db.cursor()

        cur.execute("SELECT id FROM admins WHERE email = %s", (email,))
        admin = cur.fetchone()

        cur.close()
        db.close()

        if admin:
            otp = str(random.randint(100000, 999999))
            session["reset_otp"] = otp
            session["reset_email"] = email

            send_email(
                to_email=email,
                otp=otp,
                subject="SocietyPro: Password Reset Request",
                heading="Reset Password",
                message_text="We received a request to reset your password. Use this code to proceed:",
            )

            return redirect("/verify_otp")
        else:
            return render_template(
                "auth/forgot_password.html", error="Admin email not found"
            )

    return render_template("auth/forgot_password.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp_route():
    if request.method == "POST":
        user_otp = request.form["otp"]

        if "reset_otp" in session and session["reset_otp"] == user_otp:
            return redirect("/reset_password")
        else:
            return render_template(
                "auth/verify_otp.html", error="Invalid OTP! Try again later"
            )

    return render_template("auth/verify_otp.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if "reset_email" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        new_password = request.form["password"]
        email = session["reset_email"]

        hashed_pw = generate_password_hash(new_password)

        db = get_db_connection()
        if db is None:
            return render_template(
                "auth/reset_password.html",
                error="Database offline. Try again later.",
            )

        cur = db.cursor()

        cur.execute(
            "UPDATE admins SET password = %s WHERE email = %s",
            (hashed_pw, email),
        )
        db.commit()
        cur.close()
        db.close()

        session.pop("reset_otp", None)
        session.pop("reset_email", None)

        return redirect("/admin/login")

    return render_template("auth/reset_password.html")


def send_email(to_email, otp, subject, heading, message_text):
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")
    print(f"DEBUG: OTP sent to {to_email} is: {otp}")
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 400px; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
          <h2 style="color: #ff8c00; text-align: center;">SocietyPro</h2>
          <h3 style="text-align: center; color: #444;">{heading}</h3>
          <p>Hello,</p>
          <p>{message_text}</p>
          <div style="background: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px; margin: 20px 0;">
            {otp}
          </div>
          <p style="font-size: 12px; color: #888;">If you did not request this, please ignore this email.</p>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "admin_id" in session:
        role = "admin"
        user_id = session["admin_id"]
        table = "admins"
    elif "user" in session:
        role = "user"
        user_id = session["user"]
        table = "users"
    else:
        return redirect("/")

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    msg = ""

    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        cur.execute(
            f"UPDATE {table} SET email=%s, password=%s WHERE id=%s",
            (email, password, user_id),
        )
        db.commit()
        msg = "Profile updated"

    cur.execute(f"SELECT email FROM {table} WHERE id=%s", (user_id,))
    data = cur.fetchone()

    cur.close()
    db.close()

    return render_template("user/profile.html", user=data, role=role, msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    if request.method == "POST":
        try:
            user_id = request.form.get("user_id")
            amount = request.form.get("amount")
            if user_id and amount:
                cur.execute(
                    "INSERT INTO bills (user_id, amount, status) VALUES (%s, %s, 'Unpaid')",
                    (user_id, float(amount)),
                )
                db.commit()
        except Exception:
            pass

    cur.execute(
        "SELECT amount FROM society_fund WHERE admin_id = %s", (admin_id,)
    )
    fund_row = cur.fetchone()

    if fund_row:
        total_fund = fund_row[0]
    else:
        cur.execute(
            "INSERT INTO society_fund (admin_id, amount) VALUES (%s, 0)",
            (admin_id,),
        )
        db.commit()
        total_fund = 0

    query_bills = """
        SELECT b.id, u.name, b.amount, b.status
        FROM bills b
        JOIN users u ON b.user_id = u.id
        WHERE u.admin_id = %s
        ORDER BY b.id DESC LIMIT 5
    """
    cur.execute(query_bills, (admin_id,))
    bills = cur.fetchall()

    cur.execute(
        "SELECT id, name, email FROM users WHERE admin_id = %s", (admin_id,)
    )
    users = cur.fetchall()

    cur.execute("SELECT name, society_name FROM admins WHERE id = %s", (admin_id,))
    admin_row = cur.fetchone()
    admin_name = admin_row[0] if admin_row else "Secretary"
    society_name = admin_row[1] if admin_row else "Dashboard Overview"

    cur.close()
    db.close()

    return render_template(
        "admin/admin_dashboard.html",
        bills=bills,
        users=users,
        total_fund=total_fund,
        admin_name=admin_name,
        society_name=society_name,
    )


@app.route("/admin/visitors")
def admin_visitors():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    query = """
        SELECT v.id, v.name, v.phone, v.visit_date, v.visit_time, v.status, u.email 
        FROM visitors v 
        JOIN users u ON v.user_id = u.id 
        WHERE u.admin_id = %s
        ORDER BY v.visit_date DESC
    """
    cur.execute(query, (admin_id,))
    visitors = cur.fetchall()

    cur.close()
    db.close()
    return render_template("admin/admin_visitors.html", visitors=visitors)


@app.route("/admin/polls", methods=["GET", "POST"])
def admin_polls():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        question = request.form["question"]
        opt1 = request.form["option1"]
        opt2 = request.form["option2"]

        cur.execute(
            "INSERT INTO polls (question, option1, option2, admin_id) VALUES (%s, %s, %s, %s)",
            (question, opt1, opt2, admin_id),
        )
        db.commit()

    query = """
        SELECT p.id, p.question, p.option1, p.option2, p.status,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.choice = 'option1') as vote1,
        (SELECT COUNT(*) FROM poll_votes v WHERE v.poll_id = p.id AND v.choice = 'option2') as vote2
        FROM polls p 
        WHERE p.admin_id = %s
        ORDER BY p.id DESC
    """
    cur.execute(query, (admin_id,))
    polls = cur.fetchall()

    cur.close()
    db.close()
    return render_template("admin/admin_polls.html", polls=polls)


@app.route("/admin/bookings")
def admin_bookings():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    query = """
        SELECT b.id, b.facility_name, b.booking_date, b.time_slot, b.status, u.name 
        FROM bookings b 
        JOIN users u ON b.user_id = u.id 
        WHERE u.admin_id = %s
        ORDER BY b.booking_date DESC
    """
    cur.execute(query, (admin_id,))
    bookings = cur.fetchall()

    cur.close()
    db.close()
    return render_template("admin/admin_bookings.html", bookings=bookings)


@app.route("/admin/update_fund", methods=["POST"])
def update_fund():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    new_amount = request.form.get("amount")

    if not new_amount:
        return "Error: Amount is required", 400

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    cur.execute(
        "UPDATE society_fund SET amount = %s WHERE admin_id = %s",
        (new_amount, admin_id),
    )
    db.commit()

    cur.close()
    db.close()

    return redirect("/admin/dashboard")


@app.route("/admin/delete_bill/<int:bill_id>", methods=["POST"])
def delete_bill(bill_id):
    if "admin_id" not in session:
        return redirect("/admin/login")

    try:
        db = get_db_connection()
        if db is None:
            return (
                "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
                500,
            )

        cur = db.cursor()
        cur.execute("DELETE FROM bills WHERE id = %s", (bill_id,))
        db.commit()
        cur.close()
        db.close()
    except Exception:
        pass

    return redirect("/admin/invoices")


@app.route("/admin/tenants", methods=["GET", "POST"])
def admin_tenants():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()

    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            cur = db.cursor()
            cur.execute(
                "INSERT INTO users (name, email, password, admin_id) VALUES (%s, %s, %s, %s)",
                (name, email, password, admin_id),
            )

            user_id = cur.lastrowid
            cur.execute(
                "INSERT INTO bills (user_id, amount, status) VALUES (%s, 0, 'Paid')",
                (user_id,),
            )

            db.commit()
            
            cur.execute("SELECT society_name FROM admins WHERE id = %s", (admin_id,))
            society_row = cur.fetchone()
            society_name = society_row[0] if society_row else "Society"
            
            cur.close()
            send_welcome_email(email, name, society_name)

            flash("Tenant added successfully and email sent!", "success")
            return redirect(url_for("admin_tenants"))
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    cur = db.cursor()
    cur.execute(
        "SELECT id, name, email FROM users WHERE admin_id = %s ORDER BY id DESC",
        (admin_id,),
    )
    tenants = cur.fetchall()
    cur.close()
    db.close()

    return render_template("admin/admin_tenants.html", tenants=tenants)


@app.route("/admin/delete_tenant/<int:user_id>", methods=["POST"])
def delete_tenant(user_id):
    if "admin_id" not in session:
        return redirect("/admin/login")

    try:
        db = get_db_connection()
        if db is None:
            return (
                "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
                500,
            )

        cur = db.cursor()
        cur.execute("DELETE FROM bills WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        cur.close()
        db.close()
    except Exception:
        pass

    return redirect("/admin/tenants")


@app.route("/admin/edit_tenant", methods=["POST"])
def edit_tenant():
    if "admin_id" not in session:
        return redirect("/admin/login")

    user_id = request.form["user_id"]
    name = request.form["name"]
    email = request.form["email"]
    password_input = request.form["password"]

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if password_input.strip():
        hashed_pw = generate_password_hash(password_input)
        cur.execute(
            "UPDATE users SET name=%s, email=%s, password=%s WHERE id=%s",
            (name, email, hashed_pw, user_id),
        )
    else:
        cur.execute(
            "UPDATE users SET name=%s, email=%s WHERE id=%s",
            (name, email, user_id),
        )

    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/tenants")


@app.route("/admin/invoices")
def admin_invoices():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()

    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    query = """
        SELECT bills.id, users.name, bills.amount, bills.status 
        FROM bills 
        JOIN users ON bills.user_id = users.id
        WHERE users.admin_id = %s
        ORDER BY bills.id DESC
    """
    cur.execute(query, (admin_id,))
    invoices = cur.fetchall()

    cur.close()
    db.close()
    return render_template("admin/admin_invoices.html", invoices=invoices)


@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if "admin_id" not in session:
        return redirect("/admin/login")

    msg = ""
    if request.method == "POST":
        new_password = generate_password_hash(request.form["new_password"])
        admin_id = session["admin_id"]

        db = get_db_connection()
        if db is None:
            return (
                "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
                500,
            )

        cur = db.cursor()
        cur.execute(
            "UPDATE admins SET password=%s WHERE id=%s",
            (new_password, admin_id),
        )
        db.commit()
        cur.close()
        db.close()
        msg = "Password updated successfully!"

    return render_template("admin/admin_settings.html", msg=msg)


@app.route("/admin/add_bill", methods=["POST"])
def add_bill():
    if "admin_id" not in session:
        return redirect("/admin/login")

    try:
        user_id = request.form["user_id"]
        amount = request.form["amount"]

        if not user_id or not amount:
            return "Error: Missing User or Amount", 400

        db = get_db_connection()
        if db is None:
            return (
                "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
                500,
            )

        cur = db.cursor()
        cur.execute(
            "INSERT INTO bills (user_id, amount, status) VALUES (%s, %s, 'Unpaid')",
            (user_id, float(amount)),
        )
        db.commit()
        cur.close()
        db.close()

        return redirect("/admin/dashboard")

    except Exception as e:
        return f"An error occurred: {e}", 500


@app.route("/user/dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect("/user/login")

    user_id = session["user"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    cur.execute(
        "SELECT id, amount, status FROM bills WHERE user_id = %s ORDER BY id DESC",
        (user_id,),
    )
    bills = cur.fetchall()

    cur.execute(
        "SELECT u.name, a.society_name FROM users u JOIN admins a ON u.admin_id = a.id WHERE u.id = %s",
        (user_id,),
    )
    user_row = cur.fetchone()
    user_name = user_row[0] if user_row else "Resident"
    society_name = user_row[1] if user_row else "Your Society"

    cur.close()
    db.close()

    return render_template(
        "user/user_dashboard.html", bills=bills, weather_key=WEATHER_API_KEY, user_name=user_name, society_name=society_name
    )


@app.route("/admin/notices", methods=["GET", "POST"])
def admin_notices():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        cur.execute(
            "INSERT INTO notices (title, content, admin_id) VALUES (%s, %s, %s)",
            (title, content, admin_id),
        )
        db.commit()

    cur.execute(
        "SELECT id, title, content, DATE_FORMAT(created_at, '%d %b %Y') FROM notices WHERE admin_id = %s ORDER BY id DESC",
        (admin_id,),
    )
    notices = cur.fetchall()

    cur.close()
    db.close()

    return render_template("admin/admin_notices.html", notices=notices)


@app.route("/admin/edit_notice", methods=["POST"])
def edit_notice():
    if "admin_id" not in session:
        return redirect("/admin/login")

    notice_id = request.form["notice_id"]
    title = request.form["title"]
    content = request.form["content"]

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    cur.execute(
        "UPDATE notices SET title=%s, content=%s WHERE id=%s",
        (title, content, notice_id),
    )
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/notices")


@app.route("/admin/delete_notice/<int:id>")
def delete_notice(id):
    if "admin_id" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    cur.execute("DELETE FROM notices WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/notices")


@app.route("/user/notices")
def user_notices():
    if "user" not in session:
        return redirect("/user/login")

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    cur.execute(
        "SELECT title, content, DATE_FORMAT(created_at, '%d %b %Y') as date FROM notices ORDER BY id DESC"
    )
    notices = cur.fetchall()
    cur.close()
    db.close()

    return render_template("user/user_notices.html", notices=notices)


@app.route("/admin/download_invoice/<int:bill_id>")
def download_invoice(bill_id):
    if "admin_id" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

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
        ["TOTAL", f"Rs. {amount:,.2f}"],
    ]

    table = Table(data, colWidths=[400, 100])
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ff8c00")),
            ("GRID", (0, 0), (-1, -2), 1, colors.black),
        ]
    )
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 350)

    if status == "Paid":
        c.saveState()
        c.translate(width / 2, height / 2)
        c.rotate(45)
        c.setFillColorRGB(0, 1, 0, 0.3)
        c.setFont("Helvetica-Bold", 80)
        c.drawCentredString(0, 0, "PAID")
        c.restoreState()
    else:
        c.saveState()
        c.translate(width / 2, height / 2)
        c.rotate(45)
        c.setFillColorRGB(1, 0, 0, 0.1)
        c.setFont("Helvetica-Bold", 80)
        c.drawCentredString(0, 0, "UNPAID")
        c.restoreState()

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Invoice_{invoice_id}.pdf",
        mimetype="application/pdf",
    )


@app.route("/user/complaints", methods=["GET", "POST"])
def user_complaints():
    if "user" not in session:
        return redirect("/user/login")

    user_id = session["user"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        subject = request.form["subject"]
        description = request.form["description"]
        
        text = (subject + " " + description).lower()
        category = "General"
        if any(word in text for word in ["leak", "pipe", "water", "plumb", "tap"]):
            category = "Plumbing"
        elif any(word in text for word in ["power", "light", "wire", "electric", "short"]):
            category = "Electrical"
        elif any(word in text for word in ["guard", "unknown", "visitor", "theft", "unsafe", "secur"]):
            category = "Security"
        elif any(word in text for word in ["garbage", "dirt", "dust", "sweep", "clean"]):
            category = "Cleanliness"
            
        priority = "Normal"
        if any(word in text for word in ["emergency", "urgent", "immediate", "burst", "shock", "fire", "critical", "broken", "danger"]):
            priority = "High"

        cur.execute(
            "INSERT INTO complaints (user_id, subject, description, category, priority) VALUES (%s, %s, %s, %s, %s)",
            (user_id, subject, description, category, priority),
        )
        db.commit()

    cur.execute(
        "SELECT subject, description, status, created_at, category, priority FROM complaints WHERE user_id = %s ORDER BY id DESC",
        (user_id,),
    )
    my_complaints = cur.fetchall()

    cur.close()
    db.close()
    return render_template(
        "user/user_complaints.html", complaints=my_complaints
    )


@app.route("/admin/complaints", methods=["GET", "POST"])
def admin_complaints():
    if "admin_id" not in session:
        return redirect("/admin/login")

    admin_id = session["admin_id"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        complaint_id = request.form["complaint_id"]
        status = request.form["status"]
        cur.execute(
            "UPDATE complaints SET status=%s WHERE id=%s",
            (status, complaint_id),
        )
        db.commit()
        return redirect("/admin/complaints")

    query = """
        SELECT c.id, u.email, c.subject, c.description, c.status, 
               DATE_FORMAT(c.created_at, '%d %b %Y') as date, c.category, c.priority
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE u.admin_id = %s
        ORDER BY FIELD(c.priority, 'High', 'Normal') ASC, c.status ASC, c.created_at DESC
    """
    cur.execute(query, (admin_id,))
    complaints = cur.fetchall()

    cur.close()
    db.close()
    return render_template(
        "admin/admin_complaints.html", complaints=complaints
    )


@app.route("/user/visitors", methods=["GET", "POST"])
def user_visitors():
    if "user" not in session:
        return redirect("/user/login")
    user_id = session["user"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        date = request.form["date"]
        time = request.form["time"]
        cur.execute(
            "INSERT INTO visitors (user_id, name, phone, visit_date, visit_time) VALUES (%s, %s, %s, %s, %s)",
            (user_id, name, phone, date, time),
        )
        db.commit()

    cur.execute(
        "SELECT name, phone, visit_date, visit_time, status FROM visitors WHERE user_id=%s ORDER BY id DESC",
        (user_id,),
    )
    visitors = cur.fetchall()

    cur.close()
    db.close()
    return render_template("user/user_visitors.html", visitors=visitors)


@app.route("/user/polls", methods=["GET", "POST"])
def user_polls():
    if "user" not in session:
        return redirect("/user/login")
    user_id = session["user"]
    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        poll_id = request.form["poll_id"]
        choice = request.form["choice"]

        cur.execute(
            "SELECT id FROM poll_votes WHERE user_id=%s AND poll_id=%s",
            (user_id, poll_id),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO poll_votes (user_id, poll_id, choice) VALUES (%s, %s, %s)",
                (user_id, poll_id, choice),
            )
            db.commit()

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
    return render_template("user/user_polls.html", polls=polls)


@app.route("/user/bookings", methods=["GET", "POST"])
def user_bookings():
    if "user" not in session:
        return redirect("/user/login")
    user_id = session["user"]

    facilities = [
        "Community Hall",
        "Clubhouse",
        "Tennis Court",
        "Swimming Pool Area",
    ]
    slots = [
        "Morning (9 AM - 1 PM)",
        "Afternoon (2 PM - 6 PM)",
        "Evening (7 PM - 11 PM)",
    ]

    error = None
    success = None

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()

    if request.method == "POST":
        facility = request.form["facility"]
        date = request.form["date"]
        slot = request.form["slot"]

        check_query = "SELECT id FROM bookings WHERE facility_name=%s AND booking_date=%s AND time_slot=%s AND status='Confirmed'"
        cur.execute(check_query, (facility, date, slot))
        existing_booking = cur.fetchone()

        if existing_booking:
            error = f"Sorry! The {facility} is already booked for that slot."
        else:
            insert_query = "INSERT INTO bookings (user_id, facility_name, booking_date, time_slot, status) VALUES (%s, %s, %s, %s, 'Pending')"
            cur.execute(insert_query, (user_id, facility, date, slot))
            db.commit()
            success = "Booking Request Sent! Awaiting Admin Approval."

    cur.execute(
        "SELECT facility_name, booking_date, time_slot, status FROM bookings WHERE user_id=%s ORDER BY booking_date DESC",
        (user_id,),
    )
    my_bookings = cur.fetchall()

    cur.close()
    db.close()

    return render_template(
        "user/user_bookings.html",
        facilities=facilities,
        slots=slots,
        my_bookings=my_bookings,
        error=error,
        success=success,
    )


@app.route("/admin/booking_action", methods=["POST"])
def booking_action():
    if "admin_id" not in session:
        return redirect("/admin/login")

    booking_id = request.form.get("id")
    action = request.form.get("action")

    new_status = "Confirmed" if action == "approve" else "Rejected"

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    cur.execute(
        "UPDATE bookings SET status = %s WHERE id = %s",
        (new_status, booking_id),
    )
    db.commit()
    cur.close()
    db.close()

    return redirect("/admin/bookings")


@app.route("/user/emergency")
def user_emergency():
    if "user" not in session:
        return redirect("/user/login")

    contacts = [
        {
            "name": "Police Station",
            "role": "Emergency",
            "phone": "100",
            "icon": "ri-alarm-warning-fill",
            "theme": "red",
        },
        {
            "name": "Fire Brigade",
            "role": "Emergency",
            "phone": "101",
            "icon": "ri-fire-fill",
            "theme": "red",
        },
        {
            "name": "Ambulance",
            "role": "Medical",
            "phone": "102",
            "icon": "ri-first-aid-kit-fill",
            "theme": "red",
        },
        {
            "name": "Main Gate Security",
            "role": "Security",
            "phone": "+91 98765 43210",
            "icon": "ri-shield-star-fill",
            "theme": "green",
        },
        {
            "name": "Society Office",
            "role": "Admin",
            "phone": "0120-456-7890",
            "icon": "ri-building-2-fill",
            "theme": "blue",
        },
        {
            "name": "Electrician",
            "role": "Maintenance",
            "phone": "+91 91234 56789",
            "icon": "ri-lightbulb-flash-fill",
            "theme": "orange",
        },
        {
            "name": "Plumber",
            "role": "Maintenance",
            "phone": "+91 99887 76655",
            "icon": "ri-drop-fill",
            "theme": "orange",
        },
    ]

    return render_template("user/user_emergency.html", contacts=contacts)


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
    except Exception:
        pass

    try:
        smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        sender_email = os.getenv("MAIL_USERNAME")
        password = os.getenv("MAIL_PASSWORD")
        receiver_email = sender_email

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

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()

    except Exception:
        pass

    return redirect("/#contact")


@app.route("/pay_bill/<int:bill_id>", methods=["POST"])
def pay_bill(bill_id):
    if "user" not in session:
        return redirect("/user/login")

    db = get_db_connection()
    if db is None:
        return (
            "Database Connection Error: Please check if your Local MySQL or Aiven Cloud is active.",
            500,
        )

    cur = db.cursor()
    cur.execute("SELECT amount FROM bills WHERE id = %s", (bill_id,))
    bill = cur.fetchone()
    cur.close()
    db.close()

    if not bill:
        return "Bill not found", 404

    amount_in_cents = int(bill[0] * 100)

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": f"Society Maintenance Bill #{bill_id}",
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=url_for(
                "payment_success", bill_id=bill_id, _external=True
            )
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("user_dashboard", _external=True),
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)


@app.route("/payment_success/<int:bill_id>")
def payment_success(bill_id):
    if "user" not in session:
        return redirect("/user/login")

    db = get_db_connection()
    if db:
        cur = db.cursor()

        # 1. Fetch the amount and the admin_id for this specific bill
        query_fetch = """
            SELECT b.amount, u.admin_id 
            FROM bills b 
            JOIN users u ON b.user_id = u.id 
            WHERE b.id = %s
        """
        cur.execute(query_fetch, (bill_id,))
        bill_data = cur.fetchone()

        if bill_data:
            paid_amount = bill_data[0]
            admin_id = bill_data[1]

            # 2. Update the bill status to 'Paid'
            cur.execute(
                "UPDATE bills SET status = 'Paid' WHERE id = %s", (bill_id,)
            )

            # 3. Automatically add the paid amount to the Society Fund
            cur.execute(
                "UPDATE society_fund SET amount = amount + %s WHERE admin_id = %s",
                (paid_amount, admin_id),
            )

            db.commit()
            print(
                f"💰 Fund Updated: ₹{paid_amount} added for Admin ID {admin_id}"
            )

        cur.close()
        db.close()

    return render_template("user/payment_success.html", bill_id=bill_id)


@app.route("/api/chatbot", methods=["POST"])
def chatbot_api():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    
    data = request.get_json(silent=True)
    if not data:
        return {"answer": "I didn't understand that."}, 400
        
    question = data.get("question", "").lower()

    if any(word in question for word in ["hi", "hello", "hey"]):
        answer = "Hello! I am your SocietyPro AI Assistant. How can I help you today?"
    elif any(word in question for word in ["pay", "bill", "maintenance", "due", "money"]):
        answer = "To pay your maintenance bills, go to the 'Home' dashboard and look under 'Invoice History'."
    elif any(word in question for word in ["book", "clubhouse", "pool", "gym", "facility"]):
        answer = "You can book society facilities like the Clubhouse or Swimming Pool from the 'Bookings' tab."
    elif any(word in question for word in ["visitor", "guest", "delivery"]):
        answer = "Expecting someone? Pre-approve your guests in the 'Visitors' section."
    elif any(word in question for word in ["complain", "issue", "plumber", "electrician", "broken", "water", "electricity"]):
        answer = "You can raise a ticket for any issue in the 'Complaints' section. I will automatically categorize and prioritize it for the admin!"
    elif any(word in question for word in ["contact", "admin", "emergency", "help"]):
        answer = "For emergencies, check the 'Emergency' section. For admin issues, please raise a complaint."
    else:
        answer = "I am a simple AI and I'm still learning! Could you rephrase that? Or check the specific sections in your sidebar."

    import time
    time.sleep(1) # Simulate thinking
    return {"answer": answer}

@app.route("/api/predict_crowd", methods=["GET"])
def predict_crowd():
    facility = request.args.get("facility", "")
    slot = request.args.get("slot", "")
    
    if not facility or not slot:
        return {"error": "Missing parameters"}, 400
        
    crowd_probability = 30 # Base
    
    if "pool" in facility.lower():
        if "evening" in slot.lower():
            crowd_probability += 50
        elif "afternoon" in slot.lower():
            crowd_probability += 30
            
    if "clubhouse" in facility.lower() or "hall" in facility.lower():
        if "evening" in slot.lower():
            crowd_probability += 60
            
    if "morning" in slot.lower():
        crowd_probability += 10
        
    import random
    variation = random.randint(-10, 10)
    final_prob = min(max(crowd_probability + variation, 10), 95)
    
    level = "Low"
    if final_prob > 75:
        level = "High"
    elif final_prob > 40:
        level = "Medium"
        
    return {
        "probability": final_prob,
        "level": level
    }


@app.route("/api/dashboard-stats")
def dashboard_stats():
    """Real-time dashboard stats endpoint — polled by the frontend every 10s."""
    if "admin_id" not in session:
        return {"error": "Unauthorized"}, 401

    admin_id = session["admin_id"]
    db = get_db_connection()
    if db is None:
        return {"error": "DB offline"}, 500

    cur = db.cursor()

    # Total residents
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE admin_id = %s", (admin_id,)
    )
    total_residents = cur.fetchone()[0]

    # Pending / open complaints (status = 'Open' or 'Pending')
    cur.execute(
        """SELECT COUNT(*) FROM complaints c
           JOIN users u ON c.user_id = u.id
           WHERE u.admin_id = %s AND c.status IN ('Open', 'Pending')""",
        (admin_id,),
    )
    pending_issues = cur.fetchone()[0]

    # Visitors today
    cur.execute(
        """SELECT COUNT(*) FROM visitors v
           JOIN users u ON v.user_id = u.id
           WHERE u.admin_id = %s AND DATE(v.visit_date) = CURDATE()""",
        (admin_id,),
    )
    visitors_today = cur.fetchone()[0]

    # Total fund
    cur.execute(
        "SELECT amount FROM society_fund WHERE admin_id = %s", (admin_id,)
    )
    fund_row = cur.fetchone()
    total_fund = float(fund_row[0]) if fund_row else 0.0

    cur.close()
    db.close()

    return {
        "total_residents": total_residents,
        "pending_issues": pending_issues,
        "visitors_today": visitors_today,
        "total_fund": total_fund,
    }


if __name__ == "__main__":
    app.run(debug=True)


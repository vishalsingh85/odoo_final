from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_mail import Mail, Message
import random
import mysql.connector
import bcrypt
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import qrcode
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- Database ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="iop890890",
        database="eventhive"
    )

# ---------------- Mail ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bsal000777@gmail.com'
app.config['MAIL_PASSWORD'] = 'pgnjxikfhbaxshse'
mail = Mail(app)


from PIL import Image, ImageDraw, ImageFont
import os

def create_default_image():
    """Create a default event image if it doesn't exist"""
    image_path = "static/images/default_event.jpg"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    # Create a simple default image
    img = Image.new('RGB', (400, 300), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    
    try:
        # Try to use a font if available
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        # Use default font if arial is not available
        font = ImageFont.load_default()
    
    d.text((100, 140), "Event Image", fill=(255, 255, 255), font=font)
    img.save(image_path)
    print(f"Default image created at {image_path}")

# Call this function when your app starts
create_default_image()
# ---------------- Uploads ----------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- OTP ----------------
otp_store = {}

# ---------------- Routes ----------------

@app.route("/")
def welcome():
    return render_template("welcome.html")

# ✅ Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # generate OTP
        otp = str(random.randint(100000, 999999))
        otp_store[email] = {"otp": otp, "data": (name, email, phone, password)}

        # send mail
        msg = Message("Your EventHive OTP", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your OTP for registration is {otp}"
        mail.send(msg)

        flash("📩 OTP sent to your email!", "info")
        return redirect(url_for("verify_otp", email=email))
    return render_template("signup.html")

# ✅ OTP Verification
@app.route("/verify/<email>", methods=["GET", "POST"])
def verify_otp(email):
    if request.method == "POST":
        entered_otp = request.form['otp']
        if email in otp_store and otp_store[email]["otp"] == entered_otp:
            name, email, phone, password = otp_store[email]["data"]

            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "INSERT INTO users (name, email, phone, password, is_verified) VALUES (%s,%s,%s,%s,%s)",
                (name, email, phone, hashed_pw.decode('utf-8'), True)
            )
            conn.commit()
            cursor.close()
            conn.close()

            otp_store.pop(email)
            flash("🎉 New User Created Successfully!", "success")
            return redirect(url_for("login"))
        else:
            flash("❌ Invalid OTP!", "danger")
    return render_template("verify.html", email=email)

# ✅ Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        # Admin login
        if email == "admin@gmail.com" and password == "admin123":
            session['user'] = "Admin"
            session['role'] = "admin"
            flash("Welcome Admin!", "success")
            return redirect(url_for("admin_dashboard"))

        # Normal users
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['user'] = user['name']
            session['role'] = "user"
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Invalid Credentials!", "danger")

    return render_template("login.html")

# ✅ User Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Pagination
    page = int(request.args.get("page", 1))
    per_page = 6
    offset = (page-1)*per_page

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    date_filter = request.args.get("date", "")

    query = "SELECT * FROM events WHERE publish_status = TRUE"
    params = []

    if search:
        query += " AND (name LIKE %s OR location LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category = %s"
        params.append(category)

    if date_filter == "today":
        query += " AND DATE(start_date) = CURDATE()"
    elif date_filter == "week":
        query += " AND WEEK(start_date) = WEEK(CURDATE())"

    # Total count for pagination
    cursor.execute(query, params)
    total_events = cursor.fetchall()
    total_pages = (len(total_events) + per_page - 1)//per_page

    query += " ORDER BY start_date ASC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    cursor.execute(query, params)
    events = cursor.fetchall()

    # Get loyalty points
    cursor.execute("SELECT loyalty_points FROM users WHERE id=%s", (session['user_id'],))
    user = cursor.fetchone()
    loyalty_points = user.get('loyalty_points', 0)

    # Get user bookings
    cursor.execute("SELECT event_id FROM bookings WHERE user_id=%s", (session['user_id'],))
    booked_events = [b['event_id'] for b in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template(
        "user_dashboard.html",
        username=session['user'],
        events=events,
        loyalty_points=loyalty_points,
        booked_events=booked_events,
        page=page,
        total_pages=total_pages,
        search=search,
        category=category,
        date_filter=date_filter
    )
# ✅ Admin Dashboard
# ✅ Admin Dashboard
# ✅ Admin Dashboard - Updated to properly fetch images
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get stats for admin dashboard
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user' OR role IS NULL")
    total_users = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as total FROM events")
    total_events = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as total FROM bookings WHERE status = 'paid'")
    total_bookings = cursor.fetchone()["total"]
    
    cursor.execute("SELECT SUM(total_amount) as revenue FROM bookings WHERE status = 'paid'")
    total_revenue = cursor.fetchone()["revenue"] or 0
    
    # Get events for display - ensure we're selecting image_path
    cursor.execute("SELECT id, name, image_path, start_date, location FROM events ORDER BY created_at DESC LIMIT 5")
    recent_events = cursor.fetchall()

    # Get all events with proper image paths
    query = "SELECT id, name, image_path, start_date, end_date, location, category, publish_status FROM events WHERE 1=1"
    values = []

    category = request.args.get("category")
    date_filter = request.args.get("date")

    if category:
        query += " AND category=%s"
        values.append(category)

    if date_filter == "today":
        query += " AND DATE(start_date) = CURDATE()"
    elif date_filter == "week":
        query += " AND YEARWEEK(start_date) = YEARWEEK(CURDATE())"

    query += " ORDER BY created_at DESC"
    cursor.execute(query, tuple(values))
    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_dashboard.html", 
                         events=events,
                         total_users=total_users,
                         total_events=total_events,
                         total_bookings=total_bookings,
                         total_revenue=total_revenue,
                         recent_events=recent_events)
@app.route("/admin/add_event", methods=["GET", "POST"])
def add_event():
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            name = request.form['name']
            description = request.form['description']
            location = request.form['location']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            category = request.form['category']
            reg_start = request.form['registration_start']
            reg_end = request.form['registration_end']
            publish_status = True if request.form.get("publish_status") == "on" else False
            latitude = request.form.get("latitude")
            longitude = request.form.get("longitude")

            # 🖼️ HANDLE IMAGE UPLOAD - THIS IS WHAT WAS MISSING!
            image_file = request.files.get('image')
            image_filename = None
            
            if image_file and image_file.filename != '':
                # Secure the filename and save it
                image_filename = secure_filename(image_file.filename)
                # Add timestamp to make filename unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{timestamp}_{image_filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image_file.save(image_path)
                flash("✅ Image uploaded successfully!", "success")
            else:
                flash("⚠️ No image uploaded. Using default placeholder.", "warning")
                image_filename = "default_event.jpg"  # You should have a default image

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO events 
                (name, description, location, start_date, end_date, category, 
                 registration_start, registration_end, publish_status, created_by, 
                 latitude, longitude, image_path) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (name, description, location, start_date, end_date, category, 
                  reg_start, reg_end, publish_status, session['user'], 
                  latitude, longitude, image_filename))
            conn.commit()
            cursor.close()
            conn.close()

            flash("✅ Event Created Successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "danger")
            return redirect(url_for("add_event"))

    return render_template("add_event.html")
# ✅ Edit Event
@app.route("/admin/edit_event/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cursor.fetchone()

    if not event:
        cursor.close()
        conn.close()
        flash("❌ Event not found!", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        category = request.form['category']
        reg_start = request.form['registration_start']
        reg_end = request.form['registration_end']
        publish_status = True if request.form.get("publish_status") == "on" else False

        # 🆕 Latitude & Longitude
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        cursor.execute("""
            UPDATE events
            SET name=%s, description=%s, location=%s, start_date=%s, end_date=%s,
                category=%s, registration_start=%s, registration_end=%s,
                publish_status=%s, latitude=%s, longitude=%s
            WHERE id=%s
        """, (name, description, location, start_date, end_date, category,
              reg_start, reg_end, publish_status, latitude, longitude, event_id))
        conn.commit()

        cursor.close()
        conn.close()

        flash("✅ Event updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    cursor.close()
    conn.close()
    return render_template("edit_event.html", event=event)

# ✅ Delete Event
@app.route("/admin/delete_event/<int:event_id>")
def delete_event(event_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("🗑️ Event Deleted Successfully!", "info")
    return redirect(url_for("admin_dashboard"))

# ✅ Toggle Publish
@app.route("/admin/toggle_publish/<int:event_id>")
def toggle_publish(event_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT publish_status FROM events WHERE id=%s", (event_id,))
    event = cursor.fetchone()
    new_status = not event['publish_status']

    cursor.execute("UPDATE events SET publish_status=%s WHERE id=%s", (new_status, event_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Event status updated!", "success")
    return redirect(url_for("admin_dashboard"))

# ✅ Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    session.pop("user_id", None)
    flash("Logged out successfully!", "info")
    return redirect(url_for("welcome"))

# ✅ View Attendees
@app.route("/admin/event/<int:event_id>/attendees")
def view_attendees(event_id):
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    gender_filter = request.args.get("gender", "")
    attended_filter = request.args.get("attended", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM attendees WHERE event_id=%s"
    params = [event_id]

    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")

    if gender_filter:
        query += " AND gender=%s"
        params.append(gender_filter)

    if attended_filter:
        query += " AND attended=%s"
        params.append(attended_filter == "yes")

    cursor.execute(query, tuple(params))
    attendees = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("view_attendees.html", attendees=attendees, event_id=event_id)


# ---------------- Profile Upload ----------------
@app.route("/upload_profile_pic", methods=["POST"])
def upload_profile_pic():
    if "profile_pic" in request.files:
        file = request.files["profile_pic"]
        if file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            session["profile_pic"] = filename
            flash("Profile picture updated!", "success")
    return redirect(url_for("dashboard"))
# ✅ My Bookings
# ---------------- My Bookings ----------------
@app.route("/my_bookings")
def my_bookings():
    if "user" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT id FROM users WHERE name=%s", (session["user"],))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        flash("❌ User not found!", "danger")
        return redirect(url_for("dashboard"))
    user_id = user['id']

    cursor.execute("""
        SELECT 
            b.id AS booking_id, 
            e.name AS event_name, 
            e.start_date,
            b.status,
            e.refund_policy
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.user_id=%s
        ORDER BY e.start_date ASC
    """, (user_id,))
    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("my_bookings.html", bookings=bookings)

# ---------------- Cancel Booking ----------------
@app.route("/cancel_booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if "user" not in session or session.get("role") != "user":
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT status, user_id FROM bookings WHERE id=%s", (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        flash("❌ Booking not found!", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("my_bookings"))

    if booking["user_id"] != session.get("user_id"):
        flash("❌ Unauthorized action!", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for("my_bookings"))

    if booking["status"] == "cancelled":
        flash("⚠️ Booking already cancelled!", "info")
        cursor.close()
        conn.close()
        return redirect(url_for("my_bookings"))

    cursor.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (booking_id,))
    conn.commit()

    cursor.close()
    conn.close()
    flash("✅ Booking cancelled successfully!", "success")
    return redirect(url_for("my_bookings"))
# @app.route("/my_bookings")
# def my_bookings():
#     if "user" not in session or session.get("role") != "user":
#         return redirect(url_for("login"))

#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("SELECT id FROM users WHERE name=%s", (session["user"],))
#     user = cursor.fetchone()
#     if not user:
#         cursor.close()
#         conn.close()
#         flash("❌ User not found!", "danger")
#         return redirect(url_for("dashboard"))
#     user_id = user['id']

#     cursor.execute("""
#         SELECT b.id AS booking_id, e.name AS event_name, e.start_date
#         FROM bookings b
#         JOIN events e ON b.event_id = e.id
#         WHERE b.user_id=%s
#         ORDER BY e.start_date ASC
#     """, (user_id,))
#     bookings = cursor.fetchall()

#     cursor.close()
#     conn.close()

#     return render_template("my_bookings.html", bookings=bookings)

# ✅ Book Event

from datetime import datetime

@app.route("/book_event/<int:event_id>", methods=["POST"])
def book_event(event_id):
    if "user_id" not in session:
        flash("Please login to book an event", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)  # ✅ fix here

    try:
        user_id = session["user_id"]
        booking_date = datetime.now()

        # Check if already booked
        cursor.execute("SELECT id FROM bookings WHERE user_id=%s AND event_id=%s", (user_id, event_id))
        existing = cursor.fetchone()
        if existing:
            flash("⚠️ You have already booked this event!", "info")
            return redirect(url_for("dashboard"))

        # Insert booking
        cursor.execute(
            "INSERT INTO bookings (user_id, event_id, booking_date, status) VALUES (%s,%s,%s,%s)",
            (user_id, event_id, booking_date, "pending")
        )
        conn.commit()
        booking_id = cursor.lastrowid

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error booking event: {str(e)}", "danger")
        return redirect(url_for("dashboard"))

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("payment", booking_id=booking_id))

# ✅ Event Preview
@app.route("/event/<int:event_id>")
def event_preview(event_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cursor.fetchone()
    cursor.close()
    conn.close()

    if not event:
        flash("❌ Event not found!", "danger")
        return redirect(url_for("dashboard"))
    return render_template("event_preview.html", event=event)








# ✅ Payment Page
@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
def payment(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.id, b.status, e.name, e.start_date, e.location,
               e.latitude, e.longitude,
               u.name as user_name
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id=%s
    """, (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        flash("Booking not found!", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Mock payment success
        cursor.execute("UPDATE bookings SET status=%s WHERE id=%s", ('paid', booking_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash("💳 Payment Successful!", "success")
        return redirect(url_for('ticket', booking_id=booking_id))

    cursor.close()
    conn.close()
    return render_template('payment.html', booking=booking)

# ✅ Ticket Page with QR
# ✅ Ticket Page with QR + Send Email
@app.route('/ticket/<int:booking_id>')
def ticket(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.id, b.status, e.name, e.start_date, e.location, 
               u.name as user_name, u.email
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id=%s
    """, (booking_id,))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    if not booking:
        flash("❌ Ticket not found!", "danger")
        return redirect(url_for('dashboard'))

    # ---- Generate QR ----
    qr_data = f"TicketID: {booking['id']}\nUser: {booking['user_name']}\nEvent: {booking['name']}\nDate: {booking['start_date']}\nLocation: {booking['location']}"
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # ---- Send Mail with QR ----
    try:
        msg = Message(
            subject="🎟 Your Event Ticket Confirmation",
            sender=app.config['MAIL_USERNAME'],
            recipients=[booking['email']]
        )
        msg.body = f"""
Hello {booking['user_name']},

✅ Your ticket has been confirmed!

Event: {booking['name']}
Date: {booking['start_date']}
Location: {booking['location']}
Ticket ID: {booking['id']}

📎 Your QR code ticket is attached with this email.
Show it at the entry gate.

Thanks,
EventHive Team
"""
        # QR code attach karo
        msg.attach("ticket_qr.png", "image/png", buf.read())
        mail.send(msg)
    except Exception as e:
        print("❌ Mail not sent:", e)

    return render_template('ticket.html', booking=booking)


# ✅ Generate QR Code (as image)
@app.route('/ticket_qr/<int:booking_id>')
def ticket_qr(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id, e.name, u.name as user_name, u.email
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id=%s
    """, (booking_id,))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    if not booking:
        return "Ticket not found", 404

    qr_data = f"TicketID: {booking['id']}\nUser: {booking['user_name']}\nEmail: {booking['email']}\nEvent: {booking['name']}"
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ✅ Cancel Booking Route
# ✅ View Attendees with Search and Filters (Renamed to avoid conflict)
# ✅ Admin Attendees Route (Properly indented)
@app.route("/admin/attendees")
def admin_attendees():
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))

    event_id = request.args.get('event_id', '')
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all events for dropdown
    cursor.execute("SELECT id, name FROM events ORDER BY start_date DESC")
    events = cursor.fetchall()
    
    # Build query for attendees
    query = """
        SELECT a.*, e.name as event_name, 
               CASE WHEN a.attended THEN 'Yes' ELSE 'No' END as attendance_status
        FROM attendees a 
        JOIN events e ON a.event_id = e.id 
        WHERE 1=1
    """
    params = []
    
    if event_id:
        query += " AND a.event_id = %s"
        params.append(event_id)
    
    if search:
        query += " AND (a.name LIKE %s OR a.email LIKE %s OR a.phone LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if status_filter:
        if status_filter == 'attended':
            query += " AND a.attended = TRUE"
        elif status_filter == 'not_attended':
            query += " AND a.attended = FALSE"
    
    query += " ORDER BY a.id DESC"
    
    cursor.execute(query, params)
    attendees = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("admin_attendees.html", 
                         attendees=attendees, 
                         events=events,
                         current_event_id=event_id,
                         search_query=search,
                         status_filter=status_filter)

# ✅ Export Attendees to CSV
@app.route("/admin/attendees/export")
def export_attendees_csv():
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))

    event_id = request.args.get('event_id', '')
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Build query for attendees (same as admin_attendees)
    query = """
        SELECT a.*, e.name as event_name, e.start_date as event_date,
               CASE WHEN a.attended THEN 'Yes' ELSE 'No' END as attendance_status
        FROM attendees a 
        JOIN events e ON a.event_id = e.id 
        WHERE 1=1
    """
    params = []
    
    if event_id:
        query += " AND a.event_id = %s"
        params.append(event_id)
    
    if search:
        query += " AND (a.name LIKE %s OR a.email LIKE %s OR a.phone LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if status_filter:
        if status_filter == 'attended':
            query += " AND a.attended = TRUE"
        elif status_filter == 'not_attended':
            query += " AND a.attended = FALSE"
    
    query += " ORDER BY a.id DESC"
    
    cursor.execute(query, params)
    attendees = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Create CSV content
    csv_content = "Event Name,Event Date,Attendee Name,Email,Phone,Gender,Total Guests,Attendance Status,Registration Date\n"
    
    for attendee in attendees:
        csv_content += f"\"{attendee['event_name']}\","
        csv_content += f"\"{attendee['event_date'].strftime('%Y-%m-%d %H:%M') if attendee['event_date'] else 'N/A'}\","
        csv_content += f"\"{attendee['name']}\","
        csv_content += f"\"{attendee['email']}\","
        csv_content += f"\"{attendee['phone']}\","
        csv_content += f"\"{attendee.get('gender', 'N/A')}\","
        csv_content += f"\"{attendee.get('total_guest', 1)}\","
        csv_content += f"\"{attendee['attendance_status']}\","
        csv_content += f"\"{attendee.get('registration_date', '').strftime('%Y-%m-%d %H:%M') if attendee.get('registration_date') else 'N/A'}\"\n"
    
    # Create response with CSV
    event_name = "all_events"
    if event_id and attendees:
        event_name = attendees[0]['event_name'].replace(" ", "_").lower()
    
    response = Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=attendees_{event_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )
    
    return response

# ✅ Mark Attendance
@app.route("/admin/attendee/<int:attendee_id>/attendance", methods=["POST"])
def update_attendance(attendee_id):
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    data = request.get_json()
    attended = data.get('attended', False)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "UPDATE attendees SET attended = %s WHERE id = %s",
            (attended, attendee_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Attendance updated successfully"})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        
        return jsonify({"success": False, "message": f"Error updating attendance: {str(e)}"}), 500

# ✅ Delete Attendee
@app.route("/admin/attendee/<int:attendee_id>/delete", methods=["POST"])
def delete_attendee_record(attendee_id):
    if "user" not in session or session.get("role") != "admin":
        flash("❌ Access Denied!", "danger")
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("DELETE FROM attendees WHERE id = %s", (attendee_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash("✅ Attendee deleted successfully!", "success")
        return redirect(url_for("admin_attendees"))
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        
        flash(f"❌ Error deleting attendee: {str(e)}", "danger")
        return redirect(url_for("admin_attendees"))
    
    
# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "voice_of_nagarika_secret"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ---------------- USER MODEL ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)


# ---------------- CITIZEN PROFILE ----------------
class CitizenProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))


# ---------------- AUTHORITY PROFILE ----------------
class AuthorityProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(100))
    department = db.Column(db.String(100))
    employee_id = db.Column(db.String(100))
    contact = db.Column(db.String(20))


# ---------------- COMPLAINT ----------------
class Complaint(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    complaint_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    reported_date = db.Column(db.Date, nullable=True)
    reported_time = db.Column(db.Time, nullable=True)


# ---------------- NLP PRIORITY ----------------
def predict_priority(text):
    text = text.lower()

    high_keywords = [
        "danger", "accident", "fire",
        "emergency", "crime", "flood"
    ]

    medium_keywords = [
        "garbage", "overflow",
        "leak", "water", "road"
    ]

    for word in high_keywords:
        if word in text:
            return "High"

    for word in medium_keywords:
        if word in text:
            return "Medium"

    return "Low"


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('homepage.html')


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "User already exists"

        new_user = User(username=username, password=password)

        db.session.add(new_user)
        db.session.commit()

        session.clear()
        session['username'] = username

        return redirect(url_for('role_selection'))

    return render_template('signup.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session.clear()
            session['username'] = user.username
            return redirect(url_for('role_selection'))

        return "Invalid username or password"

    return render_template('login.html')


# ---------------- ROLE SELECTION ----------------
@app.route('/roleselection')
def role_selection():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('roleselection.html')


# ---------------- CITIZEN DETAILS ----------------
@app.route('/citizendetails', methods=['GET', 'POST'])
def citizen_details():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        existing = CitizenProfile.query.filter_by(
            username=session['username']
        ).first()

        if existing:
            existing.name = request.form.get('name')
            existing.address = request.form.get('address')
            existing.phone = request.form.get('phone')
        else:
            profile = CitizenProfile(
                username=session['username'],
                name=request.form.get('name'),
                address=request.form.get('address'),
                phone=request.form.get('phone')
            )
            db.session.add(profile)

        db.session.commit()
        return redirect(url_for('citizen_dashboard'))

    return render_template('citizendetails.html')


# ---------------- AUTHORITY DETAILS ----------------
@app.route('/authoritydetails', methods=['GET', 'POST'])
def authority_details():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        profile = AuthorityProfile(
            username=session['username'],
            name=request.form.get('name'),
            role=request.form.get('role'),
            department=request.form.get('department'),
            employee_id=request.form.get('employee_id'),
            contact=request.form.get('contact')
        )

        db.session.add(profile)
        db.session.commit()

        return redirect(url_for('authority_dashboard'))

    return render_template('authoritydetails.html')


# ---------------- CITIZEN DASHBOARD ----------------
@app.route('/citizen')
def citizen_dashboard():
    return render_template('citizen.html')


# ---------------- SUBMIT COMPLAINT ----------------
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'username' not in session:
        return redirect(url_for('login'))

    complaint_id = "CMP-" + str(uuid.uuid4())[:8].upper()

    description = request.form.get('description')
    priority = predict_priority(description)

    complaint = Complaint(
        id=complaint_id,
        username=session['username'],
        complaint_type=request.form.get('complaint_type'),
        description=description,
        location=request.form.get('location'),
        priority=priority,
        reported_date=datetime.strptime(
            request.form.get('reported_date'),
            "%Y-%m-%d"
        ).date(),
        reported_time=datetime.strptime(
            request.form.get('reported_time'),
            "%H:%M"
        ).time()
    )

    db.session.add(complaint)
    db.session.commit()

    return redirect(url_for('my_complaints'))


# ---------------- MY COMPLAINTS ----------------
@app.route('/mycomplaints')
def my_complaints():
    if 'username' not in session:
        return redirect(url_for('login'))

    complaints = Complaint.query.filter_by(
        username=session['username']
    ).order_by(Complaint.submitted_at.desc()).all()

    return render_template('mycomplaints.html', complaints=complaints)


# ---------------- AUTHORITY DASHBOARD ----------------
@app.route('/authority')
def authority_dashboard():
    complaints = Complaint.query.order_by(
        Complaint.priority.desc(),
        Complaint.reported_date.asc(),
        Complaint.reported_time.asc()
    ).all()

    return render_template('authority.html', complaints=complaints)


# ---------------- HIGH PRIORITY ----------------
@app.route('/highpriority')
def high_priority():
    complaints = Complaint.query.filter_by(
        priority="High"
    ).order_by(
        Complaint.reported_date.asc(),
        Complaint.reported_time.asc()
    ).all()

    return render_template('highpriority.html', complaints=complaints)


# ---------------- ALL COMPLAINTS ----------------
@app.route('/allcomplaints')
def all_complaints():
    complaints = Complaint.query.order_by(
        Complaint.submitted_at.desc()
    ).all()

    return render_template(
        'allcomplaints.html',
        complaints=complaints
    )


# ---------------- PENDING ----------------
@app.route('/pending')
def pending_page():
    complaints = Complaint.query.filter_by(
        status="Pending"
    ).order_by(
        Complaint.reported_date.asc(),
        Complaint.reported_time.asc()
    ).all()

    return render_template('pending.html', complaints=complaints)


# ---------------- IN PROGRESS ----------------
@app.route('/progress')
def progress_page():
    complaints = Complaint.query.filter_by(
        status="In Progress"
    ).all()

    return render_template('progress.html', complaints=complaints)


# ---------------- RESOLVED ----------------
@app.route('/resolved')
def resolved_page():
    complaints = Complaint.query.filter_by(
        status="Resolved"
    ).all()

    return render_template('resolved.html', complaints=complaints)


# ---------------- UPDATE STATUS ----------------
@app.route('/update_status/<complaint_id>/<new_status>')
def update_status(complaint_id, new_status):
    complaint = Complaint.query.get(complaint_id)

    if complaint:
        complaint.status = new_status
        db.session.commit()

    if new_status == "Pending":
        return redirect(url_for('pending_page'))
    elif new_status == "In Progress":
        return redirect(url_for('progress_page'))
    elif new_status == "Resolved":
        return redirect(url_for('resolved_page'))

    return redirect(url_for('authority_dashboard'))


# ---------------- PROFILE ----------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_profile = CitizenProfile.query.filter_by(
        username=session['username']
    ).first()

    if request.method == 'POST':
        if user_profile:
            user_profile.name = request.form.get('username')
            user_profile.phone = request.form.get('phone')
            user_profile.address = request.form.get('address')
            db.session.commit()

        return redirect(url_for('profile'))

    return render_template('profile.html', profile=user_profile)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
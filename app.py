from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(BASE_DIR / "static"), template_folder=str(BASE_DIR / "templates"))
app.config["SECRET_KEY"] = "change-this-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'hospital.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Models (simple, self-contained so app.py runs without editing models.py)
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    specialty = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship("Patient", backref="appointments")
    doctor = db.relationship("Doctor", backref="appointments")


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="bills")


# Admin model + auth helpers
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return wrapped


@app.cli.command("create-admin")
def create_admin():
    """Create an admin user: flask --app app.py create-admin"""
    import getpass
    username = input("username: ").strip()
    if not username:
        print("username required")
        return
    if Admin.query.filter_by(username=username).first():
        print("admin exists")
        return
    password = getpass.getpass("password: ")
    confirm = getpass.getpass("confirm: ")
    if password != confirm:
        print("passwords do not match")
        return
    a = Admin(username=username)
    a.set_password(password)
    db.session.add(a)
    db.session.commit()
    print("Admin created:", username)


# CLI helper: create DB
@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Initialized the database.")


# Basic Pages
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/patients")
def patients_page():
    return render_template("patients.html")


@app.route("/doctors")
def doctors_page():
    return render_template("doctors.html")


@app.route("/appointments")
def appointments_page():
    return render_template("appointments.html")


@app.route("/billing")
def billing_page():
    return render_template("billing.html")


@app.route("/reports")
def reports_page():
    return render_template("reports.html")


# Simple JSON API for patients
@app.route("/api/patients", methods=["GET", "POST"])
def api_patients():
    if request.method == "GET":
        patients = Patient.query.order_by(Patient.created_at.desc()).all()
        result = []
        for p in patients:
            result.append({
                "id": p.id,
                "name": p.name,
                "age": p.age,
                "medical_history": p.medical_history,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        return jsonify(result)
    # POST: accept JSON or form
    data = request.get_json(silent=True) or request.form
    name = data.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    age = data.get("age")
    try:
        age_val = int(age) if age not in (None, "") else None
    except Exception:
        age_val = None
    p = Patient(name=name, age=age_val, medical_history=data.get("medical_history") or "")
    db.session.add(p)
    db.session.commit()
    return jsonify({
        "id": p.id,
        "name": p.name,
        "age": p.age,
        "medical_history": p.medical_history,
        "created_at": p.created_at.isoformat() if p.created_at else None
    }), 201


@app.route("/api/patients/<int:patient_id>", methods=["GET", "PUT", "DELETE"])
def api_patient_detail(patient_id):
    p = Patient.query.get_or_404(patient_id)
    if request.method == "GET":
        return jsonify({
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "medical_history": p.medical_history,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        if "name" in data:
            p.name = data.get("name") or p.name
        if "age" in data:
            try:
                p.age = int(data.get("age")) if data.get("age") not in (None, "") else None
            except Exception:
                pass
        if "medical_history" in data:
            p.medical_history = data.get("medical_history") or p.medical_history
        db.session.commit()
        return jsonify({"status": "ok"})
    # DELETE
    db.session.delete(p)
    db.session.commit()
    return jsonify({"status": "deleted"})


# Minimal APIs for doctors, appointments and billing (examples)
@app.route("/api/doctors", methods=["GET", "POST"])
def api_doctors():
    if request.method == "GET":
        doctors = Doctor.query.all()
        return jsonify([{"id": d.id, "name": d.name, "specialty": d.specialty, "phone": d.phone} for d in doctors])
    data = request.get_json() or request.form
    d = Doctor(name=data.get("name"), specialty=data.get("specialty"), phone=data.get("phone"))
    db.session.add(d)
    db.session.commit()
    return jsonify({"id": d.id}), 201


@app.route("/api/appointments", methods=["GET", "POST"])
def api_appointments():
    if request.method == "GET":
        apps = Appointment.query.all()
        return jsonify([{
            "id": a.id,
            "patient_id": a.patient_id,
            "doctor_id": a.doctor_id,
            "scheduled_at": a.scheduled_at.isoformat(),
            "notes": a.notes
        } for a in apps])
    data = request.get_json() or request.form
    try:
        scheduled_at = datetime.fromisoformat(data.get("scheduled_at"))
    except Exception:
        return jsonify({"error": "scheduled_at must be ISO datetime"}), 400
    ap = Appointment(patient_id=int(data.get("patient_id")), doctor_id=int(data.get("doctor_id")),
                     scheduled_at=scheduled_at, notes=data.get("notes"))
    db.session.add(ap)
    db.session.commit()
    return jsonify({"id": ap.id}), 201


@app.route("/api/bills", methods=["GET", "POST"])
def api_bills():
    if request.method == "GET":
        bills = Bill.query.all()
        return jsonify([{"id": b.id, "patient_id": b.patient_id, "amount": b.amount, "paid": b.paid} for b in bills])
    data = request.get_json() or request.form
    b = Bill(patient_id=int(data.get("patient_id")), amount=float(data.get("amount")), paid=bool(data.get("paid", False)))
    db.session.add(b)
    db.session.commit()
    return jsonify({"id": b.id}), 201


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# Admin UI + auth routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        data = request.form
        username = data.get("username", "")
        password = data.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_logged_in"] = True
            session["admin_username"] = admin.username
            flash("Logged in as admin.", "success")
            next_url = request.args.get("next") or url_for("admin_dashboard")
            return redirect(next_url)
        flash("Invalid credentials.", "danger")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")


# Admin CRUD: Patients
@app.route("/admin/patients", methods=["GET", "POST"])
@admin_required
def admin_patients():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name required", "danger")
            return redirect(url_for("admin_patients"))
        age = request.form.get("age")
        try:
            age_val = int(age) if age not in (None, "") else None
        except Exception:
            age_val = None
        p = Patient(name=name, age=age_val, medical_history=request.form.get("medical_history") or "")
        db.session.add(p)
        db.session.commit()
        flash("Patient created", "success")
        return redirect(url_for("admin_patients"))
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template("admin/patients.html", patients=patients)


@app.route("/admin/patients/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_patient(pid):
    p = Patient.query.get_or_404(pid)
    if request.method == "POST":
        p.name = request.form.get("name", p.name)
        age = request.form.get("age")
        try:
            p.age = int(age) if age not in (None, "") else None
        except Exception:
            pass
        p.medical_history = request.form.get("medical_history", p.medical_history)
        db.session.commit()
        flash("Patient updated", "success")
        return redirect(url_for("admin_patients"))
    return render_template("admin/edit_patient.html", patient=p)


@app.route("/admin/patients/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_delete_patient(pid):
    p = Patient.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("Patient deleted", "info")
    return redirect(url_for("admin_patients"))


# Admin CRUD: Doctors
@app.route("/admin/doctors", methods=["GET", "POST"])
@admin_required
def admin_doctors():
    if request.method == "POST":
        d = Doctor(name=request.form.get("name"), specialty=request.form.get("specialty"), phone=request.form.get("phone"))
        db.session.add(d)
        db.session.commit()
        flash("Doctor added", "success")
        return redirect(url_for("admin_doctors"))
    doctors = Doctor.query.all()
    return render_template("admin/doctors.html", doctors=doctors)


@app.route("/admin/doctors/<int:did>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_doctor(did):
    d = Doctor.query.get_or_404(did)
    if request.method == "POST":
        d.name = request.form.get("name", d.name)
        d.specialty = request.form.get("specialty", d.specialty)
        d.phone = request.form.get("phone", d.phone)
        db.session.commit()
        flash("Doctor updated", "success")
        return redirect(url_for("admin_doctors"))
    return render_template("admin/edit_doctor.html", doctor=d)


@app.route("/admin/doctors/<int:did>/delete", methods=["POST"])
@admin_required
def admin_delete_doctor(did):
    d = Doctor.query.get_or_404(did)
    db.session.delete(d)
    db.session.commit()
    flash("Doctor deleted", "info")
    return redirect(url_for("admin_doctors"))


# Admin CRUD: Appointments
@app.route("/admin/appointments", methods=["GET", "POST"])
@admin_required
def admin_appointments():
    if request.method == "POST":
        try:
            scheduled_at = datetime.fromisoformat(request.form.get("scheduled_at"))
        except Exception:
            flash("scheduled_at must be a valid datetime", "danger")
            return redirect(url_for("admin_appointments"))
        ap = Appointment(patient_id=int(request.form.get("patient_id")), doctor_id=int(request.form.get("doctor_id")),
                         scheduled_at=scheduled_at, notes=request.form.get("notes"))
        db.session.add(ap)
        db.session.commit()
        flash("Appointment created", "success")
        return redirect(url_for("admin_appointments"))
    apps = Appointment.query.order_by(Appointment.scheduled_at.desc()).all()
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    return render_template("admin/appointments.html", appointments=apps, patients=patients, doctors=doctors)


@app.route("/admin/appointments/<int:aid>/delete", methods=["POST"])
@admin_required
def admin_delete_appointment(aid):
    a = Appointment.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    flash("Appointment deleted", "info")
    return redirect(url_for("admin_appointments"))


# Admin CRUD: Bills
@app.route("/admin/bills", methods=["GET", "POST"])
@admin_required
def admin_bills():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount"))
        except Exception:
            flash("Amount must be numeric", "danger")
            return redirect(url_for("admin_bills"))
        b = Bill(patient_id=int(request.form.get("patient_id")), amount=amount, paid=bool(request.form.get("paid")))
        db.session.add(b)
        db.session.commit()
        flash("Bill created", "success")
        return redirect(url_for("admin_bills"))
    bills = Bill.query.order_by(Bill.issued_at.desc()).all()
    patients = Patient.query.all()
    return render_template("admin/bills.html", bills=bills, patients=patients)


@app.route("/admin/bills/<int:bid>/delete", methods=["POST"])
@admin_required
def admin_delete_bill(bid):
    b = Bill.query.get_or_404(bid)
    db.session.delete(b)
    db.session.commit()
    flash("Bill deleted", "info")
    return redirect(url_for("admin_bills"))


if __name__ == "__main__":
    # Ensure all tables exist (create missing tables even if hospital.db already exists)
    with app.app_context():
        db.create_all()
        # create default admin user if not present
        if not Admin.query.filter_by(username="admin").first():
            a = Admin(username="admin")
            a.set_password("abhi1234")
            db.session.add(a)
            db.session.commit()
            print("Default admin created: username='admin'")
        print("Ensured database tables exist at", BASE_DIR / "hospital.db")
    app.run(host="0.0.0.0", port=5000, debug=True)
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

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
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "medical_history": p.medical_history,
            "created_at": p.created_at.isoformat()
        } for p in patients])
    data = request.get_json() or request.form
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400
    p = Patient(name=name, age=data.get("age"), medical_history=data.get("medical_history"))
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id}), 201


@app.route("/api/patients/<int:patient_id>", methods=["GET", "PUT", "DELETE"])
def api_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    if request.method == "GET":
        return jsonify({
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "medical_history": p.medical_history,
            "created_at": p.created_at.isoformat()
        })
    if request.method == "PUT":
        data = request.get_json() or request.form
        p.name = data.get("name", p.name)
        p.age = data.get("age", p.age)
        p.medical_history = data.get("medical_history", p.medical_history)
        db.session.commit()
        return jsonify({"status": "updated"})
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


if __name__ == "__main__":
    # create DB automatically if missing (convenience for dev)
    if not (BASE_DIR / "hospital.db").exists():
        with app.app_context():
            db.create_all()
            print("Database created at", BASE_DIR / "hospital.db")
    app.run(host="0.0.0.0", port=5000, debug=True)
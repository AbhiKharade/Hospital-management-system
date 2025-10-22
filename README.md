# Hospital Management System

A small, beginner-friendly Hospital Management System built with Flask. It provides a simple web UI and JSON APIs to manage patients, doctors, appointments and billing for development and learning purposes.

## Highlights (simple / beginner level)
- Single-file runnable Flask app: [app.py](app.py)
- Example domain model: [`src.hospital.models.patient.Patient`](hospital-management/src/hospital/models/patient.py)
- Simple service helpers: [`src.hospital.services.patient_service.add_patient`](hospital-management/src/hospital/services/patient_service.py)
- Templates and static assets included for a minimal front-end
- Lightweight SQLite database (created automatically on first run)

## Quick start (development)
1. Create and activate a Python virtual environment (recommended):
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   ```
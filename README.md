# Hospital Management System

Lightweight, responsive web app to manage patients, doctors, appointments and billing. Designed to work well on phones and laptops and suitable for small clinics or demo projects.

## Features
- Patient CRUD (name, age, medical history)
- Doctor CRUD and specialties
- Appointment scheduling and listing
- Billing (create, mark paid, list)
- Simple admin interface with protected routes
- Responsive UI and mobile-first design
- Static assets support (local images)

## Requirements
- Python 3.10+
- Flask (requirements in project)
- SQLite (default) or another SQL DB if configured
- Dev container tested on Ubuntu 24.04

## Quick setup (dev)
1. Open dev container or local terminal in project root:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Initialize database (if project includes migration/initialization helper):
   ```bash
   # example - adjust to your app's commands
   python app.py init-db
   ```

3. (Optional) Create admin user (if supported):
   ```bash
   # example placeholder — replace with actual command in app.py
   python app.py create-admin
   ```

4. Download example images for the homepage (optional):
   ```bash
   mkdir -p static/images
   curl -L -o static/images/hero.jpg  "https://picsum.photos/1600/900"
   curl -L -o static/images/patient1.jpg "https://source.unsplash.com/800x600/?patient,doctor"
   curl -L -o static/images/patient2.jpg "https://source.unsplash.com/800x600/?nurse,patient"
   curl -L -o static/images/patient3.jpg "https://source.unsplash.com/800x600/?hospital,ward"
   chmod 644 static/images/*.jpg
   ```

5. Run the app:
   ```bash
   python app.py
   # open in host browser:
   $BROWSER http://127.0.0.1:5000
   ```

## Useful routes
- Public:
  - `/` — Home
  - `/dashboard` — Dashboard overview
  - `/patients` — Patient list (public page)
- API:
  - `/api/patients` — GET/POST
  - `/api/patients/<id>` — GET/PUT/DELETE
  - `/api/doctors`, `/api/appointments`, `/api/bills` (similar patterns)
- Admin:
  - `/admin/login` — Admin login
  - `/admin/patients`, `/admin/doctors`, `/admin/appointments`, `/admin/bills`

Adjust routes to match your app if names differ.

## Static files
Place images under `static/images/` and reference them in templates via:
```jinja
{{ url_for('static', filename='images/hero.jpg') }}
```

If images don't show:
- Verify files exist: `ls -l static/images`
- Check Flask static folder configuration in `app.py`
- Hard-refresh browser to bypass cache

## Contributing
- Fork, create topic branch, open PR
- Keep UI responsive and accessible
- Add tests for new backend logic where applicable

## License
Include a license file (e.g. MIT) in the project root if you plan to publish.

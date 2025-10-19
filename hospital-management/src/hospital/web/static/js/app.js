// app.js
document.addEventListener('DOMContentLoaded', function() {
    const addPatientForm = document.getElementById('add-patient-form');
    const updatePatientForm = document.getElementById('update-patient-form');

    if (addPatientForm) {
        addPatientForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(addPatientForm);
            fetch('/api/patients', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Patient added successfully!');
                    addPatientForm.reset();
                } else {
                    alert('Error adding patient: ' + data.message);
                }
            });
        });
    }

    if (updatePatientForm) {
        updatePatientForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(updatePatientForm);
            const patientId = updatePatientForm.dataset.patientId;
            fetch(`/api/patients/${patientId}`, {
                method: 'PUT',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Patient updated successfully!');
                } else {
                    alert('Error updating patient: ' + data.message);
                }
            });
        });
    }
});
import unittest
from src.hospital.services.patient_service import add_patient, update_patient, get_patient
from src.hospital.models.patient import Patient

class TestPatientService(unittest.TestCase):

    def setUp(self):
        self.patient = Patient(id=1, name="John Doe", age=30, medical_history="None")

    def test_add_patient(self):
        result = add_patient(self.patient)
        self.assertTrue(result)

    def test_update_patient(self):
        self.patient.name = "Jane Doe"
        result = update_patient(self.patient)
        self.assertTrue(result)

    def test_get_patient(self):
        add_patient(self.patient)
        result = get_patient(1)
        self.assertEqual(result.name, "John Doe")

if __name__ == '__main__':
    unittest.main()
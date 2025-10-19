document.addEventListener('DOMContentLoaded', function () {
  const addForm = document.getElementById('add-patient-form');
  if (addForm) {
    addForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        name: document.getElementById('name').value,
        age: document.getElementById('age').value,
        medical_history: document.getElementById('medical_history').value
      };
      const res = await fetch('/api/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        loadRecentPatients();
        addForm.reset();
        alert('Patient added');
      } else {
        const err = await res.json().catch(()=>({error:'server error'}));
        alert('Error: ' + (err.error || res.status));
      }
    });
    loadRecentPatients();
  }

  if (document.getElementById('patients-table')) {
    loadPatientsTable();
  }
});

async function loadRecentPatients() {
  const el = document.getElementById('patient-info');
  if (!el) return;
  const res = await fetch('/api/patients');
  if (!res.ok) { el.textContent = 'Failed to load'; return; }
  const data = await res.json();
  el.innerHTML = data.slice(0,5).map(p=>`<div><strong>${escapeHtml(p.name)}</strong> — ${p.age||''}</div>`).join('');
}

async function loadPatientsTable() {
  const res = await fetch('/api/patients');
  const tbody = document.querySelector('#patients-table tbody');
  if (!res.ok) { tbody.innerHTML = '<tr><td colspan="4">Failed to load</td></tr>'; return; }
  const rows = await res.json();
  tbody.innerHTML = rows.map(r=>`<tr><td>${r.id}</td><td>${escapeHtml(r.name)}</td><td>${r.age||''}</td><td>${escapeHtml(r.medical_history||'')}</td></tr>`).join('');
}

function escapeHtml(s){ return String(s).replace(/[&<>"']/g, (m)=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
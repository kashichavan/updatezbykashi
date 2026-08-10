// Kashii Updatez - Owner Portal Engine with Bulk Multi-Job Auto-Parser
document.addEventListener('DOMContentLoaded', () => {
  const loginView = document.getElementById('ownerLoginView');
  const dashboardView = document.getElementById('ownerDashboardView');
  const authBadge = document.getElementById('ownerAuthBadge');

  const formLogin = document.getElementById('formOwnerLogin');
  const formSmartParse = document.getElementById('formSmartParse');
  const formBulkParse = document.getElementById('formBulkParse');
  const formPostJob = document.getElementById('formOwnerPostJob');
  const formAddCategory = document.getElementById('formAddCategory');

  const categorySelect = document.getElementById('pCategory');
  const jobsTableContainer = document.getElementById('ownerJobsTableContainer');
  const categoryListContainer = document.getElementById('ownerCategoryList');

  init();

  async function init() {
    setupTabSwitching();
    await checkAuthStatus();
  }

  function setupTabSwitching() {
    document.querySelectorAll('.owner-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.owner-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');

        tab.classList.add('active');
        const targetId = tab.dataset.tab;
        const targetEl = document.getElementById(targetId);
        if (targetEl) targetEl.style.display = 'block';

        if (targetId === 'tabJobs') loadJobsList();
        if (targetId === 'tabCategory') loadCategoryList();
      });
    });
  }

  async function checkAuthStatus() {
    try {
      const res = await fetch('/api/admin/status/');
      const data = await res.json();
      if (data.is_admin) {
        showDashboard(data.username);
      } else {
        showLoginScreen();
      }
    } catch (err) {
      console.error('Auth check error:', err);
      showLoginScreen();
    }
  }

  function showLoginScreen() {
    if (loginView) loginView.style.display = 'block';
    if (dashboardView) dashboardView.style.display = 'none';
    if (authBadge) authBadge.innerHTML = '';
  }

  function showDashboard(username) {
    if (loginView) loginView.style.display = 'none';
    if (dashboardView) dashboardView.style.display = 'block';
    if (authBadge) {
      authBadge.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 13px; font-weight: 700; color: var(--ink);"><img src="/static/images/icon-apply.png" class="nav-icon" width="14" height="14" alt="Owner"> Owner: <strong>${escapeHtml(username)}</strong></span>
          <button id="btnLogoutOwner" class="button button-light" style="padding: 6px 12px; font-size: 12px;">Logout</button>
        </div>
      `;
      document.getElementById('btnLogoutOwner').addEventListener('click', handleLogout);
    }
    loadCategoriesForSelect();
  }

  if (formLogin) {
    formLogin.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('ownerUser').value.trim();
      const password = document.getElementById('ownerPass').value.trim();

      try {
        const res = await fetch('/api/admin/login/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast('Owner authenticated successfully!', 'success');
          showDashboard(data.username);
        } else {
          showToast(data.error || 'Invalid owner credentials.', 'error');
        }
      } catch (err) {
        showToast('Login request failed.', 'error');
      }
    });
  }

  async function handleLogout() {
    try {
      await fetch('/api/admin/logout/', { method: 'POST' });
      showToast('Logged out of owner session.', 'success');
      showLoginScreen();
    } catch (err) {
      console.error('Logout error:', err);
    }
  }

  // --- BULK MULTI-JOB AUTO-PARSER ENGINE ---

  if (formBulkParse) {
    formBulkParse.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawText = document.getElementById('bulkTextSnippet').value.trim();
      if (!rawText) return;

      try {
        showToast('Processing bulk job text snippet...', 'success');

        const res = await fetch('/api/owner/bulk-parse-and-post/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ raw_text: rawText })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`🚀 ${data.message}`, 'success');
          document.getElementById('bulkTextSnippet').value = '';
        } else {
          showToast(data.error || 'Failed to bulk parse job postings.', 'error');
        }
      } catch (err) {
        console.error('Error during bulk parse:', err);
        showToast('Server error during bulk auto-parsing.', 'error');
      }
    });
  }

  // --- SINGLE JOB AUTO-PARSER ENGINE ---

  if (formSmartParse) {
    formSmartParse.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawText = document.getElementById('rawTextSnippet').value.trim();
      if (!rawText) return;

      try {
        const res = await fetch('/api/owner/parse-and-post/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ raw_text: rawText })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`⚡ ${data.message} (${data.company_name} - ${data.title})`, 'success');
          document.getElementById('rawTextSnippet').value = '';
        } else {
          showToast(data.error || 'Failed to parse raw snippet.', 'error');
        }
      } catch (err) {
        showToast('Server error during smart parse.', 'error');
      }
    });
  }

  // --- MANUAL JOB POST FORM ENGINE ---

  if (formPostJob) {
    formPostJob.addEventListener('submit', async (e) => {
      e.preventDefault();

      const payload = {
        title: document.getElementById('pTitle').value.trim(),
        company_name: document.getElementById('pCompany').value.trim(),
        category_id: parseInt(document.getElementById('pCategory').value),
        job_type: document.getElementById('pJobType').value,
        apply_url: document.getElementById('pApplyUrl').value.trim(),
        stipend_salary: document.getElementById('pSalary').value.trim(),
        location: document.getElementById('pLocation').value.trim(),
        is_remote: document.getElementById('pLocation').value.toLowerCase().includes('remote'),
        skills_required: document.getElementById('pSkills').value.trim(),
        description: document.getElementById('pDescription').value.trim(),
        eligibility: document.getElementById('pEligibility').value.trim() || 'Open to all graduating students',
      };

      try {
        const res = await fetch('/api/jobs/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast('Job requirement posted! Active for 3 days.', 'success');
          formPostJob.reset();
        } else {
          showToast(data.error || 'Error creating job posting.', 'error');
        }
      } catch (err) {
        showToast('Failed to post job requirement.', 'error');
      }
    });
  }

  // --- CATEGORY & JOB MANAGEMENT ENGINES ---

  async function loadCategoriesForSelect() {
    if (!categorySelect) return;
    try {
      const res = await fetch('/api/categories/');
      const data = await res.json();
      categorySelect.innerHTML = data.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  async function loadJobsList() {
    if (!jobsTableContainer) return;
    jobsTableContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--muted);">Loading job postings...</div>';

    try {
      const res = await fetch('/api/jobs/?sort=newest');
      const data = await res.json();
      const jobs = data.jobs;

      if (!jobs || jobs.length === 0) {
        jobsTableContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--muted);">No active job requirements currently published.</div>';
        return;
      }

      jobsTableContainer.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Company & Role</th>
              <th>Apply Link</th>
              <th>Category</th>
              <th>Time Left (3-Day Limit)</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${jobs.map(j => `
              <tr>
                <td>#${j.id}</td>
                <td>
                  <strong>${escapeHtml(j.company_name)}</strong><br>
                  <span style="color: var(--muted);">${escapeHtml(j.title)}</span>
                </td>
                <td>
                  <a href="${escapeHtml(j.apply_url)}" target="_blank" style="color: var(--blue-primary); font-size: 12px; font-weight: 700; word-break: break-all;">
                    ${escapeHtml(j.apply_url ? (j.apply_url.length > 30 ? j.apply_url.substring(0, 30) + '...' : j.apply_url) : 'No link')} ↗
                  </a>
                </td>
                <td>${escapeHtml(j.category_name)}</td>
                <td><span style="font-weight: 700; color: var(--blue-primary);">${j.time_left_seconds > 0 ? Math.ceil(j.time_left_seconds / 3600) + 'h left' : 'Expired'}</span></td>
                <td>
                  <div style="display: flex; gap: 6px;">
                    <button class="button button-light btn-edit-job" data-id="${j.id}" style="padding: 4px 10px; font-size: 11px; color: var(--blue-primary); border-color: var(--blue-border);">
                      ✏️ Edit
                    </button>
                    <button class="button button-light btn-delete-job" data-id="${j.id}" style="padding: 4px 10px; font-size: 11px; color: #ef4444; border-color: #fca5a5;">
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;

      document.querySelectorAll('.btn-edit-job').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.id;
          await openEditModal(id);
        });
      });

      document.querySelectorAll('.btn-delete-job').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.id;
          if (confirm(`Delete opportunity #${id}?`)) {
            await deleteJob(id);
          }
        });
      });

    } catch (err) {
      console.error('Failed to load jobs:', err);
      jobsTableContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #ef4444;">Error loading jobs list.</div>';
    }
  }

  // --- EDIT JOB MODAL LOGIC ---
  const editModal = document.getElementById('editJobModal');
  const formEditJob = document.getElementById('formEditJob');
  const btnCloseEditModal = document.getElementById('btnCloseEditModal');
  const btnCancelEdit = document.getElementById('btnCancelEdit');

  async function openEditModal(id) {
    try {
      // Load categories into modal select
      const catRes = await fetch('/api/categories/');
      const catData = await catRes.json();
      const eCategorySelect = document.getElementById('eCategory');
      if (eCategorySelect) {
        eCategorySelect.innerHTML = catData.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
      }

      // Fetch job details
      const res = await fetch(`/api/jobs/${id}/`);
      const data = await res.json();
      const job = data.job;

      document.getElementById('eJobId').value = job.id;
      document.getElementById('eTitle').value = job.title;
      document.getElementById('eCompany').value = job.company_name;
      if (eCategorySelect) {
        const matchingCat = catData.categories.find(c => c.slug === job.category_slug);
        if (matchingCat) eCategorySelect.value = matchingCat.id;
      }
      document.getElementById('eJobType').value = job.job_type;
      document.getElementById('eApplyUrl').value = job.apply_url || '';
      document.getElementById('eSalary').value = job.stipend_salary;
      document.getElementById('eLocation').value = job.location;
      document.getElementById('eSkills').value = job.skills_required;
      document.getElementById('eDescription').value = job.description;
      document.getElementById('eEligibility').value = job.eligibility || '';

      if (editModal) editModal.style.display = 'block';
    } catch (err) {
      showToast('Error loading posting details for edit.', 'error');
    }
  }

  function closeEditModal() {
    if (editModal) editModal.style.display = 'none';
  }

  if (btnCloseEditModal) btnCloseEditModal.addEventListener('click', closeEditModal);
  if (btnCancelEdit) btnCancelEdit.addEventListener('click', closeEditModal);

  if (formEditJob) {
    formEditJob.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('eJobId').value;
      const payload = {
        title: document.getElementById('eTitle').value.trim(),
        company_name: document.getElementById('eCompany').value.trim(),
        category_id: parseInt(document.getElementById('eCategory').value),
        job_type: document.getElementById('eJobType').value,
        apply_url: document.getElementById('eApplyUrl').value.trim(),
        stipend_salary: document.getElementById('eSalary').value.trim(),
        location: document.getElementById('eLocation').value.trim(),
        skills_required: document.getElementById('eSkills').value.trim(),
        description: document.getElementById('eDescription').value.trim(),
        eligibility: document.getElementById('eEligibility').value.trim(),
      };

      try {
        const res = await fetch(`/api/owner/jobs/${id}/update/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast('Job posting updated successfully!', 'success');
          closeEditModal();
          loadJobsList();
        } else {
          showToast(data.error || 'Failed to update job posting.', 'error');
        }
      } catch (err) {
        showToast('Error saving job posting updates.', 'error');
      }
    });
  }

  async function deleteJob(id) {
    try {
      const res = await fetch(`/api/owner/jobs/${id}/delete/`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Posting deleted successfully.', 'success');
        loadJobsList();
      } else {
        showToast(data.error || 'Failed to delete posting.', 'error');
      }
    } catch (err) {
      showToast('Error deleting posting.', 'error');
    }
  }

  async function loadCategoryList() {
    if (!categoryListContainer) return;
    try {
      const res = await fetch('/api/categories/');
      const data = await res.json();
      categoryListContainer.innerHTML = data.categories.map(c => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; background: var(--paper); border: 1px solid var(--subtle-border); border-radius: 12px; margin-bottom: 8px;">
          <div>
            <strong style="font-size: 14px;">${escapeHtml(c.name)}</strong>
            <div style="font-size: 12px; color: var(--muted);">${escapeHtml(c.slug)}</div>
          </div>
          <span style="font-size: 12px; font-weight: 700; color: var(--blue-primary);">${c.active_count} Active</span>
        </div>
      `).join('');
    } catch (err) {
      console.error('Error loading category list:', err);
    }
  }

  if (formAddCategory) {
    formAddCategory.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('catName').value.trim();
      const description = document.getElementById('catDescription').value.trim();

      try {
        const res = await fetch('/api/owner/categories/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, description })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`Category "${data.name}" added successfully!`, 'success');
          formAddCategory.reset();
          loadCategoryList();
          loadCategoriesForSelect();
        } else {
          showToast(data.error || 'Failed to add category.', 'error');
        }
      } catch (err) {
        showToast('Server error adding category.', 'error');
      }
    });
  }

  function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <span>${type === 'success' ? '✅' : '⚠️'}</span>
      <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return '';
    const stripped = String(str).replace(/<[^>]*>?/gm, '');
    return stripped.replace(/[&<>"']/g, function(m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
  }
});

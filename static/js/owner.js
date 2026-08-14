// Kashii Updatez - Executive Owner CRM Engine
document.addEventListener('DOMContentLoaded', () => {
  const loginView = document.getElementById('ownerLoginView');
  const dashboardView = document.getElementById('ownerDashboardView');
  const sidebarUserLabel = document.getElementById('sidebarUserLabel');

  const formLogin = document.getElementById('formOwnerLogin');
  const formSmartParse = document.getElementById('formSmartParse');
  const formBulkParse = document.getElementById('formBulkParse');
  const formPostJob = document.getElementById('formCreateJob');
  const formAddCategory = document.getElementById('formAddCategory');

  const categorySelect = document.getElementById('postCategory');
  const filterCategorySelect = document.getElementById('crmCategoryFilter');
  const filterStatusSelect = document.getElementById('crmStatusFilter');
  const searchInput = document.getElementById('crmSearchJobs');

  const jobsTableContainer = document.getElementById('ownerJobsTableContainer');
  const categoryListContainer = document.getElementById('ownerCategoryList');
  const activityStream = document.getElementById('crmActivityLogStream');

  let allLoadedJobs = [];
  let currentJobsPage = 1;

  init();

  async function init() {
    setupTabSwitching();
    setupFiltersAndSearch();
    await checkAuthStatus();
  }

  const tabTitles = {
    'tabJobs': { title: 'Opportunity Pipeline CRM', sub: 'Track active student requirements, manage postings, run bulk parsers, and execute workflow actions.' },
    'tabBulkParse': { title: 'Bulk Multi-Job Automation', sub: 'Parse multi-job Telegram/WhatsApp messages & auto-publish all leads in 1 click.' },
    'tabSmartParse': { title: '1-Click Single Parser', sub: 'Extract details from a single job requirement snippet & publish instantly.' },
    'tabPost': { title: 'Publish New Opportunity', sub: 'Manual form to publish structured student job or internship postings.' },
    'tabCategory': { title: 'Taxonomy & Categories', sub: 'Manage job categories, view active posting counts, and organize leads.' },
    'tabActivity': { title: 'System Activity & Audit Log', sub: 'Real-time audit log of owner parsing actions, status toggles, and publishing events.' }
  };

  const tabUrlMap = {
    'tabJobs': '/owner/manage-jobs/',
    'tabBulkParse': '/owner/bulk-parser/',
    'tabSmartParse': '/owner/single-parser/',
    'tabPost': '/owner/post-job/',
    'tabCategory': '/owner/categories/',
    'tabActivity': '/owner/activity/'
  };

  const urlTabMap = {
    '/owner/': 'tabJobs',
    '/owner/manage-jobs/': 'tabJobs',
    '/owner/bulk-parser/': 'tabBulkParse',
    '/owner/single-parser/': 'tabSmartParse',
    '/owner/post-job/': 'tabPost',
    '/owner/categories/': 'tabCategory',
    '/owner/activity/': 'tabActivity'
  };

  function setupTabSwitching() {
    document.querySelectorAll('.owner-nav-item').forEach(tab => {
      tab.addEventListener('click', () => {
        const targetId = tab.dataset.tab;
        switchTab(targetId, true);
      });
    });

    const currentPath = window.location.pathname;
    if (urlTabMap[currentPath]) {
      switchTab(urlTabMap[currentPath], false);
    } else {
      switchTab('tabJobs', false);
    }

    const pageSizeSelect = document.getElementById('ownerPageSize');
    if (pageSizeSelect) {
      pageSizeSelect.addEventListener('change', () => {
        loadJobsList(1);
      });
    }
  }

  function switchTab(targetId, updateHistory = true) {
    document.querySelectorAll('.owner-nav-item').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');

    document.querySelectorAll(`.owner-nav-item[data-tab="${targetId}"]`).forEach(btn => btn.classList.add('active'));

    const targetEl = document.getElementById(targetId);
    if (targetEl) targetEl.style.display = 'block';

    const headerTitle = document.getElementById('crmWorkspaceHeading');
    const headerSub = document.getElementById('crmWorkspaceSubheading');
    if (headerTitle && tabTitles[targetId]) headerTitle.textContent = tabTitles[targetId].title;
    if (headerSub && tabTitles[targetId]) headerSub.textContent = tabTitles[targetId].sub;

    if (updateHistory && tabUrlMap[targetId]) {
      window.history.pushState({}, '', tabUrlMap[targetId]);
    }

    if (targetId === 'tabJobs') loadJobsList(1);
    if (targetId === 'tabCategory') loadCategoryList();
  }

  function setupFiltersAndSearch() {
    if (searchInput) {
      searchInput.addEventListener('input', debounce(() => {
        renderFilteredJobs();
      }, 250));
    }

    if (filterCategorySelect) {
      filterCategorySelect.addEventListener('change', () => {
        renderFilteredJobs();
      });
    }

    if (filterStatusSelect) {
      filterStatusSelect.addEventListener('change', () => {
        loadJobsList(1);
      });
    }
  }

  async function checkAuthStatus() {
    try {
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = {};
      if (jwtAccess) {
        headers['Authorization'] = `Bearer ${jwtAccess}`;
      }
      const res = await fetch('/api/admin/status/', { headers });
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
  }

  function showDashboard(username) {
    if (loginView) loginView.style.display = 'none';
    if (dashboardView) dashboardView.style.display = 'block';
    if (sidebarUserLabel) sidebarUserLabel.textContent = username || 'Owner';

    const btnLogout = document.getElementById('btnLogoutOwner');
    if (btnLogout) {
      btnLogout.addEventListener('click', handleLogout);
    }

    loadCategoriesForSelect();
    loadKpiStats();
    loadJobsList(1);
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
          if (data.access) {
            localStorage.setItem('owner_jwt_access', data.access);
            localStorage.setItem('owner_jwt_refresh', data.refresh);
          }
          showToast('Authenticated successfully as Executive Owner!', 'success');
          logActivity(`Owner login: ${username}`, 'Success');
          
          const urlParams = new URLSearchParams(window.location.search);
          const nextUrl = urlParams.get('next');
          if (nextUrl) {
            window.location.href = nextUrl;
            return;
          }
          
          showDashboard(data.username);
        } else {
          showToast(data.error || 'Invalid credentials.', 'error');
        }
      } catch (err) {
        showToast('Login request failed.', 'error');
      }
    });
  }

  async function handleLogout() {
    try {
      localStorage.removeItem('owner_jwt_access');
      localStorage.removeItem('owner_jwt_refresh');
      await fetch('/api/admin/logout/', { method: 'POST' });
      showToast('Logged out of CRM session.', 'success');
      showLoginScreen();
    } catch (err) {
      console.error('Logout error:', err);
    }
  }

  // --- KPI STATS CALCULATOR ---
  async function loadKpiStats() {
    try {
      const res = await fetch('/api/jobs/?page=1&page_size=100');
      const data = await res.json();
      const jobs = data.jobs || [];

      const activeCount = jobs.filter(j => j.time_left_seconds > 0 && j.status !== 'EXPIRED').length;
      const expiredCount = jobs.filter(j => j.time_left_seconds <= 0 || j.status === 'EXPIRED').length;

      const kpiActive = document.getElementById('kpiActiveJobs');
      const kpiTotal = document.getElementById('kpiTotalJobs');
      const kpiExpired = document.getElementById('kpiExpiredJobs');
      const sidebarBadge = document.getElementById('sidebarActiveCount');

      if (kpiActive) kpiActive.textContent = activeCount;
      if (sidebarBadge) sidebarBadge.textContent = `${activeCount} Live`;
      if (kpiTotal) kpiTotal.textContent = data.total_count || jobs.length;
      if (kpiExpired) kpiExpired.textContent = expiredCount;

      const catRes = await fetch('/api/categories/');
      const catData = await catRes.json();
      const kpiCat = document.getElementById('kpiCategories');
      if (kpiCat && catData.categories) kpiCat.textContent = catData.categories.length;

    } catch (err) {
      console.error('Error fetching KPI stats:', err);
    }
  }

  // --- BULK MULTI-JOB AUTO-PARSER ENGINE ---

  if (formBulkParse) {
    formBulkParse.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawText = document.getElementById('bulkRawText').value.trim();
      if (!rawText) return;

      try {
        showToast('Processing bulk multi-job parser pipeline...', 'success');
        const jwtAccess = localStorage.getItem('owner_jwt_access');
        const headers = { 'Content-Type': 'application/json' };
        if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

        const res = await fetch('/api/owner/bulk-parse-and-post/', {
          method: 'POST',
          headers,
          body: JSON.stringify({ raw_text: rawText })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`⚡ ${data.message}`, 'success');
          logActivity(`Bulk Multi-Job Parser executed`, data.message);
          document.getElementById('bulkRawText').value = '';
          loadKpiStats();
          switchTab('tabJobs');
        } else {
          showToast(data.error || 'Failed to bulk parse postings.', 'error');
        }
      } catch (err) {
        showToast('Server error during bulk auto-parsing.', 'error');
      }
    });
  }

  // --- SINGLE JOB AUTO-PARSER ENGINE ---

  if (formSmartParse) {
    formSmartParse.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawText = document.getElementById('rawText').value.trim();
      if (!rawText) return;

      try {
        const jwtAccess = localStorage.getItem('owner_jwt_access');
        const headers = { 'Content-Type': 'application/json' };
        if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

        const res = await fetch('/api/owner/parse-and-post/', {
          method: 'POST',
          headers,
          body: JSON.stringify({ raw_text: rawText })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`🎯 Parsed & Published: ${data.company_name} - ${data.title}`, 'success');
          logActivity(`Single Parser executed`, `${data.company_name} - ${data.title}`);
          document.getElementById('rawText').value = '';
          loadKpiStats();
          switchTab('tabJobs');
        } else {
          showToast(data.error || 'Failed to parse snippet.', 'error');
        }
      } catch (err) {
        showToast('Server error during single parse.', 'error');
      }
    });
  }

  // --- MANUAL JOB POST FORM ENGINE ---

  if (formPostJob) {
    formPostJob.addEventListener('submit', async (e) => {
      e.preventDefault();

      const payload = {
        title: document.getElementById('postTitle').value.trim(),
        company_name: document.getElementById('postCompany').value.trim(),
        category_id: parseInt(document.getElementById('postCategory').value),
        job_type: document.getElementById('postJobType').value,
        apply_url: document.getElementById('postApplyUrl').value.trim(),
        stipend_salary: document.getElementById('postSalary').value.trim(),
        location: document.getElementById('postLocation').value.trim(),
        is_remote: document.getElementById('postLocation').value.toLowerCase().includes('remote'),
        skills_required: document.getElementById('postSkills').value.trim(),
        description: document.getElementById('postDescription').value.trim(),
        eligibility: document.getElementById('postEligibility').value.trim() || 'Open to all graduating students',
      };

      try {
        const jwtAccess = localStorage.getItem('owner_jwt_access');
        const headers = { 'Content-Type': 'application/json' };
        if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

        const res = await fetch('/api/jobs/', {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast('Job requirement published to pipeline!', 'success');
          logActivity('Manual Job Published', `${payload.company_name} - ${payload.title}`);
          formPostJob.reset();
          loadKpiStats();
          switchTab('tabJobs');
        } else {
          showToast(data.error || 'Error creating job posting.', 'error');
        }
      } catch (err) {
        showToast('Failed to post job requirement.', 'error');
      }
    });
  }

  // --- CATEGORIES LOADING ---

  async function loadCategoriesForSelect() {
    if (!categorySelect) return;
    try {
      const res = await fetch('/api/categories/');
      const data = await res.json();
      const optionsHtml = data.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
      categorySelect.innerHTML = optionsHtml;
      
      const modalSelect = document.getElementById('eCategory');
      if (modalSelect) modalSelect.innerHTML = optionsHtml;

      if (filterCategorySelect) {
        filterCategorySelect.innerHTML = '<option value="ALL">All Categories</option>' + data.categories.map(c => `<option value="${c.slug}">${escapeHtml(c.name)}</option>`).join('');
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  // --- OPPORTUNITY PIPELINE LIST ENGINE ---

  async function loadJobsList(page = 1) {
    if (!jobsTableContainer) return;
    currentJobsPage = page;
    jobsTableContainer.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--crm-muted);">Loading CRM opportunity pipeline...</div>';

    const pageSizeSelect = document.getElementById('ownerPageSize');
    const pageSize = pageSizeSelect ? pageSizeSelect.value : 10;
    const statusVal = filterStatusSelect ? filterStatusSelect.value : 'ALL';

    let url = `/api/jobs/?sort=newest&page=${page}&page_size=${pageSize}`;
    if (statusVal === 'EXPIRED') {
      url += `&status=EXPIRED`;
    }

    try {
      const res = await fetch(url);
      const data = await res.json();
      allLoadedJobs = data.jobs || [];

      renderFilteredJobs(data);

    } catch (err) {
      console.error('Failed to load jobs:', err);
      jobsTableContainer.innerHTML = '<div style="padding: 24px; text-align: center; color: #ef4444;">Error loading opportunity pipeline data.</div>';
    }
  }

  function renderFilteredJobs(serverPaginationData = null) {
    if (!jobsTableContainer) return;

    let filtered = [...allLoadedJobs];
    const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
    const selectedCat = filterCategorySelect ? filterCategorySelect.value : 'ALL';

    if (query) {
      filtered = filtered.filter(j => 
        j.company_name.toLowerCase().includes(query) ||
        j.title.toLowerCase().includes(query) ||
        j.skills_required.toLowerCase().includes(query) ||
        (j.location && j.location.toLowerCase().includes(query))
      );
    }

    if (selectedCat !== 'ALL') {
      filtered = filtered.filter(j => j.category_slug === selectedCat);
    }

    if (!filtered || filtered.length === 0) {
      jobsTableContainer.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--crm-muted);">No opportunity leads matched your search or status filter.</div>';
      return;
    }

    const curPage = serverPaginationData ? serverPaginationData.current_page : 1;
    const totalPages = serverPaginationData ? serverPaginationData.total_pages : 1;
    const totalCount = serverPaginationData ? serverPaginationData.total_count : filtered.length;
    const hasPrev = serverPaginationData ? serverPaginationData.has_previous : false;
    const hasNext = serverPaginationData ? serverPaginationData.has_next : false;

    jobsTableContainer.innerHTML = `
      <table class="crm-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Company &amp; Role Title</th>
            <th>Application Link</th>
            <th>Category</th>
            <th>Pipeline Status</th>
            <th>Workflow Actions</th>
          </tr>
        </thead>
        <tbody>
          ${filtered.map(j => {
            const isExpired = j.time_left_seconds <= 0 || j.status === 'EXPIRED';
            const hoursLeft = Math.ceil(j.time_left_seconds / 3600);
            return `
            <tr>
              <td><span style="font-family: monospace; font-weight: 800; color: #64748b;">#${j.id}</span></td>
              <td>
                <strong style="color: #ffffff; font-size: 14.5px;">${escapeHtml(j.company_name)}</strong>
                <div style="color: var(--crm-muted); font-size: 12.5px; margin-top: 2px;">${escapeHtml(j.title)}</div>
                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">📍 ${escapeHtml(j.location || 'India')} • 💰 ${escapeHtml(j.stipend_salary)}</div>
              </td>
              <td>
                <a href="${escapeHtml(j.apply_url)}" target="_blank" style="color: var(--crm-cyan); font-size: 12px; font-weight: 700; text-decoration: none;">
                  ${escapeHtml(j.apply_url ? (j.apply_url.length > 28 ? j.apply_url.substring(0, 28) + '...' : j.apply_url) : 'No link')} ↗
                </a>
              </td>
              <td>
                <span style="background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 800;">
                  ${escapeHtml(j.category_name)}
                </span>
              </td>
              <td>
                <span class="crm-status-pill ${isExpired ? 'crm-status-expired' : 'crm-status-active'}">
                  ${isExpired ? '🔴 Unpublished / Expired' : '🟢 Active (' + hoursLeft + 'h left)'}
                </span>
              </td>
              <td>
                <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                  <button class="btn-crm-action btn-toggle-job" data-id="${j.id}" style="background: rgba(255,255,255,0.05); color: ${isExpired ? '#10b981' : '#f59e0b'}; border-color: ${isExpired ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'};">
                    ${isExpired ? '🚀 Publish' : '⏸️ Unpublish'}
                  </button>
                  <button class="btn-crm-action btn-edit-job" data-id="${j.id}" style="background: rgba(6, 182, 212, 0.1); color: var(--crm-cyan); border-color: rgba(6, 182, 212, 0.3);">
                    ✏️ Edit
                  </button>
                  <button class="btn-crm-action btn-delete-job" data-id="${j.id}" style="background: rgba(244, 63, 94, 0.1); color: var(--crm-rose); border-color: rgba(244, 63, 94, 0.3);">
                    🗑️ Delete
                  </button>
                </div>
              </td>
            </tr>
          `}).join('')}
        </tbody>
      </table>

      <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: rgba(13, 18, 31, 0.95); border-top: 1px solid var(--crm-border); border-radius: 0 0 16px 16px;">
        <div style="font-size: 12.5px; color: var(--crm-muted); font-weight: 600;">
          Showing Page <strong style="color: #ffffff;">${curPage}</strong> of <strong style="color: #ffffff;">${totalPages}</strong> (${totalCount} total leads)
        </div>
        <div style="display: flex; gap: 8px;">
          <button id="btnPrevPage" class="btn-crm-action" style="background: rgba(255,255,255,0.05); color: #ffffff; padding: 8px 16px; border-color: rgba(255,255,255,0.15);" ${!hasPrev ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''}>
            ← Previous
          </button>
          <button id="btnNextPage" class="btn-crm-action" style="background: rgba(255,255,255,0.05); color: #ffffff; padding: 8px 16px; border-color: rgba(255,255,255,0.15);" ${!hasNext ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''}>
            Next →
          </button>
        </div>
      </div>
    `;

    const btnPrev = document.getElementById('btnPrevPage');
    const btnNext = document.getElementById('btnNextPage');
    if (btnPrev && hasPrev) {
      btnPrev.addEventListener('click', () => loadJobsList(curPage - 1));
    }
    if (btnNext && hasNext) {
      btnNext.addEventListener('click', () => loadJobsList(curPage + 1));
    }

    document.querySelectorAll('.btn-toggle-job').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        await toggleJobStatus(id);
      });
    });

    document.querySelectorAll('.btn-edit-job').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        await openEditModal(id);
      });
    });

    document.querySelectorAll('.btn-delete-job').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        if (confirm(`Are you sure you want to delete lead #${id}?`)) {
          await deleteJob(id);
        }
      });
    });
  }

  // --- EDIT JOB MODAL DRAWER LOGIC ---
  const editModal = document.getElementById('editJobModal');
  const formEditJob = document.getElementById('formEditJob');
  const btnCloseEditModal = document.getElementById('btnCloseEditModal');
  const btnCancelEdit = document.getElementById('btnCancelEdit');

  async function openEditModal(id) {
    try {
      await loadCategoriesForSelect();
      const res = await fetch(`/api/jobs/${id}/`);
      const data = await res.json();
      const job = data.job;

      document.getElementById('eJobId').value = job.id;
      document.getElementById('eTitle').value = job.title;
      document.getElementById('eCompany').value = job.company_name;
      
      const eCategorySelect = document.getElementById('eCategory');
      if (eCategorySelect) {
        const catRes = await fetch('/api/categories/');
        const catData = await catRes.json();
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
      showToast('Error loading lead details for edit.', 'error');
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
          showToast('Lead updated successfully!', 'success');
          logActivity(`Lead updated #${id}`, `${payload.company_name} - ${payload.title}`);
          closeEditModal();
          loadJobsList(currentJobsPage);
        } else {
          showToast(data.error || 'Failed to update lead.', 'error');
        }
      } catch (err) {
        showToast('Error saving lead updates.', 'error');
      }
    });
  }

  async function toggleJobStatus(id) {
    try {
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = {};
      if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

      const res = await fetch(`/api/owner/jobs/${id}/toggle-status/`, { method: 'POST', headers });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(data.message || 'Status updated!', 'success');
        logActivity(`Status toggle #${id}`, data.message);
        loadKpiStats();
        await loadJobsList(currentJobsPage);
      } else {
        showToast(data.error || 'Failed to toggle status.', 'error');
      }
    } catch (err) {
      showToast('Error toggling status.', 'error');
    }
  }

  async function deleteJob(id) {
    try {
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = {};
      if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

      const res = await fetch(`/api/owner/jobs/${id}/delete/`, { method: 'POST', headers });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Lead deleted from pipeline.', 'success');
        logActivity(`Lead deleted #${id}`, 'Permanently removed from CRM');
        loadKpiStats();
        loadJobsList(currentJobsPage);
      } else {
        showToast(data.error || 'Failed to delete lead.', 'error');
      }
    } catch (err) {
      showToast('Error deleting lead.', 'error');
    }
  }

  // --- CATEGORIES LISTING ---

  async function loadCategoryList() {
    if (!categoryListContainer) return;
    try {
      const res = await fetch('/api/categories/');
      const data = await res.json();
      categoryListContainer.innerHTML = data.categories.map(c => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: rgba(13, 18, 31, 0.8); border: 1px solid var(--crm-border); border-radius: 16px;">
          <div>
            <strong style="font-size: 14.5px; color: #ffffff;">${escapeHtml(c.name)}</strong>
            <div style="font-size: 12px; color: var(--crm-muted); font-family: monospace; margin-top: 2px;">/${escapeHtml(c.slug)}</div>
          </div>
          <span style="font-size: 12px; font-weight: 800; color: var(--crm-cyan); background: rgba(6, 182, 212, 0.15); padding: 4px 10px; border-radius: 12px; border: 1px solid rgba(6, 182, 212, 0.3);">
            ${c.active_count} Active Leads
          </span>
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
        const jwtAccess = localStorage.getItem('owner_jwt_access');
        const headers = { 'Content-Type': 'application/json' };
        if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

        const res = await fetch('/api/owner/categories/', {
          method: 'POST',
          headers,
          body: JSON.stringify({ name, description })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`Category "${data.name}" added successfully!`, 'success');
          logActivity(`Category created`, data.name);
          formAddCategory.reset();
          loadCategoryList();
          loadCategoriesForSelect();
          loadKpiStats();
        } else {
          showToast(data.error || 'Failed to add category.', 'error');
        }
      } catch (err) {
        showToast('Server error adding category.', 'error');
      }
    });
  }

  // --- AUDIT LOG STREAM ---
  function logActivity(action, details) {
    if (!activityStream) return;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const item = document.createElement('div');
    item.className = 'crm-activity-item';
    item.innerHTML = `
      <div class="crm-activity-dot"></div>
      <div>
        <strong style="color: #ffffff; font-size: 13.5px;">${escapeHtml(action)}</strong>
        <div style="font-size: 11.5px; color: var(--crm-muted); margin-top: 2px;">${escapeHtml(details)} • ${timeStr}</div>
      </div>
    `;
    activityStream.prepend(item);
  }

  // --- HELPER UTILITIES ---

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

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function escapeHtml(str) {
    if (!str) return '';
    const stripped = String(str).replace(/<[^>]*>?/gm, '');
    return stripped.replace(/[&<>"']/g, function(m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
  }
});

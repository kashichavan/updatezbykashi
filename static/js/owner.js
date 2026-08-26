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
    loadAnalyticsData();
  }

  const tabTitles = {
    'tabJobs': { title: 'Opportunity Pipeline CRM', sub: 'Track active student requirements, manage postings, run bulk parsers, and execute workflow actions.' },
    'tabBulkParse': { title: 'Bulk Multi-Job Automation', sub: 'Parse multi-job Telegram/WhatsApp messages & auto-publish all leads in 1 click.' },
    'tabJobdexo': { title: 'Jobdexo Auto-Sync Engine', sub: 'Automatically crawl & import off-campus drives directly from Jobdexo with official apply links.' },
    'tabAnalytics': { title: 'Website Traffic & Visitor Analytics', sub: 'Real-time student visitor volume, daily trends, referrer sources, and top viewed requirements.' },
    'tabGroups': { title: 'Requirement Groups & Drives', sub: 'Shareable collections of multiple requirements for 1-click WhatsApp/Telegram broadcasting.' },
    'tabSmartParse': { title: '1-Click Single Parser', sub: 'Extract details from a single job requirement snippet & publish instantly.' },
    'tabPost': { title: 'Publish New Opportunity', sub: 'Manual form to publish structured student job or internship postings.' },
    'tabCategory': { title: 'Taxonomy & Categories', sub: 'Manage job categories, view active posting counts, and organize leads.' },
    'tabActivity': { title: 'System Activity & Audit Log', sub: 'Real-time audit log of owner parsing actions, status toggles, and publishing events.' }
  };

  const tabUrlMap = {
    'tabJobs': '/owner/manage-jobs/',
    'tabBulkParse': '/owner/bulk-parser/',
    'tabJobdexo': '/owner/jobdexo-sync/',
    'tabAnalytics': '/owner/analytics/',
    'tabGroups': '/owner/groups/',
    'tabSmartParse': '/owner/single-parser/',
    'tabPost': '/owner/post-job/',
    'tabCategory': '/owner/categories/',
    'tabActivity': '/owner/activity/'
  };

  const urlTabMap = {
    '/owner/': 'tabJobs',
    '/owner/manage-jobs/': 'tabJobs',
    '/owner/bulk-parser/': 'tabBulkParse',
    '/owner/jobdexo-sync/': 'tabJobdexo',
    '/owner/analytics/': 'tabAnalytics',
    '/owner/groups/': 'tabGroups',
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

    // On mobile screens, smoothly scroll to top of workspace
    if (window.innerWidth <= 992 && targetEl) {
      const yOffset = -20;
      const y = targetEl.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
    }

    if (targetId === 'tabJobs') loadJobsList(1);
    if (targetId === 'tabCategory') loadCategoryList();
    if (targetId === 'tabGroups') loadGroupsList();
    if (targetId === 'tabAnalytics') loadAnalyticsData();
  }

  const btnRefreshAnalytics = document.getElementById('btnRefreshAnalytics');
  if (btnRefreshAnalytics) {
    btnRefreshAnalytics.addEventListener('click', () => {
      btnRefreshAnalytics.textContent = '🔄 Updating...';
      loadAnalyticsData().finally(() => {
        setTimeout(() => { btnRefreshAnalytics.textContent = '🔄 Refresh Analytics'; }, 800);
      });
    });
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

    const btnRefreshGroups = document.getElementById('btnRefreshGroups');
    if (btnRefreshGroups) {
      btnRefreshGroups.addEventListener('click', () => {
        loadGroupsList();
        showToast('Requirement groups refreshed!', 'success');
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
    if (loginView) {
      loginView.style.display = 'block';
      loginView.style.removeProperty('display');
    }
    if (dashboardView) {
      dashboardView.style.display = 'none';
    }
    const mobileBottomNav = document.getElementById('ownerMobileBottomNav');
    if (mobileBottomNav) mobileBottomNav.style.display = 'none';
  }

  function showDashboard(username) {
    if (loginView) {
      loginView.style.display = 'none';
      loginView.style.setProperty('display', 'none', 'important');
    }
    if (dashboardView) {
      dashboardView.style.display = 'block';
      dashboardView.style.setProperty('display', 'block', 'important');
    }
    if (sidebarUserLabel) sidebarUserLabel.textContent = username || 'Owner';

    const mobileBottomNav = document.getElementById('ownerMobileBottomNav');
    if (mobileBottomNav && window.innerWidth <= 992) {
      mobileBottomNav.style.display = 'flex';
    }

    const btnLogout = document.getElementById('btnLogoutOwner');
    if (btnLogout) {
      btnLogout.addEventListener('click', handleLogout);
    }
    const btnMobileLogout = document.getElementById('btnMobileLogout');
    if (btnMobileLogout) {
      btnMobileLogout.addEventListener('click', handleLogout);
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
      const submitBtn = formLogin.querySelector('button[type="submit"]');

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Authenticating... ⏳';
      }

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
          
          showDashboard(data.username);

          // Seamless transition reload
          setTimeout(() => {
            const urlParams = new URLSearchParams(window.location.search);
            const nextUrl = urlParams.get('next');
            window.location.href = nextUrl || '/owner/manage-jobs/';
          }, 350);
        } else {
          showToast(data.error || 'Invalid credentials.', 'error');
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Authenticate CRM Access 🔑';
          }
        }
      } catch (err) {
        showToast('Login request failed. Please check network connection.', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Authenticate CRM Access 🔑';
        }
      }
    });
  }

  async function handleLogout() {
    try {
      await fetch('/api/admin/logout/', { method: 'POST' });
      localStorage.removeItem('owner_jwt_access');
      localStorage.removeItem('owner_jwt_refresh');
      showToast('Logged out successfully.', 'success');
      setTimeout(() => {
        window.location.href = '/owner/';
      }, 300);
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

      // Fetch Groups Count
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = {};
      if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;
      const groupRes = await fetch('/api/owner/groups/', { headers });
      if (groupRes.ok) {
        const groupData = await groupRes.json();
        const groups = groupData.groups || [];
        const sidebarGroups = document.getElementById('sidebarGroupsCount');
        const kpiGroups = document.getElementById('kpiTotalGroups');
        if (sidebarGroups) sidebarGroups.textContent = groups.length;
        if (kpiGroups) kpiGroups.textContent = groups.length;
      }

    } catch (err) {
      console.error('Error fetching KPI stats:', err);
    }
  }

  // --- BULK MULTI-JOB AUTO-PARSER ENGINE ---

  if (formBulkParse) {
    formBulkParse.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawText = document.getElementById('bulkRawText').value.trim();
      const groupNameInput = document.getElementById('bulkGroupName');
      const groupName = groupNameInput ? groupNameInput.value.trim() : '';

      if (!rawText) return;

      try {
        showToast('Processing bulk multi-job parser & creating shareable group...', 'success');
        const jwtAccess = localStorage.getItem('owner_jwt_access');
        const headers = { 'Content-Type': 'application/json' };
        if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

        const res = await fetch('/api/owner/bulk-parse-and-post/', {
          method: 'POST',
          headers,
          body: JSON.stringify({ raw_text: rawText, group_name: groupName })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`⚡ ${data.message}`, 'success');
          logActivity(`Bulk Multi-Job Parser executed`, data.message);
          document.getElementById('bulkRawText').value = '';
          if (groupNameInput) groupNameInput.value = '';
          loadKpiStats();

          // Open Broadcast & Share Modal directly!
          if (data.group_slug) {
            openBroadcastModal({
              group_name: data.group_name,
              full_group_url: data.full_group_url,
              whatsapp_broadcast: data.whatsapp_broadcast,
              telegram_broadcast: data.telegram_broadcast,
            });
          } else {
            switchTab('tabJobs');
          }
        } else {
          showToast(data.error || 'Failed to bulk parse postings.', 'error');
        }
      } catch (err) {
        showToast('Server error during bulk auto-parsing.', 'error');
      }
    });
  }

  // --- JOBDEXO AUTOMATION & CRAWLER ENGINE ---

  const btnFetchJobdexo5 = document.getElementById('btnFetchJobdexo5');
  const btnFetchJobdexo10 = document.getElementById('btnFetchJobdexo10');
  const formJobdexoUrlImport = document.getElementById('formJobdexoUrlImport');

  async function triggerJobdexoLatestFetch(limit = 5) {
    const groupNameInput = document.getElementById('jobdexoGroupName');
    const groupName = groupNameInput ? groupNameInput.value.trim() : '';

    try {
      showToast(`⚡ Crawling Jobdexo for latest ${limit} off-campus opportunities...`, 'success');
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = { 'Content-Type': 'application/json' };
      if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

      const res = await fetch('/api/owner/jobdexo/fetch-latest/', {
        method: 'POST',
        headers,
        body: JSON.stringify({ limit, group_name: groupName })
      });
      const data = await res.json();

      if (res.ok && data.success) {
        showToast(`🎉 ${data.message}`, 'success');
        logActivity(`Jobdexo Auto-Crawler (${limit} jobs)`, data.message);
        if (groupNameInput) groupNameInput.value = '';
        loadKpiStats();

        if (data.group_slug) {
          openBroadcastModal(data);
        } else {
          switchTab('tabJobs');
        }
      } else {
        showToast(data.error || 'Failed to crawl Jobdexo.', 'error');
      }
    } catch (err) {
      showToast('Server error while syncing from Jobdexo.', 'error');
    }
  }

  if (btnFetchJobdexo5) {
    btnFetchJobdexo5.addEventListener('click', () => triggerJobdexoLatestFetch(5));
  }

  if (btnFetchJobdexo10) {
    btnFetchJobdexo10.addEventListener('click', () => triggerJobdexoLatestFetch(10));
  }

  if (formJobdexoUrlImport) {
    formJobdexoUrlImport.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawUrls = document.getElementById('jobdexoUrlsInput').value.trim();
      const groupNameInput = document.getElementById('jobdexoGroupName');
      const groupName = groupNameInput ? groupNameInput.value.trim() : '';

      if (!rawUrls) return;

      try {
        showToast('📥 Importing jobs from provided Jobdexo URLs...', 'success');
        const jwtAccess = localStorage.getItem('owner_jwt_access');
        const headers = { 'Content-Type': 'application/json' };
        if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

        const res = await fetch('/api/owner/jobdexo/import-urls/', {
          method: 'POST',
          headers,
          body: JSON.stringify({ urls: rawUrls, group_name: groupName })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`🎉 ${data.message}`, 'success');
          logActivity('Jobdexo URL Importer', data.message);
          document.getElementById('jobdexoUrlsInput').value = '';
          if (groupNameInput) groupNameInput.value = '';
          loadKpiStats();

          if (data.group_slug) {
            openBroadcastModal(data);
          } else {
            switchTab('tabJobs');
          }
        } else {
          showToast(data.error || 'Failed to import Jobdexo URLs.', 'error');
        }
      } catch (err) {
        showToast('Server error importing Jobdexo URLs.', 'error');
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
    const isMobileView = window.innerWidth <= 768;

    jobsTableContainer.innerHTML = isMobileView ? `
      <div class="crm-mobile-jobs-list" style="display: flex; flex-direction: column; gap: 12px;">
        ${filtered.map(j => {
          const isExpired = j.time_left_seconds <= 0 || j.status === 'EXPIRED';
          const hoursLeft = Math.ceil(j.time_left_seconds / 3600);
          const compInitial = (j.company_name || 'J')[0].toUpperCase();
          return `
          <div class="crm-mobile-job-card" style="background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(13, 18, 31, 0.95) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 18px; padding: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 10px;">
              <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
                <div style="width: 38px; height: 38px; border-radius: 12px; background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(99, 102, 241, 0.25)); border: 1px solid rgba(6, 182, 212, 0.4); color: #38bdf8; font-weight: 800; font-size: 16px; display: grid; place-items: center; flex-shrink: 0;">
                  ${compInitial}
                </div>
                <div style="min-width: 0;">
                  <h4 style="margin: 0; font-size: 15px; font-weight: 800; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(j.company_name)}</h4>
                  <span style="font-size: 11px; color: #94a3b8; font-family: monospace;">#${j.id} • ${escapeHtml(j.category_name)}</span>
                </div>
              </div>
              <span class="crm-status-pill ${isExpired ? 'crm-status-expired' : 'crm-status-active'}" style="font-size: 10.5px; padding: 3px 8px; flex-shrink: 0;">
                ${isExpired ? '🔴 Expired' : '🟢 ' + hoursLeft + 'h left'}
              </span>
            </div>

            <div style="font-size: 13.5px; font-weight: 700; color: #f1f5f9; line-height: 1.4; margin-bottom: 10px;">
              ${escapeHtml(j.title)}
            </div>

            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; font-size: 11.5px;">
              <span style="background: rgba(255, 255, 255, 0.05); padding: 4px 8px; border-radius: 8px; color: #e2e8f0;">💰 ${escapeHtml(j.stipend_salary)}</span>
              <span style="background: rgba(255, 255, 255, 0.05); padding: 4px 8px; border-radius: 8px; color: #e2e8f0;">📍 ${escapeHtml(j.location || 'India')}</span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
              <button class="btn-crm-action btn-toggle-job" data-id="${j.id}" style="height: 40px; font-size: 12.5px; display: flex; align-items: center; justify-content: center; gap: 4px; background: rgba(255,255,255,0.06); color: ${isExpired ? '#10b981' : '#f59e0b'}; border: 1px solid ${isExpired ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}; border-radius: 12px;">
                ${isExpired ? '🚀 Publish' : '⏸️ Unpublish'}
              </button>
              <button class="btn-crm-action btn-edit-job" data-id="${j.id}" style="height: 40px; font-size: 12.5px; display: flex; align-items: center; justify-content: center; gap: 4px; background: rgba(6, 182, 212, 0.12); color: #38bdf8; border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 12px;">
                ✏️ Edit
              </button>
              <a href="${escapeHtml(j.apply_url)}" target="_blank" class="btn-crm-action" style="height: 40px; font-size: 12.5px; display: flex; align-items: center; justify-content: center; gap: 4px; background: rgba(99, 102, 241, 0.12); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; text-decoration: none;">
                ↗ Apply Link
              </a>
              <button class="btn-crm-action btn-delete-job" data-id="${j.id}" style="height: 40px; font-size: 12.5px; display: flex; align-items: center; justify-content: center; gap: 4px; background: rgba(244, 63, 94, 0.12); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 12px;">
                🗑️ Delete
              </button>
            </div>
          </div>
        `}).join('')}
      </div>
    ` : `
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
    `;

    jobsTableContainer.insertAdjacentHTML('beforeend', `
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

  // --- REQUIREMENT GROUPS & BUNDLES ENGINE ---

  async function loadGroupsList() {
    const container = document.getElementById('ownerGroupsTableContainer');
    if (!container) return;

    container.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--crm-muted);">Loading requirement groups...</div>';

    try {
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = {};
      if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;

      const res = await fetch('/api/owner/groups/', { headers });
      const data = await res.json();
      const groups = data.groups || [];

      if (groups.length === 0) {
        container.innerHTML = `
          <div style="padding: 48px 24px; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">📦</div>
            <h3 style="font-size: 16px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">No Requirement Groups Yet</h3>
            <p style="font-size: 13px; color: var(--crm-muted); margin-bottom: 16px;">
              Whenever you use the Bulk Parser, a group is automatically created with a direct shareable link!
            </p>
            <button class="btn-crm-primary" style="height: 38px; font-size: 13px;" onclick="document.querySelector('[data-tab=tabBulkParse]').click()">
              ⚡ Open Bulk Parser
            </button>
          </div>
        `;
        return;
      }

      let html = `
        <table class="crm-table">
          <thead>
            <tr>
              <th style="width: 32%;">Group / Drive Name</th>
              <th style="width: 14%;">Active Jobs</th>
              <th style="width: 18%;">Created Date</th>
              <th style="width: 10%;">Views</th>
              <th style="width: 26%; text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
      `;

      groups.forEach(g => {
        html += `
          <tr>
            <td>
              <div style="font-weight: 800; color: #ffffff; font-size: 13.5px;">${escapeHtml(g.name)}</div>
              <div style="font-size: 11px; color: var(--crm-cyan); font-family: monospace; margin-top: 2px;">/group/${escapeHtml(g.slug)}/</div>
            </td>
            <td>
              <span class="crm-table-badge badge-active" style="font-size: 11.5px;">
                🎯 ${g.active_jobs_count} Active
              </span>
            </td>
            <td style="color: var(--crm-muted); font-size: 12.5px;">${escapeHtml(g.created_at)}</td>
            <td style="font-weight: 700; color: #e2e8f0; font-size: 13px;">👁️ ${g.views_count}</td>
            <td style="text-align: right;">
              <div style="display: inline-flex; gap: 6px; align-items: center;">
                <a href="${escapeHtml(g.url)}" target="_blank" class="btn-crm-action" style="background: rgba(37,99,235,0.2); color: #60a5fa; border-color: rgba(37,99,235,0.4); text-decoration: none; padding: 5px 9px; font-size: 11.5px;">
                  Open ↗
                </a>
                <button class="btn-crm-action btn-group-broadcast" data-id="${g.id}" style="background: rgba(34,197,94,0.18); color: #4ade80; border-color: rgba(34,197,94,0.35); padding: 5px 9px; font-size: 11.5px;">
                  📱 Broadcast
                </button>
                <button class="btn-crm-action btn-group-delete" data-id="${g.id}" data-name="${escapeHtml(g.name)}" style="background: rgba(244,63,94,0.15); color: var(--crm-rose); border-color: rgba(244,63,94,0.3); padding: 5px 8px; font-size: 11.5px;">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        `;
      });

      html += '</tbody></table>';
      container.innerHTML = html;

      // Attach Broadcast button click handlers
      container.querySelectorAll('.btn-group-broadcast').forEach(btn => {
        btn.addEventListener('click', async () => {
          const groupId = btn.dataset.id;
          try {
            const jwtAccess = localStorage.getItem('owner_jwt_access');
            const headers = {};
            if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;
            const res = await fetch(`/api/owner/groups/${groupId}/broadcast/`, { headers });
            const data = await res.json();
            if (res.ok) {
              openBroadcastModal(data);
            }
          } catch (err) {
            showToast('Failed to fetch group broadcast details.', 'error');
          }
        });
      });

      // Attach Delete button click handlers
      container.querySelectorAll('.btn-group-delete').forEach(btn => {
        btn.addEventListener('click', async () => {
          const groupId = btn.dataset.id;
          const groupName = btn.dataset.name;
          if (confirm(`Are you sure you want to delete group "${groupName}"? (The individual job postings will remain untouched).`)) {
            try {
              const jwtAccess = localStorage.getItem('owner_jwt_access');
              const headers = { 'Content-Type': 'application/json' };
              if (jwtAccess) headers['Authorization'] = `Bearer ${jwtAccess}`;
              const res = await fetch(`/api/owner/groups/${groupId}/delete/`, {
                method: 'POST',
                headers
              });
              if (res.ok) {
                showToast(`Group "${groupName}" deleted.`, 'success');
                logActivity(`Deleted group`, groupName);
                loadGroupsList();
                loadKpiStats();
              }
            } catch (err) {
              showToast('Error deleting group.', 'error');
            }
          }
        });
      });

    } catch (err) {
      console.error('Error loading groups:', err);
      container.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--crm-rose);">Failed to load requirement groups.</div>';
    }
  }

  // --- BROADCAST MODAL HANDLER ---

  function openBroadcastModal(data) {
    const modal = document.getElementById('groupBroadcastModal');
    if (!modal) return;

    const titleEl = document.getElementById('modalGroupName');
    const urlInput = document.getElementById('modalGroupUrlInput');
    const openLink = document.getElementById('btnOpenModalLink');
    const previewEl = document.getElementById('modalBroadcastPreview');

    const groupUrl = data.full_group_url || (window.location.origin + (data.group_url || ''));
    if (titleEl) titleEl.textContent = data.group_name || 'Requirement Group Ready';
    if (urlInput) urlInput.value = groupUrl;
    if (openLink) openLink.href = groupUrl;
    if (previewEl) previewEl.value = data.whatsapp_broadcast || '';

    // Setup Copy Link
    const btnCopyLink = document.getElementById('btnCopyModalLink');
    if (btnCopyLink) {
      btnCopyLink.onclick = () => {
        navigator.clipboard.writeText(groupUrl).then(() => {
          btnCopyLink.textContent = '✅ Copied!';
          showToast('Direct group URL copied to clipboard!', 'success');
          setTimeout(() => { btnCopyLink.textContent = '🔗 Copy Link'; }, 2000);
        });
      };
    }

    // Setup Copy WhatsApp Broadcast
    const btnCopyWhatsApp = document.getElementById('btnCopyModalWhatsApp');
    if (btnCopyWhatsApp) {
      btnCopyWhatsApp.onclick = () => {
        const text = data.whatsapp_broadcast || '';
        navigator.clipboard.writeText(text).then(() => {
          btnCopyWhatsApp.textContent = '✅ WhatsApp Text Copied!';
          showToast('WhatsApp Broadcast message copied to clipboard!', 'success');
          setTimeout(() => { btnCopyWhatsApp.textContent = '📱 Copy WhatsApp Broadcast'; }, 2500);
        });
      };
    }

    // Setup Copy Telegram Broadcast
    const btnCopyTelegram = document.getElementById('btnCopyModalTelegram');
    if (btnCopyTelegram) {
      btnCopyTelegram.onclick = () => {
        const text = data.telegram_broadcast || data.whatsapp_broadcast || '';
        navigator.clipboard.writeText(text).then(() => {
          btnCopyTelegram.textContent = '✅ Telegram Post Copied!';
          showToast('Telegram Post format copied to clipboard!', 'success');
          setTimeout(() => { btnCopyTelegram.textContent = '✈️ Copy Telegram Post'; }, 2500);
        });
      };
    }

    modal.style.display = 'flex';
  }

  const btnCloseBroadcastModal = document.getElementById('btnCloseBroadcastModal');
  if (btnCloseBroadcastModal) {
    btnCloseBroadcastModal.addEventListener('click', () => {
      const modal = document.getElementById('groupBroadcastModal');
      if (modal) modal.style.display = 'none';
    });
  }

  // --- REAL-TIME WEBSITE TRAFFIC & VISITOR ANALYTICS ---
  async function loadAnalyticsData() {
    try {
      const res = await fetch('/api/owner/analytics/', {
        headers: { 'Accept': 'application/json' }
      });
      const data = await res.json();
      if (!data.success) return;

      const sum = data.summary || {};
      const dev = data.devices || {};

      // 1. KPI Cards
      const elTotalVis = document.getElementById('anaTotalVisitors');
      const elMonthVis = document.getElementById('anaMonthVisitors');
      const elTodayVis = document.getElementById('anaTodayVisitors');
      const elTodayViews = document.getElementById('anaTodayViews');
      const elTotalViews = document.getElementById('anaTotalViews');
      const elWeekVis = document.getElementById('anaWeekVisitors');
      const elDeviceSplit = document.getElementById('anaDeviceSplit');
      const elTopSource = document.getElementById('anaTopSource');

      if (elTotalVis) elTotalVis.textContent = Number(sum.total_unique_visitors || 0).toLocaleString();
      if (elMonthVis) elMonthVis.textContent = `${Number(sum.month_unique_visitors || 0).toLocaleString()} this month`;
      if (elTodayVis) elTodayVis.textContent = Number(sum.today_unique_visitors || 0).toLocaleString();
      if (elTodayViews) elTodayViews.textContent = `${Number(sum.today_page_views || 0).toLocaleString()} views today`;
      if (elTotalViews) elTotalViews.textContent = Number(sum.total_page_views || 0).toLocaleString();
      if (elWeekVis) elWeekVis.textContent = `${Number(sum.week_unique_visitors || 0).toLocaleString()} this week`;

      if (elDeviceSplit) {
        elDeviceSplit.textContent = `${dev.mobile_pct || 0}% Mobile`;
      }
      if (elTopSource && data.referrers && data.referrers.length > 0) {
        elTopSource.textContent = `Top: ${data.referrers[0].source} (${data.referrers[0].percentage}%)`;
      }

      // 2. 14-Day Daily Traffic Chart
      const chartContainer = document.getElementById('anaDailyChartContainer');
      if (chartContainer && data.daily_traffic) {
        const maxViews = Math.max(...data.daily_traffic.map(d => d.views), 10);
        chartContainer.innerHTML = data.daily_traffic.map(d => {
          const heightPct = Math.max(Math.round((d.views / maxViews) * 100), 8);
          return `
            <div style="flex: 1; min-width: 22px; display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; justify-content: flex-end;" title="${d.full_date}: ${d.views} views, ${d.unique_visitors} unique visitors">
              <span style="font-size: 9.5px; font-weight: 700; color: #38bdf8;">${d.views > 0 ? d.views : ''}</span>
              <div style="width: 100%; max-width: 28px; height: ${heightPct}%; background: linear-gradient(180deg, #38bdf8 0%, #2563eb 100%); border-radius: 6px 6px 0 0; transition: height 0.3s ease;"></div>
              <span style="font-size: 9.5px; color: #94a3b8; white-space: nowrap; margin-top: 4px;">${d.date}</span>
            </div>
          `;
        }).join('');
      }

      // 3. Top Visited Pages
      const topPagesContainer = document.getElementById('anaTopPagesList');
      if (topPagesContainer) {
        if (!data.top_pages || data.top_pages.length === 0) {
          topPagesContainer.innerHTML = '<div style="color: var(--crm-muted); font-size: 13px;">No page views recorded yet.</div>';
        } else {
          topPagesContainer.innerHTML = data.top_pages.map((p, idx) => `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--crm-border); border-radius: 12px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
              <div style="flex: 1; min-width: 0;">
                <div style="font-size: 13px; font-weight: 700; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                  <span style="color: var(--crm-cyan); font-weight: 800; margin-right: 4px;">#${idx + 1}</span> ${escapeHtml(p.page_title || p.path)}
                </div>
                <div style="font-size: 11px; color: var(--crm-muted); font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                  ${escapeHtml(p.path)}
                </div>
              </div>
              <div style="text-align: right; flex-shrink: 0;">
                <div style="font-size: 13px; font-weight: 800; color: #38bdf8;">${p.views} views</div>
                <div style="font-size: 10.5px; color: #94a3b8;">${p.unique_visitors} unique</div>
              </div>
            </div>
          `).join('');
        }
      }

      // 4. Traffic Channels & Referrers
      const referrersContainer = document.getElementById('anaReferrersList');
      if (referrersContainer) {
        if (!data.referrers || data.referrers.length === 0) {
          referrersContainer.innerHTML = '<div style="color: var(--crm-muted); font-size: 13px;">No referrer data yet.</div>';
        } else {
          referrersContainer.innerHTML = data.referrers.map(r => `
            <div>
              <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; color: #ffffff; margin-bottom: 4px;">
                <span>${escapeHtml(r.source)}</span>
                <span style="color: #38bdf8;">${r.count} hits (${r.percentage}%)</span>
              </div>
              <div style="height: 6px; width: 100%; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;">
                <div style="height: 100%; width: ${r.percentage}%; background: linear-gradient(90deg, #06b6d4, #6366f1); border-radius: 4px;"></div>
              </div>
            </div>
          `).join('');
        }
      }

      // 5. Operating Systems & Platforms
      const platformsContainer = document.getElementById('anaPlatformsList');
      if (platformsContainer) {
        const osList = (data.operating_systems || []).map(o => `
          <span style="background: rgba(255,255,255,0.05); border: 1px solid var(--crm-border); border-radius: 8px; padding: 4px 10px; font-size: 11.5px; color: #cbd5e1;">
            💻 ${escapeHtml(o.os)}: <strong style="color: #ffffff;">${o.count}</strong>
          </span>
        `);
        const browserList = (data.browsers || []).map(b => `
          <span style="background: rgba(56,189,248,0.08); border: 1px solid rgba(56,189,248,0.25); border-radius: 8px; padding: 4px 10px; font-size: 11.5px; color: #38bdf8;">
            🌐 ${escapeHtml(b.browser)}: <strong style="color: #ffffff;">${b.count}</strong>
          </span>
        `);
        platformsContainer.innerHTML = [...osList, ...browserList].join('') || '<span style="color: var(--crm-muted); font-size: 12px;">No platform data yet</span>';
      }

      // 6. Recent Real-Time Visitors Table
      const visitsBody = document.getElementById('anaRecentVisitsBody');
      if (visitsBody) {
        if (!data.recent_visits || data.recent_visits.length === 0) {
          visitsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--crm-muted); padding: 20px;">No recent live visits yet.</td></tr>';
        } else {
          visitsBody.innerHTML = data.recent_visits.map(v => `
            <tr>
              <td style="white-space: nowrap; font-size: 12px; color: #94a3b8;">
                <span style="color: var(--crm-cyan); font-weight: 700;">${escapeHtml(v.time)}</span><br>
                <small>${escapeHtml(v.date)}</small>
              </td>
              <td>
                <div style="font-weight: 700; color: #ffffff; font-size: 13px;">${escapeHtml(v.page_title)}</div>
                <div style="font-size: 11px; color: var(--crm-muted); font-family: monospace;">${escapeHtml(v.path)}</div>
              </td>
              <td>
                <span class="crm-category-tag" style="background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3);">
                  ${escapeHtml(v.referrer)}
                </span>
              </td>
              <td style="font-size: 12px; color: #cbd5e1;">
                ${v.device === 'Mobile' ? '📱 Mobile' : (v.device === 'Tablet' ? '📟 Tablet' : '💻 Desktop')} • ${escapeHtml(v.os)} (${escapeHtml(v.browser)})
              </td>
              <td style="font-family: monospace; font-size: 11.5px; color: #64748b;">
                ${escapeHtml(v.ip)}
              </td>
            </tr>
          `).join('');
        }
      }

    } catch (err) {
      console.error('Error loading website analytics:', err);
    }
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

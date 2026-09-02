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

  async function authFetch(url, options = {}) {
    const jwtAccess = localStorage.getItem('owner_jwt_access');
    const headers = { ...(options.headers || {}) };
    if (jwtAccess && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${jwtAccess}`;
    }
    if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    const csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (csrfMatch && !headers['X-CSRFToken'] && options.method && options.method !== 'GET') {
      headers['X-CSRFToken'] = csrfMatch[1];
    }
    let res = await fetch(url, {
      ...options,
      headers,
      credentials: 'same-origin'
    });

    if (res.status === 401 && headers['Authorization']) {
      localStorage.removeItem('owner_jwt_access');
      delete headers['Authorization'];
      res = await fetch(url, {
        ...options,
        headers,
        credentials: 'same-origin'
      });
    }

    return res;
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

  init();

  async function init() {
    setupTabSwitching();
    setupFiltersAndSearch();
    bindJobActionEvents();
    await checkAuthStatus();
  }

  function setupTabSwitching() {
    document.querySelectorAll('.owner-nav-item').forEach(tab => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = tab.dataset.tab;
        if (targetId) {
          switchTab(targetId, true);
        }
      });
    });

    const btnHeaderParseLead = document.getElementById('btnHeaderParseLead');
    if (btnHeaderParseLead) {
      btnHeaderParseLead.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab('tabSmartParse', true);
      });
    }

    const btnHeaderPostJob = document.getElementById('btnHeaderPostJob');
    if (btnHeaderPostJob) {
      btnHeaderPostJob.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab('tabPost', true);
      });
    }

    window.addEventListener('popstate', () => {
      const currentPath = window.location.pathname;
      if (urlTabMap[currentPath]) {
        switchTab(urlTabMap[currentPath], false);
      } else {
        switchTab('tabJobs', false);
      }
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
    if (!targetId) return;

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
    if (window.innerWidth <= 768 && targetEl) {
      const yOffset = -20;
      const y = targetEl.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
    }

    if (targetId === 'tabJobs') {
      const hasPreRenderedCards = jobsTableContainer && jobsTableContainer.querySelector('.vp-product-card');
      if (!updateHistory && hasPreRenderedCards) {
        bindJobActionEvents();
      } else {
        loadJobsList(1);
      }
    }
    if (targetId === 'tabCategory') loadCategoryList();
    if (targetId === 'tabGroups') loadGroupsList();
    if (targetId === 'tabAnalytics') loadAnalyticsData();
  }

  window.ownerSwitchTab = switchTab;

  const btnRefreshAnalytics = document.getElementById('btnRefreshAnalytics');
  if (btnRefreshAnalytics) {
    btnRefreshAnalytics.addEventListener('click', () => {
      const icon = document.getElementById('refreshIconSvg');
      const text = document.getElementById('btnRefreshText');
      if (icon) icon.classList.add('spin-animation');
      if (text) text.textContent = 'Updating...';
      btnRefreshAnalytics.disabled = true;

      loadAnalyticsData().finally(() => {
        setTimeout(() => {
          if (icon) icon.classList.remove('spin-animation');
          if (text) text.textContent = 'Refresh Data';
          btnRefreshAnalytics.disabled = false;
        }, 600);
      });
    });
  }

  let activeSearchTimeout = null;

  function setupFiltersAndSearch() {
    const btnClear = document.getElementById('btnSearchClear');

    if (searchInput) {
      const handleSearch = () => {
        const val = searchInput.value.trim();
        if (btnClear) btnClear.style.display = val ? 'block' : 'none';
        clearTimeout(activeSearchTimeout);
        activeSearchTimeout = setTimeout(() => {
          loadJobsList(1);
        }, 250);
      };

      searchInput.addEventListener('input', handleSearch);
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          clearTimeout(activeSearchTimeout);
          loadJobsList(1);
        }
      });
    }

    if (btnClear) {
      btnClear.addEventListener('click', () => {
        if (searchInput) {
          searchInput.value = '';
          btnClear.style.display = 'none';
          searchInput.focus();
        }
        loadJobsList(1);
      });
    }

    if (filterCategorySelect) {
      filterCategorySelect.addEventListener('change', () => {
        loadJobsList(1);
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
        showToast('Requirement groups refreshed and empty groups cleaned up!', 'success');
      });
    }

    const btnAutoOrganizeGroups = document.getElementById('btnAutoOrganizeGroups');
    if (btnAutoOrganizeGroups) {
      btnAutoOrganizeGroups.addEventListener('click', async () => {
        btnAutoOrganizeGroups.textContent = '⚡ Organizing & Cleaning...';
        btnAutoOrganizeGroups.disabled = true;
        try {
          const res = await authFetch('/api/owner/groups/auto-organize/', { method: 'POST' });
          const data = await res.json();
          if (res.ok) {
            showToast(data.message || 'Auto-organized requirements successfully!', 'success');
            logActivity('Auto-organized groups', data.message);
            loadGroupsList();
            loadKpiStats();
          } else {
            showToast(data.error || 'Failed to auto-organize groups.', 'error');
          }
        } catch (err) {
          showToast('Network error while auto-organizing groups.', 'error');
        } finally {
          btnAutoOrganizeGroups.textContent = '⚡ Auto-Move & Clean Empty Groups';
          btnAutoOrganizeGroups.disabled = false;
        }
      });
    }
  }

  async function checkAuthStatus() {
    const serverAuthEl = document.getElementById('ownerDashboardView');
    const isServerAuth = serverAuthEl && serverAuthEl.getAttribute('data-server-auth') === 'true';
    const serverUser = serverAuthEl ? serverAuthEl.getAttribute('data-owner-user') : '';

    if (isServerAuth) {
      showDashboard(serverUser || 'Owner');
      return;
    }

    try {
      const jwtAccess = localStorage.getItem('owner_jwt_access');
      const headers = {};
      if (jwtAccess) {
        headers['Authorization'] = `Bearer ${jwtAccess}`;
      }
      const res = await fetch('/api/admin/status/', {
        headers,
        credentials: 'same-origin'
      });
      const data = await res.json();
      if (data.is_admin) {
        showDashboard(data.username);
      } else if (!isServerAuth) {
        showLoginScreen();
      }
    } catch (err) {
      console.error('Auth check error:', err);
      if (!isServerAuth) {
        showLoginScreen();
      }
    }
  }

  function showLoginScreen() {
    document.body.classList.remove('is-owner-authenticated');
    if (loginView) {
      loginView.style.display = 'block';
      loginView.style.setProperty('display', 'block', 'important');
    }
    if (dashboardView) {
      dashboardView.style.display = 'none';
      dashboardView.style.setProperty('display', 'none', 'important');
    }
    const ownerSubNav = document.getElementById('ownerSubNav');
    if (ownerSubNav) {
      ownerSubNav.style.display = 'none';
      ownerSubNav.style.setProperty('display', 'none', 'important');
    }
    const ownerAuthActions = document.getElementById('ownerAuthActions');
    if (ownerAuthActions) {
      ownerAuthActions.style.display = 'none';
      ownerAuthActions.style.setProperty('display', 'none', 'important');
    }
    const mobileBottomNav = document.getElementById('ownerMobileBottomNav');
    if (mobileBottomNav) {
      mobileBottomNav.style.display = 'none';
      mobileBottomNav.style.setProperty('display', 'none', 'important');
    }
  }

  function showDashboard(username) {
    document.body.classList.add('is-owner-authenticated');
    if (loginView) {
      loginView.style.display = 'none';
      loginView.style.setProperty('display', 'none', 'important');
    }
    if (dashboardView) {
      dashboardView.style.display = 'block';
      dashboardView.style.setProperty('display', 'block', 'important');
    }
    const ownerSubNav = document.getElementById('ownerSubNav');
    if (ownerSubNav) {
      ownerSubNav.style.display = 'flex';
      ownerSubNav.style.setProperty('display', 'flex', 'important');
    }
    const ownerAuthActions = document.getElementById('ownerAuthActions');
    if (ownerAuthActions) {
      ownerAuthActions.style.display = 'flex';
      ownerAuthActions.style.setProperty('display', 'flex', 'important');
    }
    if (sidebarUserLabel) sidebarUserLabel.textContent = username || 'Owner';

    const mobileBottomNav = document.getElementById('ownerMobileBottomNav');
    if (mobileBottomNav && window.innerWidth <= 768) {
      mobileBottomNav.style.display = 'flex';
      mobileBottomNav.style.setProperty('display', 'flex', 'important');
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

    // If server rendered login page before client JWT auth, fetch pipeline
    if (!document.querySelector('#ownerJobsTableContainer .vp-product-card')) {
      loadJobsList(1);
    }
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
        console.warn('Fetch login failed, submitting natively...', err);
        formLogin.submit();
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
      const res = await authFetch('/api/owner/kpi-stats/');
      if (res.ok) {
        const data = await res.json();
        const kpiActive = document.getElementById('kpiActiveJobs');
        const kpiTotal = document.getElementById('kpiTotalJobs');
        const kpiExpired = document.getElementById('kpiExpiredJobs');
        const sidebarBadge = document.getElementById('sidebarActiveCount');
        const kpiCat = document.getElementById('kpiCategories');
        const sidebarGroups = document.getElementById('sidebarGroupsCount');
        const kpiGroups = document.getElementById('kpiTotalGroups');

        if (kpiActive && data.active_jobs !== undefined) kpiActive.textContent = data.active_jobs;
        if (sidebarBadge && data.active_jobs !== undefined) sidebarBadge.textContent = `${data.active_jobs} Live`;
        if (kpiTotal && data.total_jobs !== undefined) kpiTotal.textContent = data.total_jobs;
        if (kpiExpired && data.expired_jobs !== undefined) kpiExpired.textContent = data.expired_jobs;
        if (kpiCat && data.total_categories !== undefined) kpiCat.textContent = data.total_categories;
        if (sidebarGroups && data.total_groups !== undefined) sidebarGroups.textContent = data.total_groups;
        if (kpiGroups && data.total_groups !== undefined) kpiGroups.textContent = data.total_groups;
      }
    } catch (err) {
      console.warn('Fast KPI fetch error, keeping existing values:', err);
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
        const res = await authFetch('/api/owner/bulk-parse-and-post/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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
      const res = await authFetch('/api/owner/jobdexo/fetch-latest/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  const btnCleanDuplicates = document.getElementById('btnCleanDuplicates');

  if (btnFetchJobdexo5) {
    btnFetchJobdexo5.addEventListener('click', () => triggerJobdexoLatestFetch(5));
  }

  if (btnFetchJobdexo10) {
    btnFetchJobdexo10.addEventListener('click', () => triggerJobdexoLatestFetch(10));
  }

  if (btnCleanDuplicates) {
    btnCleanDuplicates.addEventListener('click', async () => {
      try {
        showToast('🧹 Cleaning database duplicates and standardizing company names...', 'success');
        const res = await authFetch('/api/owner/jobdexo/cleanup/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`✨ ${data.message}`, 'success');
          logActivity('Database Cleanup', data.message);
          loadKpiStats();
          loadRecentJobs();
        } else {
          showToast(data.error || 'Cleanup failed.', 'error');
        }
      } catch (err) {
        showToast('Server error while cleaning database.', 'error');
      }
    });
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
        const res = await authFetch('/api/owner/jobdexo/import-urls/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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
        const res = await authFetch('/api/owner/parse-and-post/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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
        const res = await authFetch('/api/jobs/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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

  // --- OPPORTUNITY PIPELINE LIST ENGINE ---

  async function loadJobsList(page = 1) {
    if (!jobsTableContainer) return;
    currentJobsPage = page;
    
    // Skeleton loading state
    jobsTableContainer.innerHTML = `
      <div class="vp-catalog-grid" style="margin-bottom: 24px;">
        ${[1, 2, 3, 4, 5, 6].map(() => `
          <div class="vp-product-card" style="opacity: 0.7; pointer-events: none;">
            <div class="vp-card-header">
              <div style="width: 90px; height: 22px; background: #e2e8f0; border-radius: var(--radius-sm);"></div>
              <div style="width: 60px; height: 20px; background: #e2e8f0; border-radius: var(--radius-full);"></div>
            </div>
            <div style="width: 75%; height: 20px; background: #e2e8f0; border-radius: var(--radius-sm); margin: 10px 0 8px;"></div>
            <div style="width: 45%; height: 16px; background: #f1f5f9; border-radius: var(--radius-sm); margin-bottom: 12px;"></div>
            <div style="width: 100%; height: 40px; background: #f8fafc; border-radius: var(--radius-sm); margin-bottom: 14px;"></div>
            <div style="display: flex; gap: 6px; margin-bottom: 14px;">
              <div style="width: 50px; height: 20px; background: #f1f5f9; border-radius: var(--radius-sm);"></div>
              <div style="width: 60px; height: 20px; background: #f1f5f9; border-radius: var(--radius-sm);"></div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px;">
              <div style="height: 38px; background: #e2e8f0; border-radius: var(--radius-sm);"></div>
              <div style="height: 38px; background: #e2e8f0; border-radius: var(--radius-sm);"></div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    const pageSizeSelect = document.getElementById('ownerPageSize');
    const pageSize = pageSizeSelect ? parseInt(pageSizeSelect.value, 10) : 10;
    const statusVal = filterStatusSelect ? filterStatusSelect.value : 'ALL';
    const query = searchInput ? searchInput.value.trim() : '';
    const selectedCat = filterCategorySelect ? filterCategorySelect.value : 'ALL';

    let url = `/api/jobs/?sort=newest&page=${page}&page_size=${pageSize}`;
    if (statusVal && statusVal !== 'ALL') {
      url += `&status=${encodeURIComponent(statusVal)}`;
    }
    if (query) {
      url += `&q=${encodeURIComponent(query)}`;
    }
    if (selectedCat && selectedCat !== 'ALL') {
      url += `&category=${encodeURIComponent(selectedCat)}`;
    }

    try {
      const res = await authFetch(url);
      const data = await res.json();
      allLoadedJobs = data.jobs || [];
      renderFilteredJobs(data);
    } catch (err) {
      console.error('Failed to load jobs:', err);
      jobsTableContainer.innerHTML = `
        <div style="padding: 36px 20px; text-align: center; background: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius-md); margin-bottom: 20px;">
          <div style="font-size: 24px; margin-bottom: 8px;">⚠️</div>
          <strong style="color: var(--color-text-danger); font-size: var(--text-base); display: block; margin-bottom: 4px;">Failed to load opportunity pipeline</strong>
          <p style="color: var(--color-text-muted); font-size: var(--text-sm); margin: 0 0 16px;">There was an issue communicating with the backend server.</p>
          <button type="button" class="btn btn-secondary" onclick="loadJobsList(${page})" style="border-color: #fca5a5; color: var(--color-text-danger);">
            🔄 Try Again
          </button>
        </div>
      `;
    }
  }

  function renderFilteredJobs(serverPaginationData = null) {
    if (!jobsTableContainer) return;

    let filtered = [...allLoadedJobs];

    if (!filtered || filtered.length === 0) {
      jobsTableContainer.innerHTML = `
        <div style="padding: 48px 20px; text-align: center; background: #ffffff; border: 1px solid var(--subtle-border); border-radius: var(--radius-lg); margin-bottom: 20px;">
          <div style="font-size: 32px; margin-bottom: 8px;">📋</div>
          <strong style="color: var(--color-text-primary); font-size: var(--text-base); display: block; margin-bottom: 4px;">No opportunity leads found</strong>
          <p style="color: var(--color-text-muted); font-size: var(--text-sm); margin: 0 0 16px;">Try clearing your search filters or post a new job requirement.</p>
          <button type="button" class="btn btn-primary" onclick="switchTab('tabPost')">
            ✍️ + Post New Job
          </button>
        </div>
      `;
      return;
    }
    const curPage = serverPaginationData ? (serverPaginationData.current_page || 1) : 1;
    const totalPages = serverPaginationData ? (serverPaginationData.total_pages || 1) : 1;
    const totalCount = serverPaginationData ? (serverPaginationData.total_count || filtered.length) : filtered.length;
    const pageSizeSelect = document.getElementById('ownerPageSize');
    const pageSize = pageSizeSelect ? parseInt(pageSizeSelect.value, 10) : 10;
    const startNum = (curPage - 1) * pageSize + 1;
    const endNum = Math.min(totalCount, curPage * pageSize);

    // Smart windowing for page numbers (e.g. 1 2 3 ... 8)
    let pageNumbers = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pageNumbers.push(i);
    } else {
      if (curPage <= 4) {
        pageNumbers = [1, 2, 3, 4, 5, '...', totalPages];
      } else if (curPage >= totalPages - 3) {
        pageNumbers = [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
      } else {
        pageNumbers = [1, '...', curPage - 1, curPage, curPage + 1, '...', totalPages];
      }
    }

    const pagesHtml = pageNumbers.map(p => {
      if (p === '...') {
        return `<span style="display:inline-flex;align-items:center;justify-content:center;min-width:32px;height:36px;color:#94a3b8;font-weight:700;">…</span>`;
      }
      return `
        <button class="pag-page-btn btn-page-number ${p === curPage ? 'active' : ''}" data-page="${p}" style="min-width: 36px; height: 36px; padding: 0 10px; border-radius: 8px; font-size: 13px; font-weight: 700; border: 1px solid ${p === curPage ? '#2563eb' : '#e2e8f0'}; background: ${p === curPage ? '#2563eb' : '#ffffff'}; color: ${p === curPage ? '#ffffff' : '#0f172a'}; cursor: pointer;">
          ${p}
        </button>
      `;
    }).join('');

    jobsTableContainer.innerHTML = `
      <div class="vp-catalog-grid" style="margin-bottom: 24px;">
        ${filtered.map(j => {
          const isExpired = j.time_left_seconds <= 0 || j.status === 'EXPIRED';
          const hoursLeft = Math.ceil(j.time_left_seconds / 3600);
          const skillsList = Array.isArray(j.skills_list) && j.skills_list.length > 0 
            ? j.skills_list 
            : (j.skills_required ? j.skills_required.split(',').map(s => s.trim()).filter(Boolean) : []);

          return `
          <div class="vp-product-card" data-id="${j.id}">
            <div class="vp-card-header">
              <span class="company-badge">${escapeHtml(j.company_name)}</span>
              <div style="display: flex; gap: 6px; align-items: center;">
                <span class="type-badge">${escapeHtml(j.job_type_display || j.job_type || 'Full-Time')}</span>
                <span class="status-pill ${isExpired ? 'status-expired' : 'status-active'}" style="font-size: 11px;">
                  ${isExpired ? '🔴 Expired' : '🟢 ' + hoursLeft + 'h left'}
                </span>
              </div>
            </div>

            <div class="vp-card-content">
              <h2 class="job-card-title">${escapeHtml(j.title)}</h2>

              <div class="vp-salary-row">
                <span>💰 ${escapeHtml(j.stipend_salary || 'Competitive')}</span>
                <span style="color: var(--color-text-muted); font-weight: 500;">📍 ${escapeHtml(j.location || 'India')}</span>
              </div>

              <div style="font-size: var(--text-xs); font-weight: 600; color: var(--color-text-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 4px;">
                <span>📅 Posted:</span> <strong style="color: var(--color-text-primary);">${escapeHtml(j.posted_date_display || j.posted_date || 'Today')}</strong>
                <span style="margin-left: auto; color: var(--color-text-muted); font-family: monospace; font-size: 11.5px;">#${j.id}</span>
              </div>

              <p style="font-size: var(--text-sm); color: var(--color-text-secondary); line-height: 1.45; margin-bottom: 10px;">${escapeHtml(j.description ? (j.description.length > 130 ? j.description.substring(0, 130) + '...' : j.description) : 'Verified student opening.')}</p>

              <div class="skills-wrapper">
                ${skillsList.slice(0, 4).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
              </div>

              <div class="vp-price-row" style="margin-top: 10px;">
                <div class="timer-tag" style="font-size: 11.5px; font-weight: 700; color: ${isExpired ? 'var(--color-text-danger)' : 'var(--color-text-success)'};">
                  ⏱️ ${isExpired ? 'Expired / Inactive' : 'Auto-Expires in 7 Days (' + hoursLeft + 'h left)'}
                </div>
              </div>

              <div class="card-action-bar" style="margin-top: 14px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                  <button type="button" class="btn btn-primary btn-edit-job" data-id="${j.id}" style="height: 38px;">
                    ✏️ Edit Lead
                  </button>
                  <a href="${escapeHtml(j.apply_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="height: 38px;">
                    ↗ Apply URL
                  </a>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px;">
                  <button type="button" class="btn btn-secondary btn-pipeline-move-job" data-id="${j.id}" data-title="${escapeHtml(j.title)}" style="height: 34px; font-size: 12px;" title="Move or assign this requirement to a specific group">
                    ⇄ Move
                  </button>
                  <button type="button" class="btn btn-ghost btn-toggle-job" data-id="${j.id}" style="height: 34px; font-size: 12px; color: ${isExpired ? 'var(--color-text-success)' : 'var(--color-text-secondary)'};">
                    ${isExpired ? '🚀 Publish' : '⏸️ Unpublish'}
                  </button>
                  <button type="button" class="btn btn-danger-ghost btn-delete-job" data-id="${j.id}" style="height: 34px; font-size: 12px;" title="Delete lead">
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        `}).join('')}
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: #ffffff; border: 1px solid var(--subtle-border); border-radius: var(--radius-md); box-shadow: var(--card-shadow); flex-wrap: wrap; gap: 12px;">
        <div style="font-size: var(--text-sm); color: var(--color-text-muted); font-weight: 600;">
          Showing <strong>${startNum}–${endNum}</strong> of <strong>${totalCount}</strong> verified leads (Page ${curPage} of ${totalPages})
        </div>
        <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
          <button id="btnPrevPage" class="btn btn-secondary" style="height: 36px; padding: 0 12px;" ${curPage <= 1 ? 'disabled' : ''}>
            ← Previous
          </button>
          ${pagesHtml}
          <button id="btnNextPage" class="btn btn-secondary" style="height: 36px; padding: 0 12px;" ${curPage >= totalPages ? 'disabled' : ''}>
            Next →
          </button>
        </div>
      </div>
    `;

    bindJobActionEvents(curPage, totalPages);
  }

  function bindJobActionEvents(curPage = null, totalPages = null) {
    if (curPage === null) {
      const urlParams = new URLSearchParams(window.location.search);
      curPage = parseInt(urlParams.get('page') || '1', 10);
    }
    if (totalPages === null) {
      const activeBtn = document.querySelector('.pag-page-btn.active');
      if (activeBtn) {
        curPage = parseInt(activeBtn.dataset.page || activeBtn.textContent.trim() || '1', 10);
      }
      const allPageBtns = document.querySelectorAll('.pag-page-btn');
      if (allPageBtns.length > 0) {
        const lastBtn = allPageBtns[allPageBtns.length - 1];
        totalPages = parseInt(lastBtn.dataset.page || lastBtn.textContent.trim() || '1', 10);
      } else {
        totalPages = 1;
      }
    }

    const btnPrev = document.getElementById('btnPrevPage');
    const btnNext = document.getElementById('btnNextPage');
    
    if (btnPrev) {
      btnPrev.onclick = (e) => {
        e.preventDefault();
        if (curPage > 1) {
          loadJobsList(curPage - 1);
        }
      };
    }
    
    if (btnNext) {
      btnNext.onclick = (e) => {
        e.preventDefault();
        if (curPage < totalPages) {
          loadJobsList(curPage + 1);
        }
      };
    }

    document.querySelectorAll('.pag-btn-link, .btn-page-number').forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        let targetPage = parseInt(btn.dataset.page, 10);
        if (!targetPage && btn.getAttribute('href')) {
          const m = btn.getAttribute('href').match(/page=(\d+)/);
          if (m) targetPage = parseInt(m[1], 10);
        }
        if (targetPage && targetPage !== curPage) {
          loadJobsList(targetPage);
        }
      };
    });

    document.querySelectorAll('.btn-toggle-job').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        await toggleJobStatus(id);
      };
    });

    document.querySelectorAll('.btn-edit-job').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        await openEditModal(id);
      };
    });

    document.querySelectorAll('.btn-delete-job').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        await deleteJob(id);
      };
    });

    document.querySelectorAll('.btn-pipeline-move-job').forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const jobId = parseInt(btn.dataset.id, 10);
        const jobTitle = btn.dataset.title;
        openMoveRequirementsModal({
          jobIds: [jobId],
          jobTitles: [jobTitle],
          fromGroupId: null,
          fromGroupName: ''
        });
      };
    });
  }

  // --- EDIT JOB MODAL DRAWER LOGIC ---
  const editModal = document.getElementById('editJobModal');
  const formEditJob = document.getElementById('formEditJob');
  const btnCloseEditModal = document.getElementById('btnCloseEditModal');
  const btnCancelEdit = document.getElementById('btnCancelEdit');

  async function openEditModal(id) {
    try {
      showToast('Opening lead editor...', 'info');
      const res = await fetch(`/api/jobs/${id}/`);
      const data = await res.json();
      const job = data.job;

      document.getElementById('eJobId').value = job.id;
      document.getElementById('eTitle').value = job.title || '';
      document.getElementById('eCompany').value = job.company_name || '';
      
      const eCategorySelect = document.getElementById('eCategory');
      if (eCategorySelect) {
        if (eCategorySelect.options.length === 0) {
          const catRes = await fetch('/api/categories/');
          const catData = await catRes.json();
          eCategorySelect.innerHTML = catData.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
        }
        for (let opt of eCategorySelect.options) {
          if (opt.text.toLowerCase() === (job.category_name || '').toLowerCase() || opt.value == job.category_id) {
            opt.selected = true;
            break;
          }
        }
      }

      document.getElementById('eJobType').value = job.job_type || 'FULL_TIME';
      document.getElementById('eApplyUrl').value = job.apply_url || '';
      document.getElementById('eSalary').value = job.stipend_salary || '';
      document.getElementById('eLocation').value = job.location || '';
      document.getElementById('eSkills').value = job.skills_required || '';
      document.getElementById('eDescription').value = job.description || '';
      document.getElementById('eEligibility').value = job.eligibility || '';

      if (editModal) {
        editModal.style.display = 'flex';
        editModal.style.opacity = '1';
        editModal.style.visibility = 'visible';
        editModal.style.pointerEvents = 'auto';
        editModal.classList.add('active');
      }
    } catch (err) {
      console.error('Failed to open edit modal:', err);
      showToast('Error loading lead details for edit.', 'error');
    }
  }

  function closeEditModal() {
    if (editModal) {
      editModal.style.display = 'none';
      editModal.style.opacity = '0';
      editModal.style.visibility = 'hidden';
      editModal.style.pointerEvents = 'none';
      editModal.classList.remove('active');
    }
  }

  if (btnCloseEditModal) btnCloseEditModal.addEventListener('click', closeEditModal);
  if (btnCancelEdit) btnCancelEdit.addEventListener('click', closeEditModal);

  if (editModal) {
    editModal.addEventListener('click', (e) => {
      if (e.target === editModal) closeEditModal();
    });
  }

  if (formEditJob) {
    formEditJob.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('eJobId').value;
      const payload = {
        title: document.getElementById('eTitle').value.trim(),
        company_name: document.getElementById('eCompany').value.trim(),
        category_id: parseInt(document.getElementById('eCategory').value, 10),
        job_type: document.getElementById('eJobType').value,
        apply_url: document.getElementById('eApplyUrl').value.trim(),
        stipend_salary: document.getElementById('eSalary').value.trim(),
        location: document.getElementById('eLocation').value.trim(),
        skills_required: document.getElementById('eSkills').value.trim(),
        description: document.getElementById('eDescription').value.trim(),
        eligibility: document.getElementById('eEligibility').value.trim(),
      };

      try {
        const res = await authFetch(`/api/owner/jobs/${id}/update/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast('Lead updated successfully!', 'success');
          logActivity(`Lead updated #${id}`, `${payload.company_name} - ${payload.title}`);
          closeEditModal();
          await loadJobsList(currentJobsPage);
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
      const res = await authFetch(`/api/owner/jobs/${id}/toggle-status/`, { method: 'POST' });
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
    if (!confirm(`Are you sure you want to permanently delete lead #${id}?`)) return;
    try {
      const res = await authFetch(`/api/owner/jobs/${id}/delete/`, { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Lead deleted from pipeline.', 'success');
        logActivity(`Lead deleted #${id}`, 'Permanently removed from CRM');
        const card = document.querySelector(`.vp-product-card[data-id="${id}"]`);
        if (card) card.remove();
        loadKpiStats();
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
        const res = await authFetch('/api/owner/categories/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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

  let allGroupsData = [];

  // --- INDIAN STANDARD TIME (IST) FORMATTING HELPERS ---
  function getIndianTimeString(dateObj = new Date()) {
    try {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      }).format(dateObj) + ' IST';
    } catch (e) {
      return dateObj.toLocaleTimeString();
    }
  }

  function getIndianDateTimeString(dateObj = new Date()) {
    try {
      return new Intl.DateTimeFormat('en-IN', {
        timeZone: 'Asia/Kolkata',
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(dateObj) + ' IST';
    } catch (e) {
      return dateObj.toLocaleString();
    }
  }

  async function loadGroupsList() {
    const container = document.getElementById('ownerGroupsTableContainer');
    if (!container) return;

    container.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--color-text-muted);">Loading requirement groups...</div>';

    try {
      const res = await authFetch('/api/owner/groups/');
      const data = await res.json();
      const groups = data.groups || [];
      allGroupsData = groups;

      if (groups.length === 0) {
        container.innerHTML = `
          <div style="padding: 48px 24px; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">📦</div>
            <h3 style="font-size: 16px; font-weight: 800; color: var(--color-text-primary); margin-bottom: 6px;">No Requirement Groups Yet</h3>
            <p style="font-size: 13px; color: var(--color-text-muted); margin-bottom: 16px;">
              Whenever you use the Bulk Parser or Create Group, a bundle is automatically created with direct shareable links!
            </p>
            <button class="btn btn-primary" style="height: 38px; font-size: 13px;" onclick="document.querySelector('[data-tab=tabBulkParse]').click()">
              ⚡ Open Bulk Parser
            </button>
          </div>
        `;
        return;
      }

      let html = `
        <table class="data-table" style="width: 100%;">
          <thead>
            <tr>
              <th style="width: 30%;">Group / Drive Name</th>
              <th style="width: 15%;">Active Jobs</th>
              <th style="width: 20%;">Created Date (IST)</th>
              <th style="width: 10%;">Views</th>
              <th style="width: 25%; text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
      `;

      groups.forEach(g => {
        const jobsCount = g.jobs ? g.jobs.length : (g.total_jobs_count || 0);
        html += `
          <tr data-group-id="${g.id}">
            <td>
              <div style="font-weight: 800; color: var(--color-text-primary); font-size: 14px;">${escapeHtml(g.name)}</div>
              <div style="font-size: 11px; color: var(--blue-primary); font-family: ui-monospace, monospace; margin-top: 2px;">/group/${escapeHtml(g.slug)}/</div>
            </td>
            <td>
              <button type="button" class="btn-toggle-group-jobs btn btn-ghost" data-group-id="${g.id}" style="height: 28px; padding: 0 8px; font-size: 12px; background: var(--blue-light); color: var(--blue-primary); border-radius: var(--radius-sm); border: 1px solid var(--blue-border);" title="Click to view & move requirements">
                📂 ${g.active_jobs_count} Jobs ▾
              </button>
            </td>
            <td style="color: var(--color-text-muted); font-size: 12.5px;">${escapeHtml(g.created_at)}</td>
            <td style="font-weight: 700; color: var(--color-text-primary); font-size: 13px;">👁️ ${g.views_count}</td>
            <td style="text-align: right;">
              <div style="display: inline-flex; gap: 6px; align-items: center;">
                <button type="button" class="btn-toggle-group-jobs btn btn-secondary" data-group-id="${g.id}" style="padding: 4px 9px; font-size: 12px; height: 32px;">
                  ⇄ Move Jobs
                </button>
                <a href="${escapeHtml(g.url)}" target="_blank" class="btn btn-secondary" style="padding: 4px 9px; font-size: 12px; height: 32px;" title="Open live public group page">
                  Open ↗
                </a>
                <button type="button" class="btn btn-secondary btn-group-broadcast" data-id="${g.id}" style="padding: 4px 9px; font-size: 12px; height: 32px; background: #ecfdf5; color: #059669; border-color: #a7f3d0;" title="Get WhatsApp / Telegram broadcast message">
                  Broadcast
                </button>
                <button type="button" class="btn btn-danger-ghost btn-group-delete" data-id="${g.id}" data-name="${escapeHtml(g.name)}" style="padding: 4px 8px; font-size: 12px; height: 32px;" title="Delete group bundle">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
          <!-- Expandable Group Requirements Drawer Row -->
          <tr id="group-jobs-drawer-${g.id}" class="group-jobs-drawer-row" style="display: none; background: #f8fafc;">
            <td colspan="5" style="padding: 16px 20px; border-bottom: 2px solid var(--blue-border);">
              <div style="background: #ffffff; border: 1px solid var(--subtle-border); border-radius: var(--radius-md); padding: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <label style="font-size: var(--text-xs); font-weight: 700; color: var(--color-text-secondary); display: flex; align-items: center; gap: 6px; cursor: pointer;">
                      <input type="checkbox" class="select-all-group-jobs" data-group-id="${g.id}">
                      <span>Select All (${jobsCount})</span>
                    </label>
                  </div>
                  <div style="display: flex; gap: 8px; align-items: center;">
                    <button type="button" class="btn-bulk-move-jobs btn btn-primary" data-group-id="${g.id}" data-group-name="${escapeHtml(g.name)}" style="height: 30px; font-size: 12px; padding: 0 10px; display: none;">
                      ⇄ Move Selected (<span class="selected-count">0</span>)
                    </button>
                  </div>
                </div>

                <div class="group-jobs-list" data-group-id="${g.id}" style="display: flex; flex-direction: column; gap: 6px;">
                  ${(!g.jobs || g.jobs.length === 0) ? `
                    <div style="padding: 14px; text-align: center; color: var(--color-text-muted); font-size: var(--text-xs);">
                      No requirements currently in this group. Use the Bulk Parser or Move tools to assign jobs here.
                    </div>
                  ` : g.jobs.map(j => `
                    <div class="group-job-item" style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: var(--surface-hover); border: 1px solid var(--subtle-border); border-radius: var(--radius-sm); gap: 10px;">
                      <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                        <input type="checkbox" class="group-job-checkbox" data-group-id="${g.id}" data-job-id="${j.id}" data-job-title="${escapeHtml(j.title)}">
                        <div style="min-width: 0; flex: 1;">
                          <div style="font-size: var(--text-sm); font-weight: 700; color: var(--color-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${escapeHtml(j.title)} <span style="font-weight: 500; color: var(--color-text-muted);">at ${escapeHtml(j.company_name)}</span>
                          </div>
                          <div style="font-size: 11px; color: var(--color-text-muted);">
                            📍 ${escapeHtml(j.location || 'India')} • 💰 ${escapeHtml(j.stipend_salary || 'Competitive')} • 📅 ${escapeHtml(j.posted_date || '')}
                          </div>
                        </div>
                      </div>
                      <div style="display: inline-flex; gap: 6px; align-items: center; flex-shrink: 0;">
                        <button type="button" class="btn-move-single-job btn btn-secondary" data-job-id="${j.id}" data-job-title="${escapeHtml(j.title)}" data-from-group-id="${g.id}" data-from-group-name="${escapeHtml(g.name)}" style="height: 28px; padding: 0 9px; font-size: 11.5px; border-color: var(--blue-border); color: var(--blue-primary);">
                          ⇄ Move
                        </button>
                        <button type="button" class="btn-remove-single-job btn btn-danger-ghost" data-job-id="${j.id}" data-job-title="${escapeHtml(j.title)}" data-group-id="${g.id}" data-group-name="${escapeHtml(g.name)}" style="height: 28px; padding: 0 8px; font-size: 11.5px;" title="Remove from this group only">
                          ✕ Remove
                        </button>
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            </td>
          </tr>
        `;
      });

      html += '</tbody></table>';
      container.innerHTML = html;

      // 1. Toggle Drawer Handlers
      container.querySelectorAll('.btn-toggle-group-jobs').forEach(btn => {
        btn.addEventListener('click', () => {
          const groupId = btn.dataset.groupId;
          const drawer = document.getElementById(`group-jobs-drawer-${groupId}`);
          if (drawer) {
            const isHidden = drawer.style.display === 'none';
            drawer.style.display = isHidden ? 'table-row' : 'none';
            btn.textContent = isHidden ? `📂 Hide Jobs ▴` : `📂 Jobs ▾`;
          }
        });
      });

      // 2. Single Job Move Button Click
      container.querySelectorAll('.btn-move-single-job').forEach(btn => {
        btn.addEventListener('click', () => {
          const jobId = parseInt(btn.dataset.jobId, 10);
          const jobTitle = btn.dataset.jobTitle;
          const fromGroupId = parseInt(btn.dataset.fromGroupId, 10);
          const fromGroupName = btn.dataset.fromGroupName;

          openMoveRequirementsModal({
            jobIds: [jobId],
            jobTitles: [jobTitle],
            fromGroupId: fromGroupId,
            fromGroupName: fromGroupName
          });
        });
      });

      // 3. Remove Single Job from Group
      container.querySelectorAll('.btn-remove-single-job').forEach(btn => {
        btn.addEventListener('click', async () => {
          const jobId = btn.dataset.jobId;
          const jobTitle = btn.dataset.jobTitle;
          const groupId = btn.dataset.groupId;
          const groupName = btn.dataset.groupName;

          if (confirm(`Remove "${jobTitle}" from group "${groupName}"? (The job posting will remain active on the student feed).`)) {
            try {
              const res = await authFetch(`/api/owner/groups/${groupId}/remove-job/${jobId}/`, {
                method: 'POST'
              });
              const data = await res.json();
              if (res.ok) {
                showToast(data.message || 'Job removed from group.', 'success');
                logActivity('Removed job from group', `${jobTitle} from ${groupName}`);
                loadGroupsList();
              } else {
                showToast(data.error || 'Failed to remove job from group.', 'error');
              }
            } catch (err) {
              showToast('Network error removing job from group.', 'error');
            }
          }
        });
      });

      // 4. Checkbox Selection & Bulk Move
      container.querySelectorAll('.select-all-group-jobs').forEach(chkAll => {
        chkAll.addEventListener('change', () => {
          const groupId = chkAll.dataset.groupId;
          const checkboxes = container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]`);
          checkboxes.forEach(c => { c.checked = chkAll.checked; });
          updateBulkMoveButtonState(groupId);
        });
      });

      container.querySelectorAll('.group-job-checkbox').forEach(chk => {
        chk.addEventListener('change', () => {
          const groupId = chk.dataset.groupId;
          updateBulkMoveButtonState(groupId);
        });
      });

      function updateBulkMoveButtonState(groupId) {
        const checked = container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]:checked`);
        const bulkBtn = container.querySelector(`.btn-bulk-move-jobs[data-group-id="${groupId}"]`);
        if (bulkBtn) {
          if (checked.length > 0) {
            bulkBtn.style.display = 'inline-flex';
            const countEl = bulkBtn.querySelector('.selected-count');
            if (countEl) countEl.textContent = checked.length;
          } else {
            bulkBtn.style.display = 'none';
          }
        }
      }

      // 5. Bulk Move Button Click
      container.querySelectorAll('.btn-bulk-move-jobs').forEach(btn => {
        btn.addEventListener('click', () => {
          const groupId = parseInt(btn.dataset.groupId, 10);
          const groupName = btn.dataset.groupName;
          const checked = Array.from(container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]:checked`));
          
          if (checked.length === 0) return;

          const jobIds = checked.map(c => parseInt(c.dataset.jobId, 10));
          const jobTitles = checked.map(c => c.dataset.jobTitle);

          openMoveRequirementsModal({
            jobIds: jobIds,
            jobTitles: jobTitles,
            fromGroupId: groupId,
            fromGroupName: groupName
          });
        });
      });

      // 6. Broadcast Button
      container.querySelectorAll('.btn-group-broadcast').forEach(btn => {
        btn.addEventListener('click', async () => {
          const groupId = btn.dataset.id;
          try {
            const res = await authFetch(`/api/owner/groups/${groupId}/broadcast/`);
            const data = await res.json();
            if (res.ok) {
              openBroadcastModal(data);
            }
          } catch (err) {
            showToast('Failed to fetch group broadcast details.', 'error');
          }
        });
      });

      // 7. Delete Button
      container.querySelectorAll('.btn-group-delete').forEach(btn => {
        btn.addEventListener('click', async () => {
          const groupId = btn.dataset.id;
          const groupName = btn.dataset.name;
          if (confirm(`Are you sure you want to delete group "${groupName}"? (The individual job postings will remain untouched).`)) {
            try {
              const res = await authFetch(`/api/owner/groups/${groupId}/delete/`, {
                method: 'POST'
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
      container.innerHTML = '<div style="padding: 32px; text-align: center; color: var(--color-text-danger);">Failed to load requirement groups.</div>';
    }
  }

  // --- MOVE REQUIREMENTS MODAL WORKFLOW ---

  async function openMoveRequirementsModal({ jobIds, jobTitles, fromGroupId, fromGroupName }) {
    const modal = document.getElementById('moveRequirementsModal');
    if (!modal) return;

    // Show modal immediately with high priority styles and class
    modal.classList.add('active', 'open');
    modal.style.setProperty('display', 'flex', 'important');

    const jobIdsInput = document.getElementById('moveJobIds');
    const manualJobIdsInput = document.getElementById('manualJobIdsInput');
    const fromGroupIdInput = document.getElementById('moveFromGroupId');
    const summaryText = document.getElementById('moveJobsSummaryText');
    const sourceGroupText = document.getElementById('moveSourceGroupText');
    const targetSelect = document.getElementById('moveToGroupSelect');
    const filterInput = document.getElementById('filterTargetGroupInput');
    const newGroupDrawer = document.getElementById('newSpecificGroupDrawer');
    const newGroupNameInput = document.getElementById('newSpecificGroupNameInput');
    const newGroupTagInput = document.getElementById('newSpecificGroupTagInput');

    const validIds = Array.isArray(jobIds) ? jobIds.filter(id => id !== undefined && id !== null && id !== '') : [];

    if (jobIdsInput) jobIdsInput.value = JSON.stringify(validIds);
    if (manualJobIdsInput) manualJobIdsInput.value = validIds.length > 0 ? validIds.join(', ') : '';
    if (fromGroupIdInput) fromGroupIdInput.value = fromGroupId || '';

    function updateSummaryFromInput() {
      const raw = manualJobIdsInput ? manualJobIdsInput.value.trim() : '';
      if (!raw) {
        if (summaryText) summaryText.textContent = 'Type Job ID(s) above';
        return;
      }
      const parsed = raw.split(',').map(x => x.trim()).filter(x => x.length > 0);
      if (summaryText) {
        if (parsed.length === 1) {
          summaryText.textContent = `Requirement #${parsed[0]} selected`;
        } else {
          summaryText.textContent = `${parsed.length} requirements selected (#${parsed.join(', #')})`;
        }
      }
    }

    if (manualJobIdsInput) {
      manualJobIdsInput.oninput = updateSummaryFromInput;
      updateSummaryFromInput();
    }

    if (sourceGroupText) {
      sourceGroupText.textContent = fromGroupName ? `From Source Group: ${fromGroupName}` : 'From: Pipeline';
    }

    if (filterInput) filterInput.value = '';
    if (newGroupNameInput) newGroupNameInput.value = '';
    if (newGroupTagInput) newGroupTagInput.value = '';
    if (newGroupDrawer) newGroupDrawer.style.display = 'none';

    function renderTargetGroupOptions(filterText = '') {
      if (!targetSelect) return;
      const lowerFilter = filterText.toLowerCase().trim();
      const filteredGroups = (allGroupsData || []).filter(g => {
        if (fromGroupId && g.id === fromGroupId) return false;
        if (!lowerFilter) return true;
        return g.name.toLowerCase().includes(lowerFilter) || (g.slug && g.slug.toLowerCase().includes(lowerFilter));
      });

      let optionsHtml = '<option value="">-- Choose Target Specific Group --</option>';
      optionsHtml += '<option value="NEW" style="font-weight: 800; color: #2563eb;">✨ + Create New Specific Group & Move...</option>';

      if (filteredGroups.length > 0) {
        filteredGroups.forEach(g => {
          optionsHtml += `<option value="${g.id}">📁 ${escapeHtml(g.name)} (${g.active_jobs_count || 0} active)</option>`;
        });
      } else if (allGroupsData && allGroupsData.length === 0) {
        optionsHtml = '<option value="NEW" selected style="font-weight: 800; color: #2563eb;">✨ + Create New Specific Group & Move...</option>';
        if (newGroupDrawer) newGroupDrawer.style.display = 'block';
      }

      targetSelect.innerHTML = optionsHtml;
    }

    // Render immediately if we already have group data in memory
    if (allGroupsData && allGroupsData.length > 0) {
      renderTargetGroupOptions('');
    } else if (targetSelect) {
      targetSelect.innerHTML = '<option value="">⏳ Loading existing groups...</option><option value="NEW" style="font-weight: 800; color: #2563eb;">✨ + Create New Specific Group & Move...</option>';
    }

    // Fetch lean summary groups from API
    try {
      const gRes = await authFetch('/api/owner/groups/?summary=true');
      if (gRes.ok) {
        const gData = await gRes.json();
        allGroupsData = gData.groups || [];
        renderTargetGroupOptions(filterInput ? filterInput.value : '');
      }
    } catch (err) {
      console.error('Error fetching groups for move modal:', err);
    }

    if (filterInput) {
      filterInput.oninput = () => {
        renderTargetGroupOptions(filterInput.value);
      };
    }

    if (targetSelect) {
      targetSelect.onchange = () => {
        if (targetSelect.value === 'NEW') {
          if (newGroupDrawer) newGroupDrawer.style.display = 'block';
          if (newGroupNameInput) newGroupNameInput.focus();
        } else {
          if (newGroupDrawer) newGroupDrawer.style.display = 'none';
        }
      };
    }

    if (manualJobIdsInput && !validIds.length) {
      setTimeout(() => manualJobIdsInput.focus(), 50);
    }
  }

  function closeMoveRequirementsModal() {
    const modal = document.getElementById('moveRequirementsModal');
    if (modal) {
      modal.classList.remove('active', 'open');
      modal.style.setProperty('display', 'none', 'important');
    }
  }

  const btnCloseMoveModal = document.getElementById('btnCloseMoveModal');
  const btnCancelMove = document.getElementById('btnCancelMove');
  if (btnCloseMoveModal) btnCloseMoveModal.addEventListener('click', closeMoveRequirementsModal);
  if (btnCancelMove) btnCancelMove.addEventListener('click', closeMoveRequirementsModal);

  // Quick Action Buttons for Move by Job ID
  const btnOpenMoveByIdPipeline = document.getElementById('btnOpenMoveByIdPipeline');
  const btnOpenMoveByIdGroups = document.getElementById('btnOpenMoveByIdGroups');

  if (btnOpenMoveByIdPipeline) {
    btnOpenMoveByIdPipeline.addEventListener('click', () => {
      openMoveRequirementsModal({
        jobIds: [],
        jobTitles: [],
        fromGroupId: null,
        fromGroupName: ''
      });
    });
  }

  if (btnOpenMoveByIdGroups) {
    btnOpenMoveByIdGroups.addEventListener('click', () => {
      openMoveRequirementsModal({
        jobIds: [],
        jobTitles: [],
        fromGroupId: null,
        fromGroupName: ''
      });
    });
  }

  const formMoveRequirements = document.getElementById('formMoveRequirements');
  if (formMoveRequirements) {
    formMoveRequirements.addEventListener('submit', async (e) => {
      e.preventDefault();
      const manualJobIdsVal = document.getElementById('manualJobIdsInput')?.value.trim() || '';
      const fromGroupId = document.getElementById('moveFromGroupId').value;
      const toGroupId = document.getElementById('moveToGroupSelect').value;
      const actionType = document.querySelector('input[name="moveActionType"]:checked')?.value || 'move';
      const btnConfirm = document.getElementById('btnConfirmMove');
      const newGroupName = document.getElementById('newSpecificGroupNameInput')?.value.trim() || '';
      const newGroupTag = document.getElementById('newSpecificGroupTagInput')?.value.trim() || '';

      if (!manualJobIdsVal) {
        showToast('Please type at least one Requirement Job ID (e.g. 263).', 'error');
        return;
      }

      if (!toGroupId) {
        showToast('Please select a destination group or choose to create a new one.', 'error');
        return;
      }

      if (toGroupId === 'NEW' && !newGroupName) {
        showToast('Please enter a name for the new specific group.', 'error');
        return;
      }

      const jobIds = manualJobIdsVal
        .split(',')
        .map(x => parseInt(x.trim(), 10))
        .filter(n => !isNaN(n) && n > 0);

      if (!jobIds || jobIds.length === 0) {
        showToast('Please enter a valid numeric Requirement Job ID (e.g. 263).', 'error');
        return;
      }

      if (btnConfirm) {
        btnConfirm.textContent = 'Moving...';
        btnConfirm.disabled = true;
      }

      try {
        const payload = {
          job_ids: jobIds,
          from_group_id: fromGroupId ? parseInt(fromGroupId, 10) : null,
          action: actionType
        };

        if (toGroupId === 'NEW') {
          payload.to_group_id = 'NEW';
          payload.new_group_name = newGroupName;
          payload.banner_tag = newGroupTag;
        } else {
          payload.to_group_id = parseInt(toGroupId, 10);
        }

        const res = await authFetch('/api/owner/groups/move-jobs/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(data.message || 'Requirements transferred successfully!', 'success');
          logActivity('Transferred requirements', data.message);
          closeMoveRequirementsModal();
          loadGroupsList();
          loadJobsList(currentJobsPage);
          loadKpiStats();
        } else {
          showToast(data.error || 'Failed to move requirements.', 'error');
        }
      } catch (err) {
        console.error('Error moving jobs between groups:', err);
        showToast('Network error while moving requirements.', 'error');
      } finally {
        if (btnConfirm) {
          btnConfirm.textContent = 'Confirm Move ⇄';
          btnConfirm.disabled = false;
        }
      }
    });
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
      const res = await authFetch('/api/owner/analytics/', {
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
          topPagesContainer.innerHTML = '<div style="color: var(--color-text-muted); font-size: var(--text-sm); padding: 12px 0;">No page views recorded yet.</div>';
        } else {
          topPagesContainer.innerHTML = data.top_pages.map((p, idx) => `
            <div class="ana-page-row">
              <div style="flex: 1; min-width: 0;">
                <a href="${escapeHtml(p.path)}" target="_blank" rel="noopener noreferrer" class="ana-page-link" title="Open ${escapeHtml(p.path)} in new tab">
                  <div class="ana-page-title">
                    <span style="color: var(--blue-primary); font-weight: 800; margin-right: 4px;">#${idx + 1}</span>
                    <span>${escapeHtml(p.page_title || p.path)}</span>
                  </div>
                  <div class="ana-page-path">
                    ${escapeHtml(p.path)} <span style="font-size: 10px; opacity: 0.7;">↗</span>
                  </div>
                </a>
              </div>
              <div style="text-align: right; flex-shrink: 0;">
                <div style="font-size: var(--text-sm); font-weight: 800; color: var(--blue-primary);">${Number(p.views || 0).toLocaleString()} views</div>
                <div style="font-size: var(--text-xs); color: var(--color-text-muted);">${Number(p.unique_visitors || 0).toLocaleString()} unique</div>
              </div>
            </div>
          `).join('');
        }
      }

      // 4. Traffic Channels & Referrers
      const referrersContainer = document.getElementById('anaReferrersList');
      if (referrersContainer) {
        if (!data.referrers || data.referrers.length === 0) {
          referrersContainer.innerHTML = '<div style="color: var(--color-text-muted); font-size: var(--text-sm);">No referrer data yet.</div>';
        } else {
          referrersContainer.innerHTML = data.referrers.map(r => `
            <div>
              <div style="display: flex; justify-content: space-between; font-size: var(--text-xs); font-weight: 600; color: var(--color-text-secondary); margin-bottom: 4px;">
                <span>${escapeHtml(r.source)}</span>
                <span style="color: var(--blue-primary); font-weight: 700;">${r.count} hits (${r.percentage}%)</span>
              </div>
              <div style="height: 6px; width: 100%; background: var(--surface-hover); border-radius: var(--radius-full); overflow: hidden; border: 1px solid var(--subtle-border);">
                <div style="height: 100%; width: ${r.percentage}%; background: linear-gradient(90deg, #2563eb, #38bdf8); border-radius: var(--radius-full);"></div>
              </div>
            </div>
          `).join('');
        }
      }

      // 5. Operating Systems & Platforms Breakdown
      const platformsContainer = document.getElementById('anaPlatformsList');
      if (platformsContainer) {
        const osItems = (data.operating_systems || []).map(o => `
          <div class="platform-card-item">
            <span style="font-weight: 600;">💻 ${escapeHtml(o.os)}</span>
            <strong style="color: var(--color-text-primary); font-weight: 700;">${o.count}</strong>
          </div>
        `);
        const browserItems = (data.browsers || []).map(b => `
          <div class="platform-card-item">
            <span style="font-weight: 600;">🌐 ${escapeHtml(b.browser)}</span>
            <strong style="color: var(--blue-primary); font-weight: 700;">${b.count}</strong>
          </div>
        `);
        platformsContainer.innerHTML = [...osItems, ...browserItems].join('') || '<div style="color: var(--color-text-muted); font-size: var(--text-xs);">No platform data yet</div>';
      }

      // 6. Recent Real-Time Visitors Table
      const visitsBody = document.getElementById('anaRecentVisitsBody');
      if (visitsBody) {
        if (!data.recent_visits || data.recent_visits.length === 0) {
          visitsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--color-text-muted); padding: 20px;">No recent live visits yet.</td></tr>';
        } else {
          visitsBody.innerHTML = data.recent_visits.map(v => `
            <tr>
              <td style="white-space: nowrap; font-size: var(--text-xs); color: var(--color-text-muted);">
                <strong style="color: var(--blue-primary);">${escapeHtml(v.time)}</strong><br>
                <small>${escapeHtml(v.date)}</small>
              </td>
              <td>
                <div style="font-weight: 700; color: var(--color-text-primary); font-size: var(--text-sm);">${escapeHtml(v.page_title || v.path)}</div>
                <div style="font-size: 11px; color: var(--color-text-muted); font-family: monospace;">${escapeHtml(v.path)}</div>
              </td>
              <td>
                <span class="company-badge" style="font-size: 11px;">
                  ${escapeHtml(v.referrer || 'Direct')}
                </span>
              </td>
              <td style="font-size: var(--text-xs); color: var(--color-text-secondary);">
                ${v.device === 'Mobile' ? '📱 Mobile' : (v.device === 'Tablet' ? '📟 Tablet' : '💻 Desktop')} • ${escapeHtml(v.os || '')} (${escapeHtml(v.browser || '')})
              </td>
              <td style="font-family: monospace; font-size: 11.5px; color: var(--color-text-muted);">
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
    const timeStr = getIndianTimeString();
    const item = document.createElement('div');
    item.className = 'crm-activity-item';
    item.innerHTML = `
      <div class="crm-activity-dot"></div>
      <div>
        <strong style="color: var(--color-text-primary); font-size: 13.5px;">${escapeHtml(action)}</strong>
        <div style="font-size: 11.5px; color: var(--color-text-muted); margin-top: 2px;">${escapeHtml(details)} • ${timeStr}</div>
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

  // --- GLOBAL EVENT DELEGATION (Bulletproof Click Handling) ---
  document.addEventListener('click', (e) => {
    // 1. Pipeline Move Button
    const btnPipelineMove = e.target.closest('.btn-pipeline-move-job');
    if (btnPipelineMove) {
      e.preventDefault();
      e.stopPropagation();
      const jobId = parseInt(btnPipelineMove.dataset.id, 10);
      const jobTitle = btnPipelineMove.dataset.title || '';
      openMoveRequirementsModal({
        jobIds: [jobId],
        jobTitles: [jobTitle],
        fromGroupId: null,
        fromGroupName: ''
      });
      return;
    }

    // 2. Toolbar Quick Move by Job ID
    const btnQuickMove = e.target.closest('#btnOpenMoveByIdPipeline, #btnOpenMoveByIdGroups');
    if (btnQuickMove) {
      e.preventDefault();
      e.stopPropagation();
      openMoveRequirementsModal({
        jobIds: [],
        jobTitles: [],
        fromGroupId: null,
        fromGroupName: ''
      });
      return;
    }

    // 3. Move Single Requirement in Group Drawer
    const btnMoveGroupJob = e.target.closest('.btn-move-group-job');
    if (btnMoveGroupJob) {
      e.preventDefault();
      e.stopPropagation();
      const jobId = parseInt(btnMoveGroupJob.dataset.jobId, 10);
      const jobTitle = btnMoveGroupJob.dataset.jobTitle || '';
      const fromGroupId = parseInt(btnMoveGroupJob.dataset.fromGroupId, 10);
      const fromGroupName = btnMoveGroupJob.dataset.fromGroupName || '';
      openMoveRequirementsModal({
        jobIds: [jobId],
        jobTitles: [jobTitle],
        fromGroupId: fromGroupId,
        fromGroupName: fromGroupName
      });
      return;
    }

    // 4. Modal Close / Cancel Buttons
    const btnCloseModal = e.target.closest('#btnCloseMoveModal, #btnCancelMove');
    if (btnCloseModal) {
      e.preventDefault();
      closeMoveRequirementsModal();
      return;
    }

    // 5. Close Modal on Backdrop Click
    if (e.target.id === 'moveRequirementsModal') {
      closeMoveRequirementsModal();
      return;
    }
  });

  window.openMoveRequirementsModal = openMoveRequirementsModal;
  window.closeMoveRequirementsModal = closeMoveRequirementsModal;
});

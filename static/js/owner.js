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
  let currentGroupsPage = 1;

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
    'tabLinkedin': { title: 'LinkedIn Post Scraper & Referrals Ingestion', sub: 'Scrape LinkedIn posts, extract requirements & employee referrals, validate quality scorecard, and pass directly to live pipeline.' },
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
    'tabLinkedin': '/owner/linkedin-scraper/',
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
    '/owner/linkedin-scraper/': 'tabLinkedin',
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

      loadAnalyticsData(true).finally(() => {
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

    const crmExperienceFilter = document.getElementById('crmExperienceFilter');
    if (crmExperienceFilter) {
      crmExperienceFilter.addEventListener('change', () => {
        const val = crmExperienceFilter.value;
        document.querySelectorAll('.owner-exp-pill').forEach(p => {
          if (p.dataset.exp === val) p.classList.add('active');
          else p.classList.remove('active');
        });
        loadJobsList(1);
      });
    }

    document.querySelectorAll('.owner-exp-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.owner-exp-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        const expVal = pill.dataset.exp || 'ALL';
        const expSelect = document.getElementById('crmExperienceFilter');
        if (expSelect) expSelect.value = expVal;
        loadJobsList(1);
      });
    });

    const crmSourceFilter = document.getElementById('crmSourceFilter');
    if (crmSourceFilter) {
      crmSourceFilter.addEventListener('change', () => {
        loadJobsList(1);
      });
    }

    const crmRecencyFilter = document.getElementById('crmRecencyFilter');
    if (crmRecencyFilter) {
      crmRecencyFilter.addEventListener('change', () => {
        loadJobsList(1);
      });
    }

    const ownerGroupsSearch = document.getElementById('ownerGroupsSearch');
    if (ownerGroupsSearch) {
      let debounceTimer;
      ownerGroupsSearch.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => loadGroupsList(1), 300);
        const clearBtn = document.getElementById('btnGroupsSearchClear');
        if (clearBtn) clearBtn.style.display = ownerGroupsSearch.value ? 'block' : 'none';
      });
    }

    const btnGroupsSearchClear = document.getElementById('btnGroupsSearchClear');
    if (btnGroupsSearchClear) {
      btnGroupsSearchClear.addEventListener('click', () => {
        const searchInput = document.getElementById('ownerGroupsSearch');
        if (searchInput) searchInput.value = '';
        btnGroupsSearchClear.style.display = 'none';
        loadGroupsList(1);
      });
    }

    const ownerGroupsFilter = document.getElementById('ownerGroupsFilter');
    if (ownerGroupsFilter) {
      ownerGroupsFilter.addEventListener('change', () => {
        loadGroupsList(1);
      });
    }

    const ownerGroupsPageSize = document.getElementById('ownerGroupsPageSize');
    if (ownerGroupsPageSize) {
      ownerGroupsPageSize.addEventListener('change', () => {
        loadGroupsList(1);
      });
    }

    const btnRefreshGroups = document.getElementById('btnRefreshGroups');
    if (btnRefreshGroups) {
      btnRefreshGroups.addEventListener('click', () => {
        loadGroupsList(currentGroupsPage || 1);
        showToast('Requirement groups refreshed and empty groups cleaned up!', 'success');
      });
    }

    const btnAutoOrganizeGroups = document.getElementById('btnAutoOrganizeGroups');
    if (btnAutoOrganizeGroups) {
      btnAutoOrganizeGroups.addEventListener('click', async () => {
        btnAutoOrganizeGroups.textContent = 'Sorting and cleaning...';
        btnAutoOrganizeGroups.disabled = true;
        try {
          const res = await authFetch('/api/owner/groups/auto-organize/', { method: 'POST' });
          const data = await res.json();
          if (res.ok) {
            showToast(data.message || 'Auto-segregated requirements successfully!', 'success');
            logActivity('Auto-segregated groups', data.message);
            loadGroupsList();
            loadKpiStats();
          } else {
            showToast(data.error || 'Failed to auto-segregate groups.', 'error');
          }
        } catch (err) {
          showToast('Network error while auto-segregating groups.', 'error');
        } finally {
          btnAutoOrganizeGroups.textContent = 'Auto-sort freshers and experienced';
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
        submitBtn.textContent = 'Signing in...';
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
            submitBtn.textContent = 'Sign in to Studio';
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
          showToast(`${data.message}`, 'success');
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
      showToast(`Crawling Jobdexo for latest ${limit} off-campus opportunities...`, 'success');
      const res = await authFetch('/api/owner/jobdexo/fetch-latest/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit, group_name: groupName })
      });
      const data = await res.json();

      if (res.ok && data.success) {
        showToast(`${data.message}`, 'success');
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
        showToast('Cleaning database duplicates and standardizing company names...', 'success');
        const res = await authFetch('/api/owner/jobdexo/cleanup/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`${data.message}`, 'success');
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
        showToast('Importing jobs from provided Jobdexo URLs...', 'success');
        const res = await authFetch('/api/owner/jobdexo/import-urls/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ urls: rawUrls, group_name: groupName })
        });
        const data = await res.json();

        if (res.ok && data.success) {
          showToast(`${data.message}`, 'success');
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
          showToast(`Parsed and published: ${data.company_name} - ${data.title}`, 'success');
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

  // --- LINKEDIN POST SCRAPER & REFERRALS PIPELINE ---

  let currentParsedLinkedInLead = null;

  window.handleScrapeAndParseLinkedIn = async function() {
    const postUrl = document.getElementById('linkedinPostUrl')?.value.trim() || '';
    const rawText = document.getElementById('linkedinRawText')?.value.trim() || '';
    const oppType = document.getElementById('linkedinOpportunityType')?.value || 'auto';
    const referrerName = document.getElementById('linkedinReferrerName')?.value.trim() || '';
    const referrerLinkedin = document.getElementById('linkedinReferrerLinkedin')?.value.trim() || '';

    if (!postUrl && !rawText) {
      showToast('Please provide either a LinkedIn URL or paste the post text.', 'warn');
      return;
    }

    const loadEl = document.getElementById('linkedinLoadingState');
    const cardEl = document.getElementById('linkedinValidationCard');
    const successAlert = document.getElementById('linkedinSuccessAlert');
    if (loadEl) loadEl.style.display = 'block';
    if (cardEl) cardEl.style.display = 'none';
    if (successAlert) successAlert.style.display = 'none';

    try {
      const res = await authFetch('/api/owner/linkedin/parse/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          post_url: postUrl,
          raw_text: rawText,
          force_referral: oppType === 'referral' ? true : (oppType === 'requirement' ? false : null),
          referrer_name: referrerName,
          referrer_linkedin: referrerLinkedin
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        currentParsedLinkedInLead = data.parsed;
        renderLinkedInValidationReview(data.parsed, data.validation);
        showToast('LinkedIn lead parsed & validated!', 'success');
      } else {
        showToast(data.error || 'Failed to parse LinkedIn post.', 'error');
      }
    } catch (err) {
      showToast('Network error while parsing LinkedIn post: ' + err.message, 'error');
    } finally {
      if (loadEl) loadEl.style.display = 'none';
    }
  };

  window.renderLinkedInValidationReview = function(parsed, validation) {
    const cardEl = document.getElementById('linkedinValidationCard');
    if (!cardEl) return;

    // Score & Badges
    const scoreEl = document.getElementById('linkedinScoreBadge');
    const statusEl = document.getElementById('linkedinStatusBadge');
    const summaryEl = document.getElementById('linkedinValidationSummary');

    if (scoreEl) {
      scoreEl.innerText = `${validation.score} / 100`;
      scoreEl.classList.toggle('is-pass', !!validation.is_valid);
      scoreEl.classList.toggle('is-fail', !validation.is_valid);
    }

    if (statusEl) {
      statusEl.innerText = validation.badge_text;
      statusEl.className = validation.is_valid ? 'status-pill status-active' : 'status-pill status-closed';
    }

    if (summaryEl) {
      summaryEl.innerText = validation.is_valid 
        ? 'All quality checks passed. You can pass & publish directly to the live student catalog.'
        : 'Quality checks require attention before publishing (check company, role or apply destination).';
    }

    // Checks List
    const checksList = document.getElementById('linkedinChecksList');
    if (checksList && Array.isArray(validation.checks)) {
      checksList.innerHTML = validation.checks.map(c => `
        <li class="ow-check ${c.passed ? 'is-pass' : 'is-fail'}">
          <span class="ow-check-mark" aria-hidden="true">${c.passed ? '✓' : '✗'}</span>
          <span><strong>${c.rule}</strong>: <span class="ow-check-detail">${c.detail}</span><span class="sr-only"> (${c.passed ? 'passed' : 'failed'})</span></span>
        </li>
      `).join('');
    }

    // Populate Editable Form
    document.getElementById('valCompName').value = parsed.company || '';
    document.getElementById('valTitle').value = parsed.title || '';
    document.getElementById('valLocation').value = parsed.location || 'Bengaluru / Hybrid';
    document.getElementById('valSalary').value = parsed.stipend_salary || 'Competitive';
    document.getElementById('valIsReferral').value = parsed.is_referral ? 'true' : 'false';
    document.getElementById('valApplyUrl').value = parsed.apply_url || '';
    document.getElementById('valSkills').value = parsed.skills_required || '';
    document.getElementById('valReferrerName').value = parsed.referrer_name || '';
    document.getElementById('valReferrerLinkedin').value = parsed.referrer_linkedin || '';
    document.getElementById('valReferralInstructions').value = parsed.referral_instructions || '';
    document.getElementById('valDescription').value = parsed.description || '';

    toggleReferralFields(parsed.is_referral);
    cardEl.style.display = 'block';
    cardEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  window.toggleReferralFields = function(isRef) {
    const grp = document.getElementById('valReferralFieldsGroup');
    if (grp) {
      grp.style.display = isRef ? 'block' : 'none';
    }
  };

  window.handlePublishLinkedInLead = async function() {
    const payload = {
      company: document.getElementById('valCompName').value.trim(),
      title: document.getElementById('valTitle').value.trim(),
      location: document.getElementById('valLocation').value.trim(),
      is_remote: document.getElementById('valLocation').value.toLowerCase().includes('remote'),
      stipend_salary: document.getElementById('valSalary').value.trim(),
      is_referral: document.getElementById('valIsReferral').value === 'true',
      apply_url: document.getElementById('valApplyUrl').value.trim(),
      skills_required: document.getElementById('valSkills').value.trim(),
      referrer_name: document.getElementById('valReferrerName').value.trim(),
      referrer_linkedin: document.getElementById('valReferrerLinkedin').value.trim(),
      referral_instructions: document.getElementById('valReferralInstructions').value.trim(),
      description: document.getElementById('valDescription').value.trim(),
      source_url: document.getElementById('linkedinPostUrl')?.value.trim() || ''
    };

    if (!payload.company || !payload.title) {
      showToast('Company Name and Role Title are required.', 'error');
      return;
    }

    try {
      const res = await authFetch('/api/owner/linkedin/publish/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`Passed and published: ${data.company} - ${data.title}!`, 'success');
        logActivity('LinkedIn Lead Published', `${data.company} - ${data.title}`);

        const successAlert = document.getElementById('linkedinSuccessAlert');
        const successMsg = document.getElementById('linkedinSuccessMsg');
        const successLink = document.getElementById('linkedinSuccessLink');

        if (successMsg) successMsg.innerText = `Successfully published to active catalog as ${data.is_referral ? 'Employee Referral' : 'Job Requirement'}.`;
        if (successLink) successLink.href = data.url;
        if (successAlert) successAlert.style.display = 'block';

        loadKpiStats();
      } else {
        showToast(data.error || 'Failed to publish lead.', 'error');
      }
    } catch (err) {
      showToast('Server error publishing lead: ' + err.message, 'error');
    }
  };

  window.resetLinkedInForm = function() {
    document.getElementById('linkedinPostUrl').value = '';
    document.getElementById('linkedinRawText').value = '';
    document.getElementById('linkedinReferrerName').value = '';
    document.getElementById('linkedinReferrerLinkedin').value = '';
    const cardEl = document.getElementById('linkedinValidationCard');
    if (cardEl) cardEl.style.display = 'none';
    const successAlert = document.getElementById('linkedinSuccessAlert');
    if (successAlert) successAlert.style.display = 'none';
  };

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
      <div class="vp-catalog-grid" aria-busy="true">
        ${[1, 2, 3, 4, 5, 6].map(() => `
          <div class="vp-product-card ow-skel-card" aria-hidden="true">
            <div class="vp-card-header">
              <div class="ow-skel ow-skel-company"></div>
              <div class="ow-skel ow-skel-pill"></div>
            </div>
            <div class="ow-skel ow-skel-title"></div>
            <div class="ow-skel ow-skel-line"></div>
            <div class="ow-skel ow-skel-block"></div>
            <div class="ow-skel-row">
              <div class="ow-skel ow-skel-tag"></div>
              <div class="ow-skel ow-skel-tag"></div>
            </div>
            <div class="ow-act-2">
              <div class="ow-skel ow-skel-btn"></div>
              <div class="ow-skel ow-skel-btn"></div>
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
    const sourceSelect = document.getElementById('crmSourceFilter');
    const recencySelect = document.getElementById('crmRecencyFilter');
    const expSelect = document.getElementById('crmExperienceFilter');
    const sourceVal = sourceSelect ? sourceSelect.value : 'ALL';
    const recencyVal = recencySelect ? recencySelect.value : 'ALL';
    const expVal = expSelect ? expSelect.value : 'ALL';

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
    if (expVal && expVal !== 'ALL') {
      url += `&experience=${encodeURIComponent(expVal)}`;
    }
    if (sourceVal && sourceVal !== 'ALL') {
      url += `&source=${encodeURIComponent(sourceVal)}`;
    }
    if (recencyVal === 'today') {
      url += `&today=true`;
    } else if (recencyVal === 'yesterday') {
      url += `&yesterday=true`;
    } else if (recencyVal === '3d') {
      url += `&time_window=72h`;
    } else if (recencyVal === '7d') {
      url += `&time_window=7d`;
    }

    try {
      const res = await authFetch(url);
      const data = await res.json();
      allLoadedJobs = data.jobs || [];
      renderFilteredJobs(data);
    } catch (err) {
      console.error('Failed to load jobs:', err);
      jobsTableContainer.innerHTML = `
        <div class="ow-state is-bad" role="alert">
          <strong class="ow-state-title">Failed to load opportunity pipeline</strong>
          <p class="ow-state-text">There was an issue communicating with the backend server.</p>
          <button type="button" class="btn btn-danger-ghost" onclick="loadJobsList(${page})">
            Try again
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
        <div class="ow-state">
          <strong class="ow-state-title">No opportunity leads found</strong>
          <p class="ow-state-text">Try clearing your search filters or post a new job requirement.</p>
          <button type="button" class="btn btn-primary" onclick="switchTab('tabPost')">
            + Post new job
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
        return `<span class="ow-pag-gap" aria-hidden="true">…</span>`;
      }
      return `
        <button class="pag-page-btn btn-page-number ${p === curPage ? 'active' : ''}" data-page="${p}"${p === curPage ? ' aria-current="page"' : ''}>
          ${p}
        </button>
      `;
    }).join('');

    jobsTableContainer.innerHTML = `
      <div class="vp-catalog-grid">
        ${filtered.map(j => {
          const isExpired = j.time_left_seconds <= 0 || j.status === 'EXPIRED';
          const hoursLeft = Math.ceil(j.time_left_seconds / 3600);
          const skillsList = Array.isArray(j.skills_list) && j.skills_list.length > 0 
            ? j.skills_list 
            : (j.skills_required ? j.skills_required.split(',').map(s => s.trim()).filter(Boolean) : []);
          const isFresher = (j.experience_tier === 'FRESHER' || j.experience_tier === 'INTERNSHIP' || j.job_type === 'INTERNSHIP' || (j.title && /fresher|intern|trainee|0-1/i.test(j.title))) && j.experience_tier !== 'SENIOR_LEVEL' && j.experience_tier !== 'MID_LEVEL';
          const expBadge = isFresher 
            ? `<span class="status-pill is-fresher">Fresher (0-1 Y)</span>`
            : `<span class="status-pill is-experienced">Experienced</span>`;

          return `
          <div class="vp-product-card" data-id="${j.id}">
            <div class="vp-card-header">
              <span class="company-badge">${escapeHtml(j.company_name)}</span>
              <div class="ow-card-tags">
                ${expBadge}
                <span class="type-badge">${escapeHtml(j.job_type_display || j.job_type || 'Full-Time')}</span>
                <span class="status-pill ${isExpired ? 'status-expired' : 'status-active'}">
                  ${isExpired ? 'Expired' : hoursLeft + 'h left'}
                </span>
              </div>
            </div>

            <div class="vp-card-content">
              <h2 class="job-card-title">${escapeHtml(j.title)}</h2>

              <div class="vp-salary-row">
                <span>${escapeHtml(j.stipend_salary || 'Competitive')}</span>
                <span class="ow-loc">${escapeHtml(j.location || 'India')}</span>
              </div>

              <div class="ow-card-meta">
                <span>Posted <strong>${escapeHtml(j.posted_date_display || j.posted_date || 'Today')}</strong></span>
                <span class="ow-id">#${j.id}</span>
              </div>

              <p class="ow-card-desc">${escapeHtml(j.description ? (j.description.length > 130 ? j.description.substring(0, 130) + '...' : j.description) : 'Verified student opening.')}</p>

              <div class="skills-wrapper">
                ${skillsList.slice(0, 4).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
              </div>

              <div class="vp-price-row">
                <div class="timer-tag${isExpired ? ' is-closed' : ''}">
                  ${isExpired ? 'Expired / Inactive' : 'Auto-expires in 7 days (' + hoursLeft + 'h left)'}
                </div>
              </div>

              <div class="card-action-bar">
                <div class="ow-act-2">
                  <button type="button" class="btn btn-secondary btn-edit-job" data-id="${j.id}">
                    Edit
                  </button>
                  <a href="${escapeHtml(j.apply_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary">
                    Apply URL ↗
                  </a>
                </div>
                <div class="ow-act-3">
                  <button type="button" class="btn btn-secondary btn-pipeline-move-job" data-id="${j.id}" data-title="${escapeHtml(j.title)}" title="Move or assign this requirement to a specific group">
                    Move
                  </button>
                  <button type="button" class="btn btn-ghost btn-toggle-job${isExpired ? ' is-publish' : ''}" data-id="${j.id}">
                    ${isExpired ? 'Publish' : 'Unpublish'}
                  </button>
                  <button type="button" class="btn btn-danger-ghost btn-delete-job" data-id="${j.id}" title="Delete lead">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        `}).join('')}
      </div>

      <div class="ow-pager">
        <p class="ow-pager-info">
          Showing <strong>${startNum}-${endNum}</strong> of <strong>${totalCount}</strong> (page ${curPage} of ${totalPages})
        </p>
        <div class="ow-pager-nav">
          <button id="btnPrevPage" class="pag-btn" ${curPage <= 1 ? 'disabled' : ''}>
            Previous
          </button>
          ${pagesHtml}
          <button id="btnNextPage" class="pag-btn" ${curPage >= totalPages ? 'disabled' : ''}>
            Next
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
        <div class="ow-cat-item">
          <div class="ow-cat-name">
            <strong>${escapeHtml(c.name)}</strong>
            <span class="ow-mono">/${escapeHtml(c.slug)}</span>
          </div>
          <span class="ow-count-pill">
            ${c.active_count} active
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

  async function loadGroupsList(page = 1) {
    const container = document.getElementById('ownerGroupsTableContainer');
    if (!container) return;

    currentGroupsPage = page;
    container.innerHTML = '<p class="ow-empty" role="status"><span class="ow-spinner ow-spinner-sm" aria-hidden="true"></span>Loading requirement groups...</p>';

    const searchInput = document.getElementById('ownerGroupsSearch');
    const filterSelect = document.getElementById('ownerGroupsFilter');
    const pageSizeSelect = document.getElementById('ownerGroupsPageSize');

    const q = searchInput ? searchInput.value.trim() : '';
    const filterVal = filterSelect ? filterSelect.value : 'all';
    const pageSizeVal = pageSizeSelect ? pageSizeSelect.value : '15';

    let url = `/api/owner/groups/?page=${page}&page_size=${encodeURIComponent(pageSizeVal)}`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (filterVal && filterVal !== 'all') url += `&filter=${encodeURIComponent(filterVal)}`;

    try {
      const res = await authFetch(url);
      const data = await res.json();
      const groups = data.groups || [];
      const totalCount = data.total_count !== undefined ? data.total_count : groups.length;
      const totalPages = data.total_pages !== undefined ? data.total_pages : 1;
      const curPage = data.current_page !== undefined ? data.current_page : page;
      const pageSize = data.page_size !== undefined ? data.page_size : 15;
      currentGroupsPage = curPage;
      allGroupsData = groups;

      if (groups.length === 0) {
        container.innerHTML = `
          <div class="ow-state">
            <h3 class="ow-state-title">
              ${q || filterVal !== 'all' ? 'No Matching Groups Found' : 'No Requirement Groups Yet'}
            </h3>
            <p class="ow-state-text">
              ${q || filterVal !== 'all' ? 'Try adjusting your search keywords or filter selection.' : 'Whenever you use the Bulk Parser or Create Group, a bundle is automatically created with direct shareable links!'}
            </p>
            ${q || filterVal !== 'all' ? `
              <button class="btn btn-secondary" onclick="if(document.getElementById('ownerGroupsSearch')) document.getElementById('ownerGroupsSearch').value=''; if(document.getElementById('ownerGroupsFilter')) document.getElementById('ownerGroupsFilter').value='all'; loadGroupsList(1);">
                Reset Filters
              </button>
            ` : `
              <button class="btn btn-primary" onclick="document.querySelector('[data-tab=tabBulkParse]').click()">
                Open bulk parser
              </button>
            `}
          </div>
        `;
        return;
      }

      let html = `
        <table class="data-table ow-groups-table">
          <thead>
            <tr>
              <th scope="col" class="ow-col-name">Group / Drive Name</th>
              <th scope="col">Active Jobs</th>
              <th scope="col">Created Date (IST)</th>
              <th scope="col">Views</th>
              <th scope="col" class="ow-col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
      `;

      groups.forEach(g => {
        const jobsCount = g.jobs ? g.jobs.length : (g.total_jobs_count || 0);
        const tierBadge = g.tier_type === 'FRESHER' 
          ? '<span class="status-pill is-fresher">Fresher</span>'
          : (g.tier_type === 'EXPERIENCED' 
              ? '<span class="status-pill is-experienced">Experienced</span>'
              : '');
        html += `
          <tr data-group-id="${g.id}">
            <td>
              <div class="ow-group-name">
                <span>${escapeHtml(g.name)}</span>
                ${tierBadge}
              </div>
              <div class="ow-group-slug">/group/${escapeHtml(g.slug)}/</div>
            </td>
            <td>
              <button type="button" class="btn-toggle-group-jobs btn btn-ghost ow-btn-sm" data-group-id="${g.id}" title="Click to view & move requirements">
                ${g.active_jobs_count} Jobs ▾
              </button>
            </td>
            <td class="ow-td-muted">${escapeHtml(g.created_at)}</td>
            <td class="ow-td-num">${g.views_count}</td>
            <td class="ow-col-actions">
              <div class="ow-row-actions">
                <button type="button" class="btn-toggle-group-jobs btn btn-secondary ow-btn-sm" data-group-id="${g.id}">
                  Move jobs
                </button>
                <a href="${escapeHtml(g.url)}" target="_blank" class="btn btn-secondary ow-btn-sm" title="Open live public group page">
                  Open ↗
                </a>
                <button type="button" class="btn btn-secondary btn-group-broadcast ow-btn-sm" data-id="${g.id}" title="Get WhatsApp / Telegram broadcast message">
                  Broadcast
                </button>
                <button type="button" class="btn btn-danger-ghost btn-group-delete ow-btn-sm" data-id="${g.id}" data-name="${escapeHtml(g.name)}" title="Delete group bundle" aria-label="Delete group">
                  Delete
                </button>
              </div>
            </td>
          </tr>
          <!-- Expandable Group Requirements Drawer Row -->
          <tr id="group-jobs-drawer-${g.id}" class="group-jobs-drawer-row" style="display: none;">
            <td colspan="5">
              <div class="ow-drawer">
                <div class="ow-drawer-head">
                  <label class="ow-check-label">
                    <input type="checkbox" class="select-all-group-jobs" data-group-id="${g.id}">
                    <span>Select all (${jobsCount})</span>
                  </label>
                  <button type="button" class="btn-bulk-move-jobs btn btn-primary ow-btn-sm" data-group-id="${g.id}" data-group-name="${escapeHtml(g.name)}" style="display: none;">
                    Move selected (<span class="selected-count">0</span>)
                  </button>
                </div>

                <div class="group-jobs-list" data-group-id="${g.id}">
                  ${(!g.jobs || g.jobs.length === 0) ? `
                    <div class="ow-empty">
                      No requirements currently in this group. Use the Bulk Parser or Move tools to assign jobs here.
                    </div>
                  ` : g.jobs.map(j => `
                    <div class="group-job-item">
                      <div class="ow-job-item-main">
                        <input type="checkbox" class="group-job-checkbox" data-group-id="${g.id}" data-job-id="${j.id}" data-job-title="${escapeHtml(j.title)}" aria-label="Select ${escapeHtml(j.title)}">
                        <div class="ow-job-item-text">
                          <div class="ow-job-item-title">
                            ${escapeHtml(j.title)} <span>at ${escapeHtml(j.company_name)}</span>
                          </div>
                          <div class="ow-job-item-meta">
                            ${escapeHtml(j.location || 'India')} · ${escapeHtml(j.stipend_salary || 'Competitive')} · ${escapeHtml(j.posted_date || '')}
                          </div>
                        </div>
                      </div>
                      <div class="ow-row-actions">
                        <button type="button" class="btn-move-single-job btn btn-secondary ow-btn-sm" data-job-id="${j.id}" data-job-title="${escapeHtml(j.title)}" data-from-group-id="${g.id}" data-from-group-name="${escapeHtml(g.name)}">
                          Move
                        </button>
                        <button type="button" class="btn-remove-single-job btn btn-danger-ghost ow-btn-sm" data-job-id="${j.id}" data-job-title="${escapeHtml(j.title)}" data-group-id="${g.id}" data-group-name="${escapeHtml(g.name)}" title="Remove from this group only">
                          Remove
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

      if (pageSizeVal !== 'all' && (totalPages > 1 || totalCount > 0)) {
        const startNum = totalCount === 0 ? 0 : (curPage - 1) * pageSize + 1;
        const endNum = Math.min(totalCount, curPage * pageSize);

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
            return `<span class="ow-pag-gap" aria-hidden="true">…</span>`;
          }
          return `
            <button type="button" class="groups-page-btn btn-page-number ${p === curPage ? 'active' : ''}" data-page="${p}"${p === curPage ? ' aria-current="page"' : ''}>
              ${p}
            </button>
          `;
        }).join('');

        html += `
          <div class="ow-pager ow-pager-sticky">
            <p class="ow-pager-info">
              Showing <strong>${startNum}-${endNum}</strong> of <strong>${totalCount}</strong> groups (page ${curPage} of ${totalPages})
            </p>
            <div class="ow-pager-nav">
              <button type="button" id="btnPrevGroupsPage" class="pag-btn" ${curPage <= 1 ? 'disabled' : ''}>
                Previous
              </button>
              ${pagesHtml}
              <button type="button" id="btnNextGroupsPage" class="pag-btn" ${curPage >= totalPages ? 'disabled' : ''}>
                Next
              </button>
            </div>
          </div>
        `;
      }

      container.innerHTML = html;

      // 0. Bind Pagination Controls
      const btnPrevGroups = container.querySelector('#btnPrevGroupsPage');
      const btnNextGroups = container.querySelector('#btnNextGroupsPage');
      if (btnPrevGroups) {
        btnPrevGroups.addEventListener('click', (e) => {
          e.preventDefault();
          if (curPage > 1) {
            loadGroupsList(curPage - 1);
          }
        });
      }
      if (btnNextGroups) {
        btnNextGroups.addEventListener('click', (e) => {
          e.preventDefault();
          if (curPage < totalPages) {
            loadGroupsList(curPage + 1);
          }
        });
      }
      container.querySelectorAll('.groups-page-btn').forEach(pBtn => {
        pBtn.addEventListener('click', (e) => {
          e.preventDefault();
          const targetPage = parseInt(pBtn.dataset.page, 10);
          if (!isNaN(targetPage) && targetPage !== curPage) {
            loadGroupsList(targetPage);
          }
        });
      });

      // 1. Toggle Drawer Handlers
      container.querySelectorAll('.btn-toggle-group-jobs').forEach(btn => {
        btn.addEventListener('click', () => {
          const groupId = btn.dataset.groupId;
          const drawer = document.getElementById(`group-jobs-drawer-${groupId}`);
          if (drawer) {
            const isHidden = drawer.style.display === 'none';
            drawer.style.display = isHidden ? 'table-row' : 'none';
            btn.textContent = isHidden ? `Hide jobs ▴` : `Jobs ▾`;
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
                loadGroupsList(currentGroupsPage || 1);
              } else {
                showToast(data.error || 'Failed to remove job from group.', 'error');
              }
            } catch (err) {
              showToast('Network error removing job from group.', 'error');
            }
          }
        });
      });

      // 4. Checkbox Selection & Global Multi-Group Bulk Move
      function updateBulkMoveStates() {
        const allChecked = Array.from(container.querySelectorAll('.group-job-checkbox:checked'));
        const totalChecked = allChecked.length;

        // A. Update individual group drawer move buttons
        const groupMap = {};
        allChecked.forEach(chk => {
          const gid = chk.dataset.groupId;
          groupMap[gid] = (groupMap[gid] || 0) + 1;
        });

        container.querySelectorAll('.btn-bulk-move-jobs').forEach(bulkBtn => {
          const gid = bulkBtn.dataset.groupId;
          const count = groupMap[gid] || 0;
          if (count > 0) {
            bulkBtn.style.display = 'inline-flex';
            const countEl = bulkBtn.querySelector('.selected-count');
            if (countEl) countEl.textContent = count;
          } else {
            bulkBtn.style.display = 'none';
          }
        });

        // B. Update global multi-group bulk bar
        const globalBar = document.getElementById('groupsGlobalBulkBar');
        const globalText = document.getElementById('groupsGlobalBulkText');
        const globalMoveBtn = document.getElementById('btnGroupsBulkMoveAll');

        if (globalBar && globalText) {
          if (totalChecked > 0) {
            const distinctGroupIds = Object.keys(groupMap);
            const groupCount = distinctGroupIds.length;
            const groupWord = groupCount === 1 ? '1 group' : `${groupCount} different groups`;
            globalText.textContent = `${totalChecked} requirement${totalChecked !== 1 ? 's' : ''} selected across ${groupWord}`;
            if (globalMoveBtn) {
              globalMoveBtn.textContent = `Move selected (${totalChecked}) to group`;
            }
            globalBar.style.display = 'flex';
          } else {
            globalBar.style.display = 'none';
          }
        }
      }

      container.querySelectorAll('.select-all-group-jobs').forEach(chkAll => {
        chkAll.addEventListener('change', () => {
          const groupId = chkAll.dataset.groupId;
          const checkboxes = container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]`);
          checkboxes.forEach(c => { c.checked = chkAll.checked; });
          updateBulkMoveStates();
        });
      });

      container.querySelectorAll('.group-job-checkbox').forEach(chk => {
        chk.addEventListener('change', () => {
          const groupId = chk.dataset.groupId;
          const allInGroup = container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]`);
          const checkedInGroup = container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]:checked`);
          const parentSelectAll = container.querySelector(`.select-all-group-jobs[data-group-id="${groupId}"]`);
          if (parentSelectAll) {
            parentSelectAll.checked = (allInGroup.length > 0 && allInGroup.length === checkedInGroup.length);
          }
          updateBulkMoveStates();
        });
      });

      // 5. Individual Group Drawer Bulk Move Button Click
      container.querySelectorAll('.btn-bulk-move-jobs').forEach(btn => {
        btn.addEventListener('click', () => {
          const groupId = parseInt(btn.dataset.groupId, 10);
          const groupName = btn.dataset.groupName;
          const checked = Array.from(container.querySelectorAll(`.group-job-checkbox[data-group-id="${groupId}"]:checked`));
          
          if (checked.length === 0) return;

          const jobIds = checked.map(c => parseInt(c.dataset.jobId, 10)).filter(n => !isNaN(n));
          const jobTitles = checked.map(c => c.dataset.jobTitle);

          openMoveRequirementsModal({
            jobIds: jobIds,
            jobTitles: jobTitles,
            fromGroupId: groupId,
            fromGroupName: groupName,
            fromGroupIds: [groupId],
            fromGroupNames: [groupName]
          });
        });
      });

      // 5B. Global Cross-Group Bulk Move & Clear Handlers
      const btnGroupsBulkMoveAll = document.getElementById('btnGroupsBulkMoveAll');
      if (btnGroupsBulkMoveAll) {
        btnGroupsBulkMoveAll.onclick = () => {
          const allChecked = Array.from(container.querySelectorAll('.group-job-checkbox:checked'));
          if (allChecked.length === 0) {
            showToast('Please select at least one requirement to move.', 'info');
            return;
          }

          const jobIds = allChecked.map(c => parseInt(c.dataset.jobId, 10)).filter(n => !isNaN(n));
          const jobTitles = allChecked.map(c => c.dataset.jobTitle || '');
          const fromGroupIds = Array.from(new Set(allChecked.map(c => parseInt(c.dataset.groupId, 10)).filter(n => !isNaN(n))));
          
          // Find group names for selected group IDs
          const fromGroupNames = [];
          fromGroupIds.forEach(gid => {
            const gObj = (allGroupsData || []).find(g => g.id === gid);
            if (gObj) fromGroupNames.push(gObj.name);
          });

          openMoveRequirementsModal({
            jobIds: jobIds,
            jobTitles: jobTitles,
            fromGroupId: fromGroupIds.length === 1 ? fromGroupIds[0] : null,
            fromGroupName: fromGroupNames.length === 1 ? fromGroupNames[0] : '',
            fromGroupIds: fromGroupIds,
            fromGroupNames: fromGroupNames
          });
        };
      }

      const btnGroupsClearSelection = document.getElementById('btnGroupsClearSelection');
      if (btnGroupsClearSelection) {
        btnGroupsClearSelection.onclick = () => {
          container.querySelectorAll('.group-job-checkbox, .select-all-group-jobs').forEach(c => { c.checked = false; });
          updateBulkMoveStates();
        };
      }

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
                loadGroupsList(currentGroupsPage || 1);
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
      container.innerHTML = '<p class="ow-empty is-bad" role="alert">Failed to load requirement groups.</p>';
    }
  }

  // --- MOVE REQUIREMENTS MODAL WORKFLOW ---

  async function openMoveRequirementsModal({ jobIds, jobTitles, fromGroupId, fromGroupName, fromGroupIds, fromGroupNames }) {
    const modal = document.getElementById('moveRequirementsModal');
    if (!modal) return;

    // Store global source group IDs for payload submission
    window._currentMoveFromGroupIds = fromGroupIds || (fromGroupId ? [fromGroupId] : []);

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
    if (fromGroupIdInput) fromGroupIdInput.value = fromGroupId || (fromGroupIds && fromGroupIds.length === 1 ? fromGroupIds[0] : '');

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
      if (fromGroupNames && fromGroupNames.length > 1) {
        sourceGroupText.textContent = `From ${fromGroupNames.length} groups: ${fromGroupNames.join(', ')}`;
      } else if (fromGroupName) {
        sourceGroupText.textContent = `From Source Group: ${fromGroupName}`;
      } else {
        sourceGroupText.textContent = 'From: Pipeline / Current Groups';
      }
    }

    if (filterInput) filterInput.value = '';
    if (newGroupNameInput) newGroupNameInput.value = '';
    if (newGroupTagInput) newGroupTagInput.value = '';
    if (newGroupDrawer) newGroupDrawer.style.display = 'none';

    function renderTargetGroupOptions(filterText = '') {
      if (!targetSelect) return;
      const lowerFilter = filterText.toLowerCase().trim();
      const filteredGroups = (allGroupsData || []).filter(g => {
        if (!lowerFilter) return true;
        return g.name.toLowerCase().includes(lowerFilter) || (g.slug && g.slug.toLowerCase().includes(lowerFilter));
      });

      let optionsHtml = '<option value="">-- Choose Target Specific Group --</option>';
      optionsHtml += '<option value="NEW" class="ow-opt-new">+ Create new group and move...</option>';

      if (filteredGroups.length > 0) {
        filteredGroups.forEach(g => {
          optionsHtml += `<option value="${g.id}">${escapeHtml(g.name)} (${g.active_jobs_count || 0} active)</option>`;
        });
      } else if (allGroupsData && allGroupsData.length === 0) {
        optionsHtml = '<option value="NEW" selected class="ow-opt-new">+ Create new group and move...</option>';
        if (newGroupDrawer) newGroupDrawer.style.display = 'block';
      }

      targetSelect.innerHTML = optionsHtml;
    }

    // Render immediately if we already have group data in memory
    if (allGroupsData && allGroupsData.length > 0) {
      renderTargetGroupOptions('');
    } else if (targetSelect) {
      targetSelect.innerHTML = '<option value="">Loading existing groups...</option><option value="NEW" class="ow-opt-new">+ Create new group and move...</option>';
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

  // Quick Action Button for Link Health Verification
  const btnVerifyJobLinks = document.getElementById('btnVerifyJobLinks');
  if (btnVerifyJobLinks) {
    btnVerifyJobLinks.addEventListener('click', async () => {
      if (!confirm('Scan active requirements and automatically soft-expire dead, 404, closed, or redirected links?')) return;
      btnVerifyJobLinks.disabled = true;
      btnVerifyJobLinks.textContent = 'Verifying links...';
      try {
        const res = await authFetch('/api/owner/verify-links/?limit=40');
        const data = await res.json();
        if (data.success && data.result) {
          alert(`Link Health Verification Complete!\n\n• Checked: ${data.result.checked}\n• Active & Verified: ${data.result.active}\n• Expired/Closed: ${data.result.expired}`);
          window.location.reload();
        } else {
          alert('Verification failed: ' + (data.error || 'Server error'));
        }
      } catch (err) {
        alert('Verification error: ' + err.message);
      } finally {
        btnVerifyJobLinks.disabled = false;
        btnVerifyJobLinks.textContent = 'Verify links';
      }
    });
  }

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
          from_group_ids: window._currentMoveFromGroupIds || [],
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
          loadGroupsList(currentGroupsPage || 1);
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
          btnCopyLink.textContent = 'Copied';
          showToast('Direct group URL copied to clipboard!', 'success');
          setTimeout(() => { btnCopyLink.textContent = 'Copy link'; }, 2000);
        });
      };
    }

    // Setup Copy WhatsApp Broadcast
    const btnCopyWhatsApp = document.getElementById('btnCopyModalWhatsApp');
    if (btnCopyWhatsApp) {
      btnCopyWhatsApp.onclick = () => {
        const text = data.whatsapp_broadcast || '';
        navigator.clipboard.writeText(text).then(() => {
          btnCopyWhatsApp.textContent = 'WhatsApp text copied';
          showToast('WhatsApp Broadcast message copied to clipboard!', 'success');
          setTimeout(() => { btnCopyWhatsApp.textContent = 'Copy WhatsApp Broadcast'; }, 2500);
        });
      };
    }

    // Setup Copy Telegram Broadcast
    const btnCopyTelegram = document.getElementById('btnCopyModalTelegram');
    if (btnCopyTelegram) {
      btnCopyTelegram.onclick = () => {
        const text = data.telegram_broadcast || data.whatsapp_broadcast || '';
        navigator.clipboard.writeText(text).then(() => {
          btnCopyTelegram.textContent = 'Telegram post copied';
          showToast('Telegram Post format copied to clipboard!', 'success');
          setTimeout(() => { btnCopyTelegram.textContent = 'Copy Telegram Post'; }, 2500);
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
  async function loadAnalyticsData(forceRefresh = false) {
    try {
      const url = forceRefresh ? '/api/owner/analytics/?refresh=1' : '/api/owner/analytics/';
      const res = await authFetch(url, {
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
            <div class="ow-bar-col" title="${d.full_date}: ${d.views} views, ${d.unique_visitors} unique visitors">
              <span class="ow-bar-num">${d.views > 0 ? d.views : ''}</span>
              <div class="ow-bar" style="height: ${heightPct}%;"></div>
              <span class="ow-bar-date">${d.date}</span>
            </div>
          `;
        }).join('');
      }

      // 3. Top Visited Pages
      const topPagesContainer = document.getElementById('anaTopPagesList');
      if (topPagesContainer) {
        if (!data.top_pages || data.top_pages.length === 0) {
          topPagesContainer.innerHTML = '<p class="ow-hint">No page views recorded yet.</p>';
        } else {
          topPagesContainer.innerHTML = data.top_pages.map((p, idx) => `
            <div class="ana-page-row">
              <div class="ow-grow">
                <a href="${escapeHtml(p.path)}" target="_blank" rel="noopener noreferrer" class="ana-page-link" title="Open ${escapeHtml(p.path)} in new tab">
                  <div class="ana-page-title">
                    <span class="ow-rank">#${idx + 1}</span>
                    <span>${escapeHtml(p.page_title || p.path)}</span>
                  </div>
                  <div class="ana-page-path">
                    ${escapeHtml(p.path)} <span aria-hidden="true">↗</span>
                  </div>
                </a>
              </div>
              <div class="ow-page-stats">
                <div class="ow-page-views">${Number(p.views || 0).toLocaleString()} views</div>
                <div class="ow-hint">${Number(p.unique_visitors || 0).toLocaleString()} unique</div>
              </div>
            </div>
          `).join('');
        }
      }

      // 4. Traffic Channels & Referrers
      const referrersContainer = document.getElementById('anaReferrersList');
      if (referrersContainer) {
        if (!data.referrers || data.referrers.length === 0) {
          referrersContainer.innerHTML = '<p class="ow-hint">No referrer data yet.</p>';
        } else {
          referrersContainer.innerHTML = data.referrers.map(r => `
            <div class="ow-ref">
              <div class="ow-ref-head">
                <span>${escapeHtml(r.source)}</span>
                <span class="ow-ref-count">${r.count} hits (${r.percentage}%)</span>
              </div>
              <div class="ow-meter">
                <div class="ow-meter-fill" style="width: ${r.percentage}%;"></div>
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
            <span>${escapeHtml(o.os)}</span>
            <strong>${o.count}</strong>
          </div>
        `);
        const browserItems = (data.browsers || []).map(b => `
          <div class="platform-card-item">
            <span>${escapeHtml(b.browser)}</span>
            <strong>${b.count}</strong>
          </div>
        `);
        platformsContainer.innerHTML = [...osItems, ...browserItems].join('') || '<p class="ow-hint">No platform data yet</p>';
      }

      // 6. Recent Real-Time Visitors Table
      const visitsBody = document.getElementById('anaRecentVisitsBody');
      if (visitsBody) {
        if (!data.recent_visits || data.recent_visits.length === 0) {
          visitsBody.innerHTML = '<tr><td colspan="5" class="ow-td-empty">No recent live visits yet.</td></tr>';
        } else {
          visitsBody.innerHTML = data.recent_visits.map(v => `
            <tr>
              <td class="ow-td-time">
                <strong>${escapeHtml(v.time)}</strong><br>
                <small>${escapeHtml(v.date)}</small>
              </td>
              <td>
                <div class="ow-td-title">${escapeHtml(v.page_title || v.path)}</div>
                <div class="ow-mono ow-td-muted">${escapeHtml(v.path)}</div>
              </td>
              <td>
                <span class="ow-source">
                  ${escapeHtml(v.referrer || 'Direct')}
                </span>
              </td>
              <td class="ow-td-small">
                ${v.device === 'Mobile' ? 'Mobile' : (v.device === 'Tablet' ? 'Tablet' : 'Desktop')} · ${escapeHtml(v.os || '')} (${escapeHtml(v.browser || '')})
              </td>
              <td class="ow-mono ow-td-muted">
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
        <strong>${escapeHtml(action)}</strong>
        <div>${escapeHtml(details)} · ${timeStr}</div>
      </div>
    `;
    activityStream.prepend(item);
  }

  // --- HELPER UTILITIES ---

  function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ow-toast ${type === 'success' ? 'is-ok' : 'is-bad'}`;
    toast.innerHTML = `
      <span class="ow-toast-mark" aria-hidden="true"></span>
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

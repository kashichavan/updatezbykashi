// Kashii Updatez - Global Engine with Category Navigation & Paginated Job Feed
document.addEventListener('DOMContentLoaded', () => {
  const isHomePage = window.location.pathname === '/' || window.location.pathname === '';
  const isCategoryPage = window.location.pathname.startsWith('/category/');

  let currentCategory = 'all';
  if (isCategoryPage) {
    const match = window.location.pathname.match(/\/category\/([^\/]+)/);
    if (match && match[1]) currentCategory = match[1];
  } else if (window.CATEGORY_SLUG_OVERRIDE) {
    currentCategory = window.CATEGORY_SLUG_OVERRIDE;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const isTodayOnly = urlParams.get('today') === 'true' || urlParams.get('today') === '1';
  const isYesterdayOnly = urlParams.get('yesterday') === 'true' || urlParams.get('yesterday') === '1';
  const isPreviousOnly = urlParams.get('previous') === 'true' || urlParams.get('previous') === '1';

  const state = {
    searchQuery: '',
    category: currentCategory,
    jobType: 'all',
    sort: 'newest',
    isTodayOnly: isTodayOnly,
    isYesterdayOnly: isYesterdayOnly,
    isPreviousOnly: isPreviousOnly,
    page: 1,
    pageSize: 9, // 9 opportunities per page (3x3 grid layout)
    totalPages: 1,
    totalCount: 0,
    jobs: [],
    categories: [],
    activeJobId: null,
    timerInterval: null,
  };

  // DOM Elements
  const categorySelect = document.getElementById('filterCategory');
  const jobTypeSelect = document.getElementById('filterJobType');
  const sortSelect = document.getElementById('filterSort');
  const searchInput = document.getElementById('searchInput');
  const jobsGrid = document.getElementById('jobsGrid');
  const paginationContainer = document.getElementById('paginationContainer');

  // Side Drawer Elements
  const drawerOverlay = document.getElementById('drawerOverlay');
  const btnToggleDrawer = document.getElementById('btnToggleDrawer');
  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  const drawerCategoryNav = document.getElementById('drawerCategoryNav');

  // Flash Banner
  const flashBanner = document.getElementById('flashBanner');
  const flashClose = document.getElementById('flashClose');

  // Detail Modal
  const detailModal = document.getElementById('detailModal');
  const btnCloseDetail = document.getElementById('btnCloseDetail');

  init();

  function init() {
    setupGlobalDrawer();
    loadCategories();

    if (isHomePage || isCategoryPage) {
      if (isHomePage) startTypewriter();
      bindCardClicks();
      loadJobs();
      setupHomePageListeners();
      startCountdownTimer();
    }
  }

  // --- CONSOLAS TYPEWRITER TYPING ANIMATION ENGINE ---

  function startTypewriter() {
    const el = document.getElementById('typewriterText');
    if (!el) return;

    const part1 = "Daily Student Jobs & ";
    const part2 = "Internship Requirements";

    let i = 0;
    el.innerHTML = "";

    function typePart1() {
      if (i < part1.length) {
        el.innerHTML += part1.charAt(i);
        i++;
        setTimeout(typePart1, 40);
      } else {
        const em = document.createElement('em');
        em.style.fontStyle = 'italic';
        em.style.color = 'var(--blue-primary)';
        el.appendChild(em);

        let j = 0;
        function typePart2() {
          if (j < part2.length) {
            em.textContent += part2.charAt(j);
            j++;
            setTimeout(typePart2, 45);
          }
        }
        typePart2();
      }
    }

    typePart1();
  }

  window.startTypewriter = startTypewriter;

  // --- GLOBAL SIDE DRAWER SETUP ---

  function setupGlobalDrawer() {
    if (btnToggleDrawer && drawerOverlay) {
      btnToggleDrawer.addEventListener('click', (e) => {
        e.preventDefault();
        drawerOverlay.classList.add('is-open');
      });
    }

    if (btnCloseDrawer && drawerOverlay) {
      btnCloseDrawer.addEventListener('click', (e) => {
        e.preventDefault();
        drawerOverlay.classList.remove('is-open');
      });
    }

    if (drawerOverlay) {
      drawerOverlay.addEventListener('click', (e) => {
        if (e.target === drawerOverlay) {
          drawerOverlay.classList.remove('is-open');
        }
      });
    }

    if (flashClose && flashBanner) {
      flashClose.addEventListener('click', () => {
        flashBanner.style.display = 'none';
      });
    }
  }

  async function loadCategories() {
    try {
      const res = await fetch('/api/categories/');
      const data = await res.json();
      state.categories = data.categories || [];

      if (categorySelect) {
        categorySelect.innerHTML = data.categories.map(c => 
          `<option value="${c.slug}" selected>${c.name} (${c.active_count})</option>`
        ).join('');
      }

      if (drawerCategoryNav) {
        const catIcons = {
          'software-engineering': '💻',
          'non-it': '📞',
        };
        drawerCategoryNav.innerHTML = data.categories.map(c => {
          const icon = catIcons[c.slug] || (c.slug.includes('non') ? '📞' : '💻');
          return `
            <a href="/category/${c.slug}/" class="drawer-link" data-slug="${c.slug}">
              <span>${icon} ${escapeHtml(c.name)}</span>
              <span class="d-tag">${c.active_count} OPEN</span>
            </a>
          `;
        }).join('');
      }

    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  // --- PAGINATED JOBS ENGINE (NEWEST FIRST) ---

  async function loadJobs() {
    if (!jobsGrid) return;

    try {
      jobsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem;">
          <div style="font-size: 14px; font-weight: 700; color: var(--blue-primary);">Syncing latest student requirements...</div>
        </div>`;

      const params = new URLSearchParams({
        q: state.searchQuery,
        category: state.category || 'all',
        job_type: state.jobType,
        today: state.isTodayOnly ? 'true' : '',
        yesterday: state.isYesterdayOnly ? 'true' : '',
        previous: state.isPreviousOnly ? 'true' : '',
        sort: state.sort,
        page: state.page,
        page_size: state.pageSize,
      });

      const res = await fetch(`/api/jobs/?${params.toString()}`);
      const data = await res.json();

      state.jobs = data.jobs || [];
      state.totalCount = data.total_count || 0;
      state.totalPages = data.total_pages || 1;
      state.page = data.current_page || 1;

      renderJobs(state.jobs);
      renderPagination();

    } catch (err) {
      console.error('Failed to load jobs:', err);
      jobsGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: #ef4444; font-weight: 700;">Error loading opportunities feed.</div>`;
    }
  }

  async function loadJobDetail(id) {
    try {
      const res = await fetch(`/api/jobs/${id}/`);
      const data = await res.json();
      renderDetailModal(data.job);
    } catch (err) {
      console.error('Failed to load job detail:', err);
      showToast('Error loading job detail.', 'error');
    }
  }

  function bindCardClicks() {
    document.querySelectorAll('.vp-product-card').forEach(card => {
      if (card._hasClickBound) return;
      card._hasClickBound = true;
      card.style.cursor = 'pointer';
      card.addEventListener('click', (e) => {
        // Don't intercept direct external apply clicks
        if (e.target.closest('.external-apply-btn')) return;
        const shareUrl = card.dataset.shareUrl;
        if (shareUrl) {
          window.location.href = shareUrl;
        }
      });
    });
  }

  function renderJobs(jobs) {
    if (!jobsGrid) return;

    if (!jobs || jobs.length === 0) {
      jobsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; background: #ffffff; border-radius: 16px; border: 1px solid var(--subtle-border);">
          <h3 style="font-family: var(--font-serif); font-size: 20px; margin-bottom: 6px;">No active opportunities</h3>
          <p style="color: var(--muted); font-size: 14px;">Postings older than 7 days automatically deactivate.</p>
        </div>`;
      return;
    }

    jobsGrid.innerHTML = jobs.map(j => {
      const formattedTime = formatTimeLeft(j.time_left_seconds);
      const skillsHtml = (j.skills_list || []).slice(0, 3).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
      const isDeactivated = j.status === 'EXPIRED' || j.time_left_seconds <= 0;
      const postedDate = j.posted_date_display || 'Today';
      const isNewToday = postedDate === 'Today';

      const isNonIT = j.category_slug === 'non-it' || (j.category_slug || '').includes('non');
      const catStyle = isNonIT
        ? 'background:#fef3c7;color:#b45309;border:1px solid #fde68a;'
        : 'background:#eff6ff;color:#1d4ed8;border:1px solid #dbeafe;';
      const catIcon = isNonIT ? '📞' : '💻';
      const catLabel = isNonIT ? 'Non IT' : 'Software Eng';

      const shareUrl = j.share_url || `/category/${j.category_slug}/job/${j.uuid}/`;
      return `
        <div class="vp-product-card" data-id="${j.id}" data-share-url="${escapeHtml(shareUrl)}">
          <div class="vp-card-header">
            <span class="company-badge">${escapeHtml(j.company_name)}</span>
            <div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap;justify-content:flex-end;">
              <span style="${catStyle}font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;letter-spacing:0.3px;">${catIcon} ${escapeHtml(j.category_name || catLabel)}</span>
              ${isNewToday ? '<span style="background:#fef2f2;color:#dc2626;font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;border:1px solid #fecaca;letter-spacing:0.5px;">NEW</span>' : ''}
              <span class="type-badge">${j.job_type_display}</span>
            </div>
          </div>

          <div class="vp-card-content">
            <h3><a href="${escapeHtml(shareUrl)}" style="color:inherit;text-decoration:none;">${escapeHtml(j.title)}</a></h3>
            
            <div class="vp-salary-row">
              <span style="display:inline-flex;align-items:center;gap:4px;"><img src="/static/images/icon-salary.png" class="nav-icon" width="16" height="16" alt="Salary"> ${escapeHtml(j.stipend_salary)}</span>
              <span style="color: var(--muted); font-weight: 500; display:inline-flex;align-items:center;gap:4px;"><img src="/static/images/icon-location.png" class="nav-icon" width="16" height="16" alt="Location"> ${escapeHtml(j.location)}</span>
            </div>

            <p>${escapeHtml(j.description)}</p>

            ${skillsHtml ? `<div class="skills-wrapper">${skillsHtml}</div>` : ''}

            <div class="vp-price-row">
              <div class="timer-tag" data-timer="${j.id}" data-seconds="${j.time_left_seconds}">
                ⏱️ <span>${isDeactivated ? 'Closed / Expired' : formattedTime}</span>
              </div>
            </div>

            <!-- Balanced 50/50 Action Grid -->
            <div class="card-action-grid">
              ${!isDeactivated && j.apply_url ? `
                <a href="${escapeHtml(j.apply_url)}" target="_blank" rel="noopener"
                   class="external-apply-btn"
                   onclick="event.stopPropagation();">
                  <img src="/static/images/icon-apply.png" class="nav-icon" style="filter:brightness(0) invert(1);" width="14" height="14" alt="Apply"> Apply Now ↗
                </a>
                <a href="${escapeHtml(shareUrl)}"
                   class="detail-page-btn"
                   onclick="event.stopPropagation();">
                  <img src="/static/images/icon-share.png" class="nav-icon" width="14" height="14" alt="Detail"> Detail Page
                </a>
              ` : isDeactivated ? `
                <div style="grid-column: 1 / -1; display:flex;align-items:center;justify-content:center;height:38px;background:#f1f5f9;color:#94a3b8;font-size:12px;font-weight:700;border-radius:var(--radius-sm, 6px);border:1px solid #e2e8f0;">
                  ⛔ Closed Opportunity
                </div>
              ` : `
                <a href="${escapeHtml(shareUrl)}"
                   class="external-apply-btn"
                   onclick="event.stopPropagation();"
                   style="grid-column: 1 / -1;">
                  <img src="/static/images/icon-feed.png" class="nav-icon" width="14" height="14" alt="View"> View Requirement Page ↗
                </a>
              `}
            </div>
          </div>
        </div>
      `;
    }).join('');

    bindCardClicks();
  }

  // --- RENDER PAGINATION CONTROLS ---

  function renderPagination() {
    if (!paginationContainer) return;

    if (state.totalCount === 0) {
      paginationContainer.innerHTML = '';
      return;
    }

    if (state.totalPages <= 1) {
      paginationContainer.innerHTML = `
        <div class="pagination-wrapper">
          <div class="pagination-info">
            Showing all <strong>${state.totalCount}</strong> active opportunities
          </div>
        </div>`;
      return;
    }

    const startNum = (state.page - 1) * state.pageSize + 1;
    const endNum = Math.min(state.totalCount, state.page * state.pageSize);
    const total = state.totalPages;
    const curr = state.page;

    // Smart windowing for page numbers (e.g. 1 2 3 ... 8)
    let pageNumbers = [];
    if (total <= 7) {
      for (let i = 1; i <= total; i++) pageNumbers.push(i);
    } else {
      if (curr <= 4) {
        pageNumbers = [1, 2, 3, 4, 5, '...', total];
      } else if (curr >= total - 3) {
        pageNumbers = [1, '...', total - 4, total - 3, total - 2, total - 1, total];
      } else {
        pageNumbers = [1, '...', curr - 1, curr, curr + 1, '...', total];
      }
    }

    const pagesHtml = pageNumbers.map(p => {
      if (p === '...') {
        return `<span style="display:inline-flex;align-items:center;justify-content:center;min-width:32px;height:38px;color:var(--muted);font-weight:700;">…</span>`;
      }
      return `
        <button class="pag-page-btn ${p === curr ? 'active' : ''}" data-page="${p}">
          ${p}
        </button>
      `;
    }).join('');

    paginationContainer.innerHTML = `
      <div class="pagination-wrapper">
        <div class="pagination-info">
          Showing <strong>${startNum}–${endNum}</strong> of <strong>${state.totalCount}</strong> active requirements
        </div>

        <nav class="pagination-nav" aria-label="Requirement pagination">
          <button class="pag-btn" id="btnPrevPage" ${curr <= 1 ? 'disabled' : ''} aria-label="Previous Page">
            ‹ Previous
          </button>

          <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap; justify-content: center;">
            ${pagesHtml}
          </div>

          <button class="pag-btn" id="btnNextPage" ${curr >= total ? 'disabled' : ''} aria-label="Next Page">
            Next ›
          </button>
        </nav>
      </div>
    `;

    // Event Listeners for Pagination Buttons
    const btnPrev = document.getElementById('btnPrevPage');
    if (btnPrev && curr > 1) {
      btnPrev.addEventListener('click', () => {
        state.page--;
        scrollAndLoadJobs();
      });
    }

    const btnNext = document.getElementById('btnNextPage');
    if (btnNext && curr < total) {
      btnNext.addEventListener('click', () => {
        state.page++;
        scrollAndLoadJobs();
      });
    }

    paginationContainer.querySelectorAll('.pag-page-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetPage = parseInt(btn.dataset.page);
        if (targetPage && targetPage !== state.page) {
          state.page = targetPage;
          scrollAndLoadJobs();
        }
      });
    });
  }

  function scrollAndLoadJobs() {
    loadJobs();
    const catalogSection = document.getElementById('catalogSection');
    if (catalogSection) {
      catalogSection.scrollIntoView({ behavior: 'smooth' });
    }
  }

  function renderDetailModal(j) {
    if (!detailModal) return;

    document.getElementById('detailTitle').textContent = j.title;
    document.getElementById('detailCompany').textContent = `${j.company_name} • ${j.category_name}`;
    document.getElementById('detailJobType').textContent = j.job_type_display;
    document.getElementById('detailSalary').textContent = j.stipend_salary;
    document.getElementById('detailLocation').textContent = j.location;
    document.getElementById('detailPostedDate').textContent = j.posted_date_display || 'Today';
    document.getElementById('detailDescription').textContent = j.description;
    document.getElementById('detailEligibility').textContent = j.eligibility;

    const skillsContainer = document.getElementById('detailSkills');
    skillsContainer.innerHTML = j.skills_list.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join(' ');

    const externalBtn = document.getElementById('detailExternalLink');
    if (j.apply_url && j.status === 'ACTIVE' && j.time_left_seconds > 0) {
      externalBtn.href = j.apply_url;
      externalBtn.style.display = 'inline-flex';
    } else {
      externalBtn.style.display = 'none';
    }

    const pageLink = document.getElementById('detailPageLink');
    if (pageLink) {
      pageLink.href = j.share_url || `/job/${j.uuid || j.id}/`;
    }

    detailModal.classList.add('active');
  }

  function setupHomePageListeners() {
    const btnFilterToday = document.getElementById('btnFilterToday');

    if (btnFilterToday) {
      btnFilterToday.addEventListener('click', () => {
        state.isTodayOnly = !state.isTodayOnly;
        state.page = 1;
        
        document.querySelectorAll('.vp-tabs .vp-tab').forEach(t => t.classList.remove('active'));
        if (state.isTodayOnly) {
          btnFilterToday.classList.add('active');
        } else {
          const defaultTab = document.querySelector('.vp-tab[data-category="all"]') || document.querySelector('.vp-tab[data-category]');
          if (defaultTab) defaultTab.classList.add('active');
        }

        loadJobs();
      });
    }

    document.querySelectorAll('.vp-tabs .vp-tab[data-category]').forEach(tab => {
      tab.addEventListener('click', () => {
        state.isTodayOnly = false;
        state.isYesterdayOnly = false;
        state.isPreviousOnly = false;
        state.category = tab.dataset.category || 'all';
        state.page = 1;

        document.querySelectorAll('.vp-tabs .vp-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        loadJobs();
      });
    });

    if (searchInput) {
      let searchTimeout;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          state.searchQuery = e.target.value;
          state.page = 1;
          loadJobs();
        }, 300);
      });
    }

    if (jobTypeSelect) {
      jobTypeSelect.addEventListener('change', (e) => {
        state.jobType = e.target.value;
        state.page = 1;
        loadJobs();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        state.sort = e.target.value;
        state.page = 1;
        loadJobs();
      });
    }

    if (btnCloseDetail && detailModal) {
      btnCloseDetail.addEventListener('click', () => detailModal.classList.remove('active'));
      detailModal.addEventListener('click', (e) => {
        if (e.target === detailModal) detailModal.classList.remove('active');
      });
    }
  }

  function startCountdownTimer() {
    state.timerInterval = setInterval(() => {
      document.querySelectorAll('.timer-tag').forEach(el => {
        let sec = parseInt(el.dataset.seconds);
        if (sec > 0) {
          sec--;
          el.dataset.seconds = sec;
          el.querySelector('span').textContent = formatTimeLeft(sec);
        } else {
          el.querySelector('span').textContent = 'Deactivated';
        }
      });
    }, 1000);
  }

  function formatTimeLeft(seconds) {
    if (seconds <= 0) return 'Deactivated';
    const days = Math.floor(seconds / 86400);
    const hrs = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hrs}h left`;
    return `${hrs}h ${mins}m left`;
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
    return str.replace(/[&<>"']/g, function(m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
  }
});

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
  const expParam = (urlParams.get('experience') || urlParams.get('exp') || '').toLowerCase().trim();
  if (['fresher', 'freshers', '0-1'].includes(expParam)) {
    currentCategory = 'freshers';
  } else if (['experienced', 'experience', '1+', 'lateral'].includes(expParam)) {
    currentCategory = 'experienced';
  }

  // Saved view preference (cards vs list)
  const savedViewMode = localStorage.getItem('kashii_job_view_mode') || 'grid';

  // CRITICAL: Default state MUST have zero filters applied on initial page load
  const state = {
    searchQuery: urlParams.get('q') || urlParams.get('keyword') || '',
    category: isCategoryPage ? currentCategory : (urlParams.get('category') || 'all'),
    city: urlParams.get('city') || urlParams.get('location') || '', // Default: '' (All Locations)
    jobType: urlParams.get('job_type') || urlParams.get('type') || 'all', // Default: 'all' (All Types)
    sort: urlParams.get('sort') || 'newest', // Default: 'newest'
    isTodayOnly: isTodayOnly,
    isYesterdayOnly: isYesterdayOnly,
    isPreviousOnly: isPreviousOnly,
    page: 1,
    pageSize: 18, // 18 opportunities per page (6x3 grid layout)
    totalPages: 1,
    totalCount: 0,
    jobs: [],
    categories: [],
    activeJobId: null,
    timerInterval: null,
    viewMode: savedViewMode,
  };

  // DOM Elements
  const categorySelect = document.getElementById('filterCategory');
  const jobTypeSelect = document.getElementById('filterJobType');
  const sortSelect = document.getElementById('sorter') || document.getElementById('filterSort');
  const searchInput = document.getElementById('header-keyword-search') || document.getElementById('searchInput');
  const jobsGrid = document.getElementById('jobsGrid');
  const paginationContainer = document.getElementById('paginationContainer');
  const jobsFoundHeading = document.getElementById('jobsFoundHeading');

  // Side Drawer Elements
  const drawerOverlay = document.getElementById('drawerOverlay');
  const btnToggleDrawer = document.getElementById('btnToggleDrawer');
  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  const drawerCategoryNav = document.getElementById('drawerCategoryNav');
  const drawerSearchInput = document.getElementById('drawerSearchInput');

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
      bindCardClicks();
      setupViewToggle();
      setupFilterPopovers();
      loadJobs();
      setupHomePageListeners();
      startCountdownTimer();
    }
  }


  // --- GLOBAL SIDE DRAWER SETUP ---

  function setupGlobalDrawer() {
    if (btnToggleDrawer && drawerOverlay) {
      btnToggleDrawer.addEventListener('click', (e) => {
        e.preventDefault();
        drawerOverlay.classList.add('is-open');
        if (drawerSearchInput) {
          setTimeout(() => drawerSearchInput.focus(), 120);
        }
      });
    }

    const mobileToggleDrawer = document.getElementById('mobileToggleDrawer');
    if (mobileToggleDrawer && drawerOverlay) {
      mobileToggleDrawer.addEventListener('click', (e) => {
        e.preventDefault();
        drawerOverlay.classList.add('is-open');
        if (drawerSearchInput) {
          setTimeout(() => drawerSearchInput.focus(), 120);
        }
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

    // Mobile Instant Drawer Search
    if (drawerSearchInput) {
      let drawerSearchTimeout;
      drawerSearchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        // 1. Live filter category items inside the drawer
        document.querySelectorAll('#drawerCategoryNav .drawer-link').forEach(link => {
          const text = link.textContent.toLowerCase();
          link.style.display = (!query || text.includes(query)) ? 'flex' : 'none';
        });

        // 2. Debounce and sync with main catalog search
        clearTimeout(drawerSearchTimeout);
        drawerSearchTimeout = setTimeout(() => {
          if (searchInput) searchInput.value = e.target.value;
          state.searchQuery = e.target.value;
          state.page = 1;
          if (isHomePage || isCategoryPage) {
            loadJobs();
          }
        }, 300);
      });

      drawerSearchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (drawerOverlay) drawerOverlay.classList.remove('is-open');
          if (isHomePage || isCategoryPage) {
            scrollAndLoadJobs();
          } else {
            window.location.href = `/?q=${encodeURIComponent(drawerSearchInput.value)}#catalogSection`;
          }
        }
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
        drawerCategoryNav.innerHTML = data.categories.map(c => {
          const isTech = !c.slug.includes('non');
          const svgPath = isTech
            ? '<path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />'
            : '<path stroke-linecap="round" stroke-linejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />';
          return `
            <a href="/category/${c.slug}/" class="drawer-link" data-slug="${c.slug}">
              <div class="drawer-link-left">
                <span class="drawer-link-icon drawer-icon-cat">
                  <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                    ${svgPath}
                  </svg>
                </span>
                <span class="drawer-link-label">${escapeHtml(c.name)}</span>
              </div>
              <span class="drawer-badge badge-count">${c.active_count} OPEN</span>
            </a>
          `;
        }).join('');

        // Smooth category selection in mobile drawer on Homepage
        drawerCategoryNav.querySelectorAll('.drawer-link').forEach(link => {
          link.addEventListener('click', (e) => {
            const slug = link.dataset.slug;
            if (isHomePage) {
              e.preventDefault();
              if (drawerOverlay) drawerOverlay.classList.remove('is-open');

              state.isTodayOnly = false;
              state.isYesterdayOnly = false;
              state.isPreviousOnly = false;
              state.category = slug || 'all';
              state.page = 1;

              document.querySelectorAll('.vp-tabs .vp-tab').forEach(t => {
                t.classList.toggle('active', t.dataset.category === slug);
              });

              scrollAndLoadJobs();
            }
          });
        });
      }

    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  // --- SHIMMER SKELETON RENDERER ---
  function renderShimmerSkeletons(count = 6) {
    if (!jobsGrid) return;
    const cardHtml = '<div class="vp-product-card vp-shimmer-card" aria-hidden="true"></div>';
    jobsGrid.innerHTML = cardHtml.repeat(count);
  }

  // --- PAGINATED JOBS ENGINE (NEWEST FIRST) ---

  async function loadJobs() {
    if (!jobsGrid) return;

    try {
      renderShimmerSkeletons(state.pageSize || 6);

      const expFilterVal = state.category === 'freshers' ? 'fresher' : (state.category === 'experienced' ? 'experienced' : '');
      const params = new URLSearchParams({
        q: state.searchQuery,
        category: state.category || 'all',
        experience: expFilterVal,
        job_type: state.jobType,
        city: state.city || '',
        today: state.isTodayOnly ? 'true' : '',
        yesterday: state.isYesterdayOnly ? 'true' : '',
        previous: state.isPreviousOnly ? 'true' : '',
        sort: state.sort,
        page: state.page,
        page_size: state.pageSize,
      });

      const res = await fetch(`/api/jobs/?${params.toString()}`);

      if (res.status === 429) {
        const errorData = await res.json().catch(() => ({}));
        showToast(errorData.message || 'Rate limit reached. Please wait a moment before searching again.', 'error');
        jobsGrid.innerHTML = `
          <div class="glass empty-state">
            <h3>Too many searches</h3>
            <p>Please wait a moment, then try again.</p>
          </div>
        `;
        return;
      }

      const data = await res.json();

      state.jobs = data.jobs || [];
      state.totalCount = (data.total_count !== undefined) ? data.total_count : (data.count || 0);
      state.totalPages = (data.total_pages !== undefined) ? data.total_pages : 1;
      state.page = (data.current_page !== undefined) ? data.current_page : (data.page || 1);

      updateHeadingAndTags();
      renderJobs(state.jobs);
      renderPagination();

    } catch (err) {
      console.error('Failed to load jobs:', err);
      if (jobsFoundHeading) jobsFoundHeading.textContent = 'Could not load jobs';
      jobsGrid.innerHTML = `
        <div class="glass empty-state">
          <h3>Could not load jobs</h3>
          <p>Check your connection, then try again.</p>
          <button type="button" id="btnRetryLoadJobs" class="button button-primary">Retry</button>
        </div>`;
      const btnRetry = document.getElementById('btnRetryLoadJobs');
      if (btnRetry) {
        btnRetry.addEventListener('click', (e) => {
          e.preventDefault();
          loadJobs();
        });
      }
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
        <div class="glass empty-state">
          <h3>No jobs match these filters</h3>
          <p>Try another location or clear the filters.</p>
          <button type="button" id="btnEmptyClearFilters" class="button button-primary">Clear filters</button>
        </div>`;
      const btnEmptyClear = document.getElementById('btnEmptyClearFilters');
      if (btnEmptyClear) {
        btnEmptyClear.addEventListener('click', (e) => {
          e.preventDefault();
          clearAllFiltersAction();
        });
      }
      return;
    }

    jobsGrid.innerHTML = jobs.map(j => {
      const formattedTime = formatTimeLeft(j.time_left_seconds);
      const rawSkills = j.skills_list || j.skills || [];
      const skillsHtml = (Array.isArray(rawSkills) ? rawSkills : []).slice(0, 3).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
      const isClosed = j.status === 'EXPIRED';
      const postedDate = j.posted_date_display || j.relative_time || 'Today';
      const shareUrl = j.share_url || `/category/${j.category_slug}/job/${j.uuid}/`;
      const pay = j.stipend_salary && j.stipend_salary !== 'Competitive' ? `<span>${escapeHtml(j.stipend_salary)}</span>` : '';
      return `
        <article class="vp-product-card" data-id="${j.id}" data-share-url="${escapeHtml(shareUrl)}">
          <div class="vp-card-header">
            <span class="company-badge">${escapeHtml(j.company_name)}</span>
            <span class="type-badge">${j.is_referral ? 'Referral' : escapeHtml(j.job_type_display)}</span>
          </div>
          <h3><a href="${escapeHtml(shareUrl)}">${escapeHtml(j.title)}</a></h3>
          <p class="job-meta">
            <span>${escapeHtml(j.normalized_city || j.location)}</span>
            ${pay}
            <span>${escapeHtml(j.experience_display || 'Fresher / All Levels')}</span>
          </p>
          ${j.contact_phone ? `<p class="job-phone">HR contact: <a href="tel:${escapeHtml(j.contact_phone)}">${escapeHtml(j.contact_phone)}</a></p>` : ''}
          ${skillsHtml ? `<div class="skills-wrapper">${skillsHtml}</div>` : ''}
          <div class="job-foot">
            <span class="timer-tag${isClosed ? ' is-closed' : ''}" data-timer="${j.id}" data-seconds="${j.time_left_seconds}"><span>${isClosed ? 'Closed' : formattedTime}</span></span>
            <span>Posted ${escapeHtml(postedDate)}</span>
          </div>
          <div class="card-action-grid">
            ${isClosed ? '<span class="button wide" aria-disabled="true">This job has closed</span>' : `
              <a href="${escapeHtml(j.apply_url || shareUrl)}" ${j.apply_url ? 'target="_blank" rel="noopener noreferrer"' : ''} class="button external-apply-btn">${j.apply_url ? 'Apply' : 'View job'}</a>
              <a href="/resume-studio/?job_id=${escapeHtml(j.uuid)}" class="button resume-btn">Make resume</a>
            `}
          </div>
        </article>
      `;
    }).join('');

    bindCardClicks();
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      try { window.lucide.createIcons(); } catch(e){}
    }
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
            Showing all <strong>${state.totalCount}</strong> open jobs
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
        return '<span aria-hidden="true">…</span>';
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
          Showing <strong>${startNum}–${endNum}</strong> of <strong>${state.totalCount}</strong> open jobs
        </div>

        <nav class="pagination-nav" aria-label="Pages of jobs">
          <button class="pag-btn" id="btnPrevPage" ${curr <= 1 ? 'disabled' : ''} aria-label="Previous Page">
            Previous
          </button>

          <div class="pagination-nav">
            ${pagesHtml}
          </div>

          <button class="pag-btn" id="btnNextPage" ${curr >= total ? 'disabled' : ''} aria-label="Next Page">
            Next
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
    document.getElementById('detailDescription').textContent = String(j.description || '').replace(/\*\*/g, '');
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

  const CATEGORY_LABELS = {
    'all': 'All Fields',
    'software-tech': 'Software & Tech',
    'freshers': 'Fresher Hiring (0-1 Yrs)',
    'experienced': 'Experienced (1-5+ Yrs)',
    'qa-testing': 'QA & Testing',
    'hr-recruitment': 'HR & Hiring',
    'mba-business': 'MBA & Business',
    'non-it': 'Non IT & Ops'
  };

  function clearAllFiltersAction() {
    state.city = '';
    state.category = isCategoryPage ? currentCategory : 'all';
    state.jobType = 'all';
    state.searchQuery = '';
    state.isTodayOnly = false;
    state.isYesterdayOnly = false;
    state.isPreviousOnly = false;
    state.sort = 'newest';
    state.page = 1;
    if (searchInput) searchInput.value = '';
    const clearBtn = document.getElementById('headerSearchClearBtn');
    if (clearBtn) clearBtn.style.display = 'none';
    if (sortSelect) sortSelect.value = 'Date';
    loadJobs();
  }

  function updateHeadingAndTags() {
    if (jobsFoundHeading) {
      const locText = state.city ? ` in ${state.city}` : '';
      if (state.searchQuery) {
        jobsFoundHeading.textContent = `${state.totalCount} jobs found for "${state.searchQuery}"${locText}`;
      } else {
        jobsFoundHeading.textContent = `${state.totalCount} jobs found${locText}`;
      }
    }

    const selectedFiltersRow = document.getElementById('selectedFiltersRow');
    const selectedCityTag = document.getElementById('selectedCityTag');
    const selectedCityTagName = document.getElementById('selectedCityTagName');
    const selectedJobTypeTag = document.getElementById('selectedJobTypeTag');
    const selectedJobTypeTagName = document.getElementById('selectedJobTypeTagName');
    const selectedSpecialismTag = document.getElementById('selectedSpecialismTag');
    const selectedSpecialismTagName = document.getElementById('selectedSpecialismTagName');
    const selectedKeywordTag = document.getElementById('selectedKeywordTag');
    const selectedKeywordTagName = document.getElementById('selectedKeywordTagName');

    const locationBadge = document.getElementById('locationFilterBadgeCount');
    const jobTypeBadge = document.getElementById('jobTypeFilterBadgeCount');
    const specialismBadge = document.getElementById('specialismFilterBadgeCount');
    const allFiltersBadge = document.getElementById('allFiltersBadgeCount');

    const locationBtnText = document.getElementById('locationFilterBtnText');
    const jobTypeBtnText = document.getElementById('jobTypeFilterBtnText');
    const specialismBtnText = document.getElementById('specialismFilterBtnText');

    const btnLocation = document.querySelector('[data-locator-id="searchjobs_filters_location"]');
    const btnJobType = document.querySelector('[data-locator-id="searchjobs_filters_jobType"]');
    const btnSpecialism = document.querySelector('[data-locator-id="searchjobs_filters_specialism"]');
    const btnAllFilters = document.querySelector('[data-locator-id="searchjobs_filters_allFilters"]');

    let activeFilterCount = 0;

    // 1. City Filter Sync (Default: '' All Locations)
    if (state.city) {
      activeFilterCount++;
      if (locationBtnText) locationBtnText.textContent = state.city;
      if (locationBadge) { locationBadge.textContent = '1'; locationBadge.style.display = 'inline-flex'; }
      if (btnLocation) btnLocation.classList.add('is-active');
      if (selectedCityTag && selectedCityTagName) {
        selectedCityTagName.textContent = state.city;
        selectedCityTag.style.display = 'inline-flex';
      }
    } else {
      if (locationBtnText) locationBtnText.textContent = 'Location';
      if (locationBadge) locationBadge.style.display = 'none';
      if (btnLocation) btnLocation.classList.remove('is-active');
      if (selectedCityTag) selectedCityTag.style.display = 'none';
    }

    // 2. Job Type Filter Sync (Default: 'all' All Types)
    if (state.jobType && state.jobType !== 'all') {
      activeFilterCount++;
      const typeLabel = state.jobType === 'FULL_TIME' ? 'Full-Time' : 'Internships';
      if (jobTypeBtnText) jobTypeBtnText.textContent = typeLabel;
      if (jobTypeBadge) { jobTypeBadge.textContent = '1'; jobTypeBadge.style.display = 'inline-flex'; }
      if (btnJobType) btnJobType.classList.add('is-active');
      if (selectedJobTypeTag && selectedJobTypeTagName) {
        selectedJobTypeTagName.textContent = typeLabel;
        selectedJobTypeTag.style.display = 'inline-flex';
      }
    } else {
      if (jobTypeBtnText) jobTypeBtnText.textContent = 'Job type';
      if (jobTypeBadge) jobTypeBadge.style.display = 'none';
      if (btnJobType) btnJobType.classList.remove('is-active');
      if (selectedJobTypeTag) selectedJobTypeTag.style.display = 'none';
    }

    // 3. Category / Specialism Filter Sync (Default: 'all' All Fields)
    if (state.category && state.category !== 'all') {
      activeFilterCount++;
      const catLabel = CATEGORY_LABELS[state.category] || state.category;
      if (specialismBtnText) specialismBtnText.textContent = catLabel;
      if (specialismBadge) { specialismBadge.textContent = '1'; specialismBadge.style.display = 'inline-flex'; }
      if (btnSpecialism) btnSpecialism.classList.add('is-active');
      if (selectedSpecialismTag && selectedSpecialismTagName) {
        selectedSpecialismTagName.textContent = catLabel;
        selectedSpecialismTag.style.display = 'inline-flex';
      }
    } else {
      if (specialismBtnText) specialismBtnText.textContent = 'Field';
      if (specialismBadge) specialismBadge.style.display = 'none';
      if (btnSpecialism) btnSpecialism.classList.remove('is-active');
      if (selectedSpecialismTag) selectedSpecialismTag.style.display = 'none';
    }

    // 4. Keyword Search Tag Sync
    if (state.searchQuery) {
      if (selectedKeywordTag && selectedKeywordTagName) {
        selectedKeywordTagName.textContent = `"${state.searchQuery}"`;
        selectedKeywordTag.style.display = 'inline-flex';
      }
    } else {
      if (selectedKeywordTag) selectedKeywordTag.style.display = 'none';
    }

    // 5. All Filters Badge & Overall Selected Row
    if (allFiltersBadge) {
      allFiltersBadge.textContent = activeFilterCount.toString();
      allFiltersBadge.style.display = activeFilterCount > 0 ? 'inline-flex' : 'none';
    }
    if (btnAllFilters) {
      btnAllFilters.classList.toggle('is-active', activeFilterCount > 0);
    }

    // Hide entire selected row when zero active filters and no keyword
    const hasAnyActive = activeFilterCount > 0 || !!state.searchQuery;
    if (selectedFiltersRow) {
      selectedFiltersRow.style.display = hasAnyActive ? 'flex' : 'none';
    }

    // Sync options active classes in popovers
    document.querySelectorAll('#popoverLocation [data-city]').forEach(opt => {
      opt.classList.toggle('active', opt.dataset.city === (state.city || ''));
    });
    document.querySelectorAll('#popoverJobType [data-job-type]').forEach(opt => {
      opt.classList.toggle('active', opt.dataset.jobType === (state.jobType || 'all'));
    });
    document.querySelectorAll('#popoverSpecialism [data-category]').forEach(opt => {
      opt.classList.toggle('active', opt.dataset.category === (state.category || 'all'));
    });

    // Sync options active classes in All Filters Modal
    const modalAllFilters = document.getElementById('modalAllFilters');
    if (modalAllFilters) {
      modalAllFilters.querySelectorAll('#modalLocationChips [data-city]').forEach(x => {
        x.classList.toggle('active', x.dataset.city === (state.city || ''));
      });
      modalAllFilters.querySelectorAll('#modalJobTypeChips [data-job-type]').forEach(x => {
        x.classList.toggle('active', x.dataset.jobType === (state.jobType || 'all'));
      });
      modalAllFilters.querySelectorAll('#modalCategoryChips [data-category]').forEach(x => {
        x.classList.toggle('active', x.dataset.category === (state.category || 'all'));
      });
      modalAllFilters.querySelectorAll('#modalSortChips [data-sort]').forEach(x => {
        x.classList.toggle('active', (state.sort || 'newest') === x.dataset.sort);
      });
    }

    // Sync sorter dropdown display
    if (sortSelect) {
      if (state.sort === 'deadline') sortSelect.value = 'Proximity';
      else if (state.sort === 'relevance') sortSelect.value = 'Relevance';
      else sortSelect.value = 'Date';
    }
  }

  function setupViewToggle() {
    const btnList = document.querySelector('[data-locator-id="joblisting_toggle_listview"]');
    const btnGrid = document.querySelector('[data-locator-id="joblisting_toggle_sortview"]');

    function applyView(mode) {
      state.viewMode = mode;
      localStorage.setItem('kashii_job_view_mode', mode);
      if (mode === 'list') {
        if (btnList) {
          btnList.setAttribute('aria-pressed', 'true');
          btnList.classList.add('active', 'rel_bg-trigger-active');
        }
        if (btnGrid) {
          btnGrid.setAttribute('aria-pressed', 'false');
          btnGrid.classList.remove('active', 'rel_bg-trigger-active');
        }
        if (jobsGrid) jobsGrid.classList.add('is-list-view');
      } else {
        if (btnGrid) {
          btnGrid.setAttribute('aria-pressed', 'true');
          btnGrid.classList.add('active', 'rel_bg-trigger-active');
        }
        if (btnList) {
          btnList.setAttribute('aria-pressed', 'false');
          btnList.classList.remove('active', 'rel_bg-trigger-active');
        }
        if (jobsGrid) jobsGrid.classList.remove('is-list-view');
      }
    }

    if (btnList) {
      btnList.addEventListener('click', (e) => {
        e.preventDefault();
        applyView('list');
      });
    }

    if (btnGrid) {
      btnGrid.addEventListener('click', (e) => {
        e.preventDefault();
        applyView('grid');
      });
    }

    // Apply saved or default view
    applyView(state.viewMode);
  }

  function setupFilterPopovers() {
    const popoverLocation = document.getElementById('popoverLocation');
    const popoverJobType = document.getElementById('popoverJobType');
    const popoverSpecialism = document.getElementById('popoverSpecialism');
    const modalAllFilters = document.getElementById('modalAllFilters');

    const btnFilterLocation = document.querySelector('[data-locator-id="searchjobs_filters_location"]');
    const btnFilterJobType = document.querySelector('[data-locator-id="searchjobs_filters_jobType"]');
    const btnFilterSpecialism = document.querySelector('[data-locator-id="searchjobs_filters_specialism"]');

    function closeAllPopovers() {
      if (popoverLocation) popoverLocation.style.display = 'none';
      if (popoverJobType) popoverJobType.style.display = 'none';
      if (popoverSpecialism) popoverSpecialism.style.display = 'none';

      document.querySelectorAll('.rel_filter_dropdown_wrapper').forEach(w => w.classList.remove('is-open'));

      if (btnFilterLocation) { btnFilterLocation.classList.remove('is-open'); btnFilterLocation.setAttribute('aria-expanded', 'false'); }
      if (btnFilterJobType) { btnFilterJobType.classList.remove('is-open'); btnFilterJobType.setAttribute('aria-expanded', 'false'); }
      if (btnFilterSpecialism) { btnFilterSpecialism.classList.remove('is-open'); btnFilterSpecialism.setAttribute('aria-expanded', 'false'); }
    }

    document.querySelectorAll('[data-close-popover]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAllPopovers();
      });
    });

    if (btnFilterLocation && popoverLocation) {
      btnFilterLocation.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popoverLocation.style.display === 'block';
        closeAllPopovers();
        if (!isOpen) {
          popoverLocation.style.display = 'block';
          btnFilterLocation.classList.add('is-open');
          btnFilterLocation.setAttribute('aria-expanded', 'true');
          const wrap = btnFilterLocation.closest('.rel_filter_dropdown_wrapper');
          if (wrap) wrap.classList.add('is-open');
        }
      });
    }

    if (btnFilterJobType && popoverJobType) {
      btnFilterJobType.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popoverJobType.style.display === 'block';
        closeAllPopovers();
        if (!isOpen) {
          popoverJobType.style.display = 'block';
          btnFilterJobType.classList.add('is-open');
          btnFilterJobType.setAttribute('aria-expanded', 'true');
          const wrap = btnFilterJobType.closest('.rel_filter_dropdown_wrapper');
          if (wrap) wrap.classList.add('is-open');
        }
      });
    }

    if (btnFilterSpecialism && popoverSpecialism) {
      btnFilterSpecialism.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popoverSpecialism.style.display === 'block';
        closeAllPopovers();
        if (!isOpen) {
          popoverSpecialism.style.display = 'block';
          btnFilterSpecialism.classList.add('is-open');
          btnFilterSpecialism.setAttribute('aria-expanded', 'true');
          const wrap = btnFilterSpecialism.closest('.rel_filter_dropdown_wrapper');
          if (wrap) wrap.classList.add('is-open');
        }
      });
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.rel_filter_dropdown_wrapper') && !e.target.closest('.rel_popover')) {
        closeAllPopovers();
      }
    });

    // Global Escape Key Listener for dismissing modals and popovers
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' || e.key === 'Esc' || e.keyCode === 27) {
        closeAllPopovers();
        closeModal();
        closeAlertsModal();
      }
    });

    if (popoverLocation) {
      popoverLocation.querySelectorAll('[data-city]').forEach(opt => {
        opt.addEventListener('click', (e) => {
          e.preventDefault();
          state.city = opt.dataset.city;
          state.page = 1;
          closeAllPopovers();
          loadJobs();
        });
      });
    }

    if (popoverJobType) {
      popoverJobType.querySelectorAll('[data-job-type]').forEach(opt => {
        opt.addEventListener('click', (e) => {
          e.preventDefault();
          state.jobType = opt.dataset.jobType;
          state.page = 1;
          closeAllPopovers();
          loadJobs();
        });
      });
    }

    if (popoverSpecialism) {
      popoverSpecialism.querySelectorAll('[data-category]').forEach(opt => {
        opt.addEventListener('click', (e) => {
          e.preventDefault();
          state.category = opt.dataset.category;
          state.page = 1;
          closeAllPopovers();
          loadJobs();
        });
      });
    }

    // All Filters Modal Handlers
    const btnAllFilters = document.querySelector('[data-locator-id="searchjobs_filters_allFilters"]');
    const btnMobileFilters = document.querySelector('[data-rs-modal-trigger="mobile-filters"]');
    const btnCloseAllFilters = document.getElementById('btnCloseAllFilters');
    const btnResetModal = document.getElementById('btnResetModalFilters');
    const btnApplyModal = document.getElementById('btnApplyModalFilters');

    let modalDraftState = {
      city: '',
      jobType: 'all',
      category: 'all',
      sort: 'newest'
    };

    function syncModalChipVisuals() {
      if (!modalAllFilters) return;
      modalAllFilters.querySelectorAll('#modalLocationChips [data-city]').forEach(x => {
        x.classList.toggle('active', x.dataset.city === modalDraftState.city);
      });
      modalAllFilters.querySelectorAll('#modalJobTypeChips [data-job-type]').forEach(x => {
        x.classList.toggle('active', x.dataset.jobType === modalDraftState.jobType);
      });
      modalAllFilters.querySelectorAll('#modalCategoryChips [data-category]').forEach(x => {
        x.classList.toggle('active', x.dataset.category === modalDraftState.category);
      });
      modalAllFilters.querySelectorAll('#modalSortChips [data-sort]').forEach(x => {
        x.classList.toggle('active', x.dataset.sort === modalDraftState.sort);
      });
    }

    function openModal() {
      if (modalAllFilters) {
        modalDraftState.city = state.city || '';
        modalDraftState.jobType = state.jobType || 'all';
        modalDraftState.category = state.category || 'all';
        modalDraftState.sort = state.sort || 'newest';

        syncModalChipVisuals();
        modalAllFilters.style.display = 'flex';
        document.body.style.overflow = 'hidden';
      }
    }
    function closeModal() {
      if (modalAllFilters) {
        modalAllFilters.style.display = 'none';
        document.body.style.overflow = '';
      }
    }

    if (btnAllFilters) btnAllFilters.addEventListener('click', openModal);
    if (btnMobileFilters) btnMobileFilters.addEventListener('click', openModal);
    if (btnCloseAllFilters) btnCloseAllFilters.addEventListener('click', closeModal);
    if (modalAllFilters) {
      modalAllFilters.addEventListener('click', (e) => {
        if (e.target === modalAllFilters) closeModal();
      });

      modalAllFilters.querySelectorAll('#modalLocationChips [data-city]').forEach(b => {
        b.addEventListener('click', () => {
          modalDraftState.city = b.dataset.city;
          syncModalChipVisuals();
        });
      });

      modalAllFilters.querySelectorAll('#modalJobTypeChips [data-job-type]').forEach(b => {
        b.addEventListener('click', () => {
          modalDraftState.jobType = b.dataset.jobType;
          syncModalChipVisuals();
        });
      });

      modalAllFilters.querySelectorAll('#modalCategoryChips [data-category]').forEach(b => {
        b.addEventListener('click', () => {
          modalDraftState.category = b.dataset.category;
          syncModalChipVisuals();
        });
      });

      modalAllFilters.querySelectorAll('#modalSortChips [data-sort]').forEach(b => {
        b.addEventListener('click', () => {
          modalDraftState.sort = b.dataset.sort;
          syncModalChipVisuals();
        });
      });
    }

    if (btnApplyModal) {
      btnApplyModal.addEventListener('click', () => {
        state.city = modalDraftState.city;
        state.jobType = modalDraftState.jobType;
        state.category = modalDraftState.category;
        state.sort = modalDraftState.sort;
        if (sortSelect) {
          if (state.sort === 'deadline') sortSelect.value = 'Proximity';
          else if (state.sort === 'relevance') sortSelect.value = 'Relevance';
          else sortSelect.value = 'Date';
        }
        closeModal();
        state.page = 1;
        loadJobs();
      });
    }

    if (btnResetModal) {
      btnResetModal.addEventListener('click', () => {
        modalDraftState = {
          city: '',
          jobType: 'all',
          category: isCategoryPage ? currentCategory : 'all',
          sort: 'newest'
        };
        state.city = '';
        state.jobType = 'all';
        state.category = isCategoryPage ? currentCategory : 'all';
        state.sort = 'newest';
        if (sortSelect) sortSelect.value = 'Date';
        closeModal();
        state.page = 1;
        loadJobs();
      });
    }

    // Individual Tag Clear Handlers
    const btnClearCityTag = document.getElementById('btnClearCityTag');
    if (btnClearCityTag) {
      btnClearCityTag.addEventListener('click', (e) => {
        e.preventDefault();
        state.city = '';
        state.page = 1;
        loadJobs();
      });
    }

    const btnClearJobTypeTag = document.getElementById('btnClearJobTypeTag');
    if (btnClearJobTypeTag) {
      btnClearJobTypeTag.addEventListener('click', (e) => {
        e.preventDefault();
        state.jobType = 'all';
        state.page = 1;
        loadJobs();
      });
    }

    const btnClearSpecialismTag = document.getElementById('btnClearSpecialismTag');
    if (btnClearSpecialismTag) {
      btnClearSpecialismTag.addEventListener('click', (e) => {
        e.preventDefault();
        state.category = isCategoryPage ? currentCategory : 'all';
        state.page = 1;
        loadJobs();
      });
    }

    const btnClearKeywordTag = document.getElementById('btnClearKeywordTag');
    if (btnClearKeywordTag) {
      btnClearKeywordTag.addEventListener('click', (e) => {
        e.preventDefault();
        state.searchQuery = '';
        if (searchInput) searchInput.value = '';
        const clearBtn = document.getElementById('headerSearchClearBtn');
        if (clearBtn) clearBtn.style.display = 'none';
        state.page = 1;
        loadJobs();
      });
    }

    const btnClearAllFilters = document.getElementById('btnClearAllFilters');
    if (btnClearAllFilters) {
      btnClearAllFilters.addEventListener('click', (e) => {
        e.preventDefault();
        clearAllFiltersAction();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val === 'Date' || val === '' || val === 'newest') {
          state.sort = 'newest';
        } else if (val === 'Relevance' || val === 'relevance') {
          state.sort = 'relevance';
        } else if (val === 'Proximity' || val === 'deadline') {
          state.sort = 'deadline';
        } else {
          state.sort = 'newest';
        }
        state.page = 1;
        loadJobs();
      });
    }

  }

  function setupHomePageListeners() {
    const btnFilterToday = document.getElementById('btnFilterToday');

    if (state.category && state.category !== 'all') {
      const activeTab = document.querySelector(`.vp-tabs .vp-tab[data-category="${state.category}"]`);
      if (activeTab) {
        document.querySelectorAll('.vp-tabs .vp-tab').forEach(t => t.classList.remove('active'));
        activeTab.classList.add('active');
      }
    }

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

    const clearBtn = document.getElementById('headerSearchClearBtn');
    if (searchInput) {
      if (clearBtn && searchInput.value) clearBtn.style.display = 'inline-flex';

      let searchTimeout;
      searchInput.addEventListener('input', (e) => {
        if (clearBtn) clearBtn.style.display = e.target.value.trim() ? 'inline-flex' : 'none';
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          state.searchQuery = e.target.value.trim();
          state.page = 1;
          loadJobs();
        }, 300);
      });

      if (clearBtn) {
        clearBtn.addEventListener('click', () => {
          searchInput.value = '';
          clearBtn.style.display = 'none';
          state.searchQuery = '';
          state.page = 1;
          loadJobs();
        });
      }
    }

    if (jobTypeSelect) {
      jobTypeSelect.addEventListener('change', (e) => {
        state.jobType = e.target.value;
        state.page = 1;
        loadJobs();
      });
    }

    // Sort changes are handled once, with the value mapping, in setupFilterPopovers.

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
        const sec = Math.max(0, (parseInt(el.dataset.seconds, 10) || 0) - 60);
        el.dataset.seconds = sec;
        el.querySelector('span').textContent = formatTimeLeft(sec);
      });
    }, 60000);
  }

  function formatTimeLeft(seconds) {
    if (!seconds || seconds <= 0) return 'Closed';
    const days = Math.floor(seconds / 86400);
    if (days >= 1) return `${days} day${days === 1 ? '' : 's'} left`;
    const hours = Math.max(1, Math.floor(seconds / 3600));
    return `${hours} hour${hours === 1 ? '' : 's'} left`;
  }

  function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
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

  // --- INSTAGRAM STORY COPY ENGINE ---
  window.copyCardStoryDirect = function(event, btn) {
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }
    if (!btn) return;

    function toUnicodeBold(text) {
      if (!text) return '';
      return String(text).split('').map(ch => {
        const code = ch.charCodeAt(0);
        if (code >= 65 && code <= 90) return String.fromCodePoint(0x1D5D4 + (code - 65));
        if (code >= 97 && code <= 122) return String.fromCodePoint(0x1D5EE + (code - 97));
        if (code >= 48 && code <= 57) return String.fromCodePoint(0x1D7EC + (code - 48));
        return ch;
      }).join('');
    }

    let storyText = btn.getAttribute('data-story') || '';
    if (!storyText || storyText.trim().length === 0) {
      const company = btn.getAttribute('data-company') || 'Hiring Company';
      const companyHighlight = toUnicodeBold(company.trim().toUpperCase());
      const title = btn.getAttribute('data-title') || 'Software Professional';
      const exp = btn.getAttribute('data-exp') || 'Fresher / All Levels';
      const salary = btn.getAttribute('data-salary') || 'Competitive Package (Best in Industry)';
      const location = btn.getAttribute('data-location') || 'Pan India / Remote';
      const skills = btn.getAttribute('data-skills') || 'Software Engineering, Problem Solving';
      let eligibility = btn.getAttribute('data-eligibility') || '';
      if (!eligibility || eligibility.length < 5 || eligibility.toLowerCase().includes('open to eligible')) {
        eligibility = 'Any Graduate / BE / B.Tech / MCA / All Batches';
      } else if (eligibility.length > 75) {
        const firstSent = eligibility.split('.')[0].trim();
        if (firstSent.length > 10 && firstSent.length <= 75) {
          eligibility = firstSent;
        } else {
          eligibility = 'Any Graduate / BE / B.Tech / MCA / All Batches';
        }
      }
      const contact = btn.getAttribute('data-contact') || '';

      const isFresher = /fresher|0-|0 yr|intern|entry/i.test(exp);
      const expLine = isFresher
        ? `🎯 Experience: ${exp} 🚀 (Freshers Eligible!)`
        : `🎯 Experience: ${exp} ⚠️ (Experience Required)`;

      const lines = [
        '🚨 URGENT HIRING ALERT! 🚨',
        '',
        `🏢 Company: ${companyHighlight}`,
        `📌 Role: ${title}`,
        expLine,
        `💰 Salary / CTC: ${salary}`,
        `📍 Location: ${location}`,
        `⚡ Key Skills: ${skills}`,
        `🎓 Eligibility: ${eligibility}`,
      ];
      if (contact) {
        lines.push(`📞 HR Contact: ${contact}`);
      }
      storyText = lines.join('\n');
    }

    const origHtml = btn.innerHTML;
    function markCopied() {
      btn.innerHTML = '<span>✅ Story Text Copied!</span>';
      btn.style.background = '#059669';
      btn.style.color = '#ffffff';
      btn.style.borderColor = '#059669';
      showToast('Instagram Story text copied! Ready to paste into Instagram Story.', 'success');
      setTimeout(() => {
        btn.innerHTML = origHtml;
        btn.style.background = '';
        btn.style.color = '';
        btn.style.borderColor = '';
      }, 2500);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(storyText).then(markCopied).catch(() => {
        fallbackCopyText(storyText, markCopied);
      });
    } else {
      fallbackCopyText(storyText, markCopied);
    }
  };

  function fallbackCopyText(text, callback) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
      document.execCommand('copy');
      if (callback) callback();
    } catch (err) {
      alert('Instagram Story Text:\n\n' + text);
    }
    document.body.removeChild(ta);
  }

  window.showToast = showToast;

});



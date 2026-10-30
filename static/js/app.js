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
  if (expParam in ['fresher', 'freshers', '0-1']) {
    currentCategory = 'freshers';
  } else if (expParam in ['experienced', 'experience', '1+', 'lateral']) {
    currentCategory = 'experienced';
  }

  const state = {
    searchQuery: urlParams.get('q') || urlParams.get('keyword') || '',
    category: currentCategory,
    city: 'Bengaluru',
    jobType: 'all',
    sort: 'newest',
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
    viewMode: 'grid',
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
      if (isHomePage) startTypewriter();
      bindCardClicks();
      setupViewToggle();
      setupFilterPopovers();
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
    const cardHtml = `
      <div class="vp-product-card vp-shimmer-card">
        <div class="vp-card-header" style="margin-bottom: 16px;">
          <div class="shimmer-placeholder" style="width: 100px; height: 22px; border-radius: 9999px;"></div>
          <div class="shimmer-placeholder" style="width: 75px; height: 22px; border-radius: 9999px;"></div>
        </div>
        <div class="vp-card-content">
          <div class="shimmer-placeholder" style="width: 85%; height: 20px; margin-bottom: 12px; border-radius: 6px;"></div>
          <div style="display: flex; gap: 12px; margin-bottom: 12px;">
            <div class="shimmer-placeholder" style="width: 90px; height: 16px; border-radius: 4px;"></div>
            <div class="shimmer-placeholder" style="width: 70px; height: 16px; border-radius: 4px;"></div>
          </div>
          <div class="shimmer-placeholder" style="width: 110px; height: 14px; margin-bottom: 12px; border-radius: 4px;"></div>
          <div class="shimmer-placeholder" style="width: 100%; height: 13px; margin-bottom: 6px; border-radius: 4px;"></div>
          <div class="shimmer-placeholder" style="width: 70%; height: 13px; margin-bottom: 16px; border-radius: 4px;"></div>
          <div class="skills-wrapper" style="display: flex; gap: 6px; margin-bottom: 18px;">
            <div class="shimmer-placeholder" style="width: 55px; height: 22px; border-radius: 6px;"></div>
            <div class="shimmer-placeholder" style="width: 65px; height: 22px; border-radius: 6px;"></div>
            <div class="shimmer-placeholder" style="width: 50px; height: 22px; border-radius: 6px;"></div>
          </div>
          <div class="shimmer-placeholder" style="width: 140px; height: 18px; margin-bottom: 16px; border-radius: 6px;"></div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: auto;">
            <div class="shimmer-placeholder" style="height: 38px; border-radius: 10px;"></div>
            <div class="shimmer-placeholder" style="height: 38px; border-radius: 10px;"></div>
          </div>
        </div>
      </div>
    `;
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
          <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; background: #ffffff; border-radius: 16px; border: 1px solid #fed7aa;">
            <h3 style="color: #c2410c; margin-bottom: 6px;">Too Many Requests</h3>
            <p style="color: #64748b; font-size: 14px;">You have temporarily reached the request rate limit. Please retry in a few moments.</p>
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
      const formattedTime = (typeof j.time_left_seconds === 'number' && j.time_left_seconds > 0)
        ? formatTimeLeft(j.time_left_seconds)
        : 'Auto-Expires in 7 Days';
      const rawSkills = j.skills_list || j.skills || [];
      const skillsHtml = (Array.isArray(rawSkills) ? rawSkills : []).slice(0, 3).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
      const isDeactivated = j.status === 'EXPIRED';
      const postedDate = j.posted_date_display || j.relative_time || 'Today';
      const isNewToday = postedDate === 'Today';

      let catStyle = 'background:#eff6ff;color:#1d4ed8;border:1px solid #dbeafe;';
      let catIcon = '💻';
      let catLabel = j.category_name || 'Software Eng';

      const catSlug = (j.category_slug || '').toLowerCase();
      const titleLower = (j.title || '').toLowerCase();
      if (catSlug.includes('qa') || titleLower.includes('test') || titleLower.includes('qa')) {
        catStyle = 'background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;';
        catIcon = '🧪';
        catLabel = 'QA & Testing';
      } else if (catSlug.includes('hr') || titleLower.includes('recruiter') || titleLower.includes('talent') || titleLower.includes('hr ')) {
        catStyle = 'background:#faf5ff;color:#7e22ce;border:1px solid #e9d5ff;';
        catIcon = '👥';
        catLabel = 'HR & Hiring';
      } else if (catSlug.includes('mba') || titleLower.includes('mba') || titleLower.includes('management trainee') || titleLower.includes('business analyst')) {
        catStyle = 'background:#fdf2f8;color:#be185d;border:1px solid #fbcfe8;';
        catIcon = '📈';
        catLabel = 'MBA & Business';
      } else if (catSlug.includes('non') || j.industry_domain === 'NON_TECHNICAL') {
        catStyle = 'background:#fef3c7;color:#b45309;border:1px solid #fde68a;';
        catIcon = '📞';
        catLabel = 'Non IT';
      }
      const srcCode = j.source_code || ((j.source_name || '').toLowerCase().includes('linkedin') ? 'L' : ((j.source_name || '').toLowerCase().includes('naukri') ? 'N' : ((j.source_name || '').toLowerCase().includes('startup') ? 'S' : 'JD')));

      const shareUrl = j.share_url || `/category/${j.category_slug}/job/${j.uuid}/`;
      return `
        <div class="vp-product-card" data-id="${j.id}" data-share-url="${escapeHtml(shareUrl)}">
          <div class="vp-card-header">
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
              <span class="company-badge" title="${escapeHtml(j.company_name)}">${escapeHtml(j.company_name)}</span>
              <span class="source-tag" title="Verified Opportunity" style="font-size:10px;font-weight:800;padding:1px 6px;border-radius:4px;background:#f1f5f9;color:#64748b;border:1px solid #cbd5e1;letter-spacing:0.3px;">${srcCode}</span>
            </div>
            <div class="vp-badge-cluster">
              ${j.is_referral ? '<span style="background:#eff6ff;color:#2563eb;font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;border:1px solid #bfdbfe;letter-spacing:0.3px;display:inline-flex;align-items:center;gap:3px;">🤝 Referral</span>' : ''}
              <span style="${catStyle}font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;letter-spacing:0.3px;">${catIcon} ${escapeHtml(j.category_name || catLabel)}</span>
              ${isNewToday ? '<span style="background:#fef2f2;color:#dc2626;font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;border:1px solid #fecaca;letter-spacing:0.5px;display:inline-flex;align-items:center;gap:4px;"><span class="badge-live-pulse"></span>NEW</span>' : ''}
              <span class="type-badge">${j.job_type_display}</span>
            </div>
          </div>

          <div class="vp-card-content">
            <h3><a href="${escapeHtml(shareUrl)}" style="color:inherit;text-decoration:none;">${escapeHtml(j.title)}</a></h3>
            
            <div class="vp-salary-row">
              <span style="display:inline-flex;align-items:center;gap:4px;"><img src="/static/images/icon-salary.png" class="nav-icon" width="16" height="16" alt="Salary"> ${escapeHtml(j.stipend_salary)}</span>
              <span style="color: var(--muted); font-weight: 500; display:inline-flex;align-items:center;gap:4px;"><img src="/static/images/icon-location.png" class="nav-icon" width="16" height="16" alt="Location"> ${escapeHtml(j.normalized_city || j.location)}</span>
            </div>

            <div style="font-size:12px;font-weight:600;color:var(--muted);margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:4px;">
              <div style="display:flex;align-items:center;gap:4px;">
                <img src="/static/images/icon-date.png" class="nav-icon" width="14" height="14" alt="Date"> Posted: <strong style="color:var(--ink);">${escapeHtml(postedDate)}</strong>
              </div>
              <div style="display:flex;align-items:center;gap:4px;color:var(--blue-primary);font-weight:700;">
                <span>💼</span> <span>Exp: ${escapeHtml(j.experience_display || 'Fresher / All Levels')}</span>
              </div>
            </div>

            ${j.contact_phone ? `
              <div style="font-size:11.5px;font-weight:700;color:#047857;background:#ecfdf5;border:1px solid #a7f3d0;padding:3px 8px;border-radius:6px;margin-bottom:8px;display:inline-flex;align-items:center;gap:5px;">
                <span>📞 HR Contact:</span> <a href="tel:${escapeHtml(j.contact_phone)}" style="color:#047857;text-decoration:none;font-weight:800;" onclick="event.stopPropagation();">${escapeHtml(j.contact_phone)}</a>
              </div>
            ` : ''}

            <p style="font-size:13px;color:#64748b;line-height:1.5;margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">${escapeHtml(j.description || 'Detailed job description and responsibilities available on the official requirement page.')}</p>

            ${skillsHtml ? `<div class="skills-wrapper" style="margin-bottom:12px;display:flex;flex-wrap:wrap;gap:4px;">${skillsHtml}</div>` : ''}

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

  function updateHeadingAndTags() {
    if (jobsFoundHeading) {
      const locText = state.city ? ` in ${state.city.toLowerCase()}` : '';
      if (state.searchQuery) {
        jobsFoundHeading.textContent = `${state.totalCount} jobs found for "${state.searchQuery}"${locText}.`;
      } else {
        jobsFoundHeading.textContent = `${state.totalCount} jobs found${locText}.`;
      }
    }

    const selectedCityTag = document.getElementById('selectedCityTag');
    const selectedCityTagName = document.getElementById('selectedCityTagName');
    const locationBadge = document.getElementById('locationFilterBadgeCount');
    const allFiltersBadge = document.getElementById('allFiltersBadgeCount');
    const locationBtnText = document.getElementById('locationFilterBtnText');
    const jobTypeBtnText = document.getElementById('jobTypeFilterBtnText');
    const specialismBtnText = document.getElementById('specialismFilterBtnText');

    let activeFilterCount = 0;
    if (state.city) {
      activeFilterCount++;
      if (selectedCityTag) selectedCityTag.style.display = 'inline-flex';
      if (selectedCityTagName) selectedCityTagName.textContent = `${state.city.toLowerCase()}, karnataka`;
      if (locationBtnText) locationBtnText.textContent = state.city.toLowerCase();
    } else {
      if (selectedCityTag) selectedCityTag.style.display = 'none';
      if (locationBtnText) locationBtnText.textContent = 'location';
    }

    if (state.jobType && state.jobType !== 'all') {
      activeFilterCount++;
      if (jobTypeBtnText) jobTypeBtnText.textContent = state.jobType === 'FULL_TIME' ? 'full-time' : 'internships';
    } else {
      if (jobTypeBtnText) jobTypeBtnText.textContent = 'job types';
    }

    if (state.category && state.category !== 'all') {
      activeFilterCount++;
      if (specialismBtnText) specialismBtnText.textContent = state.category;
    } else {
      if (specialismBtnText) specialismBtnText.textContent = 'professional field';
    }

    if (locationBadge) locationBadge.textContent = state.city ? '1' : '0';
    if (allFiltersBadge) allFiltersBadge.textContent = activeFilterCount.toString();
  }

  function setupViewToggle() {
    const btnList = document.querySelector('[data-locator-id="joblisting_toggle_listview"]');
    const btnGrid = document.querySelector('[data-locator-id="joblisting_toggle_sortview"]');

    if (btnList && btnGrid) {
      btnList.addEventListener('click', (e) => {
        e.preventDefault();
        state.viewMode = 'list';
        btnList.setAttribute('aria-pressed', 'true');
        btnList.classList.add('rel_bg-trigger-active');
        btnGrid.setAttribute('aria-pressed', 'false');
        btnGrid.classList.remove('rel_bg-trigger-active');
        if (jobsGrid) jobsGrid.classList.add('is-list-view');
      });

      btnGrid.addEventListener('click', (e) => {
        e.preventDefault();
        state.viewMode = 'grid';
        btnGrid.setAttribute('aria-pressed', 'true');
        btnGrid.classList.add('rel_bg-trigger-active');
        btnList.setAttribute('aria-pressed', 'false');
        btnList.classList.remove('rel_bg-trigger-active');
        if (jobsGrid) jobsGrid.classList.remove('is-list-view');
      });
    }
  }

  function setupFilterPopovers() {
    const popoverLocation = document.getElementById('popoverLocation');
    const popoverJobType = document.getElementById('popoverJobType');
    const popoverSpecialism = document.getElementById('popoverSpecialism');
    const modalAllFilters = document.getElementById('modalAllFilters');

    function closeAllPopovers() {
      if (popoverLocation) popoverLocation.style.display = 'none';
      if (popoverJobType) popoverJobType.style.display = 'none';
      if (popoverSpecialism) popoverSpecialism.style.display = 'none';
    }

    document.querySelectorAll('[data-close-popover]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAllPopovers();
      });
    });

    const btnFilterLocation = document.querySelector('[data-locator-id="searchjobs_filters_location"]');
    if (btnFilterLocation && popoverLocation) {
      btnFilterLocation.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popoverLocation.style.display === 'block';
        closeAllPopovers();
        popoverLocation.style.display = isOpen ? 'none' : 'block';
      });
    }

    const btnFilterJobType = document.querySelector('[data-locator-id="searchjobs_filters_jobType"]');
    if (btnFilterJobType && popoverJobType) {
      btnFilterJobType.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popoverJobType.style.display === 'block';
        closeAllPopovers();
        popoverJobType.style.display = isOpen ? 'none' : 'block';
      });
    }

    const btnFilterSpecialism = document.querySelector('[data-locator-id="searchjobs_filters_specialism"]');
    if (btnFilterSpecialism && popoverSpecialism) {
      btnFilterSpecialism.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = popoverSpecialism.style.display === 'block';
        closeAllPopovers();
        popoverSpecialism.style.display = isOpen ? 'none' : 'block';
      });
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.rel_filter_dropdown_wrapper') && !e.target.closest('.rel_popover')) {
        closeAllPopovers();
      }
    });

    if (popoverLocation) {
      popoverLocation.querySelectorAll('[data-city]').forEach(opt => {
        opt.addEventListener('click', (e) => {
          e.preventDefault();
          popoverLocation.querySelectorAll('[data-city]').forEach(b => b.classList.remove('active'));
          opt.classList.add('active');
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
          popoverJobType.querySelectorAll('[data-job-type]').forEach(b => b.classList.remove('active'));
          opt.classList.add('active');
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
          popoverSpecialism.querySelectorAll('[data-category]').forEach(b => b.classList.remove('active'));
          opt.classList.add('active');
          state.category = opt.dataset.category;
          state.page = 1;
          closeAllPopovers();
          loadJobs();
        });
      });
    }

    const btnAllFilters = document.querySelector('[data-locator-id="searchjobs_filters_allFilters"]');
    const btnMobileFilters = document.querySelector('[data-rs-modal-trigger="mobile-filters"]');
    const btnCloseAllFilters = document.getElementById('btnCloseAllFilters');
    const btnResetModal = document.getElementById('btnResetModalFilters');
    const btnApplyModal = document.getElementById('btnApplyModalFilters');

    function openModal() {
      if (modalAllFilters) modalAllFilters.style.display = 'flex';
    }
    function closeModal() {
      if (modalAllFilters) modalAllFilters.style.display = 'none';
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
          modalAllFilters.querySelectorAll('#modalLocationChips [data-city]').forEach(x => x.classList.remove('active'));
          b.classList.add('active');
          state.city = b.dataset.city;
        });
      });

      modalAllFilters.querySelectorAll('#modalJobTypeChips [data-job-type]').forEach(b => {
        b.addEventListener('click', () => {
          modalAllFilters.querySelectorAll('#modalJobTypeChips [data-job-type]').forEach(x => x.classList.remove('active'));
          b.classList.add('active');
          state.jobType = b.dataset.jobType;
        });
      });

      modalAllFilters.querySelectorAll('#modalCategoryChips [data-category]').forEach(b => {
        b.addEventListener('click', () => {
          modalAllFilters.querySelectorAll('#modalCategoryChips [data-category]').forEach(x => x.classList.remove('active'));
          b.classList.add('active');
          state.category = b.dataset.category;
        });
      });

      modalAllFilters.querySelectorAll('#modalSortChips [data-sort]').forEach(b => {
        b.addEventListener('click', () => {
          modalAllFilters.querySelectorAll('#modalSortChips [data-sort]').forEach(x => x.classList.remove('active'));
          b.classList.add('active');
          state.sort = b.dataset.sort;
          if (sortSelect) sortSelect.value = b.dataset.sort === 'newest' ? 'Date' : 'Relevance';
        });
      });
    }

    if (btnApplyModal) {
      btnApplyModal.addEventListener('click', () => {
        closeModal();
        state.page = 1;
        loadJobs();
      });
    }

    if (btnResetModal) {
      btnResetModal.addEventListener('click', () => {
        state.city = '';
        state.jobType = 'all';
        state.category = 'all';
        state.page = 1;
        if (modalAllFilters) {
          modalAllFilters.querySelectorAll('.rel_chip').forEach(c => c.classList.remove('active'));
          const defCity = modalAllFilters.querySelector('#modalLocationChips [data-city=""]');
          const defType = modalAllFilters.querySelector('#modalJobTypeChips [data-job-type="all"]');
          const defCat = modalAllFilters.querySelector('#modalCategoryChips [data-category="all"]');
          if (defCity) defCity.classList.add('active');
          if (defType) defType.classList.add('active');
          if (defCat) defCat.classList.add('active');
        }
        closeModal();
        loadJobs();
      });
    }

    const btnClearCityTag = document.getElementById('btnClearCityTag');
    if (btnClearCityTag) {
      btnClearCityTag.addEventListener('click', (e) => {
        e.preventDefault();
        state.city = '';
        state.page = 1;
        loadJobs();
      });
    }

    const btnClearAllFilters = document.getElementById('btnClearAllFilters');
    if (btnClearAllFilters) {
      btnClearAllFilters.addEventListener('click', (e) => {
        e.preventDefault();
        state.city = '';
        state.category = 'all';
        state.jobType = 'all';
        state.searchQuery = '';
        state.isTodayOnly = false;
        state.sort = 'newest';
        state.page = 1;
        if (searchInput) searchInput.value = '';
        if (sortSelect) sortSelect.value = '';
        loadJobs();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val === 'Date' || val === '' || val === 'newest') {
          state.sort = 'newest';
        } else if (val === 'Proximity' || val === 'Relevance') {
          state.sort = 'deadline';
        } else {
          state.sort = val;
        }
        state.page = 1;
        loadJobs();
      });
    }

    document.querySelectorAll('[data-locator-id="searchjobs_search_savedSearchAlertButton"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        showToast('🔔 Search saved! You will receive daily alerts for matching jobs.', 'success');
      });
    });
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



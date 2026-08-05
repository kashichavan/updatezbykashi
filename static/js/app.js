// Kashii Updatez - Global Engine with Category Navigation & Paginated Job Feed
document.addEventListener('DOMContentLoaded', () => {
  const isHomePage = window.location.pathname === '/' || window.location.pathname === '';
  const isCategoryPage = window.location.pathname.startsWith('/category/');

  const state = {
    searchQuery: '',
    category: window.CATEGORY_SLUG_OVERRIDE || 'all',
    jobType: 'all',
    sort: 'newest',
    page: 1,
    pageSize: isHomePage ? 3 : 6, // Show top 3 on homepage, 6 on category pages
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
    loadYouTubeMarquee();

    if (isHomePage || isCategoryPage) {
      if (isHomePage) startTypewriter();

      const urlParams = new URLSearchParams(window.location.search);
      const categoryParam = urlParams.get('category');
      if (categoryParam && !window.CATEGORY_SLUG_OVERRIDE) {
        state.category = categoryParam;
      }

      loadJobs();
      setupHomePageListeners();
      startCountdownTimer();
    }
  }

  // --- DYNAMIC REAL YOUTUBE 3D MARQUEE ENGINE ---

  async function loadYouTubeMarquee() {
    const track = document.getElementById('ytMarqueeTrack');
    if (!track) return;

    try {
      const res = await fetch('/api/youtube/videos/');
      const data = await res.json();
      const videos = data.videos || [];

      if (videos.length === 0) return;

      const doubleVideos = [...videos, ...videos, ...videos];

      track.innerHTML = doubleVideos.map(v => `
        <a href="${escapeHtml(v.watch_url)}" target="_blank" rel="noopener" class="client-card-3d" title="${escapeHtml(v.title)}">
          <img src="${escapeHtml(v.thumbnail_url)}" alt="${escapeHtml(v.title)}" loading="lazy">
          <div class="yt-play-overlay">▶</div>
          <div class="yt-title-bar">${escapeHtml(v.title)}</div>
        </a>
      `).join('');

    } catch (err) {
      console.error('Failed to load YouTube marquee:', err);
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
      state.categories = data.categories;

      if (categorySelect) {
        categorySelect.innerHTML = '<option value="all">All Categories</option>' +
          data.categories.map(c => `<option value="${c.slug}" ${state.category === c.slug ? 'selected' : ''}>${c.name} (${c.active_count})</option>`).join('');
      }

      if (drawerCategoryNav) {
        drawerCategoryNav.innerHTML = data.categories.map(c => `
          <a href="/category/${c.slug}/" class="drawer-link" data-slug="${c.slug}">
            <span>${escapeHtml(c.name)}</span>
            <span class="d-tag">${c.active_count} OPEN</span>
          </a>
        `).join('');
      }

    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }

  // --- PAGINATED JOBS ENGINE ---

  async function loadJobs() {
    if (!jobsGrid) return;

    try {
      jobsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem;">
          <div style="font-size: 14px; font-weight: 700; color: var(--blue-primary);">Syncing active 3-day student opportunities...</div>
        </div>`;

      const params = new URLSearchParams({
        q: state.searchQuery,
        category: state.category,
        job_type: state.jobType,
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

  function renderJobs(jobs) {
    if (!jobsGrid) return;

    if (!jobs || jobs.length === 0) {
      jobsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; background: #ffffff; border-radius: 16px; border: 1px solid var(--subtle-border);">
          <h3 style="font-family: var(--font-serif); font-size: 20px; margin-bottom: 6px;">No active opportunities</h3>
          <p style="color: var(--muted); font-size: 14px;">Postings older than 3 days automatically deactivate.</p>
        </div>`;
      return;
    }

    jobsGrid.innerHTML = jobs.map(j => {
      const formattedTime = formatTimeLeft(j.time_left_seconds);
      const skillsHtml = j.skills_list.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
      const isDeactivated = j.status === 'EXPIRED' || j.time_left_seconds <= 0;

      return `
        <div class="vp-product-card" data-id="${j.id}">
          <div class="vp-card-header">
            <span class="company-badge">${escapeHtml(j.company_name)}</span>
            <span class="type-badge">${j.job_type_display}</span>
          </div>

          <div class="vp-card-content">
            <h3>${escapeHtml(j.title)}</h3>
            
            <div class="vp-salary-row">
              <span>💵 ${escapeHtml(j.stipend_salary)}</span>
              <span style="color: var(--muted); font-weight: 500;">📍 ${escapeHtml(j.location)}</span>
            </div>

            <p>${escapeHtml(j.description)}</p>

            <div class="skills-wrapper">
              ${skillsHtml}
            </div>

            <div class="vp-price-row">
              <div class="timer-tag" data-timer="${j.id}" data-seconds="${j.time_left_seconds}">
                ⏱️ <span>${isDeactivated ? 'Deactivated (3-Day Limit)' : formattedTime}</span>
              </div>

              <div style="display: flex; gap: 6px;">
                ${j.apply_url && !isDeactivated ? `
                  <a href="${escapeHtml(j.apply_url)}" target="_blank" rel="noopener" class="button button-dark" style="padding: 7px 14px; font-size: 12px;" onclick="event.stopPropagation();">
                    Apply via Link ↗
                  </a>
                ` : `
                  <button class="button button-dark" disabled style="opacity: 0.5; padding: 7px 14px; font-size: 12px;">
                    Deactivated
                  </button>
                `}
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    document.querySelectorAll('.vp-product-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.dataset.id;
        state.activeJobId = id;
        loadJobDetail(id);
      });
    });
  }

  // --- RENDER PAGINATION CONTROLS ---

  function renderPagination() {
    if (!paginationContainer) return;

    if (state.totalPages <= 1) {
      paginationContainer.innerHTML = `
        <div style="font-size: 13px; font-weight: 600; color: var(--muted);">
          Showing all ${state.totalCount} active student requirements
        </div>`;
      return;
    }

    const startNum = (state.page - 1) * state.pageSize + 1;
    const endNum = Math.min(state.totalCount, state.page * state.pageSize);

    let pagesHtml = '';
    for (let p = 1; p <= state.totalPages; p++) {
      pagesHtml += `
        <button class="pag-page-btn ${p === state.page ? 'active' : ''}" data-page="${p}">
          ${p}
        </button>
      `;
    }

    paginationContainer.innerHTML = `
      <div style="font-size: 13px; font-weight: 600; color: var(--muted);">
        Showing <strong>${startNum}–${endNum}</strong> of <strong>${state.totalCount}</strong> active student requirements
      </div>

      <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        <button class="pag-btn" id="btnPrevPage" ${state.page <= 1 ? 'disabled' : ''}>
          ‹ Previous
        </button>

        <div style="display: flex; gap: 6px;">
          ${pagesHtml}
        </div>

        <button class="pag-btn" id="btnNextPage" ${state.page >= state.totalPages ? 'disabled' : ''}>
          Next ›
        </button>
      </div>
    `;

    // Event Listeners for Pagination Buttons
    const btnPrev = document.getElementById('btnPrevPage');
    if (btnPrev && state.page > 1) {
      btnPrev.addEventListener('click', () => {
        state.page--;
        scrollAndLoadJobs();
      });
    }

    const btnNext = document.getElementById('btnNextPage');
    if (btnNext && state.page < state.totalPages) {
      btnNext.addEventListener('click', () => {
        state.page++;
        scrollAndLoadJobs();
      });
    }

    paginationContainer.querySelectorAll('.pag-page-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetPage = parseInt(btn.dataset.page);
        if (targetPage !== state.page) {
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

    detailModal.classList.add('active');
  }

  function setupHomePageListeners() {
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

    // Category Tabs redirect to dedicated page /category/<slug>/
    document.querySelectorAll('.vp-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const targetCategory = tab.dataset.category;
        if (targetCategory === 'all') {
          window.location.href = '/';
        } else {
          window.location.href = `/category/${targetCategory}/`;
        }
      });
    });

    if (categorySelect) {
      categorySelect.addEventListener('change', (e) => {
        const slug = e.target.value;
        if (slug === 'all') {
          window.location.href = '/';
        } else {
          window.location.href = `/category/${slug}/`;
        }
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
          el.querySelector('span').textContent = 'Deactivated (3-Day Limit)';
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

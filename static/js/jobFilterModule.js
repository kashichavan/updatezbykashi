// jobFilterModule.js
function initializeJobFilters(config) {
    const {
        mainSearchInputId,
        moreFiltersBtnId,
        moreFiltersModalId,
        btnCloseMoreFiltersModalId,
        applyFiltersBtnId,
        clearFiltersBtnId,
        activeFiltersContainerId,
        filterLocationInputId,
        selectedLocationsContainerId,
        filterCompanyInputId,
        selectedCompaniesContainerId,
        filterMinExperienceId,
        filterMaxExperienceId,
        filterJobTypeModalId,
        filterSortModalId,
        jobsGridId,
        fetchJobsApiCallback, // User-provided function to fetch jobs from their API
        renderJobCardCallback // User-provided function to render a single job card
    } = config;

    const mainSearchInput = document.getElementById(mainSearchInputId);
    const moreFiltersBtn = document.getElementById(moreFiltersBtnId);
    const moreFiltersModal = document.getElementById(moreFiltersModalId);
    const btnCloseMoreFiltersModal = document.getElementById(btnCloseMoreFiltersModalId);
    const applyFiltersBtn = document.getElementById(applyFiltersBtnId);
    const clearFiltersBtn = document.getElementById(clearFiltersBtnId);
    const activeFiltersContainer = document.getElementById(activeFiltersContainerId);

    const filterLocationInput = document.getElementById(filterLocationInputId);
    const selectedLocationsContainer = document.getElementById(selectedLocationsContainerId);
    const filterCompanyInput = document.getElementById(filterCompanyInputId);
    const selectedCompaniesContainer = document.getElementById(selectedCompaniesContainerId);
    const filterMinExperience = document.getElementById(filterMinExperienceId);
    const filterMaxExperience = document.getElementById(filterMaxExperienceId);
    const filterJobTypeModal = document.getElementById(filterJobTypeModalId);
    const filterSortModal = document.getElementById(filterSortModalId);
    const jobsGrid = document.getElementById(jobsGridId);

    let activeFilters = {
        mainSearch: '',
        locations: [],
        companies: [],
        minExperience: '',
        maxExperience: '',
        jobType: 'all',
        sortBy: 'newest'
    };

    // --- Modal Visibility ---
    moreFiltersBtn.addEventListener('click', () => {
        moreFiltersModal.style.display = 'block';
        filterMinExperience.value = activeFilters.minExperience;
        filterMaxExperience.value = activeFilters.maxExperience;
        filterJobTypeModal.value = activeFilters.jobType;
        filterSortModal.value = activeFilters.sortBy;
        renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location');
        renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company');
    });

    btnCloseMoreFiltersModal.addEventListener('click', () => {
        moreFiltersModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === moreFiltersModal) {
            moreFiltersModal.style.display = 'none';
        }
    });

    // --- Main Search Input ---
    mainSearchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            activeFilters.mainSearch = mainSearchInput.value.trim();
            fetchJobsWrapper(activeFilters);
            renderActiveFiltersDisplay();
        }
    });
    mainSearchInput.addEventListener('blur', () => {
        const currentValue = mainSearchInput.value.trim();
        if (activeFilters.mainSearch !== currentValue) {
            activeFilters.mainSearch = currentValue;
            renderActiveFiltersDisplay();
            fetchJobsWrapper(activeFilters);
        }
    });

    // --- Tag Management Function ---
    function createTag(text, type, value = text) {
        const tag = document.createElement('span');
        tag.className = 'filter-tag'; // Using inline styles for portability
        tag.style.cssText = 'display: inline-flex; align-items: center; background: #e0f2fe; color: #0284c7; padding: 4px 10px; border-radius: 5px; font-size: 13px; margin-right: 6px; margin-bottom: 6px; border: 1px solid #bfdbfe; font-weight: 600;';
        tag.innerHTML = `${text} <button data-type="${type}" data-value="${value}" class="remove-tag-btn" style="background: none; border: none; color: #0284c7; margin-left: 8px; cursor: pointer; font-size: 14px; line-height: 1; padding: 0;">✕</button>`;
        return tag;
    }

    function renderSelectedTags(container, items, type) {
        container.innerHTML = '';
        items.forEach(item => {
            container.appendChild(createTag(item, type, item));
        });
    }

    // --- Add Location/Company on Enter/Blur ---
    filterLocationInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && filterLocationInput.value.trim() !== '') {
            const value = filterLocationInput.value.trim();
            if (!activeFilters.locations.includes(value)) {
                activeFilters.locations.push(value);
                renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location');
            }
            filterLocationInput.value = '';
            event.preventDefault();
        }
    });
    filterLocationInput.addEventListener('blur', () => {
        const value = filterLocationInput.value.trim();
        if (value !== '' && !activeFilters.locations.includes(value)) {
            activeFilters.locations.push(value);
            renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location');
        }
        filterLocationInput.value = '';
    });

    filterCompanyInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && filterCompanyInput.value.trim() !== '') {
            const value = filterCompanyInput.value.trim();
            if (!activeFilters.companies.includes(value)) {
                activeFilters.companies.push(value);
                renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company');
            }
            filterCompanyInput.value = '';
            event.preventDefault();
        }
    });
    filterCompanyInput.addEventListener('blur', () => {
        const value = filterCompanyInput.value.trim();
        if (value !== '' && !activeFilters.companies.includes(value)) {
            activeFilters.companies.push(value);
            renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company');
        }
        filterCompanyInput.value = '';
    });

    // --- Remove Tag ---
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-tag-btn')) {
            const type = event.target.dataset.type;
            const value = event.target.dataset.value;

            if (type === 'location') {
                activeFilters.locations = activeFilters.locations.filter(loc => loc !== value);
                renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location');
            } else if (type === 'company') {
                activeFilters.companies = activeFilters.companies.filter(comp => comp !== value);
                renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company');
            } else if (type === 'mainSearch') {
                activeFilters.mainSearch = '';
                mainSearchInput.value = '';
            } else if (type === 'experience') {
                activeFilters.minExperience = '';
                activeFilters.maxExperience = '';
                filterMinExperience.value = '';
                filterMaxExperience.value = '';
            } else if (type === 'jobType') {
                activeFilters.jobType = 'all';
                filterJobTypeModal.value = 'all';
            } else if (type === 'sortBy') {
                activeFilters.sortBy = 'newest';
                filterSortModal.value = 'newest';
            }
            
            renderActiveFiltersDisplay();
            fetchJobsWrapper(activeFilters);
        }
    });

    // --- Apply Filters ---
    applyFiltersBtn.addEventListener('click', () => {
        activeFilters.minExperience = filterMinExperience.value.trim();
        activeFilters.maxExperience = filterMaxExperience.value.trim();
        activeFilters.jobType = filterJobTypeModal.value;
        activeFilters.sortBy = filterSortModal.value;

        moreFiltersModal.style.display = 'none';
        renderActiveFiltersDisplay();
        fetchJobsWrapper(activeFilters);
    });

    // --- Clear All Filters ---
    clearFiltersBtn.addEventListener('click', () => {
        activeFilters = {
            mainSearch: '',
            locations: [],
            companies: [],
            minExperience: '',
            maxExperience: '',
            jobType: 'all',
            sortBy: 'newest'
        };
        mainSearchInput.value = '';
        filterLocationInput.value = '';
        selectedLocationsContainer.innerHTML = '';
        filterCompanyInput.value = '';
        selectedCompaniesContainer.innerHTML = '';
        filterMinExperience.value = '';
        filterMaxExperience.value = '';
        filterJobTypeModal.value = 'all';
        filterSortModal.value = 'newest';

        renderActiveFiltersDisplay();
        fetchJobsWrapper(activeFilters);
    });

    // --- Render Active Filters Display Below Search Bar ---
    function renderActiveFiltersDisplay() {
        activeFiltersContainer.innerHTML = '';

        const allAppliedFilters = [];

        if (activeFilters.mainSearch) {
            allAppliedFilters.push(createTag(activeFilters.mainSearch, 'mainSearch', activeFilters.mainSearch));
        }

        activeFilters.locations.forEach(loc => {
            allAppliedFilters.push(createTag(`Location: ${loc}`, 'location', loc));
        });
        activeFilters.companies.forEach(comp => {
            allAppliedFilters.push(createTag(`Company: ${comp}`, 'company', comp));
        });
        if (activeFilters.minExperience || activeFilters.maxExperience) {
            let expText = 'Experience: ';
            if (activeFilters.minExperience && activeFilters.maxExperience) {
                expText += `${activeFilters.minExperience}-${activeFilters.maxExperience} Yrs`;
            } else if (activeFilters.minExperience) {
                expText += `${activeFilters.minExperience}+ Yrs`;
            } else {
                expText += `Up to ${activeFilters.maxExperience} Yrs`;
            }
            allAppliedFilters.push(createTag(expText, 'experience', ''));
        }
        if (activeFilters.jobType !== 'all') {
            const selectedOption = filterJobTypeModal.querySelector(`option[value="${activeFilters.jobType}"]`);
            if (selectedOption) {
                allAppliedFilters.push(createTag(`Type: ${selectedOption.text}`, 'jobType', activeFilters.jobType));
            }
        }
        if (activeFilters.sortBy !== 'newest') {
            const selectedOption = filterSortModal.querySelector(`option[value="${activeFilters.sortBy}"]`);
            if (selectedOption) {
                allAppliedFilters.push(createTag(`Sort: ${selectedOption.text}`, 'sortBy', activeFilters.sortBy));
            }
        }

        allAppliedFilters.forEach(tag => activeFiltersContainer.appendChild(tag));

        if (allAppliedFilters.length === 0 && !activeFilters.mainSearch) {
            activeFiltersContainer.innerHTML = '<span style="color: #94a3b8; font-size: 13px;">No filters applied.</span>';
        }
    }

    // --- Job Rendering Logic ---
    function showLoadingIndicator() {
        jobsGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748b; font-size: 16px;">Loading jobs...</div>';
    }

    function renderJobs(jobs) {
        jobsGrid.innerHTML = '';
        if (jobs.length === 0) {
            jobsGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748b; font-size: 16px;">No jobs found matching your criteria.</div>';
            return;
        }
        jobs.forEach(job => {
            const jobCard = renderJobCardCallback(job); // Use user-provided callback
            jobsGrid.appendChild(jobCard);
        });
    }

    async function fetchJobsWrapper(filters) {
        showLoadingIndicator();
        console.log('Fetching jobs with filters:', filters);
        try {
            const jobs = await fetchJobsApiCallback(filters); // Call user-provided API function
            renderJobs(jobs);
            console.log('Jobs rendered successfully.');
        } catch (error) {
            console.error('Error fetching jobs:', error);
            jobsGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #dc2626; font-size: 16px;">Failed to load jobs. Please try again.</div>';
        }
    }

    // Initial fetch of jobs on page load
    fetchJobsWrapper(activeFilters);
    renderActiveFiltersDisplay();
}

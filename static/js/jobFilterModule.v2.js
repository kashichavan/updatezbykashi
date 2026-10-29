// jobFilterModule.v2.js

function initializeJobFiltersV2(config) {
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
        moreFiltersModal.style.display = 'flex'; // Use flex for centering
        filterMinExperience.value = activeFilters.minExperience;
        filterMaxExperience.value = activeFilters.maxExperience;
        filterJobTypeModal.value = activeFilters.jobType;
        filterSortModal.value = activeFilters.sortBy;
        renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'filter-tag-v2', 'remove-tag-btn-v2');
        renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'filter-tag-v2', 'remove-tag-btn-v2');
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
    function createTag(text, type, value = text, tagClass = 'filter-tag-v2', removeBtnClass = 'remove-tag-btn-v2') {
        const tag = document.createElement('span');
        tag.className = tagClass;
        tag.innerHTML = `${text} <button data-type="${type}" data-value="${value}" class="${removeBtnClass}">✕</button>`;
        return tag;
    }

    function renderSelectedTags(container, items, type, tagClass, removeBtnClass) {
        container.innerHTML = '';
        items.forEach(item => {
            container.appendChild(createTag(item, type, item, tagClass, removeBtnClass));
        });
    }

    // --- Add Location/Company on Enter/Blur ---
    filterLocationInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && filterLocationInput.value.trim() !== '') {
            const value = filterLocationInput.value.trim();
            if (!activeFilters.locations.includes(value)) {
                activeFilters.locations.push(value);
                renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'filter-tag-v2', 'remove-tag-btn-v2');
            }
            filterLocationInput.value = '';
            event.preventDefault();
        }
    });
    filterLocationInput.addEventListener('blur', () => {
        const value = filterLocationInput.value.trim();
        if (value !== '' && !activeFilters.locations.includes(value)) {
            activeFilters.locations.push(value);
            renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'filter-tag-v2', 'remove-tag-btn-v2');
        }
        filterLocationInput.value = '';
    });

    filterCompanyInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && filterCompanyInput.value.trim() !== '') {
            const value = filterCompanyInput.value.trim();
            if (!activeFilters.companies.includes(value)) {
                activeFilters.companies.push(value);
                renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'filter-tag-v2', 'remove-tag-btn-v2');
            }
            filterCompanyInput.value = '';
            event.preventDefault();
        }
    });
    filterCompanyInput.addEventListener('blur', () => {
        const value = filterCompanyInput.value.trim();
        if (value !== '' && !activeFilters.companies.includes(value)) {
            activeFilters.companies.push(value);
            renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'filter-tag-v2', 'remove-tag-btn-v2');
        }
        filterCompanyInput.value = '';
    });

    // --- Remove Tag ---
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-tag-btn-v2')) {
            const type = event.target.dataset.type;
            const value = event.target.dataset.value;

            if (type === 'location') {
                activeFilters.locations = activeFilters.locations.filter(loc => loc !== value);
                renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'filter-tag-v2', 'remove-tag-btn-v2');
            } else if (type === 'company') {
                activeFilters.companies = activeFilters.companies.filter(comp => comp !== value);
                renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'filter-tag-v2', 'remove-tag-btn-v2');
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
            allAppliedFilters.push(createTag(activeFilters.mainSearch, 'mainSearch', activeFilters.mainSearch, 'filter-tag-v2', 'remove-tag-btn-v2'));
        }

        activeFilters.locations.forEach(loc => {
            allAppliedFilters.push(createTag(`Location: ${loc}`, 'location', loc, 'filter-tag-v2', 'remove-tag-btn-v2'));
        });
        activeFilters.companies.forEach(comp => {
            allAppliedFilters.push(createTag(`Company: ${comp}`, 'company', comp, 'filter-tag-v2', 'remove-tag-btn-v2'));
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
            allAppliedFilters.push(createTag(expText, 'experience', '', 'filter-tag-v2', 'remove-tag-btn-v2'));
        }
        if (activeFilters.jobType !== 'all') {
            const selectedOption = filterJobTypeModal.querySelector(`option[value="${activeFilters.jobType}"]`);
            if (selectedOption) {
                allAppliedFilters.push(createTag(`Type: ${selectedOption.text}`, 'jobType', activeFilters.jobType, 'filter-tag-v2', 'remove-tag-btn-v2'));
            }
        }
        if (activeFilters.sortBy !== 'newest') {
            const selectedOption = filterSortModal.querySelector(`option[value="${activeFilters.sortBy}"]`);
            if (selectedOption) {
                allAppliedFilters.push(createTag(`Sort: ${selectedOption.text}`, 'sortBy', activeFilters.sortBy, 'filter-tag-v2', 'remove-tag-btn-v2'));
            }
        }

        allAppliedFilters.forEach(tag => activeFiltersContainer.appendChild(tag));

        if (allAppliedFilters.length === 0 && !activeFilters.mainSearch) {
            activeFiltersContainer.innerHTML = '<span style="color: var(--color-text-muted);">No filters applied.</span>';
        }
    }

    // --- Job Rendering Logic ---
    function showLoadingIndicator() {
        jobsGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--color-text-muted); font-size: 16px;">Loading jobs...</div>';
    }

    function renderJobs(jobs) {
        jobsGrid.innerHTML = '';
        if (jobs.length === 0) {
            jobsGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--color-text-muted); font-size: 16px;">No jobs found matching your criteria.</div>';
            return;
        }
        jobs.forEach(job => {
            const jobCard = renderJobCardCallback(job); // Use user-provided callback
            jobsGrid.appendChild(jobCard);
        });
    }

    async function fetchJobsWrapper(filters) {
        showLoadingIndicator();
        console.log('Fetching jobs with filters (V2):', filters);
        try {
            const jobs = await fetchJobsApiCallback(filters); // Call user-provided API function
            renderJobs(jobs);
            console.log('Jobs rendered successfully (V2).');
        } catch (error) {
            console.error('Error fetching jobs (V2):', error);
            jobsGrid.innerHTML = '<div style="text-align: center; padding: 40px; color: #dc2626; font-size: 16px;">Failed to load jobs. Please try again.</div>';
        }
    }

    // Initial fetch of jobs on page load
    fetchJobsWrapper(activeFilters);
    renderActiveFiltersDisplay();
}

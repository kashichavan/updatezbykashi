// jobFilterModule.v3.js

function initializeJobFiltersV3(config) {
    const {
        mainSearchInputId,
        moreFiltersToggleId,
        filterPanelId,
        filterPanelCloseId,
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
    const moreFiltersToggle = document.getElementById(moreFiltersToggleId);
    const filterPanel = document.getElementById(filterPanelId);
    const filterPanelClose = document.getElementById(filterPanelCloseId);
    const applyFiltersBtn = document.getElementById(applyFiltersBtnId);
    const clearFiltersBtn = document.getElementById(clearFiltersBtnId);
    const activeFiltersContainer = document.getElementById(activeFiltersContainerId);

    const filterLocationInput = document.getElementById(filterLocationInputId);
    const selectedLocationsContainer = document.getElementById(selectedLocationsContainerId);
    const filterCompanyInput = document.getElementById(filterCompanyInputId);
    const selectedCompaniesContainer = document.getElementById(selectedCompaniesContainerId);
    const filterMinExperience = document.getElementById(filterMinExperienceId);
    const filterMaxExperience = document.getElementById(filterMaxExperienceId);
    const filterJobType = document.getElementById(filterJobTypeModalId);
    const filterSort = document.getElementById(filterSortModalId);
    const jobsGrid = document.getElementById(jobsGridId);
    const filterCategoriesContainer = document.getElementById('filterCategoriesV3'); // New: Category chips container

    let activeFilters = {
        mainSearch: '',
        locations: [],
        companies: [],
        minExperience: '',
        maxExperience: '',
        jobType: 'all',
        sortBy: 'newest',
        categories: [] // New: to store active category filters
    };

    // --- Filter Panel Visibility ---
    moreFiltersToggle.addEventListener('click', () => {
        filterPanel.classList.toggle('is-open');
        if (filterPanel.classList.contains('is-open')) {
            updateCategoryChipsVisualState(); // Update visual state when panel opens
        }
    });

    filterPanelClose.addEventListener('click', () => {
        filterPanel.classList.remove('is-open');
    });

    // --- Category Chip Selection ---
    filterCategoriesContainer.addEventListener('click', (event) => {
        const clickedChip = event.target.closest('.category-chip-v3');
        if (!clickedChip) return;

        const categoryValue = clickedChip.dataset.categoryValue;

        if (categoryValue === 'all') {
            // If 'All Opportunities' is clicked
            if (!clickedChip.classList.contains('is-active')) {
                // If it's not active, activate it and deactivate all others
                activeFilters.categories = [];
                filterCategoriesContainer.querySelectorAll('.category-chip-v3').forEach(chip => {
                    chip.classList.remove('is-active');
                });
                clickedChip.classList.add('is-active');
                // 'all' category itself is not added to activeFilters.categories
            } else {
                // If 'All Opportunities' is already active and clicked again, do nothing (it's always implicitly active if no other category is selected)
                return;
            }
        } else {
            // If any other category chip is clicked
            clickedChip.classList.toggle('is-active');

            // Update activeFilters.categories array
            if (clickedChip.classList.contains('is-active')) {
                activeFilters.categories.push(categoryValue);
            } else {
                activeFilters.categories = activeFilters.categories.filter(cat => cat !== categoryValue);
            }

            // If other categories are selected, 'All Opportunities' should be inactive
            const allOpportunitiesChip = filterCategoriesContainer.querySelector('[data-category-value="all"]');
            if (activeFilters.categories.length > 0) {
                allOpportunitiesChip.classList.remove('is-active');
            } else {
                // If no other categories are selected, 'All Opportunities' becomes active
                allOpportunitiesChip.classList.add('is-active');
            }
        }

        renderActiveFiltersDisplay();
        fetchJobsWrapper(activeFilters);
    });

    // Close panel if click outside (optional, depending on desired UX)
    document.addEventListener('click', (event) => {
        if (!filterPanel.contains(event.target) && !moreFiltersToggle.contains(event.target) && filterPanel.classList.contains('is-open')) {
            filterPanel.classList.remove('is-open');
        }
    });

    // --- Main Search Input ---
    mainSearchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            activeFilters.mainSearch = mainSearchInput.value.trim();
            fetchJobsWrapper(activeFilters);
            renderActiveFiltersDisplay();
            filterPanel.classList.remove('is-open'); // Close panel after search
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
    function createTag(text, type, value = text, tagClass = 'active-filter-tag-v3', removeBtnClass = 'remove-tag-btn-v3') {
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
                renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'active-filter-tag-v3', 'remove-tag-btn-v3');
            }
            filterLocationInput.value = '';
            event.preventDefault();
        }
    });
    filterLocationInput.addEventListener('blur', () => {
        const value = filterLocationInput.value.trim();
        if (value !== '' && !activeFilters.locations.includes(value)) {
            activeFilters.locations.push(value);
            renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'active-filter-tag-v3', 'remove-tag-btn-v3');
        }
        filterLocationInput.value = '';
    });

    filterCompanyInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && filterCompanyInput.value.trim() !== '') {
            const value = filterCompanyInput.value.trim();
            if (!activeFilters.companies.includes(value)) {
                activeFilters.companies.push(value);
                renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'active-filter-tag-v3', 'remove-tag-btn-v3');
            }
            filterCompanyInput.value = '';
            event.preventDefault();
        }
    });
    filterCompanyInput.addEventListener('blur', () => {
        const value = filterCompanyInput.value.trim();
        if (value !== '' && !activeFilters.companies.includes(value)) {
            activeFilters.companies.push(value);
            renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'active-filter-tag-v3', 'remove-tag-btn-v3');
        }
        filterCompanyInput.value = '';
    });

    // --- Remove Tag ---
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-tag-btn-v3')) {
            const type = event.target.dataset.type;
            const value = event.target.dataset.value;

            if (type === 'location') {
                activeFilters.locations = activeFilters.locations.filter(loc => loc !== value);
                renderSelectedTags(selectedLocationsContainer, activeFilters.locations, 'location', 'active-filter-tag-v3', 'remove-tag-btn-v3');
            } else if (type === 'company') {
                activeFilters.companies = activeFilters.companies.filter(comp => comp !== value);
                renderSelectedTags(selectedCompaniesContainer, activeFilters.companies, 'company', 'active-filter-tag-v3', 'remove-tag-btn-v3');
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
                filterJobType.value = 'all';
            } else if (type === 'sortBy') {
                activeFilters.sortBy = 'newest';
                filterSort.value = 'newest';
            }
            
            renderActiveFiltersDisplay();
            fetchJobsWrapper(activeFilters);
        }
    });

    // --- Apply Filters ---
    applyFiltersBtn.addEventListener('click', () => {
        activeFilters.minExperience = filterMinExperience.value.trim();
        activeFilters.maxExperience = filterMaxExperience.value.trim();
        activeFilters.jobType = filterJobType.value;
        activeFilters.sortBy = filterSort.value;

        filterPanel.classList.remove('is-open');
        renderActiveFiltersDisplay();
        updateCategoryChipsVisualState(); // New: Update visual state after applying
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
            sortBy: 'newest',
            categories: [] // New: Clear categories
        };
        mainSearchInput.value = '';
        filterLocationInput.value = '';
        selectedLocationsContainer.innerHTML = '';
        filterCompanyInput.value = '';
        selectedCompaniesContainer.innerHTML = '';
        filterMinExperience.value = '';
        filterMaxExperience.value = '';
        filterJobType.value = 'all';
        filterSort.value = 'newest';

        renderActiveFiltersDisplay();
        updateCategoryChipsVisualState(); // New: Update visual state after clearing
        fetchJobsWrapper(activeFilters);
    });

    // --- Render Active Filters Display Below Search Bar ---
    function renderActiveFiltersDisplay() {
        activeFiltersContainer.innerHTML = '';

        const allAppliedFilters = [];

        if (activeFilters.mainSearch) {
            allAppliedFilters.push(createTag(activeFilters.mainSearch, 'mainSearch', activeFilters.mainSearch, 'active-filter-tag-v3', 'remove-tag-btn-v3'));
        }

        activeFilters.locations.forEach(loc => {
            allAppliedFilters.push(createTag(`Location: ${loc}`, 'location', loc, 'active-filter-tag-v3', 'remove-tag-btn-v3'));
        });
        activeFilters.companies.forEach(comp => {
            allAppliedFilters.push(createTag(`Company: ${comp}`, 'company', comp, 'active-filter-tag-v3', 'remove-tag-btn-v3'));
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
            allAppliedFilters.push(createTag(expText, 'experience', '', 'active-filter-tag-v3', 'remove-tag-btn-v3'));
        }
        if (activeFilters.jobType !== 'all') {
            const selectedOption = filterJobType.querySelector(`option[value="${activeFilters.jobType}"]`);
            if (selectedOption) {
                allAppliedFilters.push(createTag(`Type: ${selectedOption.text}`, 'jobType', activeFilters.jobType, 'active-filter-tag-v3', 'remove-tag-btn-v3'));
            }
        }
        if (activeFilters.sortBy !== 'newest') {
            const selectedOption = filterSort.querySelector(`option[value="${activeFilters.sortBy}"]`);
            if (selectedOption) {
                allAppliedFilters.push(createTag(`Sort: ${selectedOption.text}`, 'sortBy', activeFilters.sortBy, 'active-filter-tag-v3', 'remove-tag-btn-v3'));
            }
        }

        activeFilters.categories.forEach(cat => {
            // Find the display text for the category from the actual chips
            const chipElement = filterCategoriesContainer.querySelector(`[data-category-value="${cat}"]`);
            const displayText = chipElement ? chipElement.textContent.trim() : cat;
            allAppliedFilters.push(createTag(`Category: ${displayText}`, 'category', cat, 'active-filter-tag-v3', 'remove-tag-btn-v3'));
        });

        allAppliedFilters.forEach(tag => activeFiltersContainer.appendChild(tag));

        if (allAppliedFilters.length === 0 && !activeFilters.mainSearch && activeFilters.categories.length === 0) {
            activeFiltersContainer.innerHTML = '<span style="color: var(--v3-color-text-muted);">No filters applied.</span>';
        }
    }

    // --- Update Category Chips Visual State ---
    function updateCategoryChipsVisualState() {
        const allChips = filterCategoriesContainer.querySelectorAll('.category-chip-v3');
        const allOpportunitiesChip = filterCategoriesContainer.querySelector('[data-category-value="all"]');

        allChips.forEach(chip => {
            const categoryValue = chip.dataset.categoryValue;
            if (activeFilters.categories.includes(categoryValue)) {
                chip.classList.add('is-active');
            } else {
                chip.classList.remove('is-active');
            }
        });

        // Ensure 'All Opportunities' state is correct
        if (activeFilters.categories.length === 0) {
            allOpportunitiesChip.classList.add('is-active');
        } else {
            allOpportunitiesChip.classList.remove('is-active');
        }
    }

    // --- Job Rendering Logic ---
    function showLoadingIndicator() {
        jobsGrid.innerHTML = '<div style="text-align: center; padding: 50px; color: var(--v3-color-text-muted); font-size: 17px;">Loading exquisite opportunities...</div>';
    }

    function renderJobs(jobs) {
        jobsGrid.innerHTML = '';
        if (jobs.length === 0) {
            jobsGrid.innerHTML = '<div style="text-align: center; padding: 50px; color: var(--v3-color-text-muted); font-size: 17px;">No impeccable opportunities found matching your criteria.</div>';
            return;
        }
        jobs.forEach(job => {
            const jobCard = renderJobCardCallback(job); // Use user-provided callback
            jobsGrid.appendChild(jobCard);
        });
    }

    async function fetchJobsWrapper(filters) {
        showLoadingIndicator();
        console.log('Fetching jobs with filters (V3):', filters);
        try {
            const jobs = await fetchJobsApiCallback(filters); // Call user-provided API function
            renderJobs(jobs);
            console.log('Jobs rendered successfully (V3).');
        } catch (error) {
            console.error('Error fetching jobs (V3):', error);
            jobsGrid.innerHTML = '<div style="text-align: center; padding: 50px; color: #dc2626; font-size: 17px;">Failed to load opportunities. Please refine your search.</div>';
        }
    }

    // Initial fetch of jobs on page load
    fetchJobsWrapper(activeFilters);
    renderActiveFiltersDisplay();
    updateCategoryChipsVisualState(); // New: Set initial visual state for category chips
}

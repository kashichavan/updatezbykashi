document.addEventListener('DOMContentLoaded', () => {
    const moreFiltersBtn = document.getElementById('moreFiltersBtn');
    const moreFiltersModal = document.getElementById('moreFiltersModal');
    const btnCloseMoreFiltersModal = document.getElementById('btnCloseMoreFiltersModal');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const activeFiltersContainer = document.getElementById('activeFiltersContainer');

    const mainSearchInput = document.getElementById('mainSearchInput');
    const filterLocationInput = document.getElementById('filterLocation');
    const selectedLocationsContainer = document.getElementById('selectedLocations');
    const filterCompanyInput = document.getElementById('filterCompany');
    const selectedCompaniesContainer = document.getElementById('selectedCompanies');
    const filterMinExperience = document.getElementById('filterMinExperience');
    const filterMaxExperience = document.getElementById('filterMaxExperience');
    const filterJobTypeModal = document.getElementById('filterJobTypeModal');
    const filterSortModal = document.getElementById('filterSortModal');

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
        // Pre-fill modal with current active filters
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
            fetchJobs(activeFilters);
            renderActiveFiltersDisplay();
        }
    });
    mainSearchInput.addEventListener('blur', () => {
        const currentValue = mainSearchInput.value.trim();
        if (activeFilters.mainSearch !== currentValue) {
            activeFilters.mainSearch = currentValue;
            renderActiveFiltersDisplay();
            fetchJobs(activeFilters);
        }
    });

    // --- Tag Management Function ---
    function createTag(text, type, value = text) {
        const tag = document.createElement('span');
        tag.className = 'filter-tag'; // Custom class for styling
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
            event.preventDefault(); // Prevent form submission
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
            fetchJobs(activeFilters);
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
        fetchJobs(activeFilters);
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
        fetchJobs(activeFilters);
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
            allAppliedFilters.push(createTag(expText, 'experience', '')); // Value can be empty for range
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
    const jobsGrid = document.getElementById('jobsGrid');

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
            const jobCard = document.createElement('a');
            jobCard.href = job.link;
            jobCard.target = '_blank';
            jobCard.rel = 'noopener';
            jobCard.className = 'job-card';
            jobCard.style.cssText = `
                background: var(--paper);
                border: 1px solid var(--subtle-border);
                border-radius: 16px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s;
                text-decoration: none;
                color: inherit;
                padding: 20px;
                position: relative;
                margin-bottom: 15px;
            `;
            jobCard.onmouseover = function() { this.style.transform='translateY(-4px)'; this.style.boxShadow='var(--hover-shadow)'; this.style.borderColor='var(--blue-primary)'; };
            jobCard.onmouseout = function() { this.style.transform=''; this.style.boxShadow='none'; this.style.borderColor='var(--subtle-border)'; };

            jobCard.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <span class="company-badge" style="background: rgba(99, 102, 241, 0.1); color: #4f46e5; padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 700; text-transform: uppercase;">${job.company}</span>
                    <span class="type-badge" style="background: rgba(16, 185, 129, 0.1); color: #059669; padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 700; text-transform: uppercase;">${job.jobType}</span>
                </div>
                <h4 style="font: 700 18px var(--font-sans); margin: 0 0 8px; color: var(--ink);">${job.title}</h4>
                <p style="font-size: 13px; color: var(--muted); margin: 0 0 12px; flex-grow: 1;">${job.description}</p>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: auto;">
                    ${job.skills.map(skill => `<span style="background: #f0f9ff; color: #0284c7; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${skill}</span>`).join('')}
                </div>
                <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--muted);">
                    <span>📅 ${job.postedDate}</span>
                    <span>📍 ${job.location}</span>
                </div>
            `;
            jobsGrid.appendChild(jobCard);
        });
    }

    // --- Simulate API Call (Replace with actual fetch in production) ---
    function fetchJobs(filters) {
        showLoadingIndicator();
        console.log('Fetching jobs with filters:', filters);

        // Simulate network delay
        setTimeout(() => {
            const dummyJobs = [
                {
                    title: 'Software Engineer Intern',
                    company: 'Tech Solutions Inc.',
                    jobType: 'Internship',
                    description: 'Develop and maintain web applications using React and Node.js. Work closely with senior engineers.',
                    skills: ['React', 'Node.js', 'JavaScript'],
                    postedDate: '2 days ago',
                    location: 'Bangalore, India',
                    experienceYears: 0,
                    link: 'https://example.com/job1'
                },
                {
                    title: 'Junior Python Developer',
                    company: 'Data Insights Co.',
                    jobType: 'Full-Time',
                    description: 'Build robust data pipelines and APIs. Experience with Django is a plus.',
                    skills: ['Python', 'Django', 'SQL'],
                    postedDate: '3 days ago',
                    location: 'Hyderabad, India',
                    experienceYears: 1,
                    link: 'https://example.com/job2'
                },
                {
                    title: 'QA Tester',
                    company: 'Quality First Ltd.',
                    jobType: 'Full-Time',
                    description: 'Execute test plans and identify bugs for our flagship product.',
                    skills: ['Manual Testing', 'JIRA'],
                    postedDate: '1 day ago',
                    location: 'Remote',
                    experienceYears: 2,
                    link: 'https://example.com/job3'
                },
                {
                    title: 'HR Recruiter',
                    company: 'People Connect Corp.',
                    jobType: 'Full-Time',
                    description: 'Manage the full recruitment cycle for technical roles.',
                    skills: ['Recruitment', 'ATS', 'Communication'],
                    postedDate: '5 days ago',
                    location: 'Mumbai, India',
                    experienceYears: 3,
                    link: 'https://example.com/job4'
                },
                {
                    title: 'Business Analyst Intern',
                    company: 'Strategy & Growth',
                    jobType: 'Internship',
                    description: 'Analyze market trends and provide strategic recommendations.',
                    skills: ['Market Research', 'Excel', 'Presentation'],
                    postedDate: '4 days ago',
                    location: 'Chennai, India',
                    experienceYears: 0,
                    link: 'https://example.com/job5'
                },
                {
                    title: 'Senior Java Developer',
                    company: 'Enterprise Solutions',
                    jobType: 'Full-Time',
                    description: 'Lead the development of scalable enterprise applications.',
                    skills: ['Java', 'Spring Boot', 'Microservices'],
                    postedDate: '1 week ago',
                    location: 'Bangalore, India',
                    experienceYears: 5,
                    link: 'https://example.com/job6'
                },
                {
                    title: 'DevOps Engineer',
                    company: 'Cloud Innovations',
                    jobType: 'Full-Time',
                    description: 'Manage CI/CD pipelines and cloud infrastructure.',
                    skills: ['AWS', 'Docker', 'Kubernetes'],
                    postedDate: '6 days ago',
                    location: 'Remote',
                    experienceYears: 3,
                    link: 'https://example.com/job7'
                },
                {
                    title: 'Product Manager',
                    company: 'Innovate Labs',
                    jobType: 'Full-Time',
                    description: 'Define product vision and roadmap for new features.',
                    skills: ['Product Management', 'Agile', 'Roadmapping'],
                    postedDate: '2 days ago',
                    location: 'Bangalore, India',
                    experienceYears: 4,
                    link: 'https://example.com/job8'
                }
            ];

            // Filter dummy jobs based on activeFilters (simplified for demonstration)
            const filteredJobs = dummyJobs.filter(job => {
                const matchesMainSearch = !filters.mainSearch ||
                    job.title.toLowerCase().includes(filters.mainSearch.toLowerCase()) ||
                    job.company.toLowerCase().includes(filters.mainSearch.toLowerCase()) ||
                    job.location.toLowerCase().includes(filters.mainSearch.toLowerCase()) ||
                    job.skills.some(skill => skill.toLowerCase().includes(filters.mainSearch.toLowerCase()));

                const matchesLocations = filters.locations.length === 0 ||
                    filters.locations.some(loc => job.location.toLowerCase().includes(loc.toLowerCase()));

                const matchesCompanies = filters.companies.length === 0 ||
                    filters.companies.some(comp => job.company.toLowerCase().includes(comp.toLowerCase()));
                
                const jobExperience = job.experienceYears !== undefined ? job.experienceYears : -1; // Assign -1 if experience is undefined
                const minExp = filters.minExperience ? parseInt(filters.minExperience) : 0;
                const maxExp = filters.maxExperience ? parseInt(filters.maxExperience) : 999; // Arbitrarily high max

                const matchesExperience = (jobExperience >= minExp) && (jobExperience <= maxExp);

                const matchesJobType = filters.jobType === 'all' || job.jobType.toLowerCase() === filters.jobType.toLowerCase();

                return matchesMainSearch && matchesLocations && matchesCompanies && matchesExperience && matchesJobType;
            });

            // Apply sorting
            const sortedJobs = filteredJobs.sort((a, b) => {
                if (filters.sortBy === 'deadline') {
                    // For dummy data, we'll just sort by postedDate string for simplicity, assuming newer is earlier for deadline simulation
                    return a.postedDate.localeCompare(b.postedDate);
                } else { // 'newest'
                    return b.postedDate.localeCompare(a.postedDate);
                }
            });

            renderJobs(sortedJobs);
            console.log('Jobs rendered successfully.');

        }, 700); // Simulate network delay
    }

    // Initial fetch of jobs on page load
    fetchJobs(activeFilters);
    renderActiveFiltersDisplay();
});
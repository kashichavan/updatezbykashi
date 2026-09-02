import re
import html
import urllib.parse

# 1. Comprehensive Master Directory of Corporate Tech Employers & Brands
KNOWN_COMPANIES_MAP = {
    'deloitte': 'Deloitte',
    'kpmg': 'KPMG',
    'pricewaterhousecoopers': 'PwC',
    'pwc': 'PwC',
    'ernst & young': 'EY (Ernst & Young)',
    'ernst and young': 'EY (Ernst & Young)',
    'ey': 'EY (Ernst & Young)',
    'mckinsey': 'McKinsey & Company',
    'boston consulting group': 'Boston Consulting Group',
    'bcg': 'Boston Consulting Group',
    'bain & company': 'Bain & Company',
    'bain': 'Bain & Company',
    'accenture': 'Accenture',
    'tata consultancy services': 'TCS (Tata Consultancy Services)',
    'tata consultancy': 'TCS (Tata Consultancy Services)',
    'tcs': 'TCS (Tata Consultancy Services)',
    'infosys': 'Infosys',
    'cognizant': 'Cognizant',
    'cts': 'Cognizant',
    'wipro': 'Wipro',
    'hcltech': 'HCLTech',
    'hcl': 'HCLTech',
    'capgemini': 'Capgemini',
    'tech mahindra': 'Tech Mahindra',
    'lti mindtree': 'LTI Mindtree',
    'ltimindtree': 'LTI Mindtree',
    'mindtree': 'LTI Mindtree',
    'mphasis': 'Mphasis',
    'hexaware': 'Hexaware Technologies',
    'persistent': 'Persistent Systems',
    'birlasoft': 'Birlasoft',
    'coforge': 'Coforge',
    'cyient': 'Cyient',
    'zs associates': 'ZS Associates',
    'zs': 'ZS Associates',
    'softobiz': 'Softobiz Technologies',
    'thinkitive': 'Thinkitive Technologies',
    'state street': 'State Street',
    'statestreet': 'State Street',
    'paytm': 'Paytm',
    'phonepe': 'PhonePe',
    'google': 'Google',
    'alphabet': 'Google',
    'microsoft': 'Microsoft',
    'amazon': 'Amazon',
    'aws': 'Amazon Web Services (AWS)',
    'meta': 'Meta',
    'apple': 'Apple',
    'netflix': 'Netflix',
    'uber': 'Uber',
    'oracle': 'Oracle',
    'cisco': 'Cisco',
    'ibm': 'IBM',
    'intel': 'Intel',
    'nvidia': 'NVIDIA',
    'amd': 'AMD',
    'qualcomm': 'Qualcomm',
    'salesforce': 'Salesforce',
    'adobe': 'Adobe',
    'sap': 'SAP',
    'servicenow': 'ServiceNow',
    'vmware': 'VMware',
    'red hat': 'Red Hat',
    'redhat': 'Red Hat',
    'barclays': 'Barclays',
    'morgan stanley': 'Morgan Stanley',
    'goldman sachs': 'Goldman Sachs',
    'jpmorgan chase': 'JPMorgan Chase',
    'jpmorgan': 'JPMorgan Chase',
    'jpmc': 'JPMorgan Chase',
    'deutsche bank': 'Deutsche Bank',
    'hsbc': 'HSBC',
    'citigroup': 'Citigroup',
    'citi': 'Citigroup',
    'bny mellon': 'BNY Mellon',
    'american express': 'American Express',
    'amex': 'American Express',
    'metlife': 'MetLife',
    'mastercard': 'Mastercard',
    'visa': 'Visa',
    'paypal': 'PayPal',
    'stripe': 'Stripe',
    'vyapar': 'Vyapar (Simply Vyapar Apps)',
    'simply vyapar': 'Vyapar (Simply Vyapar Apps)',
    'quest global': 'Quest Global',
    'quest': 'Quest Global',
    'globallogic': 'GlobalLogic',
    'dassault': 'Dassault Systèmes',
    'siemens': 'Siemens',
    'bosch': 'Bosch',
    'philips': 'Philips',
    'general electric': 'General Electric (GE)',
    'ge': 'General Electric (GE)',
    'schneider electric': 'Schneider Electric',
    'schneider': 'Schneider Electric',
    'dell technologies': 'Dell Technologies',
    'dell': 'Dell Technologies',
    'hp inc': 'HP Inc.',
    'hp': 'HP Inc.',
    'hewlett packard': 'Hewlett Packard Enterprise (HPE)',
    'hpe': 'Hewlett Packard Enterprise (HPE)',
    'lenovo': 'Lenovo',
    'swiggy': 'Swiggy',
    'zomato': 'Zomato',
    'flipkart': 'Flipkart',
    'meesho': 'Meesho',
    'razorpay': 'Razorpay',
    'cred': 'CRED',
    'zepto': 'Zepto',
    'blinkit': 'Blinkit',
    'inmobi': 'InMobi',
    'zoho': 'Zoho Corporation',
    'freshworks': 'Freshworks',
    'bharti airtel': 'Bharti Airtel',
    'airtel': 'Bharti Airtel',
    'reliance jio': 'Reliance Jio',
    'jio': 'Reliance Jio',
    'reliance': 'Reliance Industries',
    'lsit': 'LSI Technologies',
    'lsi': 'LSI Technologies',
    'seceon': 'Seceon',
    'loginext': 'LogiNext',
    'infobip': 'Infobip',
    'spyne': 'Spyne',
    'navi': 'Navi Technologies',
    'moneyview': 'Moneyview',
    'aditya birla': 'Aditya Birla Group',
    'data eminence': 'Data Eminence',
    'rezo': 'Rezo.ai',
    'rezo.ai': 'Rezo.ai',
    'rezoai': 'Rezo.ai',
    'jobsworkable': 'Workable (Volga Partners)',
    'jobsashbyhq': 'LG Ad Solutions',
    'batches': 'Tudip Technologies',
    'rtx': 'RTX Corporation',
    'raytheon': 'RTX Corporation',
}

# 2. Known Aggregators / Job Boards to avoid extracting as the employer
JOB_AGGREGATORS = [
    'jobdexo', 'indeed', 'linkedin', 'naukri', 'foundit', 'monster',
    'glassdoor', 'shine', 'hirist', 'unstop', 'internshala', 'jobsmind',
    'freshersworld', 'timesjobs', 'placement'
]

# 3. Known ATS platform strings to strip from domains
ATS_STRINGS = [
    'myworkdayjobs', 'workday', 'taleo', 'oraclecloud', 'greenhouse',
    'lever', 'smartrecruiters', 'jobvite', 'successfactors', 'icims',
    'ashbyhq', 'bamboohr', 'breezy', 'recruitee', 'darwinbox'
]


def resolve_company_name(raw_name='', title='', description='', apply_url='', url=''):
    """
    Intelligently extracts, cleans, and normalizes corporate company names.
    Eliminates subdomains (e.g. southasiacareers.deloitte.com -> Deloitte),
    ATS domains (e.g. jobs.zs.com -> ZS Associates, careers.wipro.com -> Wipro),
    and aggregator domains by checking context and master dictionary.
    """
    raw_clean = (raw_name or '').strip().lstrip('🏢•-| ').strip()
    raw_clean = html.unescape(html.unescape(raw_clean)).replace('&amp;', '&').replace('&amp', '&')
    
    # Strip URL protocol / trailing slashes if raw_name was a full URL
    if raw_clean.startswith('http://') or raw_clean.startswith('https://'):
        raw_clean = urllib.parse.urlparse(raw_clean).netloc

    raw_low = raw_clean.lower()
    
    # Check if raw_clean is an aggregator (indeed, jobsmind, foundit)
    is_aggregator = any(agg in raw_low for agg in JOB_AGGREGATORS)
    is_generic = not raw_clean or raw_low in [
        'featured partner', 'featured hiring partner', 'tech company', 'company', 'partner', 'fresher'
    ]
    is_domain = (
        ('.' in raw_clean and not raw_clean.endswith('.ai') and not raw_clean.endswith('.io'))
        or any(ats in raw_low for ats in ATS_STRINGS)
        or raw_clean.endswith('.com') or raw_clean.endswith('.in') or raw_clean.endswith('.org') or raw_clean.endswith('.net') or raw_clean.endswith('.solutions')
    )

    # 1. If raw_clean is a good real company name (e.g. "Deloitte", "Rezo.ai", "Moneyview", "Seceon", "State Street")
    if not is_domain and not is_aggregator and not is_generic:
        for key, normalized in KNOWN_COMPANIES_MAP.items():
            if len(key) <= 4:
                if re.search(rf'\b{re.escape(key)}\b', raw_low):
                    return normalized
            else:
                if key in raw_low:
                    return normalized
        if len(raw_clean) <= 4 and raw_clean.isalpha():
            return raw_clean.upper()
        return raw_clean

    # 2. If raw_clean is a corporate domain or ATS (e.g. "jobs.zs.com", "careers.wipro.com", "lsit.solutions", "southasiacareers.deloitte.com")
    if is_domain:
        domain_parts = re.split(r'[\.\-_]', raw_clean)
        for p in domain_parts:
            p_low = p.lower()
            if p_low in KNOWN_COMPANIES_MAP:
                return KNOWN_COMPANIES_MAP[p_low]
        
        filtered = [
            p for p in domain_parts 
            if p.lower() not in ['www', 'com', 'org', 'net', 'in', 'co', 'io', 'ai', 'careers', 'jobs', 'search', 'southasia', 'wd1', 'wd2', 'wd3', 'wd4', 'wd5', 'fa', 'em2', 'ejgk', 'cloud', 'solutions'] 
            and not any(ats in p.lower() for ats in ATS_STRINGS)
            and not any(agg in p.lower() for agg in JOB_AGGREGATORS)
        ]
        if filtered:
            cand = filtered[-1] if len(filtered) == 1 else filtered[0]
            if cand.lower() in KNOWN_COMPANIES_MAP:
                return KNOWN_COMPANIES_MAP[cand.lower()]
            if len(cand) >= 3:
                return cand.capitalize()

    # 3. If raw_clean was an aggregator (e.g. indeed, jobsmind, foundit), extract real company from description / title
    if description:
        desc_start = description[:400]
        # Check first sentence corporate name: "Simply Vyapar Apps Private Limited is a fast-growing..."
        m_comp = re.search(
            r'^(?:About\s+)?([A-Z0-9][A-Za-z0-9\s&.\'\-]{2,35}?)(?:\s+(?:Private\s+Limited|Pvt\s+Ltd|Technologies|Solutions|Services|Corporation|LLC|Inc|Limited|Ltd|Apps|India))?\s+(?:is\s+(?:a|an|one|the|hiring|seeking)|was\s+founded|provides|operates|builds)',
            desc_start
        )
        if m_comp:
            extracted = m_comp.group(1).strip()
            if not any(agg in extracted.lower() for agg in JOB_AGGREGATORS) and len(extracted) > 2:
                for key, normalized in KNOWN_COMPANIES_MAP.items():
                    if key in extracted.lower():
                        return normalized
                return extracted

        for key, normalized in KNOWN_COMPANIES_MAP.items():
            if len(key) <= 4:
                if re.search(rf'\b{re.escape(key)}\b', desc_start, re.IGNORECASE):
                    return normalized
            else:
                if key in desc_start.lower():
                    return normalized

    # 4. Check Title for company (e.g. "Data Analyst at KPMG", "Deloitte Hiring")
    if title:
        m_at = re.search(r'\bat\s+([A-Z0-9][A-Za-z0-9\s&.\'\-]+?)(?:\s*—|\s*\||\s*\(|$)', title)
        if m_at:
            cand = m_at.group(1).strip()
            if not any(agg in cand.lower() for agg in JOB_AGGREGATORS) and '.' not in cand and len(cand) > 2:
                cand_low = cand.lower()
                for key, normalized in KNOWN_COMPANIES_MAP.items():
                    if key in cand_low:
                        return normalized
                return cand

        for key, normalized in KNOWN_COMPANIES_MAP.items():
            if len(key) <= 4:
                if re.search(rf'\b{re.escape(key)}\b', title, re.IGNORECASE):
                    return normalized
            else:
                if key in title.lower():
                    return normalized

    return "Featured Tech Partner"

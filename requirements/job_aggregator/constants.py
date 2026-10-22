"""
Constants, taxonomy keywords, Indian city mapping, and categorization rules
for India-wide job aggregation.
"""

from typing import Dict, List, Set

INDIAN_CITY_CANONICAL_MAP: Dict[str, str] = {
    # Bengaluru Hub
    'bengaluru': 'Bengaluru',
    'bangalore': 'Bengaluru',
    'blr': 'Bengaluru',
    'whitefield': 'Bengaluru',
    'electronic city': 'Bengaluru',
    'koramangala': 'Bengaluru',
    'indiranagar': 'Bengaluru',
    'h完善': 'Bengaluru',

    # Hyderabad Hub
    'hyderabad': 'Hyderabad',
    'hyd': 'Hyderabad',
    'secunderabad': 'Hyderabad',
    'cyberabad': 'Hyderabad',
    'gachibowli': 'Hyderabad',
    'hitec city': 'Hyderabad',

    # Pune Hub
    'pune': 'Pune',
    'hinjewadi': 'Pune',
    'magarpatta': 'Pune',

    # Chennai Hub
    'chennai': 'Chennai',
    'madras': 'Chennai',
    'omr': 'Chennai',
    'tidel park': 'Chennai',

    # Mumbai Metropolitan Region
    'mumbai': 'Mumbai',
    'bombay': 'Mumbai',
    'navi mumbai': 'Mumbai',
    'thane': 'Mumbai',
    'andheri': 'Mumbai',
    'bkc': 'Mumbai',

    # Delhi NCR Hub
    'delhi': 'Delhi NCR',
    'new delhi': 'Delhi NCR',
    'delhi ncr': 'Delhi NCR',
    'noida': 'Noida',
    'greater noida': 'Noida',
    'gurugram': 'Gurugram',
    'gurgaon': 'Gurugram',
    'faridabad': 'Delhi NCR',
    'ghaziabad': 'Delhi NCR',

    # Kolkata Hub
    'kolkata': 'Kolkata',
    'calcutta': 'Kolkata',
    'salt lake': 'Kolkata',
    'new town': 'Kolkata',

    # Gujarat
    'ahmedabad': 'Ahmedabad',
    'gandhinagar': 'Ahmedabad',
    'vadodara': 'Vadodara',
    'surat': 'Surat',

    # Rajasthan
    'jaipur': 'Jaipur',

    # Kerala
    'kochi': 'Kochi',
    'cochin': 'Kochi',
    'ernakulam': 'Kochi',
    'thiruvananthapuram': 'Thiruvananthapuram',
    'trivandrum': 'Thiruvananthapuram',

    # Central & Others
    'indore': 'Indore',
    'bhopal': 'Bhopal',
    'coimbatore': 'Coimbatore',
    'chandigarh': 'Chandigarh',
    'mohali': 'Chandigarh',
    'panchkula': 'Chandigarh',
    'lucknow': 'Lucknow',
    'bhubaneswar': 'Bhubaneswar',
    'nagpur': 'Nagpur',
    'visakhapatnam': 'Visakhapatnam',
    'vizag': 'Visakhapatnam',
    'patna': 'Patna',
    'dehradun': 'Dehradun',

    # Remote / All-India
    'remote': 'Remote',
    'work from home': 'Remote',
    'wfh': 'Remote',
    'anywhere in india': 'Remote',
    'india': 'India (Remote / Multiple)',
    'pan india': 'India (Remote / Multiple)',
    'all india': 'India (Remote / Multiple)',
}

TECHNICAL_KEYWORDS: Set[str] = {
    'python', 'django', 'flask', 'fastapi', 'java', 'spring', 'springboot',
    'javascript', 'typescript', 'react', 'reactjs', 'nextjs', 'next.js',
    'vue', 'angular', 'node', 'nodejs', 'express', 'golang', 'go', 'rust',
    'c++', 'c#', '.net', 'dotnet', 'php', 'laravel', 'ruby', 'rails',
    'software engineer', 'software developer', 'backend developer',
    'frontend developer', 'full stack developer', 'fullstack developer',
    'web developer', 'sde', 'sde 1', 'sde 2', 'sde-1', 'sde-2', 'swe',
    'data engineer', 'data analyst', 'data scientist', 'bi analyst',
    'ai engineer', 'ml engineer', 'machine learning', 'deep learning',
    'devops engineer', 'cloud engineer', 'aws', 'azure', 'gcp',
    'site reliability', 'sre', 'qa engineer', 'automation tester', 'sdet',
    'quality assurance', 'testing', 'cybersecurity', 'information security',
    'network engineer', 'database administrator', 'dba', 'sql developer',
    'mobile developer', 'android developer', 'ios developer', 'flutter',
    'react native', 'it support', 'technical support', 'system administrator',
    'linux admin', 'embedded engineer', 'firmware engineer'
}

NON_TECHNICAL_KEYWORDS: Set[str] = {
    'mba', 'business analyst', 'management trainee', 'graduate trainee',
    'marketing', 'digital marketing', 'growth marketing', 'seo specialist',
    'social media manager', 'content writer', 'copywriter', 'content marketing',
    'sales', 'sales executive', 'business development', 'bde', 'bda',
    'inside sales', 'account manager', 'account management', 'sales manager',
    'hr', 'human resources', 'recruiter', 'technical recruiter', 'talent acquisition',
    'people operations', 'hr executive', 'finance', 'financial analyst',
    'accountant', 'accounting', 'chartered accountant', 'ca', 'auditor',
    'banking', 'investment banking', 'insurance', 'wealth management',
    'operations', 'operations executive', 'operations manager', 'supply chain',
    'logistics', 'procurement', 'inventory manager', 'warehouse manager',
    'customer support', 'customer success', 'customer service', 'support executive',
    'bpo', 'kpo', 'telecaller', 'call center', 'voice process', 'non-voice',
    'administration', 'admin executive', 'office manager', 'receptionist',
    'project coordinator', 'program manager', 'product manager', 'associate product manager',
    'apm', 'consultant', 'associate consultant', 'hospitality', 'retail store manager'
}

EXPERIENCE_KEYWORDS: Dict[str, List[str]] = {
    'INTERNSHIP': [
        'intern', 'internship', 'trainee', 'apprentice', 'summer analyst',
        'winter intern', 'research intern', 'graduate intern'
    ],
    'FRESHER': [
        'fresher', 'freshers', 'entry level', '0-1 year', '0-1 yr', '0-1 yrs',
        '0 to 1 year', '0-2 year', '0 to 2 years', '2024 batch', '2025 batch',
        '2026 batch', 'campus', 'college', 'junior', 'associate'
    ],
    'EARLY_CAREER': [
        '1-3 year', '1 to 3 years', '1-3 yrs', '2-4 year', '1+ year', '2+ year',
        'early career'
    ],
    'MID_LEVEL': [
        '3-5 year', '3 to 5 years', '3-5 yrs', '4-6 year', '3+ year', '4+ year',
        'mid level', 'mid-senior'
    ],
    'SENIOR_LEVEL': [
        '5+ year', '5-8 year', '5+ yrs', 'senior', 'lead', 'staff',
        'principal', 'architect', 'engineering manager', 'head', 'director'
    ]
}

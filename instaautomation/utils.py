# Helper utilities for Instagram automation
import re

def sanitize_keyword(keyword):
    return re.sub(r'[^\w\s]', '', keyword).strip().lower()

def parse_keywords_string(keywords_str):
    if not keywords_str:
        return []
    return [k.strip().lower() for k in keywords_str.split(',') if k.strip()]

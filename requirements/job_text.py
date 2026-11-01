"""Turn stored job descriptions into readable blocks for the job page."""

import re

_BULLET_RE = re.compile(r'^\s*(?:[•●▪◦·*✓✔➤►–—-]|\d{1,2}[.)])\s+')
_INLINE_BULLET_RE = re.compile(r'\s+(?=[•●▪◦✓✔➤►]\s*)')
# These read as headings even with no colon after them.
_FIXED_HEADINGS = (
    'Job Description', 'Job Summary', 'Job Overview', 'Role Overview', 'About the Role',
    'About the Job', 'About the Company', 'About Us', 'Key Responsibilities',
    'Roles and Responsibilities', 'Roles & Responsibilities', 'Required Skills',
    'Preferred Skills', 'Key Skills', 'Technical Skills', 'Preferred Qualifications',
    'Minimum Qualifications', 'Basic Qualifications', 'Required Qualifications',
    "What You'll Do", 'What You Will Do', "What We're Looking For", 'What We Are Looking For',
    'Who You Are', 'What We Offer', 'Why Join Us',
)
_COLON_HEADINGS = (
    'Responsibilities', 'Requirements', 'Qualifications', 'Skills', 'Eligibility',
    'Experience', 'Education', 'Benefits', 'Perks', 'Location', 'Salary', 'Stipend',
    'Duration', 'Job Type', 'Note', 'Must Have', 'Nice to Have', 'Good to Have',
)
_FIXED_RE = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(h) for h in _FIXED_HEADINGS) + r')(?![\w-]):?\s*')
_COLON_RE = re.compile(
    r'(?<![\w-])((?:[A-Z][\w&-]*\s+){0,2}(?:' + '|'.join(re.escape(h) for h in _COLON_HEADINGS) + r')):\s*'
)
_HEADING_LINE_RE = re.compile(r"^[A-Z][\w&'’/ -]{1,48}:$")
_LIST_HEADING_RE = re.compile(r'responsibilit|requirement|qualification|skills|you.?ll do|you will do|looking for|must have|nice to have|good to have|offer|benefits|perks', re.I)
# A full stop here does not end the sentence.
_SENTENCE_RE = re.compile(r'(?<!\b[A-Z])(?<!\bPvt)(?<!\bLtd)(?<!\bInc)(?<!\bSr)(?<!\bJr)(?<!\bDr)(?<!\bMr)(?<!\bNo)(?<!e\.g)(?<!i\.e)(?<!\betc)(?<=[.!?])\s+(?=[A-Z(])')


# Lists flattened on import lose their punctuation, but each item still starts with a verb.
_ITEM_VERB_RE = re.compile(
    r'(?<=[a-z0-9#+)])\s+(?=(?:Analyze|Assist|Build|Collaborate|Communicate|Conduct|Coordinate|Create|'
    r'Deliver|Deploy|Design|Develop|Ensure|Identify|Implement|Improve|Lead|Maintain|Manage|Mentor|'
    r'Monitor|Optimize|Oversee|Own|Participate|Perform|Prepare|Provide|Review|Support|Test|'
    r'Troubleshoot|Work|Write)\b)'
)


def _split_flat_text(text: str) -> str:
    """Put line breaks back into a description stored as one long line."""
    text = _FIXED_RE.sub(lambda m: f'\n{m.group(1)}:\n', text)
    text = _COLON_RE.sub(lambda m: f'\n{m.group(1)}:\n', text)
    return text


def _sentences(text: str) -> list:
    return [part.strip() for part in _SENTENCE_RE.split(text) if part.strip()]


def description_blocks(text: str) -> list:
    """
    Split a description into headings, paragraphs and lists.

    Only spacing changes, never the words, apart from markers such as ** and
    bullet characters. Autoescaping still applies because the template prints
    each piece as plain text.
    """
    text = (text or '').replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\\n', '\n').replace('**', '').strip()
    if not text:
        return []
    text = _INLINE_BULLET_RE.sub('\n', text)
    # Long text with hardly any breaks was flattened when it was imported.
    if text.count('\n') * 300 < len(text):
        text = _split_flat_text(text)

    blocks = []

    def add_list_item(line: str) -> None:
        if blocks and blocks[-1]['kind'] == 'list':
            blocks[-1]['lines'].append(line)
        else:
            blocks.append({'kind': 'list', 'lines': [line]})

    for raw in text.split('\n'):
        line = ' '.join(raw.split())
        if not line:
            continue
        if _BULLET_RE.match(line):
            add_list_item(_BULLET_RE.sub('', line).strip())
        elif _HEADING_LINE_RE.match(line) and len(line.split()) <= 6:
            blocks.append({'kind': 'heading', 'text': line.rstrip(':')})
        else:
            sentences = _sentences(line)
            under_list_heading = (
                blocks and blocks[-1]['kind'] == 'heading'
                and _LIST_HEADING_RE.search(blocks[-1]['text'])
            )
            if under_list_heading:
                sentences = [item for sentence in sentences for item in _ITEM_VERB_RE.split(sentence)]
            if under_list_heading and len(sentences) > 1:
                for sentence in sentences:
                    add_list_item(sentence)
            elif len(line) <= 420:
                blocks.append({'kind': 'text', 'text': line})
            else:
                # Long unbroken passages become short paragraphs.
                for start in range(0, len(sentences), 3):
                    blocks.append({'kind': 'text', 'text': ' '.join(sentences[start:start + 3])})
    return blocks

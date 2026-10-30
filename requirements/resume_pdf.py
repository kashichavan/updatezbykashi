"""
High-Precision Single & Multi-Page ATS Resume PDF Generator using ReportLab.
Produces 100% vector, machine-readable, ATS-compliant PDF resumes with zero rasterization.
Compatible with Workday, Taleo, Greenhouse, Lever, and iCIMS parsers.
Supports dynamic multi-page flow with running headers/footers and orphan prevention.
"""

import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4

TEMPLATES_CONFIG = {
    'modern': {
        'font_name': 'Helvetica',
        'font_bold': 'Helvetica-Bold',
        'font_oblique': 'Helvetica-Oblique',
        'name_color': colors.HexColor('#1e3a8a'),
        'sec_title_color': colors.HexColor('#1e3a8a'),
        'rule_color': colors.HexColor('#2563eb'),
        'rule_thickness': 1.4,
        'project_title_color': colors.HexColor('#1e3a8a'),
        'body_color': colors.HexColor('#1e293b'),
        'bullet_color': colors.HexColor('#2563eb'),
        'header_align': 1,
    },
    'classic': {
        'font_name': 'Times-Roman',
        'font_bold': 'Times-Bold',
        'font_oblique': 'Times-Italic',
        'name_color': colors.HexColor('#0f172a'),
        'sec_title_color': colors.HexColor('#0f172a'),
        'rule_color': colors.HexColor('#475569'),
        'rule_thickness': 0.8,
        'project_title_color': colors.HexColor('#0f172a'),
        'body_color': colors.HexColor('#1e293b'),
        'bullet_color': colors.HexColor('#0f172a'),
        'header_align': 1,
    },
    'bold': {
        'font_name': 'Helvetica',
        'font_bold': 'Helvetica-Bold',
        'font_oblique': 'Helvetica-Oblique',
        'name_color': colors.HexColor('#0f172a'),
        'sec_title_color': colors.HexColor('#1d4ed8'),
        'rule_color': colors.HexColor('#1d4ed8'),
        'rule_thickness': 1.8,
        'project_title_color': colors.HexColor('#1d4ed8'),
        'body_color': colors.HexColor('#1e293b'),
        'bullet_color': colors.HexColor('#1d4ed8'),
        'header_align': 0,
    },
    'minimalist': {
        'font_name': 'Helvetica',
        'font_bold': 'Helvetica-Bold',
        'font_oblique': 'Helvetica-Oblique',
        'name_color': colors.HexColor('#0f172a'),
        'sec_title_color': colors.HexColor('#64748b'),
        'rule_color': colors.HexColor('#e2e8f0'),
        'rule_thickness': 0.6,
        'project_title_color': colors.HexColor('#0f172a'),
        'body_color': colors.HexColor('#334155'),
        'bullet_color': colors.HexColor('#64748b'),
        'header_align': 0,
    },
    'executive': {
        'font_name': 'Helvetica',
        'font_bold': 'Helvetica-Bold',
        'font_oblique': 'Helvetica-Oblique',
        'name_color': colors.HexColor('#0f172a'),
        'sec_title_color': colors.HexColor('#334155'),
        'rule_color': colors.HexColor('#cbd5e1'),
        'rule_thickness': 1.0,
        'project_title_color': colors.HexColor('#0f172a'),
        'body_color': colors.HexColor('#1e293b'),
        'bullet_color': colors.HexColor('#334155'),
        'header_align': 0,
    },
    'standard': {
        'font_name': 'Helvetica',
        'font_bold': 'Helvetica-Bold',
        'font_oblique': 'Helvetica-Oblique',
        'name_color': colors.HexColor('#0f172a'),
        'sec_title_color': colors.HexColor('#0f172a'),
        'rule_color': colors.HexColor('#0f172a'),
        'rule_thickness': 0.8,
        'project_title_color': colors.HexColor('#0f172a'),
        'body_color': colors.HexColor('#1e293b'),
        'bullet_color': colors.HexColor('#0f172a'),
        'header_align': 1,
    }
}


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that determines total page count dynamically.
    For multi-page resumes (pages >= 2), prints a discreet ATS running footer:
    'CANDIDATE NAME | Page X of Y'.
    For single-page resumes, leaves footer clean and minimal.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.candidate_name = ""

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if num_pages > 1:
                self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        footer_y = 22
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(PAGE_W - 36, footer_y, page_str)
        
        if getattr(self, 'candidate_name', None):
            self.drawString(36, footer_y, self.candidate_name.upper())

        # Subtle hairline separator
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, footer_y + 10, PAGE_W - 36, footer_y + 10)
        self.restoreState()


def make_numbered_canvas(candidate_name=""):
    class CustomNumberedCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.candidate_name = candidate_name
    return CustomNumberedCanvas


def sanitize_text(val):
    """
    Format and sanitize text for ReportLab XML/HTML-like Paragraphs.
    Converts markdown and html bold/italic, escapes ampersands and special chars,
    and strips unsupported tags so ReportLab's parser never crashes.
    """
    if not val:
        return ""
    text = str(val).strip()

    # Normalize unicode quotation marks and dashes
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2022", "&bull;")

    # Convert markdown **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert markdown *italic* to <i>italic</i>
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)

    # Convert common html formatting
    text = re.sub(r'</?strong>', lambda m: '<b>' if '<strong' in m.group().lower() else '</b>', text, flags=re.IGNORECASE)
    text = re.sub(r'</?em>', lambda m: '<i>' if '<em' in m.group().lower() else '</i>', text, flags=re.IGNORECASE)

    # Escape unescaped ampersands (do not escape entities like &amp;, &bull;, etc.)
    text = re.sub(r'&(?!(?:amp|lt|gt|bull|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', text)

    # Strip any tags other than allowed formatting tags (b, i, u, font)
    def tag_replacer(match):
        tag = match.group(0).lower()
        if any(tag.startswith(f"<{t}") or tag.startswith(f"</{t}") for t in ['b', 'i', 'u', 'font']):
            return match.group(0)
        return ''

    text = re.sub(r'<[^>]+>', tag_replacer, text)
    return text


def clean_bullet_text(text: str) -> str:
    """
    Strips leading bullet symbols, dashes, asterisks, and numbers so ReportLab's
    built-in bulletText='•' never renders a duplicate symbol (e.g. '• •', '• -').
    """
    if not text:
        return ""
    t = str(text).strip()
    t = re.sub(r'^(?:[\u2022\u25cf\u25aa\u25b8\u2013\u2014\-\*\>]|\&bull\;|\&#8226\;|\&middot\;|\&#183\;|\d+[\.\)])\s*', '', t)
    t = re.sub(r'^(?:[\u2022\u25cf\u25aa\u25b8\u2013\u2014\-\*\>]|\&bull\;|\&#8226\;|\&middot\;|\&#183\;)\s*', '', t)
    return t.strip()


def clean_contact_field(val: str) -> str:
    if not val:
        return ""
    t = str(val).strip()
    return re.sub(r'^[\|\u2022\:\-\,\s]+|[\|\u2022\:\-\,\s]+$', '', t).strip()


def format_url_link(raw_url: str) -> tuple[str, str]:
    if not raw_url:
        return "", ""
    url = str(raw_url).strip()
    url = re.sub(r'^[\|\u2022\:\-\,\s]+|[\|\u2022\:\-\,\s]+$', '', url).strip()
    if not url:
        return "", ""
    if not url.startswith('http://') and not url.startswith('https://'):
        href = f"https://{url}"
        display = url
    else:
        href = url
        display = re.sub(r'^https?://(?:www\.)?', '', url).rstrip('/')
    return href, display


def clean_project_title(title: str) -> str:
    if not title:
        return ""
    t = str(title).strip()
    t = re.sub(r'\[GitHub\s*↗\]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'View\s*ATS', '', t, flags=re.IGNORECASE)
    t = re.sub(r'ATS\s*\d+%', '', t, flags=re.IGNORECASE)
    return re.sub(r'^[\|\u2022\:\-\,\s]+|[\|\u2022\:\-\,\s]+$', '', t).strip()


def clean_tech_stack(tech: str) -> str:
    if not tech:
        return ""
    t = str(tech).strip()
    t = re.sub(r'^(?:Technologies|Tech Stack|Core Stack|Stack)\s*:\s*', '', t, flags=re.IGNORECASE)
    return re.sub(r'^[\|\u2022\:\-\,\s]+|[\|\u2022\:\-\,\s]+$', '', t).strip()


def clean_institution_and_gpa(institution: str, gpa: str) -> tuple[str, str]:
    inst = str(institution or '').strip()
    g = str(gpa or '').strip()
    if not g and ('•' in inst or '\u2022' in inst or '|' in inst):
        parts = re.split(r'[•\u2022|]', inst, maxsplit=1)
        inst = parts[0].strip()
        g = parts[1].strip()
    inst = re.sub(r'[•\u2022|,\s]+$', '', inst).strip()
    g = re.sub(r'^(?:CGPA|GPA)\s*:\s*', '', g, flags=re.IGNORECASE).strip()
    g = re.sub(r'^[•\u2022|,\s]+', '', g).strip()
    return inst, g


def _render_ats_pdf_buffer(data: dict, scale_factor: float = 1.0) -> bytes:
    """Internal renderer generating PDF bytes with specific scale factor and template themes."""
    buffer = io.BytesIO()

    summary = data.get('summary') or ''
    skills = data.get('skills') or {}
    proj_list = data.get('projects') or []
    if isinstance(proj_list, dict):
        proj_list = list(proj_list.values())
    exp_list = data.get('experience') or []
    if isinstance(exp_list, dict):
        exp_list = list(exp_list.values())
    education_raw = data.get('education')
    certs = data.get('certifications') or []
    if isinstance(certs, str):
        certs = [certs]

    template_key = str(data.get('template') or 'standard').lower()
    cfg = TEMPLATES_CONFIG.get(template_key, TEMPLATES_CONFIG['standard'])

    # Calculate content volume for intelligent dynamic A4 budget
    total_lines = 0
    if summary:
        total_lines += 2.5
    if isinstance(skills, dict):
        total_lines += len(skills) * 1.15
    elif skills:
        total_lines += 2
    for p in proj_list:
        total_lines += 2.2 + len(p.get('bullets', [])) * 1.25
    for e in exp_list:
        total_lines += 2.5 + len(e.get('bullets', [])) * 1.25
    if education_raw:
        total_lines += 3.2
    if certs:
        total_lines += len(certs) * 1.1

    page_mode = str(data.get('page_mode') or 'single').lower()
    is_multi_target = (page_mode == 'multi') or (page_mode == 'auto' and total_lines > 34)

    if not is_multi_target:
        # Standard Single-Page A4 Budget with scaling
        if total_lines <= 20:
            top_margin = int(28 * scale_factor)
            bottom_margin = int(28 * scale_factor)
            side_margin = int(32 * scale_factor)
            name_size = 20.0 * scale_factor
            sec_title_size = 11.2 * scale_factor
            body_size = 9.4 * scale_factor
            body_leading = 13.5 * scale_factor
            bullet_size = 9.0 * scale_factor
            bullet_leading = 13.0 * scale_factor
            spacer_gap = 7.5 * scale_factor
            bullet_gap = 3.0 * scale_factor
        elif total_lines <= 27:
            top_margin = int(22 * scale_factor)
            bottom_margin = int(22 * scale_factor)
            side_margin = int(30 * scale_factor)
            name_size = 18.5 * scale_factor
            sec_title_size = 10.6 * scale_factor
            body_size = 8.8 * scale_factor
            body_leading = 12.0 * scale_factor
            bullet_size = 8.5 * scale_factor
            bullet_leading = 11.6 * scale_factor
            spacer_gap = 5.2 * scale_factor
            bullet_gap = 2.2 * scale_factor
        else: # High density 1-page fit (3-4 flagship projects)
            top_margin = int(18 * scale_factor)
            bottom_margin = int(18 * scale_factor)
            side_margin = int(26 * scale_factor)
            name_size = 17.0 * scale_factor
            sec_title_size = 10.0 * scale_factor
            body_size = 8.1 * scale_factor
            body_leading = 10.6 * scale_factor
            bullet_size = 7.9 * scale_factor
            bullet_leading = 10.2 * scale_factor
            spacer_gap = 3.8 * scale_factor
            bullet_gap = 1.6 * scale_factor
    else:
        # Multi-Page A4 Budget (Executive readability across 2+ A4 sheets)
        top_margin = int(32 * scale_factor)
        bottom_margin = int(36 * scale_factor)
        side_margin = int(34 * scale_factor)
        name_size = 20.5 * scale_factor
        sec_title_size = 11.2 * scale_factor
        body_size = 9.4 * scale_factor
        body_leading = 13.4 * scale_factor
        bullet_size = 9.0 * scale_factor
        bullet_leading = 13.0 * scale_factor
        spacer_gap = 8.5 * scale_factor
        bullet_gap = 3.2 * scale_factor

    printable_w = PAGE_W - (side_margin * 2)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=side_margin,
        rightMargin=side_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    styles = getSampleStyleSheet()

    font_regular = cfg['font_name']
    font_bold = cfg['font_bold']
    font_oblique = cfg['font_oblique']

    name_style = ParagraphStyle(
        'ATSName',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=name_size,
        leading=name_size + 3.5,
        alignment=cfg.get('header_align', 1),
        textColor=cfg.get('name_color', colors.HexColor('#0f172a')),
        keepWithNext=True
    )

    contact_style = ParagraphStyle(
        'ATSContact',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=body_size - 0.2,
        leading=body_size + 3.2,
        alignment=cfg.get('header_align', 1),
        textColor=colors.HexColor('#334155'),
        keepWithNext=True
    )

    sec_title_style = ParagraphStyle(
        'ATSSecTitle',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=sec_title_size,
        leading=sec_title_size + 2.5,
        textColor=cfg.get('sec_title_color', colors.HexColor('#0f172a')),
        spaceBefore=spacer_gap,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ATSBody',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=body_size,
        leading=body_leading,
        textColor=cfg.get('body_color', colors.HexColor('#1e293b'))
    )

    right_align_style = ParagraphStyle(
        'ATSRightAlign',
        parent=body_style,
        alignment=2, # Right
        fontName=font_bold,
        textColor=cfg.get('sec_title_color', colors.HexColor('#0f172a'))
    )

    right_role_style = ParagraphStyle(
        'ATSRightRole',
        parent=body_style,
        alignment=2, # Right
        fontName=font_oblique,
        textColor=colors.HexColor('#475569')
    )

    tech_style = ParagraphStyle(
        'ATSTech',
        parent=body_style,
        fontSize=body_size - 0.2,
        leading=body_leading - 0.4,
        textColor=colors.HexColor('#334155')
    )

    bullet_style = ParagraphStyle(
        'ATSBullet',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=bullet_size,
        leading=bullet_leading,
        textColor=cfg.get('body_color', colors.HexColor('#1e293b')),
        leftIndent=12,
        bulletIndent=2,
        bulletFontName=font_regular,
        bulletFontSize=bullet_size,
        bulletColor=cfg.get('bullet_color', colors.HexColor('#0f172a'))
    )

    story = []

    # 1. Candidate Name
    raw_name = data.get('name') or 'CANDIDATE NAME'
    story.append(Paragraph(sanitize_text(raw_name).upper(), name_style))
    story.append(Spacer(1, 3))

    # 2. Contact Details Bar
    contact = data.get('contact') or {}
    if isinstance(contact, dict):
        c_parts = []
        loc = clean_contact_field(contact.get('location', ''))
        if loc:
            c_parts.append(sanitize_text(loc))
        phone = clean_contact_field(contact.get('phone', ''))
        if phone:
            c_parts.append(sanitize_text(phone))
        email = clean_contact_field(contact.get('email', ''))
        if email:
            c_parts.append(f'<a href="mailto:{sanitize_text(email)}"><font color="#1d4ed8">{sanitize_text(email)}</font></a>')
        li_href, li_disp = format_url_link(contact.get('linkedin', ''))
        if li_href:
            c_parts.append(f'<a href="{sanitize_text(li_href)}"><font color="#1d4ed8">{sanitize_text(li_disp)}</font></a>')
        gh_href, gh_disp = format_url_link(contact.get('github', ''))
        if gh_href:
            c_parts.append(f'<a href="{sanitize_text(gh_href)}"><font color="#1d4ed8">{sanitize_text(gh_disp)}</font></a>')
        c_line = ' &nbsp;|&nbsp; '.join(c_parts)
    elif isinstance(contact, str):
        c_line = sanitize_text(clean_contact_field(contact))
    else:
        c_line = ''

    if c_line:
        story.append(Paragraph(c_line, contact_style))
    story.append(Spacer(1, spacer_gap * 0.75))

    def add_section_header(title):
        story.append(Paragraph(title, sec_title_style))
        story.append(HRFlowable(
            width='100%',
            thickness=cfg.get('rule_thickness', 0.8),
            color=cfg.get('rule_color', colors.HexColor('#0f172a')),
            spaceBefore=1.5,
            spaceAfter=spacer_gap * 0.5
        ))

    # Helper for Two-Column Split Headers (Pixel-aligned to margins)
    def create_split_header(left_html, right_html=None, is_date=True):
        if not right_html:
            return Paragraph(left_html, body_style)

        r_style = right_align_style if is_date else right_role_style
        right_w = 110 if is_date else 180
        left_w = printable_w - right_w
        table = Table(
            [[
                Paragraph(left_html, body_style),
                Paragraph(right_html, r_style)
            ]],
            colWidths=[left_w, right_w]
        )
        table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1)
        ]))
        return table

    # 3. Professional Summary
    if summary and str(summary).strip():
        add_section_header('PROFESSIONAL SUMMARY')
        story.append(Paragraph(sanitize_text(summary), body_style))
        story.append(Spacer(1, spacer_gap * 0.6))

    # 4. Technical Skills
    if skills:
        add_section_header('TECHNICAL SKILLS')
        if isinstance(skills, dict):
            for cat, sk in skills.items():
                if sk and str(sk).strip():
                    line = f'<b>{sanitize_text(cat)}:</b> {sanitize_text(sk)}'
                    story.append(Paragraph(line, body_style))
                    story.append(Spacer(1, 2.0))
        elif isinstance(skills, list):
            line = f'<b>Core Skills:</b> {sanitize_text(", ".join(skills))}'
            story.append(Paragraph(line, body_style))
        elif isinstance(skills, str):
            story.append(Paragraph(sanitize_text(skills), body_style))
        story.append(Spacer(1, spacer_gap * 0.6))

    # 5. Professional Work Experience (if any)
    if exp_list:
        add_section_header('PROFESSIONAL WORK EXPERIENCE')
        for exp in exp_list:
            if not isinstance(exp, dict):
                continue
            exp_flowables = []
            company = sanitize_text(clean_project_title(exp.get('company', '')))
            role = sanitize_text(clean_project_title(exp.get('role', '')))
            duration = sanitize_text(clean_contact_field(exp.get('period') or exp.get('duration') or ''))
            location = sanitize_text(clean_contact_field(exp.get('location', '')))

            exp_flowables.append(create_split_header(f'<b>{company}</b>', duration, is_date=True))

            sub_line_parts = []
            if role:
                sub_line_parts.append(f'<i>{role}</i>')
            if location:
                sub_line_parts.append(f'<font color="#64748b">{location}</font>')
            if sub_line_parts:
                exp_flowables.append(Paragraph(' &bull; '.join(sub_line_parts), tech_style))

            tech_stack = sanitize_text(clean_tech_stack(exp.get('tech_stack', '')))
            if tech_stack:
                exp_flowables.append(Paragraph(f'<b>Core Stack:</b> {tech_stack}', tech_style))
                exp_flowables.append(Spacer(1, 1.5))

            bullets = exp.get('bullets', [])
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                clean_b = clean_bullet_text(b)
                if clean_b:
                    exp_flowables.append(Paragraph(sanitize_text(clean_b), bullet_style, bulletText='•'))
                    exp_flowables.append(Spacer(1, bullet_gap))
            exp_flowables.append(Spacer(1, spacer_gap * 0.5))

            if total_lines <= 27:
                story.append(KeepTogether(exp_flowables))
            else:
                story.extend(exp_flowables)

    # 6. Enterprise / Flagship Software Projects
    if proj_list:
        sec_name = 'FLAGSHIP SOFTWARE PROJECTS' if exp_list else 'TECHNICAL & ENTERPRISE PROJECTS'
        add_section_header(sec_name)
        for proj in proj_list:
            if not isinstance(proj, dict):
                continue
            proj_flowables = []
            title = sanitize_text(clean_project_title(proj.get('title', '')))
            role = sanitize_text(clean_project_title(proj.get('role', '')))
            duration = sanitize_text(clean_contact_field(proj.get('period') or proj.get('duration') or ''))
            tech_stack = sanitize_text(clean_tech_stack(proj.get('tech_stack', '')))
            gh_url = proj.get('github_url', '')

            p_color = cfg.get('project_title_color', colors.HexColor('#0f172a'))
            p_hex = p_color.hexval() if hasattr(p_color, 'hexval') else str(p_color)
            if not p_hex.startswith('#'):
                p_hex = '#' + p_hex

            title_html = f'<font color="{p_hex}"><b>{title}</b></font>'
            if gh_url:
                gh_href, _ = format_url_link(gh_url)
                if gh_href:
                    title_html += f' &nbsp;<a href="{sanitize_text(gh_href)}"><font color="#1d4ed8" size="-1.5"><b>[GitHub ↗]</b></font></a>'

            if duration:
                proj_flowables.append(create_split_header(f'{title_html} &nbsp;|&nbsp; <i>{role}</i>' if role else title_html, duration, is_date=True))
            elif role:
                proj_flowables.append(create_split_header(title_html, f'<i>{role}</i>', is_date=False))
            else:
                proj_flowables.append(Paragraph(title_html, body_style))

            if tech_stack:
                proj_flowables.append(Paragraph(f'<b>Technologies:</b> {tech_stack}', tech_style))
                proj_flowables.append(Spacer(1, 1.5))

            bullets = proj.get('bullets', [])
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                clean_b = clean_bullet_text(b)
                if clean_b:
                    proj_flowables.append(Paragraph(sanitize_text(clean_b), bullet_style, bulletText='•'))
                    proj_flowables.append(Spacer(1, bullet_gap))
            proj_flowables.append(Spacer(1, spacer_gap * 0.5))

            if total_lines <= 27:
                story.append(KeepTogether(proj_flowables))
            else:
                story.extend(proj_flowables)

    # 7. Education
    if education_raw:
        add_section_header('EDUCATION')
        edu_items = education_raw if isinstance(education_raw, list) else [education_raw]
        edu_flowables = []
        for edu in edu_items:
            if isinstance(edu, dict):
                degree = sanitize_text(clean_contact_field(edu.get('degree', '')))
                year = sanitize_text(clean_contact_field(edu.get('year', '')))
                inst_raw = edu.get('institution', '')
                gpa_raw = edu.get('gpa', '')
                institution, gpa = clean_institution_and_gpa(inst_raw, gpa_raw)
                institution = sanitize_text(institution)
                gpa = sanitize_text(gpa)
                coursework = sanitize_text(edu.get('coursework', ''))

                edu_flowables.append(create_split_header(f'<b>{degree}</b>', year, is_date=True))

                sub_parts = []
                if institution:
                    sub_parts.append(institution)
                if gpa:
                    sub_parts.append(f'<b>CGPA: {gpa}</b>')
                if sub_parts:
                    edu_flowables.append(Paragraph(' &bull; '.join(sub_parts), body_style))

                if coursework:
                    edu_flowables.append(Paragraph(f'<b>Core Coursework:</b> {coursework}', tech_style))
                edu_flowables.append(Spacer(1, 2.5))
            elif isinstance(edu, str) and edu.strip():
                edu_flowables.append(Paragraph(sanitize_text(clean_contact_field(edu)), body_style))
        edu_flowables.append(Spacer(1, spacer_gap * 0.5))

        if total_lines <= 27:
            story.append(KeepTogether(edu_flowables))
        else:
            story.extend(edu_flowables)

    # 8. Certifications & Achievements
    if certs:
        add_section_header('CERTIFICATIONS & ACHIEVEMENTS')
        cert_flowables = []
        for cert in certs:
            clean_c = clean_bullet_text(cert)
            if clean_c:
                cert_flowables.append(Paragraph(sanitize_text(clean_c), bullet_style, bulletText='•'))
                cert_flowables.append(Spacer(1, bullet_gap))
        story.append(KeepTogether(cert_flowables))

    doc.build(story, canvasmaker=make_numbered_canvas(raw_name))
    return buffer.getvalue()


def generate_ats_resume_pdf(data: dict) -> bytes:
    """
    Generates an ATS-compliant PDF resume from a structured resume dictionary.
    Guarantees vector-only output with 100% extractable text, zero rasterization,
    full template fidelity, and self-healing single-page fitting.
    """
    import pypdf

    page_mode = str(data.get('page_mode') or 'single').lower()

    # Pass 1: Standard render
    pdf_bytes = _render_ats_pdf_buffer(data, scale_factor=1.0)

    # If single-page mode requested, verify page count and auto-scale if slightly overflowed
    if page_mode == 'single':
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            if len(reader.pages) > 1:
                # Pass 2: Compact scale
                pdf_bytes_p2 = _render_ats_pdf_buffer(data, scale_factor=0.91)
                reader_p2 = pypdf.PdfReader(io.BytesIO(pdf_bytes_p2))
                if len(reader_p2.pages) == 1:
                    return pdf_bytes_p2
                # Pass 3: Ultra-dense scale for heavy resumes (4+ projects)
                pdf_bytes_p3 = _render_ats_pdf_buffer(data, scale_factor=0.83)
                reader_p3 = pypdf.PdfReader(io.BytesIO(pdf_bytes_p3))
                if len(reader_p3.pages) == 1:
                    return pdf_bytes_p3
                # If still multi-page, return the tightest version (p3) rather than the loosest (p1)
                return pdf_bytes_p3
        except Exception:
            pass

    return pdf_bytes

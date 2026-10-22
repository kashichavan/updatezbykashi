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


def generate_ats_resume_pdf(data: dict) -> bytes:
    """
    Generates an ATS-compliant PDF resume from a structured resume dictionary.
    Guarantees vector-only output with 100% extractable text and zero rasterization.
    Dynamically balances typography, margins, and line heights so standard resumes
    elegantly fill the A4 sheet with zero awkward white-space or misalignments.
    """
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

    page_mode = str(data.get('page_mode') or 'auto').lower()

    # Optimal scaling to ensure full-page A4 balance or clean multi-page pagination
    is_multi_target = (page_mode == 'multi') or (page_mode == 'auto' and total_lines > 25)

    if not is_multi_target:
        # Standard Single-Page A4 Budget
        if total_lines <= 20:
            top_margin = 36
            bottom_margin = 36
            side_margin = 36
            name_size = 22.0
            sec_title_size = 11.5
            body_size = 9.8
            body_leading = 14.2
            bullet_size = 9.5
            bullet_leading = 14.0
            spacer_gap = 10.5
            bullet_gap = 4.0
        else:
            top_margin = 25
            bottom_margin = 25
            side_margin = 34
            name_size = 19.5
            sec_title_size = 10.8
            body_size = 8.8
            body_leading = 12.2
            bullet_size = 8.5
            bullet_leading = 11.8
            spacer_gap = 6.0
            bullet_gap = 2.5
    else:
        # Multi-Page A4 Budget (Executive readability across 2+ A4 sheets)
        top_margin = 34
        bottom_margin = 38
        side_margin = 36
        name_size = 21.0
        sec_title_size = 11.5
        body_size = 9.6
        body_leading = 13.8
        bullet_size = 9.2
        bullet_leading = 13.4
        spacer_gap = 9.5
        bullet_gap = 3.6

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

    name_style = ParagraphStyle(
        'ATSName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=name_size,
        leading=name_size + 4,
        alignment=1, # Centered
        textColor=colors.HexColor('#0f172a'),
        keepWithNext=True
    )

    contact_style = ParagraphStyle(
        'ATSContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=body_size - 0.3,
        leading=body_size + 3.5,
        alignment=1, # Centered
        textColor=colors.HexColor('#334155'),
        keepWithNext=True
    )

    sec_title_style = ParagraphStyle(
        'ATSSecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=sec_title_size,
        leading=sec_title_size + 3,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=spacer_gap,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ATSBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=body_size,
        leading=body_leading,
        textColor=colors.HexColor('#1e293b')
    )

    right_align_style = ParagraphStyle(
        'ATSRightAlign',
        parent=body_style,
        alignment=2, # Right
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )

    right_role_style = ParagraphStyle(
        'ATSRightRole',
        parent=body_style,
        alignment=2, # Right
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#334155')
    )

    tech_style = ParagraphStyle(
        'ATSTech',
        parent=body_style,
        fontSize=body_size - 0.2,
        leading=body_leading - 0.5,
        textColor=colors.HexColor('#334155')
    )

    bullet_style = ParagraphStyle(
        'ATSBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=bullet_size,
        leading=bullet_leading,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=13,
        bulletIndent=2,
        bulletFontName='Helvetica',
        bulletFontSize=bullet_size,
        bulletColor=colors.HexColor('#0f172a')
    )

    story = []

    # 1. Candidate Name
    raw_name = data.get('name') or 'CANDIDATE NAME'
    story.append(Paragraph(sanitize_text(raw_name).upper(), name_style))
    story.append(Spacer(1, 4))

    # 2. Contact Details Bar
    contact = data.get('contact') or {}
    if isinstance(contact, dict):
        c_parts = [
            sanitize_text(contact.get('location')),
            sanitize_text(contact.get('phone')),
            sanitize_text(contact.get('email')),
            sanitize_text(contact.get('linkedin')),
            sanitize_text(contact.get('github'))
        ]
        c_parts = [p for p in c_parts if p]
        c_line = ' &nbsp;|&nbsp; '.join(c_parts)
    elif isinstance(contact, str):
        c_line = sanitize_text(contact)
    else:
        c_line = ''

    if c_line:
        story.append(Paragraph(c_line, contact_style))
    story.append(Spacer(1, spacer_gap * 0.75))

    def add_section_header(title):
        story.append(Paragraph(title, sec_title_style))
        story.append(HRFlowable(
            width='100%',
            thickness=0.8,
            color=colors.HexColor('#0f172a'),
            spaceBefore=2,
            spaceAfter=spacer_gap * 0.55
        ))

    # Helper for Two-Column Split Headers (Pixel-aligned to margins)
    def create_split_header(left_html, right_html=None, is_date=True):
        if not right_html:
            return Paragraph(left_html, body_style)

        r_style = right_align_style if is_date else right_role_style
        right_w = 110 if is_date else 170
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
        story.append(Spacer(1, spacer_gap * 0.7))

    # 4. Technical Skills
    if skills:
        add_section_header('TECHNICAL SKILLS')
        if isinstance(skills, dict):
            for cat, sk in skills.items():
                if sk and str(sk).strip():
                    line = f'<b>{sanitize_text(cat)}:</b> {sanitize_text(sk)}'
                    story.append(Paragraph(line, body_style))
                    story.append(Spacer(1, 2.5))
        elif isinstance(skills, list):
            line = f'<b>Core Skills:</b> {sanitize_text(", ".join(skills))}'
            story.append(Paragraph(line, body_style))
        elif isinstance(skills, str):
            story.append(Paragraph(sanitize_text(skills), body_style))
        story.append(Spacer(1, spacer_gap * 0.7))

    # 5. Professional Work Experience (if any)
    if exp_list:
        add_section_header('PROFESSIONAL WORK EXPERIENCE')
        for exp in exp_list:
            if not isinstance(exp, dict):
                continue
            exp_flowables = []
            company = sanitize_text(exp.get('company', ''))
            role = sanitize_text(exp.get('role', ''))
            duration = sanitize_text(exp.get('period') or exp.get('duration') or '')
            location = sanitize_text(exp.get('location', ''))

            # Line 1: Company (Left) | Duration (Right)
            exp_flowables.append(create_split_header(f'<b>{company}</b>', duration, is_date=True))

            # Line 2: Role • Location
            sub_line_parts = []
            if role:
                sub_line_parts.append(f'<i>{role}</i>')
            if location:
                sub_line_parts.append(f'<font color="#64748b">{location}</font>')
            if sub_line_parts:
                exp_flowables.append(Paragraph(' &bull; '.join(sub_line_parts), tech_style))

            tech_stack = sanitize_text(exp.get('tech_stack', ''))
            if tech_stack:
                exp_flowables.append(Paragraph(f'<b>Core Stack:</b> {tech_stack}', tech_style))
                exp_flowables.append(Spacer(1, 1.8))

            bullets = exp.get('bullets', [])
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                if b and str(b).strip():
                    exp_flowables.append(Paragraph(sanitize_text(b), bullet_style, bulletText='•'))
                    exp_flowables.append(Spacer(1, bullet_gap))
            exp_flowables.append(Spacer(1, spacer_gap * 0.6))

            # Keep individual experience entry cohesive on a single page
            story.append(KeepTogether(exp_flowables))

    # 6. Enterprise / Flagship Software Projects
    if proj_list:
        sec_name = 'FLAGSHIP SOFTWARE PROJECTS' if exp_list else 'TECHNICAL & ENTERPRISE PROJECTS'
        add_section_header(sec_name)
        for proj in proj_list:
            if not isinstance(proj, dict):
                continue
            proj_flowables = []
            title = sanitize_text(proj.get('title', ''))
            role = sanitize_text(proj.get('role', ''))
            duration = sanitize_text(proj.get('period') or proj.get('duration') or '')
            tech_stack = sanitize_text(proj.get('tech_stack', ''))

            # Left: Project Title (Bold), Right: Role (Italics) or Date
            if duration:
                proj_flowables.append(create_split_header(f'<b>{title}</b> &nbsp;|&nbsp; <i>{role}</i>' if role else f'<b>{title}</b>', duration, is_date=True))
            elif role:
                proj_flowables.append(create_split_header(f'<b>{title}</b>', f'<i>{role}</i>', is_date=False))
            else:
                proj_flowables.append(Paragraph(f'<b>{title}</b>', body_style))

            if tech_stack:
                proj_flowables.append(Paragraph(f'<b>Technologies:</b> {tech_stack}', tech_style))
                proj_flowables.append(Spacer(1, 1.8))

            bullets = proj.get('bullets', [])
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                if b and str(b).strip():
                    proj_flowables.append(Paragraph(sanitize_text(b), bullet_style, bulletText='•'))
                    proj_flowables.append(Spacer(1, bullet_gap))
            proj_flowables.append(Spacer(1, spacer_gap * 0.6))

            # Keep individual project entry cohesive on a single page
            story.append(KeepTogether(proj_flowables))

    # 7. Education
    if education_raw:
        add_section_header('EDUCATION')
        edu_items = education_raw if isinstance(education_raw, list) else [education_raw]
        edu_flowables = []
        for edu in edu_items:
            if isinstance(edu, dict):
                degree = sanitize_text(edu.get('degree', ''))
                year = sanitize_text(edu.get('year', ''))
                institution = sanitize_text(edu.get('institution', ''))
                gpa = sanitize_text(edu.get('gpa', ''))
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
                edu_flowables.append(Spacer(1, 3.0))
            elif isinstance(edu, str) and edu.strip():
                edu_flowables.append(Paragraph(sanitize_text(edu), body_style))
        edu_flowables.append(Spacer(1, spacer_gap * 0.7))
        story.append(KeepTogether(edu_flowables))

    # 8. Certifications & Achievements
    if certs:
        add_section_header('CERTIFICATIONS & ACHIEVEMENTS')
        cert_flowables = []
        for cert in certs:
            if cert and str(cert).strip():
                cert_flowables.append(Paragraph(sanitize_text(cert), bullet_style, bulletText='•'))
                cert_flowables.append(Spacer(1, bullet_gap))
        story.append(KeepTogether(cert_flowables))

    doc.build(story, canvasmaker=make_numbered_canvas(raw_name))
    return buffer.getvalue()

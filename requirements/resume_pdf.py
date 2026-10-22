"""
High-Precision Single-Page ATS Resume PDF Generator using ReportLab.
Produces 100% vector, machine-readable, ATS-compliant PDF resumes with zero rasterization.
Compatible with Workday, Taleo, Greenhouse, Lever, and iCIMS parsers.
"""

import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


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

    # Strip any tags other than allowed formatting tags (b, i, u)
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
    """
    buffer = io.BytesIO()

    # Determine density based on project count, bullet count & experience count
    proj_list = data.get('projects') or []
    if isinstance(proj_list, dict):
        proj_list = list(proj_list.values())
    proj_count = len(proj_list)
    
    exp_list = data.get('experience') or []
    if isinstance(exp_list, dict):
        exp_list = list(exp_list.values())
    exp_count = len(exp_list)

    total_bullets = sum(len(p.get('bullets', [])) for p in proj_list if isinstance(p, dict))
    total_bullets += sum(len(e.get('bullets', [])) for e in exp_list if isinstance(e, dict))

    is_dense = (proj_count >= 3) or (exp_count >= 1 and proj_count >= 2) or (total_bullets >= 9)

    top_margin = 24 if is_dense else 28
    bottom_margin = 24 if is_dense else 28
    side_margin = 32

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=side_margin,
        rightMargin=side_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )

    styles = getSampleStyleSheet()

    # Dynamic typography sizing to optimize single-page fit while preserving legibility
    name_size = 17 if is_dense else 18.5
    sec_title_size = 10 if is_dense else 10.5
    body_size = 8.2 if is_dense else 8.6
    body_leading = 10.5 if is_dense else 11.5
    bullet_size = 8.0 if is_dense else 8.4
    bullet_leading = 10.2 if is_dense else 11.2
    spacer_gap = 4 if is_dense else 6

    # Styles
    name_style = ParagraphStyle(
        'ATSName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=name_size,
        leading=name_size + 2,
        alignment=1,
        textColor=colors.HexColor('#0f172a'),
        keepWithNext=True
    )
    contact_style = ParagraphStyle(
        'ATSContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3 if is_dense else 8.6,
        leading=11,
        alignment=1,
        textColor=colors.HexColor('#334155'),
        keepWithNext=True
    )
    sec_title_style = ParagraphStyle(
        'ATSSecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=sec_title_size,
        leading=sec_title_size + 2,
        textColor=colors.HexColor('#0f172a'),
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
    right_date_style = ParagraphStyle(
        'ATSRightDate',
        parent=body_style,
        alignment=2,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )
    bullet_style = ParagraphStyle(
        'ATSBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=bullet_size,
        leading=bullet_leading,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=12,
        firstLineIndent=-8
    )

    story = []

    # 1. Header (Name + Contact line)
    raw_name = data.get('name') or 'CANDIDATE NAME'
    story.append(Paragraph(sanitize_text(raw_name).upper(), name_style))
    story.append(Spacer(1, 3))

    contact = data.get('contact') or {}
    if isinstance(contact, dict):
        c_parts = [
            sanitize_text(contact.get('location')),
            sanitize_text(contact.get('phone')),
            sanitize_text(contact.get('email')),
            sanitize_text(contact.get('linkedin')),
            sanitize_text(contact.get('github'))
        ]
        c_line = ' &bull; '.join([p for p in c_parts if p])
    elif isinstance(contact, str):
        c_line = sanitize_text(contact)
    else:
        c_line = ''

    if c_line:
        story.append(Paragraph(c_line, contact_style))
    story.append(Spacer(1, spacer_gap))

    def add_section_header(title):
        story.append(Paragraph(title, sec_title_style))
        story.append(HRFlowable(
            width='100%',
            thickness=1,
            color=colors.HexColor('#0f172a'),
            spaceBefore=1,
            spaceAfter=3 if is_dense else 4
        ))

    # 2. Professional Summary
    summary = data.get('summary')
    if summary and str(summary).strip():
        add_section_header('PROFESSIONAL SUMMARY')
        story.append(Paragraph(sanitize_text(summary), body_style))
        story.append(Spacer(1, spacer_gap))

    # 3. Technical Skills
    skills = data.get('skills')
    if skills:
        add_section_header('TECHNICAL SKILLS')
        if isinstance(skills, dict):
            for cat, sk in skills.items():
                if sk and str(sk).strip():
                    line = f'<b>{sanitize_text(cat)}:</b> {sanitize_text(sk)}'
                    story.append(Paragraph(line, body_style))
                    story.append(Spacer(1, 1.5))
        elif isinstance(skills, list):
            line = f'<b>Core Skills:</b> {sanitize_text(", ".join(skills))}'
            story.append(Paragraph(line, body_style))
        elif isinstance(skills, str):
            story.append(Paragraph(sanitize_text(skills), body_style))
        story.append(Spacer(1, spacer_gap))

    # 4. Professional Work Experience (if present)
    if exp_list:
        add_section_header('PROFESSIONAL WORK EXPERIENCE')
        for exp in exp_list:
            if not isinstance(exp, dict):
                continue
            company = sanitize_text(exp.get('company', ''))
            role = sanitize_text(exp.get('role', ''))
            duration = sanitize_text(exp.get('period') or exp.get('duration') or '')
            location = sanitize_text(exp.get('location', ''))

            company_role = f'<b>{company}</b>'
            if role:
                company_role += f' &mdash; <i>{role}</i>'
            if location:
                company_role += f' &bull; <font color="#64748b">{location}</font>'

            header_table = Table(
                [[
                    Paragraph(company_role, body_style),
                    Paragraph(f'<b>{duration}</b>' if duration else '', right_date_style)
                ]],
                colWidths=['75%', '25%']
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1)
            ]))
            story.append(header_table)

            tech_stack = sanitize_text(exp.get('tech_stack', ''))
            if tech_stack:
                story.append(Paragraph(f'<b>Core Stack:</b> {tech_stack}', ParagraphStyle('ExpTech', parent=body_style, textColor=colors.HexColor('#334155'))))
                story.append(Spacer(1, 1))

            bullets = exp.get('bullets', [])
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                if b and str(b).strip():
                    story.append(Paragraph(f'&bull; {sanitize_text(b)}', bullet_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, spacer_gap - 1))

    # 5. Enterprise Software Projects
    if proj_list:
        section_label = 'FLAGSHIP SOFTWARE PROJECTS' if exp_list else 'TECHNICAL & ENTERPRISE PROJECTS'
        add_section_header(section_label)
        for proj in proj_list:
            if not isinstance(proj, dict):
                continue
            title = sanitize_text(proj.get('title', ''))
            role = sanitize_text(proj.get('role', ''))
            duration = sanitize_text(proj.get('period') or proj.get('duration') or '')
            tech_stack = sanitize_text(proj.get('tech_stack', ''))

            left_header = f'<b>{title}</b>'
            if role:
                left_header += f' &mdash; <i>{role}</i>'

            header_table = Table(
                [[
                    Paragraph(left_header, body_style),
                    Paragraph(f'<b>{duration}</b>' if duration else '', right_date_style)
                ]],
                colWidths=['75%', '25%']
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1)
            ]))
            story.append(header_table)

            if tech_stack:
                story.append(Paragraph(f'<b>Technologies:</b> {tech_stack}', ParagraphStyle('Tech', parent=body_style, textColor=colors.HexColor('#334155'))))
                story.append(Spacer(1, 1))

            bullets = proj.get('bullets', [])
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                if b and str(b).strip():
                    story.append(Paragraph(f'&bull; {sanitize_text(b)}', bullet_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, spacer_gap - 1))

    # 6. Education
    education_raw = data.get('education')
    if education_raw:
        add_section_header('EDUCATION')
        edu_items = education_raw if isinstance(education_raw, list) else [education_raw]
        for edu in edu_items:
            if isinstance(edu, dict):
                degree = sanitize_text(edu.get('degree', ''))
                year = sanitize_text(edu.get('year', ''))
                institution = sanitize_text(edu.get('institution', ''))
                gpa = sanitize_text(edu.get('gpa', ''))
                coursework = sanitize_text(edu.get('coursework', ''))

                edu_table = Table(
                    [[
                        Paragraph(f'<b>{degree}</b>' if degree else '', body_style),
                        Paragraph(f'<b>{year}</b>' if year else '', right_date_style)
                    ]],
                    colWidths=['75%', '25%']
                )
                edu_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1)
                ]))
                story.append(edu_table)

                sub_parts = []
                if institution:
                    sub_parts.append(institution)
                if gpa:
                    sub_parts.append(f'<b>CGPA: {gpa}</b>')
                if sub_parts:
                    story.append(Paragraph(' &bull; '.join(sub_parts), body_style))

                if coursework:
                    story.append(Paragraph(f'<b>Core Coursework:</b> {coursework}', ParagraphStyle('Course', parent=body_style, textColor=colors.HexColor('#475569'))))
                story.append(Spacer(1, 2))
            elif isinstance(edu, str) and edu.strip():
                story.append(Paragraph(sanitize_text(edu), body_style))
        story.append(Spacer(1, spacer_gap))

    # 7. Certifications & Achievements
    certs = data.get('certifications') or []
    if isinstance(certs, str):
        certs = [certs]
    if certs:
        add_section_header('CERTIFICATIONS & ACHIEVEMENTS')
        for cert in certs:
            if cert and str(cert).strip():
                story.append(Paragraph(f'&bull; {sanitize_text(cert)}', bullet_style))

    doc.build(story)
    return buffer.getvalue()

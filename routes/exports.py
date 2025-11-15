import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from models import db, Ticket, Clinic, FpaModification, StandardizedReason
from routes.utils import log_action, _build_tickets_query
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pytz

exports_bp = Blueprint('exports', __name__)

def create_ticket_pdf_final(ticket):
    try:
        buffer = BytesIO()
        
        # --- Colors ---
        dark_teal = colors.HexColor("#0d7a71")
        light_teal_bg = colors.HexColor("#e6f3f3")
        white = colors.white
        black = colors.black
        light_blue_border = colors.HexColor("#a9d4e4")

        # --- Document Setup ---
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=0.5*inch, leftMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)

        # --- Styles ---
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='MainTitle', fontName='Helvetica-Bold', fontSize=24, textColor=white, alignment=TA_LEFT, leading=30))
        styles.add(ParagraphStyle(name='TicketNumber', fontName='Helvetica-Bold', fontSize=11, textColor=black, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='PatientLabel', fontName='Helvetica-Bold', fontSize=16, textColor=dark_teal, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='PatientName', fontName='Helvetica-Bold', fontSize=18, textColor=black, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=12, textColor=white, alignment=TA_LEFT, spaceBefore=10, spaceAfter=5))
        styles.add(ParagraphStyle(name='FieldLabel', fontName='Helvetica-Bold', fontSize=16, textColor=dark_teal, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='FieldValue', fontName='Helvetica-Bold', fontSize=16, textColor=black, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='DoctorLabel', fontName='Helvetica', fontSize=14, textColor=white, alignment=TA_LEFT, spaceBefore=10))
        styles.add(ParagraphStyle(name='SignatureLabel', fontName='Helvetica', fontSize=12, textColor=colors.grey, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='ReasonText', fontName='Helvetica', fontSize=12, textColor=white, alignment=TA_LEFT, spaceBefore=6))

        # --- Patient Name Formatting ---
        patient_name_formatted = ticket.patient.primer_nombre.upper()
        if ticket.patient.apellido_paterno:
            patient_name_formatted += f" {ticket.patient.apellido_paterno[0].upper()}."

        # --- Story Elements ---
        story = []

        # Header
        ticket_id_box = Table([ [Paragraph(f"ID Ticket<br/><b>{ticket.id}</b>", styles['TicketNumber'])] ], colWidths=[1.2*inch], rowHeights=[0.6*inch])
        ticket_id_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), light_teal_bg),
            ('BOX', (0,0), (-1,-1), 1, black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        header_table = Table([[Paragraph("Programación del Alta", styles['MainTitle']), ticket_id_box]], colWidths=[6*inch, 1.5*inch])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(header_table)
        story.append(Spacer(1, 0.2*inch))

        # Patient Box
        patient_table = Table([[Paragraph('Paciente:', styles['PatientLabel']), Paragraph(patient_name_formatted, styles['PatientName'])]], colWidths=[1.8*inch, 5.2*inch], rowHeights=0.7*inch)
        patient_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), light_teal_bg), ('BOX', (0,0), (-1,-1), 2, dark_teal), ('ROUNDEDCORNERS', [10]), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (0,0), 20)]))
        story.append(patient_table)
        story.append(Spacer(1, 0.2*inch))

        # --- Original FPA Section ---
        # Calculate discharge time block for INITIAL FPA (FPA is END of block)
        initial_fpa_hour = ticket.initial_fpa.hour
        initial_fpa_minute = ticket.initial_fpa.minute

        # Si hay minutos, redondeamos a la siguiente hora
        if initial_fpa_minute > 0:
            initial_fpa_hour += 1

        # Redondear al siguiente bloque par si es necesario
        if initial_fpa_hour % 2 != 0:
            initial_fpa_hour += 1

        # Manejar caso edge de medianoche
        if initial_fpa_hour == 0:
            initial_time_block = "22:00 - 00:00"
        elif initial_fpa_hour >= 24:
            initial_time_block = "22:00 - 24:00"
        else:
            # El FPA es el FIN del bloque
            block_end_hour = initial_fpa_hour
            block_start_hour = block_end_hour - 2
            initial_time_block = f"{block_start_hour:02d}:00 - {block_end_hour:02d}:00"

        story.append(Paragraph(f"Fecha probable de alta original ({ticket.overnight_stays} días de pernocte)", styles['SectionTitle']))
        original_fpa_data = [
            [Paragraph("Fecha:", styles['FieldLabel']), Paragraph(ticket.initial_fpa.strftime('%d/%m/%Y'), styles['FieldValue'])],
            [Spacer(1, 0.1*inch)],
            [Paragraph("Hora (entre):", styles['FieldLabel']), Paragraph(initial_time_block, styles['FieldValue'])]
        ]
        original_fpa_table = Table(original_fpa_data, colWidths=[2*inch, 4.5*inch], rowHeights=[0.5*inch, 0.1*inch, 0.5*inch])
        original_fpa_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), white), ('BOX', (0,0), (-1,-1), 3, light_blue_border), ('ROUNDEDCORNERS', [10]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (0,0), 15), ('SPAN', (0,1), (-1,1)),
        ]))
        story.append(original_fpa_table)
        story.append(Spacer(1, 0.2*inch))

        # --- Modification Section (Conditional) ---
        last_mod = sorted(ticket.modifications, key=lambda m: m.modified_at)[-1] if ticket.modifications else None
        if last_mod:
            # Calculate discharge time block for the modification (FPA is END of block)
            fpa_hour = last_mod.new_fpa.hour
            fpa_minute = last_mod.new_fpa.minute

            # Si hay minutos, redondeamos a la siguiente hora
            if fpa_minute > 0:
                fpa_hour += 1

            # Redondear al siguiente bloque par si es necesario
            if fpa_hour % 2 != 0:
                fpa_hour += 1

            # Manejar caso edge de medianoche
            if fpa_hour == 0:
                mod_time_block = "22:00 - 00:00"
            elif fpa_hour >= 24:
                mod_time_block = "22:00 - 24:00"
            else:
                # El FPA es el FIN del bloque
                block_end_hour = fpa_hour
                block_start_hour = block_end_hour - 2
                mod_time_block = f"{block_start_hour:02d}:00 - {block_end_hour:02d}:00"

            story.append(Paragraph("Última Modificación", styles['SectionTitle']))
            mod_fpa_data = [
                [Paragraph("Nueva Fecha:", styles['FieldLabel']), Paragraph(last_mod.new_fpa.strftime('%d/%m/%Y'), styles['FieldValue'])],
                [Spacer(1, 0.1*inch)],
                [Paragraph("Nueva Hora:", styles['FieldLabel']), Paragraph(mod_time_block, styles['FieldValue'])]
            ]
            mod_fpa_table = Table(mod_fpa_data, colWidths=[2*inch, 4.5*inch], rowHeights=[0.5*inch, 0.1*inch, 0.5*inch])
            mod_fpa_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), white), ('BOX', (0,0), (-1,-1), 3, light_blue_border), ('ROUNDEDCORNERS', [10]),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (0,0), 15), ('SPAN', (0,1), (-1,1)),
            ]))
            story.append(mod_fpa_table)
            story.append(Spacer(1, 0.2*inch))

        # --- Signature Section ---
        signature_box = Table([["Firma Médico Tratante y Notas Adicionales"]], colWidths=[7*inch], rowHeights=[1.2*inch]) # Height increased
        signature_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), white), ('BOX', (0,0), (-1,-1), 1, light_blue_border),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.grey), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        signature_section = Table([
            [Paragraph(f"Médico tratante: {ticket.attending_doctor.name if ticket.attending_doctor else 'N/A'}", styles['DoctorLabel'])],
            [Spacer(1, 0.1*inch)],
            [signature_box]
        ], colWidths=[7.5*inch])
        signature_section.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0)]))
        story.append(signature_section)

        # --- Build ---
        main_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main_frame')
        def background_and_content(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(dark_teal)
            canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1)
            canvas.restoreState()

        doc.addPageTemplates([PageTemplate(id='main', frames=[main_frame], onPage=background_and_content)])
        doc.build(story)
        
        buffer.seek(0)
    
    except Exception as e:
        import traceback
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(72, 800, "Error al generar el PDF.")
        c.drawString(72, 780, f"Ticket ID: {ticket.id}")
        c.drawString(72, 760, f"Error: {str(e)}")
        tb_str = traceback.format_exc()
        y = 740
        for line in tb_str.split('\n'):
            c.drawString(72, y, line)
            y -= 15
        c.showPage()
        c.save()
        buffer.seek(0)

    return buffer

@exports_bp.route('/ticket/<ticket_id>/pdf')
@login_required
def export_pdf(ticket_id):
    query = db.session.query(Ticket).filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()
    
    pdf_buffer = create_ticket_pdf_final(ticket)
    
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="ticket_{ticket.id}.pdf"'
    return response

@exports_bp.route('/tickets/reports/excel')
@login_required
def export_excel():
    filters = {
        'status': request.args.get('status', ''),
        'surgery': request.args.get('surgery', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
    }
    query = _build_tickets_query(filters)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Tickets"
    
    headers = [
        'N° Ticket', 'Estado', 'RUT Paciente', 'Nombre Completo', 'Cama', 'Ubicación',
        'Especialidad', 'Cirugía', 'Médico', 'FPA Inicial', 'FPA Actual', 'Noches de Estancia',
        'Criterios de Ajuste', 'Creado Por', 'Fecha Creación',
        'Fecha Posible de Alta (Indicación Médica)', 'Fecha de Alta Calculada (Hoja Maestra)'
    ]

    if current_user.is_superuser:
        headers.insert(6, 'Clínica')

    for i in range(1, 6):
        headers.extend([
            f'Fecha Modificación {i}',
            f'Bloque Modificación {i}',
            f'Usuario Modificación {i}',
            f'Motivo Modificación {i}',
            f'Justificación Modificación {i}'
        ])
        
    ws.append(headers)
    
    for ticket in tickets:
        adjustment_names = ''
        if ticket.adjustment_criteria_snapshot:
            try:
                adjustments = json.loads(ticket.adjustment_criteria_snapshot)
                adjustment_names = ', '.join([adj['name'] for adj in adjustments])
            except (json.JSONDecodeError, TypeError):
                adjustment_names = 'Error en datos de ajuste'

        row = [
            ticket.id,
            ticket.status,
            ticket.patient.rut,
            ticket.patient.full_name,
            ticket.bed_number or '',
            ticket.location or '',
            ticket.surgery.specialty.name,
            ticket.surgery_name_snapshot or ticket.surgery.name,
            ticket.attending_doctor.name if ticket.attending_doctor else 'N/A',
            ticket.initial_fpa.strftime('%Y-%m-%d %H:%M'),
            f"{ticket.current_fpa.strftime('%Y-%m-%d')} {ticket.calculated_discharge_time_block}",
            ticket.overnight_stays,
            adjustment_names,
            ticket.created_by,
            ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            ticket.medical_discharge_date.strftime('%Y-%m-%d') if ticket.medical_discharge_date else 'N/A',
            ticket.system_calculated_fpa.strftime('%Y-%m-%d %H:%M') if ticket.system_calculated_fpa else 'N/A'
        ]

        if current_user.is_superuser:
            row.insert(6, ticket.clinic.name if ticket.clinic else 'N/A')
        
        modifications = sorted(ticket.modifications, key=lambda m: m.modified_at)
        
        for i in range(5):
            if i < len(modifications):
                mod = modifications[i]
                # Calculate discharge time block for this modification (FPA is END of block)
                fpa_hour = mod.new_fpa.hour
                fpa_minute = mod.new_fpa.minute

                # Si hay minutos, redondeamos a la siguiente hora
                if fpa_minute > 0:
                    fpa_hour += 1

                # Redondear al siguiente bloque par si es necesario
                if fpa_hour % 2 != 0:
                    fpa_hour += 1

                # Manejar caso edge de medianoche
                if fpa_hour == 0:
                    slot_name = "22:00 - 00:00"
                elif fpa_hour >= 24:
                    slot_name = "22:00 - 24:00"
                else:
                    # El FPA es el FIN del bloque
                    block_end_hour = fpa_hour
                    block_start_hour = block_end_hour - 2
                    slot_name = f"{block_start_hour:02d}:00 - {block_end_hour:02d}:00"

                row.extend([
                    mod.new_fpa.strftime('%Y-%m-%d'),
                    slot_name,
                    mod.modified_by,
                    mod.reason,
                    mod.justification
                ])
            else:
                row.extend(['', '', '', '', ''])
                
        ws.append(row)
        
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename="reporte_tickets.xlsx"'
    return response

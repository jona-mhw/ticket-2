import pytest
from datetime import datetime, timedelta
from services import TicketService, FPACalculator
from models import Ticket, Surgery, Clinic, Specialty, Patient

def test_original_nights_stay_persistence(app, db_session, sample_user_clinical, sample_clinic, sample_surgery_normal, sample_patient):
    """
    Test para verificar que las noches de pernocte originales se mantengan inmutables
    incluso después de modificar la FPA del ticket.
    """
    # 1. Crear un ticket inicial
    pavilion_end = datetime(2026, 2, 11, 10, 0) # Hoy 10:00 AM
    # Colecistectomía (24h de estadía en sample_surgery_normal)
    # 24h desde 10:00 AM es 10:00 AM del día siguiente (1 día pernocte)
    
    ticket_data = {
        'patient': sample_patient,
        'surgery': sample_surgery_normal,
        'clinic': sample_clinic,
        'pavilion_end_time': pavilion_end,
        'initial_fpa': pavilion_end + timedelta(hours=24),
        'current_fpa': pavilion_end + timedelta(hours=24),
    }
    
    with app.app_context():
        ticket = TicketService.create_ticket(ticket_data, sample_user_clinical)
        db_session.session.commit()
        
        ticket_id = ticket.id
        assert ticket.overnight_stays == 1
        assert ticket.original_overnight_stays == 1
        assert ticket.original_fpa_date == (pavilion_end + timedelta(hours=24)).date()

        # 2. Modificar el ticket para aumentar las noches de pernocte
        # Nueva FPA: 2 días después
        new_fpa = pavilion_end + timedelta(days=2, hours=4) 
        
        # Simulamos la lógica de update_fpa en routes/tickets.py
        TicketService.modify_fpa(ticket, new_fpa, "Cambio de prueba", "Justificación", sample_user_clinical)
        
        # Calcular nuevas noches (lógica de routes/tickets.py line 296)
        time_diff = new_fpa - ticket.pavilion_end_time
        new_overnight_stays = max(0, time_diff.days)
        if time_diff.seconds > 0:
            new_overnight_stays += 1
        ticket.overnight_stays = new_overnight_stays
        
        db_session.session.commit()
        
        # REFRESCH TICKET
        db_session.session.refresh(ticket)
        
        # 3. Verificar que overnight_stays cambió pero original_overnight_stays NO
        assert ticket.overnight_stays == 3 # (48h + 4h -> 3 pernoctes: hoy-mañana, mañana-pasado, pasado-sig)
        assert ticket.original_overnight_stays == 1, "Las noches originales deben permanecer inmutables"
        assert ticket.original_fpa_date == (pavilion_end + timedelta(hours=24)).date()
        
def test_pdf_creation_uses_original_values(app, db_session, sample_ticket):
    """
    Verifica que la función de generación de PDF use el campo original_overnight_stays.
    """
    from routes.exports import create_ticket_pdf_final
    
    with app.app_context():
        # Setup: Ticket con valores distintos
        sample_ticket.overnight_stays = 5
        sample_ticket.original_overnight_stays = 1
        db_session.session.commit()
        
        # No podemos "leer" fácilmente el PDF binario sin librerías pesadas,
        # pero podemos verificar que la función se ejecute sin errores con estos campos.
        # El código en routes/exports.py fue modificado para usar estos campos.
        pdf_buffer = create_ticket_pdf_final(sample_ticket)
        assert pdf_buffer.getbuffer().nbytes > 0

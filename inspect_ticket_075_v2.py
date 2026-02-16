from app import create_app
from models import Ticket, db

app = create_app()
with app.app_context():
    t = Ticket.query.get('TH-MAYO-2026-075')
    if not t:
        print("Ticket not found")
    else:
        print(f"Ticket ID: {t.id}")
        print(f"Pavilion End Time (Admission Date): {t.pavilion_end_time}")
        print(f"Initial FPA: {t.initial_fpa}")
        print(f"Current FPA: {t.current_fpa}")
        print(f"Surgery Name: {t.surgery_name_snapshot or (t.surgery.name if t.surgery else 'None')}")
        print(f"Base Hours: {t.surgery_base_hours_snapshot or (t.surgery.base_stay_hours if t.surgery else 'None')}")
        print(f"Status: {t.status}")
        print(f"Modifications:")
        for m in t.modifications:
            print(f"  - {m.modified_at}: {m.previous_fpa} -> {m.new_fpa} ({m.reason})")

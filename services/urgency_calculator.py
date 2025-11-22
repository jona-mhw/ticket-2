"""
Urgency Calculator - Centralized logic for ticket urgency
"""
from datetime import datetime
from utils.datetime_utils import calculate_time_remaining

class UrgencyCalculator:
    @staticmethod
    def calculate_urgency(ticket):
        """
        Calculate urgency level and time remaining for a ticket.

        Updates the ticket object with:
        - is_scheduled (bool)
        - time_remaining (dict or None)
        - urgency_level (str)

        Urgency Levels:
        - scheduled: Surgery hasn't finished yet (pavilion_end_time > now)
        - expired: FPA passed
        - critical: <= 1 hour remaining
        - warning: <= 6 hours remaining
        - normal: > 6 hours remaining
        - unknown: No FPA
        """
        if not ticket.current_fpa:
            ticket.time_remaining = None
            ticket.urgency_level = 'unknown'
            ticket.is_scheduled = False
            return

        now = datetime.now()

        # Check if scheduled (pavilion end time is in the future)
        # Note: Some legacy code uses strict comparison, we use standard
        if ticket.pavilion_end_time and now < ticket.pavilion_end_time:
            ticket.is_scheduled = True
            ticket.time_remaining = None
            ticket.urgency_level = 'scheduled'
            return

        ticket.is_scheduled = False
        ticket.time_remaining = calculate_time_remaining(ticket.current_fpa)

        if ticket.time_remaining and ticket.time_remaining['expired']:
            ticket.urgency_level = 'expired'
        elif ticket.time_remaining:
            total_hours = ticket.time_remaining['days'] * 24 + ticket.time_remaining['hours']
            if total_hours <= 1:
                ticket.urgency_level = 'critical'
            elif total_hours <= 6:
                ticket.urgency_level = 'warning'
            else:
                ticket.urgency_level = 'normal'
        else:
            # Should not be reached if calculate_time_remaining works correctly for valid dates
            ticket.urgency_level = 'unknown'

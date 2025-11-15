"""
TimeBlockHelper - Utilidad para generar bloques horarios de 2 horas.

Issue #54: Eliminación de redundancia DischargeTimeSlot BD vs Lógica.
Los bloques horarios son FIJOS (24 bloques de 2h) y no requieren almacenamiento en BD.
"""
from datetime import datetime, time


class TimeBlockHelper:
    """Helper estático para generar y manipular bloques horarios de 2 horas."""

    @staticmethod
    def get_all_blocks():
        """
        Genera todos los bloques horarios posibles (24 bloques de 2 horas).

        Cada bloque termina en una hora específica y tiene 2 horas de duración.
        El extremo DERECHO del bloque es la hora de referencia.

        Returns:
            list[dict]: Lista de 24 bloques con estructura:
                - value (int): Hora de fin del bloque (0-23)
                - label (str): Nombre del bloque "HH:00 - HH:00"
                - start_hour (int): Hora de inicio (0-23)
                - end_hour (int): Hora de fin (0-23)

        Example:
            >>> blocks = TimeBlockHelper.get_all_blocks()
            >>> blocks[14]
            {
                'value': 14,
                'label': '12:00 - 14:00',
                'start_hour': 12,
                'end_hour': 14
            }
        """
        blocks = []
        for end_hour in range(24):  # 0, 1, 2, ..., 23
            start_hour = (end_hour - 2) % 24

            blocks.append({
                'value': end_hour,
                'label': f'{start_hour:02d}:00 - {end_hour:02d}:00',
                'start_hour': start_hour,
                'end_hour': end_hour
            })

        return blocks

    @staticmethod
    def get_block_for_time(dt):
        """
        Calcula el bloque horario correspondiente a un datetime dado.

        Aplica redondeo a la hora entera más cercana (Issue #53):
        - 0-29 minutos → Redondear ABAJO
        - 30-59 minutos → Redondear ARRIBA

        Esa hora es el extremo DERECHO del bloque de 2 horas.

        Args:
            dt (datetime): Datetime para el cual calcular el bloque

        Returns:
            dict: Bloque horario con la misma estructura que get_all_blocks()

        Example:
            >>> dt = datetime(2025, 11, 15, 14, 30)
            >>> block = TimeBlockHelper.get_block_for_time(dt)
            >>> block['label']
            '13:00 - 15:00'  # 14:30 redondea a 15:00, bloque 13-15
        """
        hour = dt.hour
        minute = dt.minute

        # Redondeo a hora más cercana (Issue #53)
        if minute >= 30:
            hour += 1  # Redondear ARRIBA
        # Si < 30, mantener hora actual (redondear ABAJO)

        # Manejar medianoche (24:00 → 00:00)
        if hour >= 24:
            hour = 0

        # La hora redondeada es el extremo DERECHO del bloque
        block_end = hour
        block_start = (block_end - 2) % 24

        return {
            'value': block_end,
            'label': f'{block_start:02d}:00 - {block_end:02d}:00',
            'start_hour': block_start,
            'end_hour': block_end
        }

    @staticmethod
    def get_block_label(end_hour):
        """
        Genera el label de un bloque dado su hora de fin.

        Args:
            end_hour (int): Hora de fin del bloque (0-23)

        Returns:
            str: Label del bloque "HH:00 - HH:00"

        Example:
            >>> TimeBlockHelper.get_block_label(14)
            '12:00 - 14:00'
        """
        start_hour = (end_hour - 2) % 24
        return f'{start_hour:02d}:00 - {end_hour:02d}:00'

    @staticmethod
    def get_end_time(end_hour):
        """
        Genera un objeto time para la hora de fin de un bloque.

        Args:
            end_hour (int): Hora de fin del bloque (0-23)

        Returns:
            time: Objeto time con la hora de fin

        Example:
            >>> end_time = TimeBlockHelper.get_end_time(14)
            >>> end_time
            datetime.time(14, 0)
        """
        return time(hour=end_hour, minute=0, second=0)

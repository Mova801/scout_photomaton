# import cups

class PrinterJobStates:
    # Stati possibili:
    # 3 = pending (in attesa)
    # 4 = pending-held (in attesa, bloccato)
    # 5 = processing (in elaborazione)
    # 6 = processing-stopped (elaborazione fermata)
    # 7 = canceled (annullato)
    # 8 = aborted (interrotto)
    # 9 = completed (completato)
    PENDING = 3
    PENDING_HELD = 4
    PROCESSING = 5
    PROCESSING_STOPPED = 6
    CANCELED = 7
    ABORTED = 8
    COMPLETED = 9

class PrinterManager:
    
    def __init__(self):
        pass
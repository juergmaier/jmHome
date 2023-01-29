

import os

absPfadDaten = None

def setAbsPfadDaten(relPfadDaten):
    global absPfadDaten
    absPfadDaten = os.path.abspath(relPfadDaten)
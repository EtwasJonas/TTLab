import os
import sys

# Tests laufen aus backend/ heraus: app-Paket auffindbar machen,
# unabhängig vom aktuellen Arbeitsverzeichnis.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

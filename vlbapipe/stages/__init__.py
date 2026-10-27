from .importdata import ImportData
from .priorcals import PriorCals

# Pipeline order. Later stages (fringefit, bandpass, applycal, selfcal,
# imaging) are appended here as they are ported from the notebook.
ALL_STAGES = [ImportData, PriorCals]

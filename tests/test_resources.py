from eeg_uhb.utils.EEGStressDetector import EEGStressDetector

def test_fuzzy_loads():
    system = EEGStressDetector.load_fuzzy_system()
    assert system is not None
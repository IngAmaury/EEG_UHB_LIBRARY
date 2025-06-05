from .utils.EEGStressDetector import EEGStressDetector
import numpy as np

def process_data(samples):
    eeg_segment = np.array(samples)
    features = EEGStressDetector.feature_extraction(eeg_segment[:, :8])
    print("Características extraídas.")
    return features

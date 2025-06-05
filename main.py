from eeg_uhb.acquisition import EEGAcquisitionManager
import time

if __name__ == "__main__":
    EEG = EEGAcquisitionManager()
    start_time = time.time()
    duration = 15
    try:
        EEG.start_acquisition()
        while time.time() - start_time < duration:
            time.sleep(0.05)
        EEG.stop_acquisition(save_path="./data", username="test_user")
    except Exception as e:
        print(f"Error: {e}")

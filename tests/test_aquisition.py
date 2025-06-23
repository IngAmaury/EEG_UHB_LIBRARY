from eeg_uhb import EEGAcquisitionManager
import time

if __name__=='__main__':
    EEG = EEGAcquisitionManager()
    start_time = time.time()
    duration = 0.04  # segundos
    
    # Prueba con guardado automático
    EEG.start_acquisition(stream_name='UN-2023.07.40',save=True)
    # Monitoreo en tiempo real
    start = time.sleep(duration)
    print(EEG.data)
    print(f'Length: {len(EEG.data)}')
    EEG.stop_acquisition()
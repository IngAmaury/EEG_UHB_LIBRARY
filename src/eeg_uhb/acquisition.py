import time
import threading
import queue
import numpy as np
import logging
from pylsl import StreamInlet, resolve_stream

from .processing import process_data
from .io import data_write, save_data
from .errors import EEGConnectionError

class EEGAcquisitionManager:
    def __init__(self, buffer_size=500, callback=None):
        self.running = False
        self.stream_inlet = None
        self.task_queue = None
        self.acquisition_thread = None
        self.processing_thread = None
        self.buffer = []
        self.EEG_data = []
        self.sample_count = 0
        self.start_time = None
        self.buffer_size = buffer_size
        self.callback = callback
        self.channels = None
        self.fs = None

    def resolve_eeg_stream(self, timeout=1):
        print("Buscando flujo EEG...")
        streams = []
        def resolve():
            streams.extend(resolve_stream('type', 'EEG'))
        try:
            resolve_thread = threading.Thread(target=resolve, daemon=True)
            resolve_thread.start()
            resolve_thread.join(timeout=timeout)
            if not streams:
                logging.warning("No se encontró ningún flujo de datos de EEG.")
                raise EEGConnectionError("No se encontró ningún flujo EEG.")
        except EEGConnectionError:
            raise
        except Exception as e:
            print(f"Error: {e}")
        return streams if not streams else streams[0]

    def start_acquisition(self):
        try:
            self.task_queue = queue.Queue()
            self.sample_count = 0
            self.EEG_data = []
            self.buffer = []
            self.start_time = time.time()

            streams = self.resolve_eeg_stream()
            if not streams:
                raise EEGConnectionError("No se encontró ningún equipo EEG disponible.")

            self.stream_inlet = StreamInlet(streams)
            self.channels = self.stream_inlet.info().channel_count()
            self.fs = self.stream_inlet.info().nominal_srate()

            print(f"Conectado a: {self.stream_inlet.info().name()} con {self.channels} canales a {self.fs} Hz")

            self.running = True
            self.acquisition_thread = threading.Thread(target=self.record_data, daemon=True)
            self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)

            self.acquisition_thread.start()
            self.processing_thread.start()

            if self.callback:
                self.callback("info", "Adquisición iniciada.")
            return True
        except EEGConnectionError:
            self.running = False
            raise
        except Exception as e:
            self.running = False
            if self.callback:
                self.callback("error", f"Error en adquisición EEG: {e}")
            print(f"Error crítico: {e}")
            return False

    def record_data(self):
        try:
            while self.running:
                samples, timestamps = self.stream_inlet.pull_chunk(timeout=1, max_samples=int(self.fs))
                if samples:
                    try:
                        self.task_queue.put((samples, timestamps), timeout=1)
                    except queue.Full:
                        print("Advertencia: Cola llena.")
        except Exception as e:
            print(f"Error en adquisición: {e}")
        finally:
            print("Hilo de adquisición terminado.")

    def process_queue(self):
        while self.running or not self.task_queue.empty():
            try:
                samples, timestamps = self.task_queue.get(timeout=1.1)
                self.buffer.extend(samples)
                if len(self.buffer) >= self.buffer_size:
                    process_data(self.buffer[:self.buffer_size])
                    self.buffer = self.buffer[self.buffer_size:]
                data_write(self.EEG_data, samples, timestamps)
                self.task_queue.task_done()
            except queue.Empty:
                pass

    def stop_acquisition(self, save_path=None, username="user"):
        self.running = False
        try:
            if self.acquisition_thread:
                self.acquisition_thread.join(timeout=2)
        except Exception as e:
            print(f"Error al detener hilos: {e}")
        if save_path:
            save_data(self.EEG_data, save_path, username)
        if self.callback:
            self.callback("info", "Adquisición detenida.")

from .errors import EEGConnectionError
from .processing import EEGStressDetector
from pylsl import StreamInlet, resolve_stream
import csv
import datetime
import logging
import numpy as np
import os
import pickle
import queue
import threading
import time

class EEGAcquisitionManager:
    def __init__(self, buffer_size=500, callback=None):
        """
       Initializes the EEG acquisition system.
        
        Args:
            buffer_size: Buffer size for processing (samples)
            callback: Notifications function (optional)
        """
        # Basic config
        self.buffer_size = buffer_size
        self.callback = callback
        self.headers = (['Timestamp','Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8', 'ACC1', 'ACC2',
                                    'ACC3', 'GYR1', 'GYR2', 'GYR3', 'BAT', 'CNT', 'VALID', 'DT', 'TRIG'])

        # System state
        self.data = []
        self.running = False
        self.sample_count = 0
        self.start_time = None
        self.timestamps = []

        # Hardware
        self.channels = None
        self.fs = None
        self.stream_inlet = None

        # Processing
        self._create_reference = False
        self._reference_count = 0
        self._reference_sum = None
        self.buffer = []
        self.current_stress_level = None
        self.fuzzy_system = EEGStressDetector.load_fuzzy_system()

        # Saving
        self.csv_writer = None
        self.current_save_path = None
        self.data_file = None


        # Threads and queues
        self.acquisition_thread = None
        self.processing_thread = None
        self.storage_thread = None
        self.data_queue = queue.Queue()  # Raw Data
        self.process_queue = queue.Queue()  # Processed Data

    @staticmethod
    def resolve_eeg_stream(name: None|str = None, timeout=1):
        """Searches and resolves an EEG stream available in LSL."""
        print("Searching EEG flow...")
        streams = []
        stream_type = 'name' if name else 'type'
        stream_id = name if name else 'EEG'
        def resolve(st_type, st_id):
            # Search and save stream
            streams.extend(resolve_stream(st_type, st_id))  
        
        try:
            resolve_thread = threading.Thread(target=resolve, 
                                              args=(stream_type,stream_id),
                                              daemon=True)
            resolve_thread.start()
            resolve_thread.join(timeout=timeout)
            if not streams:
                print("DEBUG - LSL return empty list")  # Para confirmar
                raise EEGConnectionError("No EEG data stream found.")

        except EEGConnectionError:
            raise
        except Exception as e:
            print(f"DEBUG - Error: {type(e).__name__}: {str(e)}")  # <--- Esto revelará el error real
        finally:
            return streams if not streams else streams[0]
    
    def _initialize_data_file(self):
        """Create the CSV file and write the headers."""
        
        filename = f"EEG_RAW_{datetime.datetime.now().strftime('%d_%m_%Y__%H_%M_%S')}.csv"
        os.makedirs(self.current_save_path, exist_ok=True)
        self.filepath = os.path.join(self.current_save_path, filename)
        self.data_file = open(self.filepath, mode="a", newline="")
        self.csv_writer = csv.writer(self.data_file)
        
        if self.channels == 19 and self.stream_inlet.info().name() == 'UnicornRecorderLSLStream':
            """
            These labels are only valid for the 8-electrode UHB and if all channels are marked 
            in the Unicorn Recorderd app configuration.
            """
            self.csv_writer.writerow(self.headers)
        elif self.channels == 17:
            '''
            These labels are only valid for the 8-electrode UHB and if you are using the UnicornLSL tool.
            '''
            self.csv_writer.writerow(self.headers[:18])
    
    def _initialize_features_file(self):
        """Crea archivo CSV para features si no existe."""
        if not self.current_save_path:
            return
            
        self.features_filepath = os.path.join(
            self.current_save_path,
            f"EEG_FEATURES_{datetime.datetime.now().strftime('%d_%m_%Y__%H_%M_%S')}.csv"
        )
        self.features_writer = None
        # Abrir archivo en modo append si es la primera vez
        if not hasattr(self, 'features_writer') or self.features_writer is None:
            self.features_file = open(self.features_filepath, 'a', newline='')
        # Esperar a tener el primer feature para escribir los headers
        self.features_headers_written = False
    
    def _initialize_zero_reference(self):
        """Initializes a reference dictionary with values at zero for all expected stress characteristics"""
        # Aquí asumo que conoces las claves de las características extraídas
        feature_keys = ["Energy_Theta", "Energy_Alpha", "Energy_Beta", "Theta/Beta", "Alpha/Beta"]
        self._reference = {k: 0.0 for k in feature_keys}
        logging.info("An EEG reference with zero values was created.")


    def start_acquisition(self, stream_name: None | str = None, save: bool = False, 
                          save_path: str | None = None, process: bool = False, 
                          create_reference: bool = False):
        """
        Starts EEG data acquisition.
        
        Args:
            save: If True, the data will be stored.
            save_path: Path to save data (optional)
            only_acquisition: If True, it only acquires data without processing.
        """
        try:
            # Configuración inicial
            self.buffer = []
            self.running = True
            self.sample_count = 0
            self.start_time = time.time()

            # Resolver conexión EEG
            streams = self.resolve_eeg_stream(name = stream_name)
            if not streams:
                logging.warning("It was not possible to find an EEG stream available at LSL.")
                raise EEGConnectionError("No available EEG equipment was found. Check the connection.")
            
            self.stream_inlet = StreamInlet(streams)
            self.channels = self.stream_inlet.info().channel_count()
            self.fs = self.stream_inlet.info().nominal_srate()
            
            self.acquisition_thread = threading.Thread(
                target=self._acquisition_loop, 
                daemon=True
            )
            self.acquisition_thread.start()
            print('Acquisition started')
            if save:
                self.current_save_path = save_path if save_path else './Data'
                # Crear archivo de guardado
                self._initialize_data_file()

                self.storage_thread = threading.Thread(
                    target=self._storage_loop,
                    daemon=True
                )
                self.storage_thread.start()
            
            if process:
                self._create_reference = create_reference
                if self._create_reference:
                    self._reference_sum: dict[str, np.ndarray] = {}
                    self._reference_count: int = 0
                else:
                    # Caso: No se va a crear referencia pero sí procesamiento.
                    # Intentar cargar referencia si existe
                    _parent_dir = os.path.dirname(self.current_save_path or ".")
                    ref_dir = os.path.join(_parent_dir, "Stage_0")
                    if os.path.exists(ref_dir) and os.path.isdir(ref_dir):
                        ref_files = [f for f in os.listdir(ref_dir) if f.startswith("EEG_REFERENCE") and f.endswith(".pkl")]
                        if ref_files:
                            # Tomar el primero en orden alfabético
                            ref_files.sort()
                            ref_path = os.path.join(ref_dir, ref_files[0])
                            try:
                                with open(ref_path, "rb") as f:
                                    self._reference = pickle.load(f)
                                logging.info(f"Referencia EEG cargada desde: {ref_path}")
                            except Exception as e:
                                logging.warning(f"No se pudo cargar la referencia EEG ({ref_path}): {e}")
                                self._initialize_zero_reference()
                        else:
                            logging.warning("No se encontraron archivos de referencia EEG en Stage_0.")
                            self._initialize_zero_reference()
                    else:
                        logging.warning("No se encontró la carpeta Stage_0 para la referencia EEG.")
                        self._initialize_zero_reference()

                if not hasattr(self, 'features_filepath'):
                    self._initialize_features_file()
                self.processing_thread = threading.Thread(
                    target=self._processing_loop,
                    daemon=True
                )
                self.processing_thread.start()
            
            if self.callback:
                # Conditional on callback logic
                self.callback("info", "Start of EEG acquisition.")
            
            logging.info('Start of EEG acquisition.')
            return True
            
        except Exception as e:
            self.running = False
            logging.error(f"Error al iniciar adquisición EEG: {str(e)}")
            if self.callback:
                self.callback("error", f"Error al iniciar: {str(e)}")
            return False

    def _acquisition_loop(self):
        """Data acquisition loop."""
        try:
            while self.running:
                sample, timestamp = self.stream_inlet.pull_sample()
                self.data.append(sample)
                self.timestamps.append(timestamp)
                if sample:
                    # Enviar datos para almacenamiento
                    self.data_queue.put((sample, timestamp))
                    self.process_queue.put((sample, timestamp))
                        
        except Exception as e:
            logging.error(f"Acquisition error: {str(e)}")
        finally:
            logging.info("Acquisition thread completed")

    def _storage_loop(self):
        """Data storage loop."""
        while self.running or not self.data_queue.empty():
            try:
                sample, timestamp = self.data_queue.get(timeout=1)
                
                # Escribir datos si hay configuración de almacenamiento
                if hasattr(self, 'csv_writer'):
                    try:
                        self.csv_writer.writerow([timestamp] + sample)
                        self.sample_count += 1
                    except Exception as e:
                        logging.error(f"Error writing data: {str(e)}")
                        self._close_storage()
                            
                self.data_queue.task_done()
                
            except queue.Empty:
                pass

    def _processing_loop(self):
        """Bucle para procesamiento de datos."""
        while self.running or not self.process_queue.empty():
            try:
                samples, timestamps = self.process_queue.get(timeout=2)
                self.buffer.extend(samples)
                
                # Procesar cuando tengamos suficientes muestras
                if len(self.buffer) >= self.buffer_size:
                    segment = np.array(self.buffer[:self.buffer_size])
                    features = EEGStressDetector.feature_extraction_v2(segment[:, :8])
                    if not self._create_reference:
                        _stress_per_channel = EEGStressDetector.process_fuzzy_inference(self.fuzzy_system, features, self._reference)
                        self.current_stress_level = EEGStressDetector.stress_state(_stress_per_channel)

                    self.buffer = self.buffer[self.buffer_size:]
                    
                    # Añadir timestamp de referencia (primera muestra del segmento)
                    features_dict = {
                        'timestamp': timestamps[0],  # Usamos el primer timestamp del chunk
                        **features  # Desempaquetamos todas las características
                    }
                    
                    # Guardar features (nueva funcionalidad)
                    self._save_features(features_dict)

                    if getattr(self, "_create_reference", False):
                        for k, v in features.items():          # saltamos timestamp
                            self._reference_sum.setdefault(k, np.zeros_like(v))
                            self._reference_sum[k] += v
                        self._reference_count += 1
                    
                self.process_queue.task_done()
                
            except queue.Empty:
                pass

    def _save_features(self, features_dict):
        """Guarda features desagregando los valores por canal."""
        if not hasattr(self, 'features_filepath'):
            self._initialize_features_file()
            
        try:
            # Generar filas desagregadas por canal
            rows = self._expand_feature_rows(features_dict)
            
            # Escribir al archivo
            for row in rows:
                if not self.features_headers_written:
                    self.features_writer = csv.DictWriter(self.features_file, 
                                                        fieldnames=row.keys())
                    self.features_writer.writeheader()
                    self.features_headers_written = True
                    
                self.features_writer.writerow(row)
                
        except Exception as e:
            logging.error(f"Error al guardar features: {str(e)}")
            
        except Exception as e:
            logging.error(f"Error al guardar features: {str(e)}")
            if hasattr(self, 'features_file'):
                self.features_file.close()
            self.features_writer = None

    def _expand_feature_rows(self, features_dict):
        """Convierte un diccionario de features en filas por canal."""
        rows = []
        channel_names = ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8']
        
        for feature_name, feature_values in features_dict.items():
            # Saltar el timestamp (no es un array)
            if feature_name == 'timestamp':
                timestamp = feature_values
                continue
                
            # Solo procesar arrays del tamaño correcto
            if not isinstance(feature_values, (list, np.ndarray)) or len(feature_values) != 8:
                continue
                
            for channel_idx, channel_value in enumerate(feature_values):
                rows.append({
                    'timestamp': timestamp,
                    'feature': feature_name,
                    'channel': channel_names[channel_idx],
                    'value': channel_value
                })
        
        return rows

    def _close_storage(self):
        """Cierra los recursos de almacenamiento de manera segura."""
        if hasattr(self, 'data_file') and self.data_file:
            try:
                self.data_file.close()
            except Exception as e:
                logging.error(f"Error al cerrar archivo: {str(e)}")
            finally:
                del self.data_file
                del self.csv_writer
        # Cerrar archivo de features si existe
        if hasattr(self, 'features_file') and self.features_file:
            try:
                self.features_file.close()
            except Exception as e:
                logging.error(f"Error al cerrar archivo de features: {str(e)}")

    def stop_acquisition(self):
        """Detiene la adquisición y libera recursos."""
        self.running = False
        self.data = []
        self.timestamps = []

        try:
            # Esperar a que los hilos terminen
            if self.acquisition_thread:
                self.acquisition_thread.join(timeout=2)
            if self.storage_thread:
                self.storage_thread.join(timeout=1)
            if self.processing_thread:
                self.processing_thread.join(timeout=1)
                
            # Cerrar almacenamiento
            self._close_storage()

            # Cálculo y guardado del prototipo
            if getattr(self, "_create_reference", False) and self._reference_count:
                reference = {
                    k: v / self._reference_count for k, v in self._reference_sum.items()
                }
                ts = datetime.datetime.now().strftime('%d_%m_%Y__%H_%M_%S')
                
                # Crear la referencia dentro de la ruta actual
                ref_path = os.path.join(self.current_save_path, f"EEG_REFERENCE_{ts}.pkl")
                with open(ref_path, "wb") as f:
                    pickle.dump(reference, f)
                logging.info(f"Referencia EEG guardada en: {ref_path}")
            
            logging.info('Fin de adquisición de EEG.')
            
        except Exception as e:
            logging.error(f"Error al detener adquisición: {str(e)}")

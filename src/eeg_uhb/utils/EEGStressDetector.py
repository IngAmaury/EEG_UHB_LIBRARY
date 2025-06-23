"""
============================================
EEG Stress Detector
============================================
Autor: AmaurySH

Descripción:
------------
Este módulo implementa una clase para el procesamiento y análisis de señales EEG,
incluyendo preprocesamiento, eliminación de artefactos, extracción de características
y evaluación del nivel de estrés mediante lógica difusa.

Funcionamiento:
---------------
1. Se recibe una señal EEG en formato `numpy.ndarray`.
2. Se aplican filtros de preprocesamiento y eliminación de artefactos.
3. Se extraen características mediante transformada wavelet.
4. Se calculan distancias euclidianas relativas y desviaciones estándar (Z-score).
5. Se evalúa el nivel de estrés utilizando un sistema de inferencia difusa.

Clases y Métodos:
-----------------
- **EEGStressDetector**: Clase principal con métodos para el procesamiento y análisis de EEG.
  - `bandpass_filter()`: Aplica un filtro pasa banda a la señal EEG.
  - `remove_artifacts_ica()`: Aplica ICA para eliminación de artefactos.
  - `preprocess_eeg()`: Preprocesa los datos EEG (filtrado y normalización).
  - `feature_extraction()`: Extrae características usando transformada wavelet.
  - `relativeEuclideanDistance()`: Calcula distancias euclidianas relativas.
  - `StressScore()`: Calcula el porcentaje de canales fuera de umbral mediante Z-score.
  - `evaluate_fuzzy_stress()`: Evalúa el nivel de estrés con lógica difusa.
  - `StressLevel()`: Integra las funciones anteriores para determinar el nivel de estrés.

  - **Fuzzy Stress System (fuzzy_stress.py)**: Implementa el sistema de inferencia difusa para la evaluación del estrés.
  - `create_fuzzy_system()`: Crea y configura el sistema difuso con sus entradas, salidas y reglas.
Parámetros de Entrada:
----------------------
- Señal EEG (`numpy.ndarray` o lista de listas).
- Frecuencia de muestreo (`int`, por defecto 250 Hz).
- Estado basal (`dict` con métricas de referencia).
- Estado actual (`dict` con métricas EEG recientes).

Salida:
------
- Un diccionario con:
  - **`metrics`**: Contiene `relative_distances` y `stres_score`.
  - **`stress_level`**: Tuple con el nivel de estrés (`'Bajo'`, `'Medio'`, `'Alto'`) y su valor numérico (0-100).

Ejemplo de Uso:
---------------
```python
# Cargar datos EEG
df = pd.read_csv("test.csv", usecols=range(2, 11), nrows=500)
eeg_data = df.to_numpy()

# Preprocesamiento
eeg_preprocesado = EEGStressDetector.preprocess_eeg(eeg_data, sampling_rate=250)

# Extracción de características
caracteristicas = EEGStressDetector.feature_extraction(eeg_preprocesado, 250)

# Cálculo del nivel de estrés
nivel_estres = EEGStressDetector.StressLevel(basal, basal_std, actual)
print(f"Nivel de estrés: {nivel_estres['stress_level'][0]}, valor: {nivel_estres['stress_level'][1]:.2f}%")
```

Dependencias:
-------------
- `numpy`: Para operaciones matemáticas y manejo de arreglos.
- `scipy.signal`: Para filtrado digital de señales EEG.
- `sklearn.decomposition.FastICA`: Para eliminación de artefactos.
- `pywt`: Para extracción de características con transformada wavelet.
- `skfuzzy`: Para la implementación del sistema de inferencia difusa.
- `pandas`: Para carga y manipulación de datos EEG desde archivos CSV.

Notas:
------
- Asegurar que la señal EEG esté correctamente formateada antes de procesarla.
- Se recomienda una frecuencia de muestreo de 250 Hz para mejores resultados.
- La evaluación del estrés difuso está basada en estudios EEG y puede ajustarse según el contexto de aplicación.
"""
import numpy as np
from scipy.signal import filtfilt
import time
import pickle
import skfuzzy as fuzz
from collections import Counter
from typing import Union, Dict, Any, Tuple, List
import os

def measureRunTime(funcion):
    """
    Decorador para medir el tiempo de ejecución de una función.

    :param funcion: function
        La función cuya ejecución se desea medir.
    
    :return: function
        Una función envuelta que, al ser llamada, ejecutará la función original
        y mostrará el tiempo que tomó en ejecutarse.

    Uso:
        @measureRunTime
        def mi_funcion():
            # Código que tarda en ejecutarse
            time.sleep(2)

        mi_funcion()  
        # Salida: Tiempo de ejecución: 2.0000 segundos
    """
    def envoltura(*args, **kwargs):
        inicio = time.perf_counter()  # Usa perf_counter para mayor precisión
        resultado = funcion(*args, **kwargs)
        fin = time.perf_counter()
        print(f"Tiempo de ejecución: {fin - inicio:.5f} segundos")
        return resultado
    return envoltura

class EEGStressDetector:
    """
    Clase para el procesamiento y análisis de señales EEG con métodos de filtrado, eliminación de artefactos y extracción de características.
    """

    # Obtener la ruta absoluta del directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(current_dir, "..", "resources")
    resources_dir = os.path.abspath(resources_dir)
    fuzzy_path = os.path.join(resources_dir, "Fuzzy_Systems.pkl")
    coefficient_filters_path = os.path.join(resources_dir,'coefficient_filters_dict.pkl')

    @staticmethod
    def load_fuzzy_system(pkl_file: str = fuzzy_path, system_name: str = "Sistema 1", onlySystem: bool = True) -> Union[Any, Dict[str, Any]]:
        """
        Carga un sistema difuso desde un archivo `.pkl` y retorna el sistema solicitado.

        Esta función permite recuperar un sistema difuso almacenado en un diccionario dentro de un archivo `.pkl`.
        Se puede seleccionar si solo se desea obtener el sistema (`system`) o también su descripción (`description`).

        Parámetros:
        -----------
        pkl_file : str
            Ruta del archivo `.pkl` que contiene los sistemas difusos serializados.
        
        system_name : str
            Nombre del sistema difuso a cargar. Debe coincidir con una de las claves del diccionario en el archiv: "Sistema #",
            actualmente (17/03/2025) tiene 3.
        
        onlySystem : bool, opcional (por defecto = True)
            - Si `True`, solo devuelve el objeto `system` (modelo difuso).
            - Si `False`, devuelve un diccionario con el `system` y su `description`.

        Retorna:
        --------
        Union[Any, Dict[str, Any]]
            - Si `onlySystem=True`, retorna solo el objeto `system` correspondiente al sistema difuso.
            - Si `onlySystem=False`, retorna un diccionario con las claves:
            - `"system"`: El sistema difuso cargado.
            - `"description"`: Descripción del sistema en formato string.

        Excepciones:
        ------------
        - FileNotFoundError: Si el archivo especificado no existe.
        - KeyError: Si el `system_name` no se encuentra en el diccionario de sistemas.
        - pickle.UnpicklingError: Si el archivo no es un `.pkl` válido o está corrupto.
        - Exception: Para otros errores inesperados al abrir o deserializar el archivo.

        Ejemplo de uso:
        ---------------
        >>> sistema = load_fuzzy_system("Fuzzy_Systems.pkl", "Sistema 1")
        >>> print(sistema)

        >>> sistema_completo = load_fuzzy_system("Fuzzy_Systems.pkl", "Sistema 1", onlySystem=False)
        >>> print(sistema_completo["description"])

        Notas:
        ------
        - La función carga el archivo solo en modo lectura (`rb`).
        - Se recomienda verificar los nombres de los sistemas almacenados antes de llamarlos.
        - El archivo `.pkl` debe contener un diccionario con sistemas en la estructura esperada:
        { "Sistema X": { "system": objeto_sistema, "description": "texto descriptivo" }, ... }
        """
        try:
            # Cargar el diccionario de sistemas difusos
            with open(pkl_file, "rb") as archivo:
                sistemas_difusos: Dict[str, Dict[str, Any]] = pickle.load(archivo)

            # Verificar si el sistema solicitado está en el diccionario
            if system_name not in sistemas_difusos:
                raise KeyError(f"El sistema '{system_name}' no se encuentra en el archivo '{pkl_file}'.")

            # Retornar según la opción onlySystem
            if onlySystem:
                return sistemas_difusos[system_name]["system"]
            else:
                return sistemas_difusos[system_name]  # Devuelve todo el diccionario { "system": ..., "description": ... }
            print('Modelo difuso cargado')
            

        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{pkl_file}' no fue encontrado.")
        except KeyError as e:
            raise KeyError(str(e))
        except pickle.UnpicklingError:
            raise ValueError(f"Error al deserializar el archivo '{pkl_file}'. Asegúrate de que sea un archivo pickle válido.")
        except Exception as e:
            raise RuntimeError(f"Ocurrió un error al cargar el sistema difuso desde '{pkl_file}': {e}")


    @staticmethod
    def load_dict_coefficient_filters(pkl_file: str = coefficient_filters_path) -> dict:
        """
        Carga un diccionario desde un archivo en formato `.pkl`.

        Esta función estática permite cargar un diccionario previamente guardado 
        en un archivo `.pkl` (pickle). Se utiliza para recuperar coeficientes de 
        filtros almacenados.

        Parámetros:
        -----------
        pkl_file : str, opcional
            Ruta del archivo `.pkl` que contiene el diccionario serializado.
            Por defecto, se asume 'coefficient_filters_dict.pkl'.

        Retorna:
        --------
        dict
            Un diccionario con los coeficientes de filtros almacenados en el archivo.
            La estructura del diccionario es la siguiente:

            coefficient_filters_dict = {
                'butter': [b_butter, a_butter],
                'chebyshev_theta': [b_theta, a_theta],
                'chebyshev_alpha': [b_alpha, a_alpha],
                'chebyshev_beta': [b_beta, a_beta]
            }

            Donde:
            - `b_x` y `a_x` representan los coeficientes del filtro `x` en formato de listas o arrays.
            - `butter` corresponde a un filtro Butterworth.
            - `chebyshev_theta`, `chebyshev_alpha` y `chebyshev_beta` son variantes del filtro Chebyshev.

        Excepciones:
        ------------
        - FileNotFoundError: Si el archivo especificado no existe.
        - pickle.UnpicklingError: Si el archivo no es un `.pkl` válido o está corrupto.
        - Exception: Para otros errores inesperados al abrir o deserializar el archivo.

        Ejemplo de uso:
        --------------
        >>> coeficientes = EEGStressDetector.load_dict_coefficient_filters()
        >>> print(coeficientes)

        Notas:
        ------
        - La función es estática (`@staticmethod`), lo que significa que puede ser 
          llamada sin necesidad de instanciar la clase.
        - Se recomienda verificar que el archivo `.pkl` esté al mismo nivel de carpeta 
          que el archivo EEGStressDetector.py.
        """
        try:
            with open(pkl_file, "rb") as archivo:
                return pickle.load(archivo)
        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{pkl_file}' no fue encontrado.")
        except pickle.UnpicklingError:
            raise ValueError(f"Error al deserializar el archivo '{pkl_file}'. Asegúrate de que sea un archivo pickle válido.")
        except Exception as e:
            raise RuntimeError(f"Ocurrió un error al cargar el diccionario desde '{pkl_file}': {e}")

    @staticmethod
    def energy(signal, axis=0):
        """
        Calcula la energía de una señal multidimensional de cualquier orientación.
        
        Parámetros:
            signal (numpy.ndarray): Arreglo N-dimensional con la señal.
            axis (int): opcional, por defecto = 0
            Eje a lo largo del cual se aplicará la suma:
            - `axis=0`: Filtra a lo largo de las filas (canales organizados en columnas).
            - `axis=1`: Filtra a lo largo de las columnas (canales organizados en filas).

        Retorna:
            float: Energía total de la señal.
        """
        return np.sum(signal ** 2, axis=axis)

    @staticmethod
    def bandpass_filter(data, b, a, axis=0):
        """
        Aplica un filtro digital IIR pasa banda a la señal EEG.

        :param data: ndarray, Señal EEG de entrada.
        :param b: array, Coeficientes del numerador del filtro digital.
        :param a: array, Coeficientes del denominador del filtro digital.
        :param axis : int, opcional (por defecto = 0)
        Eje a lo largo del cual se aplicará el filtro:
        - `axis=0`: Filtra a lo largo de las filas (canales organizados en columnas).
        - `axis=1`: Filtra a lo largo de las columnas (canales organizados en filas).
    
        Retorna:
        --------
        ndarray
            Señal EEG filtrada con el filtro pasa banda aplicado.

        Excepciones:
        ------------
        - ValueError: Se genera si las dimensiones de `data` no son compatibles con los coeficientes `b` y `a`.

        Ejemplo de uso:
        ---------------
        >>> import numpy as np
        >>> from scipy.signal import butter
        >>> fs = 250  # Frecuencia de muestreo (Hz)
        >>> lowcut, highcut = 1, 50  # Frecuencias de corte (Hz)
        >>> b, a = butter(4, [lowcut / (fs / 2), highcut / (fs / 2)], btype='band')
        >>> eeg_data = np.random.randn(1000, 8)  # Simulación de EEG con 1000 muestras y 8 canales
        >>> filtered_data = FiltroCoeficientes.bandpass_filter(eeg_data, b, a, axis=0)
        
        Notas:
        ------
        - `filtfilt` aplica el filtrado en ambas direcciones, eliminando el desfase.
        - Es recomendable verificar que `data` tenga la misma estructura esperada antes de aplicar el filtro
        """
        try:
            filtered_data = filtfilt(b, a, data, axis=axis)
            return filtered_data
        except ValueError as e:
            print(f"❌ Error en filtfilt: {e}. Dimensiones de data: {data.shape}")
            return data  # Devolver los datos sin filtrar en caso de error
        
    @staticmethod
    def standardize(signal: np.ndarray, axis: int = 0) -> float:
        """
        Estandariza una señal multicanal mediante normalización Z-score.

        Esta función aplica la normalización estándar (Z-score) a una señal EEG multicanal, 
        restando la media y dividiendo por la desviación estándar de cada canal. 
        Esto garantiza que cada canal tenga media 0 y varianza 1, facilitando la comparación 
        entre señales y mejorando la estabilidad en modelos de aprendizaje automático.

        Parámetros:
        -----------
        signal : ndarray
            Matriz de la señal EEG de entrada con dimensiones (muestras, canales) o (canales, muestras).
            Puede ser un arreglo unidimensional o multidimensional.

        axis : int, opcional (por defecto = 0)
            Especifica el eje a lo largo del cual se calcularán la media y la desviación estándar:
            - `axis=0`: Estandariza cada columna (canales organizados en columnas).
            - `axis=1`: Estandariza cada fila (canales organizados en filas).

        Retorna:
        --------
        ndarray
            Señal EEG estandarizada con media 0 y desviación estándar 1 en cada canal.

        Excepciones:
        ------------
        - ValueError: Si la señal tiene valores no numéricos o dimensiones incorrectas.

        Ejemplo de uso:
        ---------------
        >>> import numpy as np
        >>> eeg_data = np.random.randn(1000, 8)  # EEG con 1000 muestras y 8 canales
        >>> eeg_standardized = EEGStressDetector.standardize(eeg_data, axis=0)
        >>> print(eeg_standardized.mean(axis=0))  # Debe estar cerca de 0
        >>> print(eeg_standardized.std(axis=0))   # Debe estar cerca de 1

        Notas:
        ------
        - Se utiliza `keepdims=True` para mantener la dimensionalidad original tras el cálculo de la media y la desviación.
        - Se reemplaza cualquier desviación estándar igual a 0 con 1 para evitar divisiones por cero en canales con valores constantes.
        - Este método es común en preprocesamiento de señales fisiológicas y redes neuronales.
        """
        try:
            # Verificar que la entrada sea un ndarray
            if not isinstance(signal, np.ndarray):
                raise TypeError("La señal de entrada debe ser un ndarray.")

            # Verificar si la señal contiene datos no numéricos
            if not np.issubdtype(signal.dtype, np.number):
                raise ValueError("La señal de entrada contiene valores no numéricos.")

            mean = np.mean(signal, axis=axis, keepdims=True)  # Media por canal
            std = np.std(signal, axis=axis, keepdims=True, ddof=0)  # Desviación estándar sin sesgo
            std[std == 0] = 1  # Evitar división por 0 en canales constantes
            return (signal - mean) / std

        except ValueError as e:
            raise ValueError(f"Error en la estandarización: {e}")

        except TypeError as e:
            raise TypeError(f"Error en la entrada de datos: {e}")

        except Exception as e:
            raise RuntimeError(f"Ocurrió un error inesperado durante la estandarización: {e}")

    @staticmethod
    def remove_outliers(signal: np.ndarray, axis: int = 0) -> Tuple[np.ndarray, float]:
        """
        Elimina valores atípicos en una señal multicanal de EEG estandarizada basándose en 2 sigmas.

        Esta función identifica valores atípicos que superen 2 veces la desviación estándar 
        respecto a la media de cada canal y los sustituye por 0. Además, calcula el porcentaje 
        de valores que fueron modificados para evaluar el nivel de ruido en la señal.

        Parámetros:
        -----------
        signal : np.ndarray
            Matriz de la señal EEG de entrada con dimensiones (muestras, canales) o (canales, muestras).
            Se asume que la señal ha sido previamente estandarizada (Z-score).

        axis : int, opcional (por defecto = 0)
            Especifica el eje a lo largo del cual se calculan la media y la desviación estándar:
            - `axis=0`: Evalúa cada columna (canales organizados en columnas).
            - `axis=1`: Evalúa cada fila (canales organizados en filas).

        Retorna:
        --------
        tuple[np.ndarray, float]
            - Señal EEG con valores atípicos reemplazados por 0.
            - Porcentaje de valores que fueron reemplazados.

        Excepciones:
        ------------
        - TypeError: Si la señal de entrada no es un ndarray.
        - ValueError: Si la señal contiene valores no numéricos o si tiene dimensiones incorrectas.

        Ejemplo de uso:
        ---------------
        >>> import numpy as np
        >>> eeg_data = np.random.randn(1000, 8)  # EEG con 1000 muestras y 8 canales
        >>> eeg_cleaned, percentage_removed = remove_outliers(eeg_data, axis=0)
        >>> print(f"Porcentaje de valores eliminados: {percentage_removed:.2f}%")

        Notas:
        ------
        - Se recomienda aplicar esta función después de estandarizar la señal.
        - Un alto porcentaje de eliminación podría indicar una señal con alto nivel de ruido.
        - Se conservan las dimensiones originales de la señal reemplazando outliers con ceros.
        """
        try:
            # Verificar que la entrada sea un ndarray
            if not isinstance(signal, np.ndarray):
                raise TypeError("La señal de entrada debe ser un ndarray.")

            # Verificar si la señal contiene datos no numéricos
            if not np.issubdtype(signal.dtype, np.number):
                raise ValueError("La señal de entrada contiene valores no numéricos.")

             # Determinar valores atípicos (mayores a 2 o menores a -2)
            outliers = np.abs(signal) > 2

            # Calcular porcentaje de valores modificados
            percentage_removed = np.sum(outliers) / len(signal) * 100

            # Reemplazar outliers por 0
            signal_cleaned = np.where(outliers, 0, signal)

            return signal_cleaned, percentage_removed

        except TypeError as e:
            raise TypeError(f"Error en la entrada de datos: {e}")

        except ValueError as e:
            raise ValueError(f"Error en la validación de la señal: {e}")

        except Exception as e:
            raise RuntimeError(f"Ocurrió un error inesperado durante la eliminación de valores atípicos: {e}")


    @staticmethod
    def preprocess_eeg(samples, by_rows=True):
        """
        Realiza el preprocesamiento de los datos EEG, incluyendo filtrado pasa banda y estandarización.

        Esta función aplica filtrado pasa banda en diferentes rangos de frecuencia y estandariza la señal EEG. 
        Se utilizan filtros Butterworth y Chebyshev para extraer las bandas de interés.

        Parámetros:
        -----------
        samples : ndarray o list
            Datos EEG a procesar. Puede ser una lista o un array de NumPy.

        by_rows : bool, opcional (por defecto = True)
            Indica si las filas representan muestras:
            - `True`: Cada fila es una muestra, y cada columna representa un canal.
            - `False`: Cada fila es un canal, y cada columna representa una muestra. Se reorganiza internamente.

        Retorna:
        --------
        tuple(ndarray, ndarray, ndarray)
            Una tupla con tres arrays que representan las siguientes bandas de frecuencia:
            - `theta` (3.6 - 8 Hz)
            - `alpha` (8 - 12 Hz)
            - `beta` (12 - 30 Hz)

        Excepciones:
        ------------
        - ValueError: Si los datos no pueden convertirse en un `ndarray` válido.
        - RuntimeError: Si ocurre un error inesperado en el procesamiento.

        Ejemplo de uso:
        ---------------
        >>> eeg_data = np.random.randn(1000, 8)  # 1000 muestras, 8 canales
        >>> theta, alpha, beta = EEGStressDetector.preprocess_eeg(eeg_data, by_rows=True)
        >>> print(theta.shape, alpha.shape, beta.shape)  # Deben coincidir con la forma de entrada

        Notas:
        ------
        - Se asume una frecuencia de muestreo (250 Hz) adecuada para los filtros aplicados.
        - Los filtros Chebyshev utilizados son de 5° y 6° orden con diferentes bandas de paso.
        - `by_rows` garantiza que el formato de salida sea consistente con la entrada.
        """
        try:
            # Cargar coeficientes de los filtros
            coefficient_filters = EEGStressDetector.load_dict_coefficient_filters()
            eeg_data = np.array(samples)

            # Asegurar que los datos sean 2D (si es 1D, convertir a (N_muestras, 1))
            if eeg_data.ndim == 1:
                eeg_data = eeg_data.reshape(-1, 1)

            # Reorganizar si los datos tienen la forma (n_canales, n_muestras)
            if not by_rows:
                eeg_data = eeg_data.T  # Transponer para que sea (n_muestras, n_canales)

            # Estandarización de la señal de entrada
            eeg_data = EEGStressDetector.standardize(eeg_data)

            # Filtrado pasa banda Butterworth 5° orden (2 - 38 Hz)
            eeg_data = EEGStressDetector.bandpass_filter(eeg_data, coefficient_filters['butter'][0], coefficient_filters['butter'][1])

            # Eliminación de outliers
            eeg_data, No = EEGStressDetector.remove_outliers(eeg_data)

            # Filtrado pasa banda Chebyshev 5° orden (3.6 - 8 Hz) - Banda Theta
            theta = EEGStressDetector.bandpass_filter(eeg_data, coefficient_filters['chebyshev_theta'][0], coefficient_filters['chebyshev_theta'][1])

            # Filtrado pasa banda Chebyshev 6° orden (8 - 12 Hz) - Banda Alpha
            alpha = EEGStressDetector.bandpass_filter(eeg_data, coefficient_filters['chebyshev_alpha'][0], coefficient_filters['chebyshev_alpha'][1])

            # Filtrado pasa banda Chebyshev 6° orden (12 - 30 Hz) - Banda Beta
            beta = EEGStressDetector.bandpass_filter(eeg_data, coefficient_filters['chebyshev_beta'][0], coefficient_filters['chebyshev_beta'][1])

            # Si los datos se reorganizaron, devolverlos en su formato original
            if not by_rows:
                theta, alpha, beta = theta.T, alpha.T, beta.T

            return theta, alpha, beta

        except ValueError as e:
            raise ValueError(f"Error en la conversión de los datos EEG: {e}")

        except Exception as e:
            raise RuntimeError(f"Ocurrió un error inesperado durante el preprocesamiento de EEG: {e}")

    @staticmethod
    def feature_extraction(eeg_segment, by_rows=True):
        """
        Extrae características de la señal EEG basadas en la energía de las bandas de frecuencia.

        Esta función aplica el preprocesamiento a un segmento de EEG para obtener las bandas Theta, 
        Alpha y Beta mediante filtrado. Luego, calcula la energía de cada banda, con base en el Teorema de Parseval, y extrae relaciones 
        de energía entre ellas, como los índices Theta/Beta y Alpha/Beta, que son relevantes en el 
        análisis del estrés y la actividad cognitiva.

        Parámetros:
        -----------
        eeg_segment : ndarray
            Segmento de EEG en forma de matriz `(n_muestras, n_canales)` o `(n_canales, n_muestras)`. 
            Puede ser una lista o un array de NumPy.

        by_rows : bool, opcional (por defecto = True)
            Indica si las filas representan muestras:
            - `True`: Cada fila es una muestra y cada columna un canal.
            - `False`: Cada fila es un canal y cada columna una muestra. Se reorganiza internamente.

        Retorna:
        --------
        dict
            Diccionario con las características extraídas:
            - `'Energy_Theta'`: Energía normalizada de la banda Theta (3.6 - 8 Hz).
            - `'Energy_Alpha'`: Energía normalizada de la banda Alpha (8 - 12 Hz).
            - `'Energy_Beta'`: Energía normalizada de la banda Beta (12 - 30 Hz).
            - `'Theta/Beta'`: Relación entre la energía de las bandas Theta y Beta.
            - `'Alpha/Beta'`: Relación entre la energía de las bandas Alpha y Beta.

        Excepciones:
        ------------
        - ValueError: Si `eeg_segment` no es un array válido o tiene dimensiones incorrectas.
        - RuntimeError: Si ocurre un error inesperado en el procesamiento.

        Ejemplo de uso:
        ---------------
        >>> eeg_data = np.random.randn(500, 8)  # EEG con 500 muestras y 8 canales
        >>> features = EEGStressDetector.feature_extraction(eeg_data, by_rows=True)
        >>> print(features)

        Notas:
        ------
        - La energía se normaliza dividiendo por el número de muestras (`n_samples`).
        - Se evita la división por cero añadiendo un factor pequeño (`1e-9`) en las relaciones.
        - La función `preprocess_eeg` realiza el filtrado para obtener las bandas de interés.
        - La relación Theta/Beta se usa en estudios de neurociencia para medir estrés y concentración.
        """
        try:
            eeg_segment = np.array(eeg_segment)
            
            # Ajustar la forma si es necesario
            if not by_rows:
                eeg_segment = eeg_segment.T  # Convertir a (n_muestras, n_canales)
            
            shape = eeg_segment.shape
            total_energy = shape[0] if by_rows else shape[1]

            theta, alpha, beta = EEGStressDetector.preprocess_eeg(eeg_segment, by_rows)

            
            energy_theta = EEGStressDetector.energy(theta)/total_energy
            energy_alpha = EEGStressDetector.energy(alpha)/total_energy
            energy_beta = EEGStressDetector.energy(beta)/total_energy
            
            results = {
                'Energy_Theta': energy_theta,
                'Energy_Alpha': energy_alpha,
                'Energy_Beta': energy_beta,
                'Theta/Beta': energy_theta / (energy_beta + 1e-9),
                'Alpha/Beta': energy_alpha / (energy_beta + 1e-9),
            }
            
            return results
    
        except ValueError as e:
            raise ValueError(f"Error en los datos de entrada de EEG: {e}")

        except Exception as e:
            raise RuntimeError(f"Ocurrió un error inesperado durante la extracción de características EEG: {e}")


    @staticmethod
    def feature_extraction_v2(eeg_segment, by_rows=True):
        """
        Extrae características de la señal EEG basadas en la energía de las bandas de frecuencia.

        Esta función aplica el preprocesamiento a un segmento de EEG para obtener las bandas Theta, 
        Alpha y Beta mediante filtrado. Luego, calcula la energía de cada banda, con base en el Teorema de Parseval, y extrae relaciones 
        de energía entre ellas, como los índices Theta/Beta y Alpha/Beta, que son relevantes en el 
        análisis del estrés y la actividad cognitiva.

        Parámetros:
        -----------
        eeg_segment : ndarray
            Segmento de EEG en forma de matriz `(n_muestras, n_canales)` o `(n_canales, n_muestras)`. 
            Puede ser una lista o un array de NumPy.

        by_rows : bool, opcional (por defecto = True)
            Indica si las filas representan muestras:
            - `True`: Cada fila es una muestra y cada columna un canal.
            - `False`: Cada fila es un canal y cada columna una muestra. Se reorganiza internamente.

        Retorna:
        --------
        dict
            Diccionario con las características extraídas:
            - `'Energy_Theta'`: Energía normalizada de la banda Theta (3.6 - 8 Hz).
            - `'Energy_Alpha'`: Energía normalizada de la banda Alpha (8 - 12 Hz).
            - `'Energy_Beta'`: Energía normalizada de la banda Beta (12 - 30 Hz).
            - `'Theta/Beta'`: Relación entre la energía de las bandas Theta y Beta.
            - `'Alpha/Beta'`: Relación entre la energía de las bandas Alpha y Beta.

        Excepciones:
        ------------
        - ValueError: Si `eeg_segment` no es un array válido o tiene dimensiones incorrectas.
        - RuntimeError: Si ocurre un error inesperado en el procesamiento.

        Ejemplo de uso:
        ---------------
        >>> eeg_data = np.random.randn(500, 8)  # EEG con 500 muestras y 8 canales
        >>> features = EEGStressDetector.feature_extraction(eeg_data, by_rows=True)
        >>> print(features)

        Notas:
        ------
        - La energía se normaliza dividiendo por el número de muestras (`n_samples`).
        - Se evita la división por cero añadiendo un factor pequeño (`1e-9`) en las relaciones.
        - La función `preprocess_eeg` realiza el filtrado para obtener las bandas de interés.
        - La relación Theta/Beta se usa en estudios de neurociencia para medir estrés y concentración.
        """
        try:
            eeg_segment = np.array(eeg_segment)
            
            # Ajustar la forma si es necesario
            if not by_rows:
                eeg_segment = eeg_segment.T  # Convertir a (n_muestras, n_canales)

            theta, alpha, beta = EEGStressDetector.preprocess_eeg(eeg_segment, by_rows)
            total_energy = theta + alpha + beta
            
            energy_theta = EEGStressDetector.energy(theta)/total_energy
            energy_alpha = EEGStressDetector.energy(alpha)/total_energy
            energy_beta = EEGStressDetector.energy(beta)/total_energy
            
            results = {
                'Energy_Theta': energy_theta,
                'Energy_Alpha': energy_alpha,
                'Energy_Beta': energy_beta,
                'Theta/Beta': energy_theta / (energy_beta + 1e-9),
                'Alpha/Beta': energy_alpha / (energy_beta + 1e-9),
            }
            
            return results
    
        except ValueError as e:
            raise ValueError(f"Error en los datos de entrada de EEG: {e}")

        except Exception as e:
            raise RuntimeError(f"Ocurrió un error inesperado durante la extracción de características EEG: {e}")

    @staticmethod
    def relativeEuclideanDistance(basal, actual):
        """
        Calcula la distancia euclidiana relativa entre el estado basal y actual en múltiples canales.

        :param basal: dict con matrices de referencia (n_canales,)
        :param actual: dict con matrices actuales (n_canales,)
        :return: dict con las distancias relativas (%) para cada métrica.
        """
        distancias_relativas = {}
        
        for key in basal:
            # Calcular distancia euclidiana normal
            distancia = np.linalg.norm(actual[key] - basal[key])
            
            # Normalizar dividiendo entre la magnitud del vector basal
            # magnitud_basal = np.linalg.norm(basal[key]) + 1e-9  # Para evitar divisiones por 0
            distancias_relativas[key] = distancia
        
        return distancias_relativas
    
    @staticmethod
    def difference(actual: dict, basal: dict) -> dict:
        """
        Realiza la comparación entre los valores de dos diccionarios,
        devolviendo el valor de la diferencia de cada elemento.

        Parámetros:
        -----------
        actual : dict
            Diccionario con los valores actuales a comparar.

        basal : dict
            Diccionario con los valores de referencia.
        
        Retorna:
        --------
        dict
            Diccionario con los mismos keys, pero los valores son:
            - `x<0` si el valor actual es menor que el basal.
            - `0` si son iguales.
            - `x>0` si el valor actual es mayor que el basal.

        Ejemplo de uso:
        ---------------
        >>> basal = {"a": 10, "b": 20, "c": 30}
        >>> actual = {"a": 15, "b": 20, "c": 25}
        >>> result = difference(actual, basal)
        >>> print(result)  # {'a': 5, 'b': 0, 'c': -5}
        """
        return {key: actual[key] - basal[key] for key in basal}
    
    @staticmethod
    def comparisonSign(basal:dict, actual:dict) -> dict:
        """
        Realiza la comparación entre los valores de dos diccionarios,
        devolviendo únicamente el signo de la diferencia.

        Parámetros:
        -----------
        basal : dict
            Diccionario con los valores de referencia.

        actual : dict
            Diccionario con los valores actuales a comparar.

        Retorna:
        --------
        dict
            Diccionario con los mismos keys, pero los valores son:
            - `-1` si el valor actual es menor que el basal.
            - `0` si son iguales.
            - `1` si el valor actual es mayor que el basal.

        Ejemplo de uso:
        ---------------
        >>> basal = {"a": 10, "b": 20, "c": 30}
        >>> actual = {"a": 15, "b": 20, "c": 25}
        >>> result = relativeComparision(basal, actual)
        >>> print(result)  # {'a': 1, 'b': 0, 'c': -1}
        """
        return {key: np.sign(actual[key] - basal[key]) for key in basal}
    
    @staticmethod
    def StressScore(basal_promedio: dict, basal_std: dict, actual: dict, umbral: float =2.0) -> dict:
        """
        Calcula cuántas desviaciones estándar se aleja cada canal del estado basal.
        Con los Z-scores de cada métrica, analiza cuántos canales están fuera del umbral de normalidad.
        :return: dict con porcentaje de canales fuera de rango
        """
        z_scores = {key: (actual[key] - (basal_promedio[key])) / (basal_std[key] + 1e-9) for key in actual}

        resultado = {}
        for key, valores in z_scores.items():
            canales_fuera_rango = np.sum(np.abs(valores) > umbral)  # Canales con Z > 2
            porcentaje_fuera = canales_fuera_rango / len(valores)
            resultado[key] = porcentaje_fuera
        
        return z_scores
    
    @staticmethod
    def calculate_z_score(basal_promedio, basal_std, actual):
        """
        Calcula el Z-score de cada canal basado en la media y la desviación estándar del estado basal.

        Parámetros:
        -----------
        basal_promedio : dict
            Diccionario con la media basal de cada canal.
        basal_std : dict
            Diccionario con la desviación estándar basal de cada canal.
        actual : dict
            Diccionario con los valores actuales de cada canal.

        Retorna:
        --------
        dict
            Diccionario con los Z-scores de cada canal.
        
        Ejemplo de uso:
        ---------------
        >>> basal_mean = {'canal1': 10, 'canal2': 15}
        >>> basal_std = {'canal1': 2, 'canal2': 3}
        >>> actual = {'canal1': 14, 'canal2': 20}
        >>> z_scores = EEGStressDetector.calculate_z_score(basal_mean, basal_std, actual)
        >>> print(z_scores)
        """
        return {key: (actual[key] - basal_promedio[key]) / (basal_std[key] + 1e-9) for key in actual}

    @staticmethod
    def count_channels_above_threshold(z_scores, umbral=2.0):
        """
        Calcula el porcentaje de canales cuyo Z-score supera el umbral especificado.

        Parámetros:
        -----------
        z_scores : dict
            Diccionario con los Z-scores de cada canal.
        umbral : float, opcional
            Umbral de normalidad para detectar canales fuera de rango (por defecto, 2.0).

        Retorna:
        --------
        dict
            Diccionario con el porcentaje de canales fuera del umbral para cada métrica.

        Ejemplo de uso:
        ---------------
        >>> z_scores = {'canal1': 2.5, 'canal2': 1.8}
        >>> resultado = EEGStressDetector.count_channels_above_threshold(z_scores)
        >>> print(resultado)
        """
        resultado = {}
        for key, valores in z_scores.items():
            canales_fuera_rango = np.sum(np.abs(valores) > umbral)  # Canales con Z > umbral
            porcentaje_fuera = canales_fuera_rango / len(valores) if isinstance(valores, (list, np.ndarray)) else int(np.abs(valores) > umbral)
            resultado[key] = porcentaje_fuera
        
        return resultado

    @staticmethod
    def get_stress_category(output_value: float) -> str:
        """
        Determines the fuzzy stress category with the highest membership value 
        given the output value of a fuzzy inference system.

        This function uses `skfuzzy.interp_membership` to compute the degree of membership
        of the output value in each predefined fuzzy set ('Bajo', 'Medio', 'Alto') of the 
        `Stress_level` output variable. It returns the label of the fuzzy set with the highest 
        membership degree.

        Parameters:
        -----------
        output_value : float
            The numerical output obtained from the fuzzy system after calling `fuzzy_system.compute()`.
        Returns:
        --------
        str
            The name of the fuzzy set (e.g., 'Bajo', 'Medio', or 'Alto') with the highest membership degree.

        Example:
        --------
        >>> stress_value = fuzzy_system.output['Nivel estrés']
        >>> category = get_stress_category(stress_value, Stress_level)
        >>> print(f"The most representative stress category is: {category}")
        
        Notes:
        ------
        - The membership functions must be defined using arrays over a shared universe of discourse.
        - The output variable must contain the keys 'Bajo', 'Medio', and 'Alto'.
        """
        Stress_level_range = np.arange(0, 1, 0.01)

        # Definir funciones de membresía para nivel de estrés
        Stress_level_low = 1 - fuzz.sigmf(Stress_level_range, 0.25, 22)
        Stress_level_medium = fuzz.gaussmf(Stress_level_range, 0.5, 0.2)
        Stress_level_high = fuzz.sigmf(Stress_level_range, 0.75, 22)

        memberships = {
            'Bajo': fuzz.interp_membership(Stress_level_range, Stress_level_low, output_value),
            'Medio': fuzz.interp_membership(Stress_level_range, Stress_level_medium, output_value),
            'Alto': fuzz.interp_membership(Stress_level_range, Stress_level_high, output_value)
        }

        return max(memberships, key=memberships.get)


    @staticmethod
    def process_fuzzy_inference(
        fuzzy_system: Any,
        actual_data: Dict[str, np.ndarray],
        basal_data: Dict[str, np.ndarray]
    ) -> List[Tuple[float, str, bool]]:
        """
        Procesa la inferencia en un sistema difuso para múltiples canales utilizando las diferencias de energía EEG.

        Esta función realiza la inferencia difusa por canal, utilizando las diferencias entre los valores actuales 
        y basales de energía EEG. Calcula dichas diferencias usando `EEGStressDetector.difference(actual, basal)`, 
        valida que cada conjunto de entradas esté dentro del rango permitido [-1,1], y luego ejecuta la inferencia 
        canal por canal. El resultado es una lista con las salidas del sistema difuso para cada canal de entrada.

        Parámetros:
        -----------
        fuzzy_system : Any
            Sistema de inferencia difuso previamente cargado.

        actual_data : Dict[str, np.ndarray]
            Diccionario con los valores actuales de las energías EEG para cada banda. 
            Cada clave debe contener un arreglo `np.ndarray` con un valor por canal.
            Las claves esperadas son:
            - 'Energy_Theta'
            - 'Energy_Alpha'
            - 'Energy_Beta'

        basal_data : Dict[str, np.ndarray]
            Diccionario con los valores basales de las energías EEG para cada banda. 
            Debe tener las mismas claves que `actual_data` y arreglos del mismo tamaño por clave.

        Retorna:
        --------
        List[Tuple[float, str, bool]]
            Lista de resultados por canal. Cada elemento contiene:
            - **Nivel de estrés (float)**: Valor de salida del sistema difuso.
            - **Categoría de mayor pertenencia (str)**: Etiqueta con mayor grado de pertenencia.
            - **Bandera de rango excedido (bool)**: `True` si algún valor está fuera del rango [-1,1], `False` en caso contrario.

        Excepciones:
        ------------
        - KeyError: Si los diccionarios de entrada no contienen las claves esperadas.
        - ValueError: Si los arreglos no tienen el mismo número de canales.
        - RuntimeError: Si ocurre un error durante la ejecución del sistema difuso.

        Ejemplo de uso:
        ---------------
        >>> fuzzy_system = load_fuzzy_system("Fuzzy_Systems.pkl", "Sistema 1")
        >>> actual = {
        ...     "Energy_Theta": np.array([0.5, 0.6]),
        ...     "Energy_Alpha": np.array([0.3, 0.4]),
        ...     "Energy_Beta":  np.array([-0.2, -0.1])
        ... }
        >>> basal = {
        ...     "Energy_Theta": np.array([0.4, 0.5]),
        ...     "Energy_Alpha": np.array([0.2, 0.3]),
        ...     "Energy_Beta":  np.array([-0.3, -0.2])
        ... }
        >>> results = process_fuzzy_inference_multichannel(fuzzy_system, actual, basal)
        >>> for nivel_estres, categoria, fuera_rango in results:
        ...     print(nivel_estres, categoria, fuera_rango)

        Notas:
        ------
        - La inferencia se realiza de manera independiente por canal.
        - Si algún valor de entrada en un canal específico está fuera del rango [-1,1], ese canal se marca como "Fuera de rango" 
          y no se ejecuta la inferencia para él.
        - El orden de los resultados corresponde al orden de los canales en los arreglos de entrada.
        """
        try:
            diff_values = EEGStressDetector.difference(actual_data, basal_data)

            # Verifica que todos los arrays tengan el mismo tamaño (número de canales)
            num_channels = len(next(iter(diff_values.values())))
            for key in ['Energy_Theta', 'Energy_Alpha', 'Energy_Beta']:
                if key not in diff_values:
                    raise KeyError(f"Falta la clave '{key}' en las diferencias.")
                if len(diff_values[key]) != num_channels:
                    raise ValueError(f"El número de canales no coincide para '{key}'.")

            results = []

            # Procesar canal por canal
            for ch in range(num_channels):
                theta = diff_values['Energy_Theta'][ch]
                alpha = diff_values['Energy_Alpha'][ch]
                beta  = diff_values['Energy_Beta'][ch]

                # Verificar si está dentro de [-1, 1]
                if any(v < -1 or v > 1 for v in [theta, alpha, beta]):
                    results.append((0.0, "Fuera de rango", True))
                    continue

                # Asignar entradas para el sistema difuso
                fuzzy_system.inputs({
                    'Energía theta': theta,
                    'Energía alpha': alpha,
                    'Energía beta': beta
                })

                # Ejecutar inferencia
                fuzzy_system.compute()
                stress_value = fuzzy_system.output['Nivel estrés']

                max_category = EEGStressDetector.get_stress_category(stress_value)

                results.append((stress_value, max_category, False))

            return results

        except KeyError as e:
            raise KeyError(f"Error en los datos de entrada: {e}")

        except Exception as e:
            raise RuntimeError(f"Error durante la inferencia difusa: {e}")
        
    @staticmethod
    def stress_state(stress_list: List):
        out_of_range_list = [current_channel[2] for current_channel in stress_list]
        if out_of_range_list.count(True) >= 3:
            return {'stress level': 'Fuera de rango',
                    'stress value': 0}
        else:
            stress_list_values = [current_channel[0] for current_channel in stress_list]
            stress_list_labels = [current_channel[1] for current_channel in stress_list]
            
            stress_value = sum(stress_list_values)/len(stress_list_values)
            stress_state = Counter(stress_list_labels).most_common(1)[0][0]
            return {'stress level': stress_state,
                    'stres value': stress_value}

if __name__ == '__main__':
    import pandas as pd

    # Cargar solo las primeras 500 filas del CSV
    df = pd.read_csv("test.csv", usecols=range(1, 9), nrows=500)
    fs=250

    # Mostrar las primeras filas para verificar la carga correcta
    print(df.head())

    print(df.shape)  # Debería imprimir (500, 8)
    # Convertir a numpy array
    eeg_data = df.to_numpy()  # Equivalente a df.values pero recomendado en NumPy moderno

    # Verificar las dimensiones
    print("Dimensiones de eeg_data:", eeg_data.shape)  # (500, 9) esperado

    print('Ejecutando preprocesamiento')
    # Aplicar preprocesamiento
    @measureRunTime
    def preprocessed_eeg():
        return EEGStressDetector.preprocess_eeg(eeg_data)

    # Llamar a la función decorada
    theta, alpha, beta = preprocessed_eeg()
    print(alpha)

    print('Extrayendo características')

    # Decorar la extracción de características
    @measureRunTime
    def features():
        return EEGStressDetector.feature_extraction(eeg_data)

    # Llamar a la función decorada
    features_result = features()

    print(features_result)

    # Simulación de datos EEG con 8 canales
    n_canales = 8

    basal = {key: np.random.rand(n_canales)/10 for key in ["Energy_Theta", "Energy_Alpha", "Energy_Beta", "Theta/Beta", "Alpha/Beta"]}
    actual = {key: basal[key] - np.random.randn(n_canales) for key in basal}

    print('Estado basal (aleatorio): ')
    print(basal)
    print('Estado actual (aleatorio): ')
    print(actual)

    @measureRunTime
    def load_fuzzy():
        return EEGStressDetector.load_fuzzy_system(system_name='Sistema 2')
    print('Cargando sistema difuso...')
    fuzzy_system = load_fuzzy()


    diff = EEGStressDetector.difference(actual, basal)
    
    print(diff)

    # Evaluar el nivel de estrés
    @measureRunTime
    def stress():
        return EEGStressDetector.process_fuzzy_inference(fuzzy_system, actual, basal)
    
    print("Realizando inferencia difusa...")
    stress_per_channel = stress()
    print(stress_per_channel)

    dict_stress = EEGStressDetector.stress_state(stress_per_channel)
    print(dict_stress)
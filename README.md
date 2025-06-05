# EEG_UHB

Librería para adquisición y procesamiento de señales Electroencefalografía (EEG) utilizando el equipo comercial Unicorn Hybrid Black (UHB) usando Lab Streaming Layer (LSL).

## Instalación

Puedes instalar la librería directamente desde PyPI usando pip:

```bash
pip install eeg-uhb
```

## Instalación desde GitHub (opcional)

Si deseas instalar la versión más reciente directamente desde el repositorio, ejecuta:

```bash
pip install git+https://github.com/IngAmaury/EEG_UHB_LIBRARY.git
```

### Instalación en un entorno virtual en Python

1. Abra una terminal o Anaconda Prompt.
2. Cree un nuevo entorno virtual (por ejemplo, llamado myenv):
```bash
python -m venv myenv
```
    - Utilizando Anaconda Prompt:
    ```bash
    conda create --name myenv python=3.8
    ```
3. Active el entorno virtual:
    - En Windows:
    ```bash
    myenv\Scripts\activate
    ```
    - En Anaconda Prompt:
    ```bash
    conda activate myenv
    ```
    -En En macOS/Linux::
    ```bash
    source myenv/bin/activate
    ```
4. Instale la librería dentro del entorno virtual:
```bash
pip install eeg-uhb
```

> **Nota:** Se recomienda realizar la instalación en un entorno virtual para evitar conflictos con otras librerías del sistema.

## Dependencias

La librería requiere las siguientes dependencias, que se instalarán automáticamente con pip:

- numpy
- pylsl
- scipy
- scikit-fuzzy

## Uso

```python
from eeg_uhb.acquisition import EEGAcquisitionManager

eeg_manager = EEGAcquisitionManager()
eeg_manager.start_acquisition()
# ...
eeg_manager.stop_acquisition(save_path="./data", username="user")
```

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.  
See the LICENSE file for details.


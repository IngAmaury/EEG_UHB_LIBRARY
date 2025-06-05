# EEG_UHB

Library for Electroencephalography (EEG) signal acquisition and processing using Unicorn Hybrid Black (UHB) commercial equipment using Lab Streaming Layer (LSL).

## Install

You can install the library directly from PyPI using pip:

```bash
pip install eeg-uhb
```

## Installation from GitHub (optional)

If you want to install the latest version directly from the repository, run:

```bash
pip install git+https://github.com/IngAmaury/EEG_UHB_LIBRARY.git
```

### Installation in a Python virtual environment

1. Open a terminal or Anaconda Prompt.
2. Cree un nuevo entorno virtual (por ejemplo, llamado myenv):
```bash
python -m venv myenv
```
   - Using Anaconda Prompt:
    ```bash
    conda create --name myenv python=3.8
    ```
3. Enable the virtual environment:
    - Windows:
    ```bash
    myenv\Scripts\activate
    ```
    - Anaconda Prompt:
    ```bash
    conda activate myenv
    ```
    - macOS/Linux::
    ```bash
    source myenv/bin/activate
    ```
4. Install the library inside the virtual environment:
```bash
(myenv) pip install eeg-uhb
```

> [!NOTE]
> It is recommended to install in a virtual environment to avoid conflicts with other system libraries.

## Dependencies

The library requires the following dependencies, which will be installed automatically with pip:
- numpy
- pylsl
- scipy
- scikit-fuzzy

## Use

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


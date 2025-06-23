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
2. Create a new virtual environment (for example: myenv):
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

> [!IMPORTANT]
> If you want to make the acquisition with Unicorn Hybrid Black you need to install [Unicorn Suite Hybrid Black](https://github.com/unicorn-bi/Unicorn-Suite-Hybrid-Black-User-Manual/blob/main/UnicornSuite.md#install-unicorn-suite-hybrid-black), You can also watch their [video tutorial](https://www.youtube.com/watch?v=LOfIr2F7-Tc). Within the application, you will need to install the Unicorn Recorder from the Apps section or the Unicorn LSL from the DevTools section.

## Use

If you are acquiring through the Unicorn LSL Interface, see the image below, you can use the example code below the image, you must put in the start_adquisition function in the stream_name attribute the same name that you put in the “Streamname” box inside the LSL settings of the Unicorn LSL.

> [!TIP]
> If you have never used the Unicorn LSL Interface before, we recommend that you read its user [documentation](https://github.com/unicorn-bi/Unicorn-Network-Interfaces-Hybrid-Black/blob/main/LSL/unicorn-lsl-interface.md).

![Unicorn Hybrid Black acquisition tool using LSL protocol](docs/images/UnicornLSL.png)

```python
from eeg_uhb import EEGAcquisitionManager
import time

if __name__=='__main__':
    EEG = EEGAcquisitionManager()
    start_time = time.time()
    duration = 0.04  # segundos

    '''
    # Connect to any available stream without saving
    eeg.start_acquisition(stream_name='UN-2023.07.40')  

    # Connect to specific stream and save data
    eeg.start_acquisition(stream_name='UN-2023.07.40', 
                        save=True,
                        save_path='./eeg_data/')
    '''
    
    # the stream_name depends on the one you choose
    EEG.start_acquisition(stream_name='UN-2023.07.40', save=True)
    start = time.sleep(duration)
    print(EEG.data)
    print(f'Length: {len(EEG.data)}')
    EEG.stop_acquisition()
```

If you are acquiring through the Unicorn Recorder App, see the image below, you can use the example code below the image, you must not put anything in start_acquisition in the stream_name attribute as the app assigns one internally, the other attributes can be used as normal.

![Unicorn Recorder App acquisition tool](docs/images/UnicornLSL.png)

```python
from eeg_uhb import EEGAcquisitionManager
import time

if __name__=='__main__':
    EEG = EEGAcquisitionManager()
    start_time = time.time()
    duration = 0.04  # segundos

    '''
    eeg.start_acquisition(stream_name=None)  
    # Connect stream and save data
    eeg.start_acquisition(save=True, save_path='./eeg_data/')
    '''
    
    # the stream_name depends on the one you choose
    EEG.start_acquisition()
    start = time.sleep(duration)
    print(EEG.data)
    print(f'Length: {len(EEG.data)}')
    EEG.stop_acquisition()
```

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.  
See the LICENSE file for details.


from pylsl import resolve_stream, StreamInlet
import time

print('Buscando flujo...')
# 1. Busca el flujo LSL
streams = resolve_stream('name', 'UN-2023.07.40')  # Usa el nombre que asignaste
inlet = StreamInlet(streams[0])
try:
    print(inlet.info().name())
except RuntimeError as e:
    print(e)
    

# 2. Lee datos en tiempo real

start = time.perf_counter()  # Temporizador de alta precisión
while time.perf_counter() - start < 0.5:
    sample, timestamp = inlet.pull_sample()  # sample: vector de canales EEG
    print(f"Timestamp: {timestamp}, Sample: Done, Length: {len(sample)}")
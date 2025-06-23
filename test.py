from pylsl import resolve_stream, StreamInlet

# 1. Busca el flujo LSL
streams = resolve_stream('name', 'UnicornHybridBlack_EEG')  # Usa el nombre que asignaste
inlet = StreamInlet(streams[0])

# 2. Lee datos en tiempo real
while True:
    sample, timestamp = inlet.pull_sample()  # sample: vector de canales EEG
    print(f"Timestamp: {timestamp}, Sample: {sample}, Length: {len(sample)}")
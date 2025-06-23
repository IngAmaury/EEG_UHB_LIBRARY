from pylsl import resolve_stream, StreamInlet
import time
import xml.etree.ElementTree as ET

def print_stream_info(info):
    """Extrae y muestra todos los metadatos disponibles directamente del objeto info"""
    print("\n=== INFORMACIÓN BÁSICA DEL STREAM ===")
    print(f"• Nombre del stream: {info.name()}")
    print(f"• Tipo: {info.type()}")
    print(f"• Número de canales: {info.channel_count()}")
    print(f"• Frecuencia de muestreo: {info.nominal_srate()} Hz")
    print(f"• Formato de datos: {info.channel_format()}")
    print(f"• ID único: {info.source_id()}")
    print(f"• Versión protocolo: {info.version()}")
    print(f"• Tiempo creación: {info.created_at()}")
    
    print("\n=== INFORMACIÓN DEL DISPOSITIVO ===")
    desc = info.desc()
    if desc:
        print("• Fabricante:", desc.child_value("manufacturer") or "No especificado")
        print("• Modelo:", desc.child_value("model") or "No especificado")
        print("• Serie:", desc.child_value("serial_number") or "No especificado")
        print("• Versión firmware:", desc.child_value("firmware_version") or "No especificado")

    else:
        print("No hay metadatos adicionales disponibles")

# Uso práctico
print("Buscando stream...")
streams = resolve_stream('name', 'UN-2023.07.40')  # Reemplaza con tu nombre de stream

if streams:
    inlet = StreamInlet(streams[0])
    print_stream_info(inlet.info())
else:
    print("No se encontró el stream")

# 2. Lee datos en tiempo real

start = time.perf_counter()  # Temporizador de alta precisión
while time.perf_counter() - start < 0.1:
    sample, timestamp = inlet.pull_sample()  # sample: vector de canales EEG
    print(f"Timestamp: {timestamp}, Sample: {sample}, Length: {len(sample)}")
# config.py

from cryptography.fernet import Fernet

# La IP de tu máquina principal (PC 1)
MIDDLEWARE_HOST = "192.168.50.26"   
MIDDLEWARE_PORT = 5000

# Las IPs de las máquinas donde correrás los servidores
SERVERS = [
    {"name": "Server1", "host": "192.168.50.26", "port": 5001}, # Puede correr en tu PC principal
    {"name": "Server2", "host": "192.168.50.21", "port": 5002},  # Reemplaza X por la IP de la PC 2
    {"name": "Server3", "host": "192.168.50.23", "port": 5003},  # Reemplaza Y por la IP de la PC 3
]

# Conexión a las réplicas de Mongo alojadas en la PC 1
MONGO_URI = "mongodb://192.168.50.26:27017"
# MONGO_URI = "mongodb://192.168.50.26:27017,192.168.50.22:27017,192.168.50.23:27017/?replicaSet=rs0"

# === NUEVO: CIFRADO DEL CANAL ===
# Para producción, esta llave se genera con Fernet.generate_key() y se guarda en un .env
# Aquí la dejamos estática para que todos los nodos la compartan en tu demostración.
ENCRYPTION_KEY = b'G-Ka8o3yR3aK_xL-8GkF8aH2-P0o2_7G7V-9bY-9x3s='
import Pyro5.api
import threading
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import SERVERS, ENCRYPTION_KEY # NUEVO

try:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import SERVERS
    
except:
    SERVERS = [
    {"name": "Server1", "host": "192.168.50.26", "port": 5001}, # Puede correr en tu PC principal
    {"name": "Server2", "host": "192.168.50.21", "port": 5002},  # Reemplaza X por la IP de la PC 2
    {"name": "Server3", "host": "192.168.50.23", "port": 5003},  # Reemplaza Y por la IP de la PC 3
]


@Pyro5.api.expose
class Middleware:

    def __init__(self):
        self.lamport_clock = 0 # NUEVO: Reloj lógico del middleware
        self.current_server = None
        self.lock = threading.Lock()
        self.vector_clock = [0, 0, 0]  # índice 1 es el nuestro
        self.lock = threading.Lock()

        print("✅ Middleware iniciado")

        self.find_active_server()

        threading.Thread(
            target=self.health_monitor,
            daemon=True
        ).start()

    def sync_clock(self, received_vc):
        """Merge del Vector Clock recibido + incremento del componente propio."""
        with self.lock:
            for i in range(3):
                self.vector_clock[i] = max(self.vector_clock[i], received_vc[i])
            self.vector_clock[1] += 1  # el middleware es el componente 1
        return list(self.vector_clock)


    def create_proxy(self, server):

        uri = f"PYRO:obj@{server['host']}:{server['port']}"

        proxy = Pyro5.api.Proxy(uri)

        proxy._pyroTimeout = 3

        return proxy

    def is_alive(self, server):

        try:

            with self.create_proxy(server) as proxy:

                proxy._pyroBind()

            return True

        except:

            return False

    def find_active_server(self):

        with self.lock:

            for server in SERVERS:

                if self.is_alive(server):

                    self.current_server = server

                    print(
                        f"✅ Servidor activo: {server['name']}"
                    )

                    return True

            self.current_server = None

            print("❌ No hay servidores disponibles")

            return False

    def health_monitor(self):

        while True:

            time.sleep(5)

            if self.current_server is None:

                self.find_active_server()

                continue

            if not self.is_alive(self.current_server):

                print(
                    f"⚠️ {self.current_server['name']} caído"
                )

                self.find_active_server()

    def get_proxy(self):

        if self.current_server is None:

            if not self.find_active_server():

                raise Exception(
                    "No hay servidores disponibles"
                )

        try:

            return self.create_proxy(self.current_server)

        except:

            self.find_active_server()

            if self.current_server is None:

                raise Exception(
                    "No hay servidores disponibles"
                )

            return self.create_proxy(
                self.current_server
            )

    # -----------------------------
    # Operaciones bancarias
    # -----------------------------

    def login(self, client_vc, acc, encrypted_password):
        try:
            current_vc = self.sync_clock(client_vc)

            with self.get_proxy() as proxy:
                res = proxy.login(current_vc, acc, encrypted_password)

            server_vc = res.get("vector_clock", [0, 0, 0])
            final_vc = self.sync_clock(server_vc)
            res["vector_clock"] = final_vc
            return res

        except Exception as e:
            self.find_active_server()
            return {"status": "error", "msg": str(e),
                    "vector_clock": self.vector_clock}

    def create_account(self, client_vc, acc, encrypted_password):
        try:
            current_vc = self.sync_clock(client_vc)

            with self.get_proxy() as proxy:
                res = proxy.create_account(current_vc, acc, encrypted_password)

            server_vc = res.get("vector_clock", [0, 0, 0])
            final_vc = self.sync_clock(server_vc)
            res["vector_clock"] = final_vc
            return res

        except Exception as e:
            self.find_active_server()
            return {"status": "error", "msg": str(e),
                    "vector_clock": self.vector_clock}

    def deposit(self, token, amount):

        for _ in range(len(SERVERS)):

            try:

                with self.get_proxy() as proxy:

                    result = proxy.deposit(token, amount)

                    if "Token inválido" in str(result):

                        print(
                            f"⚠️ {self.current_server['name']} rechazó el token"
                        )

                        self.find_active_server()
                        continue

                    return f"[{self.current_server['name']}] {result}"

            except Exception:

                self.find_active_server()

        return "No hay servidores disponibles"

    def get_balance(self, token):

        for _ in range(len(SERVERS)):

            try:

                with self.get_proxy() as proxy:

                    result = proxy.get_balance(token)

                    if isinstance(result, str) and \
                    "Token inválido" in result:

                        print(
                            f"⚠️ {self.current_server['name']} rechazó el token"
                        )

                        self.find_active_server()
                        continue

                    return f"Saldo: ${result} [{self.current_server['name']}]"

            except Exception:

                self.find_active_server()

        return "No hay servidores capaces de procesar la solicitud"

    def get_account_info(self, token):

        for _ in range(len(SERVERS)):

            try:

                with self.get_proxy() as proxy:

                    result = proxy.get_account_info(token)

                    if isinstance(result, dict) and \
                    result.get("status") == "error":

                        if "Token" in result.get("msg", ""):
                            self.find_active_server()
                            continue

                    return result

            except:
                self.find_active_server()

        return {
            "status": "error",
            "msg": "No hay servidores disponibles"
        }
    
    def withdraw(self, token, amount):

        for _ in range(len(SERVERS)):

            try:
                with self.get_proxy() as proxy:

                    result = proxy.withdraw(token, amount)

                    if isinstance(result, dict):
                        if result.get("status") == "error" and "Token" in result.get("msg", ""):
                            self.find_active_server()
                            continue

                    return result

            except Exception as e:
                print("Error en withdraw middleware:", e)
                self.find_active_server()

        return {
            "status": "error",
            "msg": "No hay servidores disponibles"
        }
    
    def transfer(self, token, destination_account, amount):

        for _ in range(len(SERVERS)):

            try:

                with self.get_proxy() as proxy:

                    result = proxy.transfer(
                        token,
                        destination_account,
                        amount
                    )

                    if isinstance(result, dict):

                        if result.get("status") == "error" and \
                        "Token" in result.get("msg", ""):

                            self.find_active_server()
                            continue

                    return result

            except:
                self.find_active_server()

        return {
            "status": "error",
            "msg": "No hay servidores disponibles"
        }

if __name__ == "__main__":

    daemon = Pyro5.api.Daemon(
        host="0.0.0.0",
        port=5000
    )

    daemon.register(
        Middleware(),
        objectId="obj"
    )

    print("🚀 Middleware activo")

    daemon.requestLoop()
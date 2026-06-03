import threading
import Pyro5.api
from pymongo import MongoClient
import sys
import os
import jwt
import datetime

# 🔥 PRIMERO arreglar path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 🔥 DESPUÉS importar config
from config import SERVERS, MONGO_URI, ENCRYPTION_KEY
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

SECRET_KEY = "tu_super_secreto_bancario_2026_seguro_y_largo"
cipher_suite = Fernet(ENCRYPTION_KEY) # Inicializar cifrado

@Pyro5.api.expose
class BankServer:
    def __init__(self, server_name):
        self.lamport_clock = 0
        self.server_name = server_name
        self.client = MongoClient(MONGO_URI)
        self.db = self.client["bank"]
        self.accounts = self.db.accounts
        print("METODOS DISPONIBLES:", dir(self))
        print("WITHDRAW EXISTE:", hasattr(self, "withdraw"))
        print(f"Servidor {server_name} iniciado")
        print("--- CONECTANDO A MONGODB ---")
        try:
            # Usamos Replica Set en la URI para MongoDB
            # Reemplaza la línea que tiene "mongodb://mongo1..." por esta:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client["bank"]
            self.accounts = self.db.accounts
            self.vector_clock = [0, 0, 0]
            self.lock = threading.Lock()
            self.client.admin.command('ping') 
            print("✅ Mongo conectado correctamente")
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")

    def verify_token(self, token):
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return data["account_id"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def account_exists(self, account_id):
        return self.accounts.find_one({"account_id": account_id}) is not None

#    def create_account(self, account_id, password):
 #       if self.account_exists(account_id):
  #          return {"status": "error", "msg": f"La cuenta {account_id} ya existe"}
   #     
    #    hashed_pw = generate_password_hash(password)
     #   self.accounts.insert_one({"account_id": account_id, "password": hashed_pw, "balance": 0})
      #  return {"status": "ok", "msg": "Cuenta creada OK"}
      

    def sync_clock(self, received_vc):
        with self.lock:
            for i in range(3):
                self.vector_clock[i] = max(self.vector_clock[i], received_vc[i])
            self.vector_clock[2] += 1  # el servidor es el componente 2
        print(f"[VC] Vector Clock actualizado: {self.vector_clock}")
        return list(self.vector_clock)

    def login(self, client_vc, account_id, encrypted_password):
        current_vc = self.sync_clock(client_vc)

        if isinstance(encrypted_password, dict):
            encrypted_bytes = bytes(encrypted_password['data'])
        else:
            encrypted_bytes = bytes(encrypted_password)

        password = cipher_suite.decrypt(encrypted_bytes).decode('utf-8')

        doc = self.accounts.find_one({"account_id": account_id})

        if not doc or not check_password_hash(doc["password"], password):
            return {"status": "error", "msg": "Credenciales inválidas",
                    "vector_clock": current_vc}

        token = jwt.encode({
            'account_id': account_id,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm="HS256")

        return {"status": "ok", "token": token, "account_id": account_id,
                "msg": "Login exitoso", "vector_clock": current_vc}

    def deposit(self, token, amount):
        account_id = self.verify_token(token)
        if not account_id: return "Error: Token inválido o expirado"
        
        result = self.accounts.update_one({"account_id": account_id}, {"$inc": {"balance": amount}})
        if result.matched_count > 0:
            return f"Depósito de ${amount} OK en cuenta {account_id}"
        return "Error: Cuenta no encontrada"
    
    def withdraw(self, token, amount):
        account_id = self.verify_token(token)

        if not account_id:
            return {
                "status": "error",
                "msg": "Token inválido o expirado"
            }

        doc = self.accounts.find_one({"account_id": account_id})

        if not doc:
            return {
                "status": "error",
                "msg": "Cuenta no encontrada"
            }

        if doc["balance"] < amount:
            return {
                "status": "error",
                "msg": "Saldo insuficiente"
            }

        self.accounts.update_one(
            {"account_id": account_id},
            {"$inc": {"balance": -amount}}
        )

        return {
            "status": "ok",
            "msg": f"Retiro de ${amount} realizado correctamente"
        }
    def get_balance(self, token):
        account_id = self.verify_token(token)
        if not account_id: return "Error: Token inválido o expirado"
        
        doc = self.accounts.find_one({"account_id": account_id})
        return doc["balance"] if doc else "Error"
    
    def get_account_info(self, token):

        account_id = self.verify_token(token)

        if not account_id:
            return {
                "status": "error",
                "msg": "Token inválido"
            }

        doc = self.accounts.find_one({
            "account_id": account_id
        })

        if not doc:
            return {
                "status": "error",
                "msg": "Cuenta no encontrada"
            }

        return {
            "status": "ok",
            "account_id": account_id,
            "balance": doc["balance"]
        }

    def transfer(self, token, destination_account, amount):

        account_id = self.verify_token(token)

        if not account_id:
            return {
                "status": "error",
                "msg": "Token inválido o expirado"
            }

        if account_id == destination_account:
            return {
                "status": "error",
                "msg": "No puedes transferir a tu propia cuenta"
            }

        origin = self.accounts.find_one({
            "account_id": account_id
        })

        if not origin:
            return {
                "status": "error",
                "msg": "Cuenta origen inexistente"
            }

        destination = self.accounts.find_one({
            "account_id": destination_account
        })

        if not destination:
            return {
                "status": "error",
                "msg": "Cuenta inexistente. Transferencia fallida"
            }

        balance = origin["balance"]

        if balance >= amount:

            self.accounts.update_one(
                {"account_id": account_id},
                {"$inc": {"balance": -amount}}
            )

            self.accounts.update_one(
                {"account_id": destination_account},
                {"$inc": {"balance": amount}}
            )

            self.replicate("replica_transfer",account_id,destination_account,amount)


            return {
                "status": "ok",
                "msg": f"Transferidos ${amount}"
            }

        transfer_amount = balance

        self.accounts.update_one(
            {"account_id": account_id},
            {"$set": {"balance": 0}}
        )

        self.accounts.update_one(
            {"account_id": destination_account},
            {"$inc": {"balance": transfer_amount}}
        )

        faltante = amount - transfer_amount

        return {
            "status": "partial",
            "msg": f"Se transfirieron ${transfer_amount}. Faltaron ${faltante}"
        }

    def create_account(self, client_vc, account_id, encrypted_password):
        current_vc = self.sync_clock(client_vc)

        # Descifrar — igual que login
        password = cipher_suite.decrypt(bytes(encrypted_password)).decode('utf-8')

        if self.account_exists(account_id):
            return {"status": "error",
                    "msg": f"La cuenta {account_id} ya existe",
                    "vector_clock": current_vc}

        hashed_pw = generate_password_hash(password)
        self.accounts.insert_one({
            "account_id": account_id,
            "password": hashed_pw,
            "balance": 0
        })
        return {"status": "ok", "msg": "Cuenta creada OK",
                "vector_clock": current_vc}

    def replicate(self, method_name, *args):

        for server in SERVERS:

            if server["name"] == self.server_name:
                continue

            try:

                uri = (
                    f"PYRO:obj@"
                    f"{server['host']}:"
                    f"{server['port']}"
                )

                proxy = Pyro5.api.Proxy(uri)

                getattr(proxy, method_name)(*args)

                print(
                    f"Replicado en {server['name']}"
                )

            except Exception as e:

                print(
                    f"Error replicando "
                    f"{server['name']}: {e}"
                )

    def replica_create_account(
        self,
        account_id,
        hashed_pw
    ):

        if self.account_exists(account_id):
            return True

        self.accounts.insert_one({
            "account_id": account_id,
            "password": hashed_pw,
            "balance": 0
        })

        return True
    
    def replica_transfer(
        self,
        origin,
        destination,
        amount
    ):

        self.accounts.update_one(
            {"account_id": origin},
            {
                "$inc": {
                    "balance": -amount
                }
            }
        )

        self.accounts.update_one(
            {"account_id": destination},
            {
                "$inc": {
                    "balance": amount
                }
            }
        )

        return True

if __name__ == "__main__":
    server_name = sys.argv[1]
    port = int(sys.argv[2])

    daemon = Pyro5.api.Daemon(host="0.0.0.0", port=5001)

    server_obj = BankServer(server_name)

    daemon.register(server_obj, objectId="obj")

    print(f"🚀 {server_name} LISTO en puerto {port}")

    daemon.requestLoop()
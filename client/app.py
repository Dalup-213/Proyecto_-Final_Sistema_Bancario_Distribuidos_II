from pathlib import Path
import time
import streamlit as st
from PIL import Image
import Pyro5.api
import sys  # <--- IMPORTANTE: Esto debe ir antes de usar sys.path
import os   # <--- IMPORTANTE: Esto debe ir antes de usar os.path

# --- NUEVO: Le decimos a Python que busque una carpeta arriba ---
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cryptography.fernet import Fernet # NUEVO
from config import ENCRYPTION_KEY # NUEVO
cipher_suite = Fernet(ENCRYPTION_KEY)

st.set_page_config(
    page_title="Banco Distribuido",
)
st.markdown("""
<style>

/* ==========================
   FONDO GENERAL
========================== */
.stApp{
    background: linear-gradient(
        135deg,
        #1f1f1f 0%,
        #2b2b2b 50%,
        #3a3a3a 100%
    );
}

/* ==========================
   TEXTO
========================== */
html, body, [class*="css"]{
    font-family: "Segoe UI", sans-serif;
    color: white;
}

/* ==========================
   TITULOS
========================== */
h1,h2,h3,h4{
    color: white !important;
    font-weight: 700 !important;
}

/* ==========================
   CONTENEDORES STREAMLIT
========================== */
div[data-testid="stVerticalBlock"] > div{
    border-radius: 16px;
}

/* ==========================
   TARJETAS
========================== */
.bank-card{
    background: #f8f9fa;
    color: #111111;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 20px;
    border: 1px solid #d1d1d1;
    box-shadow:
        0 8px 24px rgba(0,0,0,0.25);
}

/* ==========================
   FORMULARIOS
========================== */
.stTextInput input,
.stNumberInput input{
    background: #ffffff !important;
    color: #111111 !important;
    border: 1px solid #bdbdbd !important;
    border-radius: 10px !important;
}

.stTextInput input:focus,
.stNumberInput input:focus{
    border: 1px solid #666666 !important;
    box-shadow: 0 0 8px rgba(255,255,255,0.15);
}

/* ==========================
   BOTONES
========================== */
.stButton button{
    width:100%;
    height:50px;

    background: linear-gradient(
        180deg,
        #4a4a4a,
        #2f2f2f
    );

    color:white;
    border:none;
    border-radius:10px;

    font-weight:600;
    letter-spacing:0.3px;

    transition:0.25s;
}

.stButton button:hover{
    background: linear-gradient(
        180deg,
        #616161,
        #404040
    );

    transform:translateY(-2px);
}

.stButton button:active{
    transform:scale(0.98);
}

/* ==========================
   SIDEBAR
========================== */
section[data-testid="stSidebar"]{
    background:
    linear-gradient(
        180deg,
        #191919,
        #111111
    );
}

section[data-testid="stSidebar"] *{
    color:white !important;
}

/* ==========================
   ALERTAS
========================== */
[data-testid="stAlert"]{
    border-radius:12px;
}

/* ==========================
   TABLAS
========================== */
[data-testid="stDataFrame"]{
    border-radius:12px;
    overflow:hidden;
}

/* ==========================
   STREAMLIT
========================== */
#MainMenu{
    visibility:hidden;
}

header{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
logo_path = BASE_DIR / "assets" / "logo.png"

logo = Image.open(logo_path)



col1, col2 = st.columns([1,5])

with col1:
    st.image(logo, width=90)

with col2:
    st.markdown("""
    <h1 style="margin-bottom:0;">
    Banco Distribuido
    </h1>
    <p style="margin-top:0;color:#000000;">
    Sistema Bancario Seguro y Tolerante a Fallos
    </p>
    """, unsafe_allow_html=True)



if 'token' not in st.session_state:
    st.session_state['token'] = None

if 'confirmar_transferencia' not in st.session_state:
    st.session_state['confirmar_transferencia'] = False

if 'lamport_clock' not in st.session_state:
    st.session_state['lamport_clock'] = 0

if 'vector_clock' not in st.session_state:
    st.session_state['vector_clock'] = [0, 0, 0]  # [app, mid, srv]


MIDDLEWARE_HOST = "192.168.50.26"
MIDDLEWARE_PORT = 5000


def obtener_proxy():
    uri = f"PYRO:obj@{MIDDLEWARE_HOST}:{MIDDLEWARE_PORT}"
    proxy = Pyro5.api.Proxy(uri)
    proxy._pyroTimeout = 5
    return proxy

def update_client_clock(received_vc):
    vc = st.session_state['vector_clock']
    # Merge: tomar máximo por componente, luego incrementar el propio (índice 0)
    merged = [max(vc[i], received_vc[i]) for i in range(3)]
    merged[0] += 1
    st.session_state['vector_clock'] = merged
# ==========================================
# LOGIN
# ==========================================

if not st.session_state['token']:


    

    col1, col2 = st.columns(2)

    with col1:
        account = st.text_input(
            "Número de Cuenta"
        )

    with col2:
        password = st.text_input(
            "Contraseña",
            type="password"
        )

    col_a, col_b = st.columns(2)

    with col_a:

        if st.button(" Login"):

            try:

                encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
                encrypted_to_send = list(encrypted_password)

                with obtener_proxy() as middleware:
                    res = middleware.login(
                        st.session_state['vector_clock'],
                        account,
                        encrypted_to_send  # lista en vez de bytes
                    )
                update_client_clock(res.get("vector_clock", [0,0,0]))

                if res["status"] == "ok":
                    st.session_state['token'] = res["token"]
                    st.success(f"{res['msg']} | VC: {st.session_state['vector_clock']}")
                    st.rerun()
                else:
                    st.error(res["msg"])
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    with col_b:

        if st.button(" Crear Cuenta"):
            try:
                encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
                encrypted_to_send = list(encrypted_password)
                #st.session_state['vector_clock'][0] += 1

                with obtener_proxy() as middleware:
                    res = middleware.create_account(
                        st.session_state['vector_clock'],
                        account,
                        encrypted_to_send
                    )
                update_client_clock(res.get("vector_clock", [0,0,0]))

                if res["status"] == "ok":
                    st.success(res["msg"])
                else:
                    st.warning(res["msg"])
            except Exception as e:
                st.error(f"Error de conexión: {e}")
                st.markdown(
    "</div>",
    unsafe_allow_html=True
)

# ==========================================
# PANEL PRINCIPAL
# ==========================================

else:

    st.success(" Sesión Activa")

    try:

        with obtener_proxy() as middleware:

            info = middleware.get_account_info(
                st.session_state['token']
            )

            if info["status"] == "ok":

                st.info(
                    f" Cuenta actual: {info['account_id']}"
                )
                st.markdown(
    "</div>",
    unsafe_allow_html=True
)

    except:
        pass

    if st.button(" Cerrar Sesión"):

        st.session_state['token'] = None

        st.rerun()

    st.divider()

    # ==========================================
    # SALDO
    # ==========================================

    if st.button(" Consultar Saldo"):

        try:

            with obtener_proxy() as middleware:

                res = middleware.get_balance(
                    st.session_state['token']
                )

                st.info(res)

        except Exception as e:

            st.error(f"Error: {e}")

    st.divider()

    # ==========================================
    # DEPÓSITO
    # ==========================================

    st.subheader(" Depósito")
    

    amount = st.number_input(
        "Monto a depositar",
        min_value=1,
        value=10
    )

    if st.button("Realizar Depósito"):

        try:

            with obtener_proxy() as middleware:

                res = middleware.deposit(
                    st.session_state['token'],
                    amount
                )

                st.success(res)
                st.markdown(
    "</div>",
    unsafe_allow_html=True
)

        except Exception as e:

            st.error(f"Error: {e}")

    st.divider()

    #========================================
    #Retiro
    #=========================================
    st.subheader("Retiro")

    withdraw_amount = st.number_input(
        "Monto a retirar",
        min_value=1,
        value=10,
        key="withdraw"
    )

    if st.button("Retirar dinero"):
        try:
            with obtener_proxy() as m:
                res = m.withdraw(
                    st.session_state['token'],
                    withdraw_amount
                )

            if isinstance(res, dict):
                if res.get("status") == "ok":
                    st.success(res["msg"])
                else:
                    st.error(res["msg"])
            else:
                st.info(res)

        except Exception as e:
            st.error(f"Error: {e}")

    # ==========================================
    # TRANSFERENCIA
    # ==========================================


    st.subheader(" Transferencia")

    # =========================
    # Inicializar estados
    # =========================
    if "confirmar_transferencia" not in st.session_state:
        st.session_state.confirmar_transferencia = False

    if "transfer_done" not in st.session_state:
        st.session_state.transfer_done = False

    if "cuenta_destino" not in st.session_state:
        st.session_state.cuenta_destino = ""

    if "monto_transferencia" not in st.session_state:
        st.session_state.monto_transferencia = 1

    if "transferencia_en_proceso" not in st.session_state:
        st.session_state.transferencia_en_proceso = False


    # =========================
    # Campos de captura
    # =========================
    st.session_state.cuenta_destino = st.text_input(
        "Cuenta destino",
        value=st.session_state.cuenta_destino,
        disabled=st.session_state.transferencia_en_proceso
    )

    st.session_state.monto_transferencia = st.number_input(
        "Monto a transferir",
        min_value=1,
        value=st.session_state.monto_transferencia,
        disabled=st.session_state.transferencia_en_proceso
    )


    # =========================
    # Botón Transferir
    # =========================
    
    if st.button(
        "Transferir",
        disabled=st.session_state.transferencia_en_proceso
    ):

        if st.session_state.cuenta_destino.strip() == "":
            st.error("Ingrese una cuenta destino.")
        else:
            st.session_state.confirmar_transferencia = True
            st.session_state.transfer_done = False


    # =========================
    # Confirmación
    # =========================
    if st.session_state.confirmar_transferencia:

        st.warning(
            f"¿Seguro de transferir "
            f"${st.session_state.monto_transferencia:,.2f} "
            f"a la cuenta {st.session_state.cuenta_destino}?"
        )

        col1, col2 = st.columns(2)

        # =========================
        # Confirmar transferencia
        # =========================
        with col1:

            if st.button(
                "Confirmar transferencia",
                disabled=st.session_state.transferencia_en_proceso
            ):

                st.session_state.transferencia_en_proceso = True

                try:

                    with st.spinner("Enviando transferencia..."):

                        with obtener_proxy() as middleware:

                            res = middleware.transfer(
                                st.session_state["token"],
                                st.session_state.cuenta_destino,
                                st.session_state.monto_transferencia
                            )

                    if res["status"] == "ok":

                        st.success("✅ Transferencia realizada correctamente")

                        # Limpiar formulario
                        st.session_state.cuenta_destino = ""
                        st.session_state.monto_transferencia = 1
                        st.session_state.confirmar_transferencia = False
                        st.session_state.transfer_done = True
                        st.session_state.transferencia_en_proceso = False

                        time.sleep(1)
                        st.rerun()

                    elif res["status"] == "partial":

                        st.warning(res["msg"])

                        # Limpiar formulario
                        st.session_state.cuenta_destino = ""
                        st.session_state.monto_transferencia = 1
                        st.session_state.confirmar_transferencia = False
                        st.session_state.transfer_done = True
                        st.session_state.transferencia_en_proceso = False

                        time.sleep(1)
                        st.rerun()

                    else:

                        st.error(res["msg"])
                        st.session_state.transferencia_en_proceso = False

                except Exception as e:

                    st.error(f"Error al realizar la transferencia: {e}")
                    st.session_state.transferencia_en_proceso = False


        # =========================
        # Cancelar transferencia
        # =========================
        with col2:

            if st.button(
                "Cancelar transferencia",
                disabled=st.session_state.transferencia_en_proceso
            ):

                st.session_state.confirmar_transferencia = False
                st.session_state.cuenta_destino = ""
                st.session_state.monto_transferencia = 1
                st.session_state.transferencia_en_proceso = False

                st.info("Transferencia cancelada")

                time.sleep(1)
                st.rerun()
            st.markdown(
    "</div>",
    unsafe_allow_html=True
)
st.markdown("""
<br><br>
<hr>
<div style="
text-align:center;
color:#9CA3AF;
font-size:13px;
">
Banco Distribuido • Proyecto de Sistemas Distribuidos
</div>
""", unsafe_allow_html=True)
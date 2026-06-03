Sistema Bancario Distribuido
Descripción General

Sistema Bancario Distribuido desarrollado como proyecto académico para la materia de Sistemas Distribuidos. La aplicación implementa una arquitectura cliente-servidor con middleware intermedio, comunicación remota mediante Pyro5 y almacenamiento persistente en MongoDB.

El sistema permite la gestión de cuentas bancarias, autenticación de usuarios, consultas de saldo, depósitos y transferencias entre cuentas, garantizando la integridad de la información mediante mecanismos de sincronización y replicación de datos.

Características Principales
Autenticación segura de usuarios.
Creación de cuentas bancarias.
Consulta de saldo en tiempo real.
Depósitos a cuentas.
Transferencias entre usuarios.
Comunicación distribuida mediante Pyro5.
Middleware para coordinación de solicitudes.
Persistencia de datos en MongoDB.
Manejo de tolerancia a fallos.
Uso de relojes vectoriales para seguimiento de eventos distribuidos.
Cifrado de credenciales mediante Fernet.
Arquitectura del Sistema

El sistema está compuesto por tres capas principales:

Cliente

Interfaz gráfica desarrollada en Streamlit que permite a los usuarios interactuar con el sistema bancario.

Middleware

Actúa como intermediario entre los clientes y los servidores, gestionando las solicitudes y coordinando las operaciones distribuidas.

Servidores Bancarios

Procesan las operaciones bancarias y administran la información almacenada en la base de datos.

Cliente (Streamlit)
        │
        ▼
Middleware (Pyro5)
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
Server1 Server2 Server3
        │
        ▼
     MongoDB
Tecnologías Utilizadas
Python 3
Streamlit
Pyro5
MongoDB
Cryptography (Fernet)
JWT (JSON Web Tokens)
Funcionalidades
Inicio de Sesión

Permite autenticar usuarios registrados utilizando credenciales cifradas.

Creación de Cuenta

Registro de nuevas cuentas bancarias dentro del sistema.

Consulta de Saldo

Visualización del saldo actual de una cuenta.

Depósitos

Incremento del saldo disponible mediante depósitos.

Transferencias

Transferencia de fondos entre cuentas registradas dentro del sistema.

Seguridad

El sistema implementa diferentes mecanismos de seguridad:

Cifrado de contraseñas mediante Fernet.
Autenticación basada en tokens JWT.
Comunicación controlada a través del middleware.
Validación de operaciones bancarias.
Objetivo Académico

Este proyecto tiene como finalidad aplicar los conceptos fundamentales de Sistemas Distribuidos, incluyendo:

Comunicación remota entre procesos.
Coordinación de servicios distribuidos.
Sincronización de eventos.
Tolerancia a fallos.
Persistencia de información.
Seguridad en sistemas distribuidos.
***************************************NOTA******************************************
Para que el sistema sea distribuido, debe de ejecutarse cada sevidor en una maquina diferente, ademas de cambiar el puerto, dependiendo del servidor a ejecutarse
Ej. si es el sevidor 2, seria el puerto 5002
esto se debe configurar en cada uno

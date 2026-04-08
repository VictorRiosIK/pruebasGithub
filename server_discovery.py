import socket
import threading
import time

# ===== Configuración =====
IP_SERVIDOR = '0.0.0.0'
PUERTO_SERVER = 4040
PUERTO_COMANDOS = 4041
PUERTO_DISCOVERY = 4000
conexion = None
direccion = None
#comentario de prueba desde github
# =========================
# DISCOVERY (UDP)
# =========================
def discovery_server():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("", PUERTO_DISCOVERY))

    print(f"Discovery activo en puerto {PUERTO_DISCOVERY}...")

    while True:
        try:
            data, addr = udp.recvfrom(1024)
            print(f"DISCOVEY DATA {addr} → {data}")
            # respuesta simple
            response = b"C09\\n"
            udp.sendto(response, addr)

        except Exception as e:
            print(f"[DISCOVERY ERROR] {e}")
            time.sleep(1)

# =========================
# SERVIDOR PRINCIPAL
# =========================
while True:
    try:
        sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_server.bind((IP_SERVIDOR, PUERTO_SERVER))
        sock_server.listen(1)
        print(f"Servidor principal escuchando en puerto {PUERTO_SERVER}...")
        break
    except Exception as e:
        print(f"No se pudo enlazar: {e}")
        time.sleep(3)

def aceptar_cliente():
    global conexion, direccion
    while True:
        try:
            conn, addr = sock_server.accept()
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            conn.settimeout(5)
            conexion = conn
            direccion = addr
            print(f"[TCP] Conexión establecida desde {direccion}")
        except Exception as e:
            print(f"Error aceptando conexión: {e}")
            time.sleep(1)

# =========================
# SERVIDOR DE COMANDOS
# =========================
while True:
    try:
        sock_cmd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_cmd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_cmd.bind((IP_SERVIDOR, PUERTO_COMANDOS))
        sock_cmd.listen(5)
        print(f"Servidor de comandos en puerto {PUERTO_COMANDOS}...")
        break
    except Exception as e:
        print(f"No se pudo enlazar comandos: {e}")
        time.sleep(3)

def recibir_comandos():
    global conexion
    while True:
        try:
            conn, addr = sock_cmd.accept()
            datos = conn.recv(1024)

            if datos:
                comando = datos.decode(errors='ignore').strip()
                print(f"[CMD RX] {addr} → {comando}")

                if conexion:
                    try:
                        conexion.send((comando + "\n").encode())
                        print("[CMD] Enviado al dispositivo")
                    except:
                        print("[CMD] Cliente desconectado")
                        conexion = None
                else:
                    print("[CMD] No hay cliente conectado")

            conn.close()

        except Exception as e:
            print(f"Error en comandos: {e}")
            time.sleep(1)

# =========================
# HILOS
# =========================
threading.Thread(target=discovery_server, daemon=True).start()
threading.Thread(target=aceptar_cliente, daemon=True).start()
threading.Thread(target=recibir_comandos, daemon=True).start()

# =========================
# LOOP PRINCIPAL (TCP)
# =========================
while True:
    if conexion:
        try:
            datos = conexion.recv(1024)

            if not datos:
                raise ConnectionResetError

            print(f"[DATA RX] {direccion} → {datos}")
            conexion.send(b"C\n")

        except (ConnectionResetError, BrokenPipeError):
            print(f"[TCP] Cliente {direccion} desconectado")

            try:
                conexion.close()
            except:
                pass

            conexion = None
            direccion = None

        except socket.timeout:
            # no pasa nada, seguimos
            pass

        except Exception as e:
            print(f"[TCP ERROR] {e}")

    time.sleep(0.01)

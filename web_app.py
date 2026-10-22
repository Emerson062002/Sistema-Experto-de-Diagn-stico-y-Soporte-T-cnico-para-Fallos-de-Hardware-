"""Servidor web local para la interfaz del sistema experto."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from typing import Any

from motor_inferencia import MotorInferencia
from pyswip.prolog import PrologError


HOST = "127.0.0.1"
PORT = 8000
RUTA_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
PATRONES_PITIDOS = {
    "tres_cortos",
    "un_largo_dos_cortos",
    "cortos_repetidos",
    "un_largo_tres_cortos",
}
PRUEBAS_VALIDAS = {
    "fuente_con_probador",
    "cambio_cable",
    "otro_monitor",
    "gpu_en_otro_equipo",
    "reasentar_ram",
    "smart_disco",
    "cambio_bateria",
}
RESULTADOS_VALIDOS = {"falla", "ok", "resuelve", "no_resuelve"}


def crear_condiciones(datos: Any, sintomas_validos: set[str]) -> list[str]:
    """Valida el formulario y arma términos Prolog solo con valores permitidos."""
    if not isinstance(datos, dict):
        raise ValueError("El contenido de la solicitud no tiene el formato esperado.")

    sintomas = datos.get("sintomas", [])
    if not isinstance(sintomas, list) or any(
        not isinstance(item, str) or item not in sintomas_validos for item in sintomas
    ):
        raise ValueError("Selecciona síntomas válidos de la lista.")

    condiciones = list(dict.fromkeys(sintomas))

    temperatura = datos.get("temperatura")
    if temperatura not in (None, ""):
        try:
            grados = int(temperatura)
        except (TypeError, ValueError):
            raise ValueError("La temperatura debe ser un número entero.") from None
        if not 0 <= grados <= 150:
            raise ValueError("La temperatura debe estar entre 0 y 150 °C.")
        condiciones.append(f"temp_cpu({grados})")

    pitidos = datos.get("pitidos")
    if pitidos not in (None, ""):
        if not isinstance(pitidos, str) or pitidos not in PATRONES_PITIDOS:
            raise ValueError("Selecciona un patrón de pitidos válido.")
        condiciones.append(f"pitidos({pitidos})")

    pruebas = datos.get("pruebas", [])
    if not isinstance(pruebas, list) or len(pruebas) > len(PRUEBAS_VALIDAS):
        raise ValueError("La lista de pruebas no es válida.")
    for item in pruebas:
        if not isinstance(item, dict):
            raise ValueError("Cada prueba debe tener un nombre y un resultado.")
        nombre = item.get("nombre")
        resultado = item.get("resultado")
        if (
            not isinstance(nombre, str)
            or nombre not in PRUEBAS_VALIDAS
            or not isinstance(resultado, str)
            or resultado not in RESULTADOS_VALIDOS
        ):
            raise ValueError("Selecciona una prueba y un resultado válidos.")
        condiciones.append(f"prueba({nombre}, {resultado})")

    tipo_equipo = datos.get("tipo_equipo")
    antiguedad = datos.get("antiguedad")
    if tipo_equipo not in (None, "") or antiguedad not in (None, ""):
        if not isinstance(tipo_equipo, str) or tipo_equipo not in {"escritorio", "portatil"}:
            raise ValueError("Selecciona el tipo de equipo.")
        try:
            anios = int(antiguedad)
        except (TypeError, ValueError):
            raise ValueError("La antigüedad debe ser un número entero.") from None
        if not 0 <= anios <= 100:
            raise ValueError("La antigüedad debe estar entre 0 y 100 años.")
        condiciones.append(f"equipo({tipo_equipo}, {anios})")

    return condiciones


class SistemaExpertoHandler(BaseHTTPRequestHandler):
    motor: MotorInferencia
    sintomas: list[tuple[str, str]]
    sintomas_validos: set[str]

    def _responder(self, estado: int, contenido: bytes, tipo: str) -> None:
        self.send_response(estado)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(contenido)

    def _responder_json(self, estado: int, datos: Any) -> None:
        contenido = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self._responder(estado, contenido, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            try:
                with open(RUTA_HTML, "rb") as archivo:
                    contenido = archivo.read()
            except OSError as error:
                self._responder_json(500, {"error": f"No se pudo abrir la interfaz: {error}"})
                return
            self._responder(200, contenido, "text/html; charset=utf-8")
            return
        if self.path == "/api/sintomas":
            self._responder_json(
                200,
                [{"id": sintoma, "descripcion": descripcion}
                 for sintoma, descripcion in self.sintomas],
            )
            return
        self._responder_json(404, {"error": "Recurso no encontrado."})

    def do_POST(self) -> None:
        if self.path != "/api/diagnosticar":
            self._responder_json(404, {"error": "Recurso no encontrado."})
            return
        try:
            longitud = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._responder_json(400, {"error": "Longitud de solicitud no válida."})
            return
        if longitud <= 0 or longitud > 65536:
            self._responder_json(400, {"error": "La solicitud está vacía o es demasiado grande."})
            return
        try:
            datos = json.loads(self.rfile.read(longitud).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._responder_json(400, {"error": "El formulario no contiene JSON válido."})
            return
        try:
            condiciones = crear_condiciones(datos, self.sintomas_validos)
        except ValueError as error:
            self._responder_json(400, {"error": str(error)})
            return

        try:
            respuesta = self.motor.consultar_lista(condiciones)
        except (PrologError, RuntimeError) as error:
            self.log_error("Falló la consulta al motor de inferencia: %s", error)
            self._responder_json(
                500, {"error": "No se pudo completar el diagnóstico. Revisa SWI-Prolog."}
            )
            return

        self._responder_json(
            200,
            {
                "estado": respuesta.estado,
                "diagnosticos": [
                    {
                        "nombre": item.nombre,
                        "certeza": item.certeza,
                        "severidad": item.severidad,
                        "prioridad": item.prioridad,
                        "cobertura": item.cobertura,
                        "accion": item.accion,
                    }
                    for item in respuesta.diagnosticos
                ],
                "sospechosos": [
                    {"componente": componente, "indicios": cantidad}
                    for componente, cantidad in respuesta.sospechosos
                ],
                "descartados": respuesta.descartados,
            },
        )

    def log_message(self, formato: str, *argumentos: Any) -> None:
        print(f"[web] {self.address_string()} - {formato % argumentos}")


def main() -> None:
    motor = MotorInferencia()
    sintomas = motor.listar_sintomas()
    handler = type(
        "ConfiguredSistemaExpertoHandler",
        (SistemaExpertoHandler,),
        {
            "motor": motor,
            "sintomas": sintomas,
            "sintomas_validos": {sintoma for sintoma, _ in sintomas},
        },
    )
    servidor = HTTPServer((HOST, PORT), handler)
    print("Sistema experto disponible en http://127.0.0.1:8000")
    print("Presiona Ctrl+C para detener el servidor.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()

"""
motor_inferencia.py
===================
Puente Python <-> SWI-Prolog (PySwip) del Sistema Experto de Diagnóstico y
Soporte Técnico para Fallos de Hardware.

RESPONSABILIDAD DE ESTE MÓDULO
    Python solo hace tres cosas:
      1. Cargar ``base_conocimiento.pl`` en el motor de SWI-Prolog.
      2. Enviar los datos de entrada e invocar los predicados de Prolog.
      3. Recibir las listas de resultados y presentarlas en consola.

    NO hay lógica de inferencia, descarte, validación ni cálculo de severidad
    aquí: todo eso vive en Prolog.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable

from pyswip import Prolog

RUTA_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "base_conocimiento.pl")


# --------------------------------------------------------------------------- #
#  Estructuras de datos (solo transportan lo que devuelve Prolog)
# --------------------------------------------------------------------------- #
@dataclass
class Diagnostico:
    """Un diagnóstico tal como lo entrega Prolog."""
    nombre: str
    certeza: str
    severidad: str
    prioridad: int
    cobertura: int
    accion: str


@dataclass
class Respuesta:
    """Respuesta completa de ``consultar_caso/2``."""
    estado: str
    diagnosticos: list[Diagnostico] = field(default_factory=list)
    sospechosos: list[tuple[str, int]] = field(default_factory=list)
    descartados: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
#  Motor
# --------------------------------------------------------------------------- #
class MotorInferencia:
    """Carga la base de conocimiento y expone funciones que consultan Prolog."""

    def __init__(self, ruta_base: str = RUTA_BASE) -> None:
        if not os.path.isfile(ruta_base):
            raise FileNotFoundError(f"No se encontró la base de conocimiento: {ruta_base}")
        self._prolog = Prolog()
        # PySwip espera rutas con "/" aunque el sistema operativo sea Windows.
        list(self._prolog.query(f"consult('{ruta_base.replace(os.sep, '/')}')"))

    # -- utilidades internas ------------------------------------------------ #
    @staticmethod
    def _atomo(texto: str) -> str:
        """Escapa un texto para enviarlo a Prolog como átomo entre comillas."""
        return "'" + texto.replace("\\", "\\\\").replace("'", "\\'") + "'"

    @staticmethod
    def _lista_prolog(items: Iterable[str]) -> str:
        """Arma el texto ``[a, b, c]`` con los elementos (términos Prolog)."""
        return "[" + ", ".join(items) + "]"

    def _una_solucion(self, consulta: str) -> dict:
        """Ejecuta una consulta y devuelve su primera solución."""
        soluciones = list(self._prolog.query(consulta, maxresult=1))
        if not soluciones:
            raise RuntimeError(f"Prolog no devolvió solución para: {consulta}")
        return soluciones[0]

    @staticmethod
    def _a_respuesta(crudo: list) -> Respuesta:
        """Convierte la lista que devuelve Prolog en una ``Respuesta``."""
        estado, diagnosticos, sospechosos, descartados = crudo
        return Respuesta(
            estado=str(estado),
            diagnosticos=[
                Diagnostico(str(d[0]), str(d[1]), str(d[2]),
                            int(d[3]), int(d[4]), str(d[5]))
                for d in diagnosticos
            ],
            sospechosos=[(str(s[0]), int(s[1])) for s in sospechosos],
            descartados=[str(x) for x in descartados],
        )

    # -- consultas a Prolog ------------------------------------------------- #
    def consultar_texto(self, texto: str) -> Respuesta:
        """Invoca ``consultar_texto(+Texto, -Respuesta)``."""
        consulta = f"consultar_texto({self._atomo(texto)}, R)"
        return self._a_respuesta(self._una_solucion(consulta)["R"])

    def consultar_lista(self, items: Iterable[str]) -> Respuesta:
        """Invoca ``consultar_caso(+Entrada, -Respuesta)`` con una lista."""
        consulta = f"consultar_caso({self._lista_prolog(items)}, R)"
        return self._a_respuesta(self._una_solucion(consulta)["R"])

    def diagnosticar_todos(self, items: Iterable[str]) -> tuple[str, list[Diagnostico]]:
        """Invoca ``diagnosticar_todos(+Entrada, -Estado, -Diagnosticos)``."""
        consulta = f"diagnosticar_todos({self._lista_prolog(items)}, E, D)"
        sol = self._una_solucion(consulta)
        diagnosticos = [Diagnostico(str(d[0]), str(d[1]), str(d[2]),
                                    int(d[3]), int(d[4]), str(d[5]))
                        for d in sol["D"]]
        return str(sol["E"]), diagnosticos

    def listar_sintomas(self) -> list[tuple[str, str]]:
        """Invoca ``listar_sintomas(-Lista)``."""
        sol = self._una_solucion("listar_sintomas(L)")
        return [(str(s[0]), str(s[1])) for s in sol["L"]]


# --------------------------------------------------------------------------- #
#  Presentación en consola
# --------------------------------------------------------------------------- #
_MENSAJES_ESTADO = {
    "ok": "Diagnóstico generado.",
    "datos_insuficientes": "Datos insuficientes: ninguna regla se cumple con la información dada.",
    "entrada_vacia": "No se ingresó ninguna condición.",
    "entrada_invalida": "Ninguna condición válida en la entrada.",
}


def formatear_respuesta(resp: Respuesta) -> str:
    """Devuelve la respuesta de Prolog como texto legible para la consola."""
    lineas = [f"Estado: {resp.estado} - {_MENSAJES_ESTADO.get(resp.estado, '')}"]
    if resp.descartados:
        lineas.append("Condiciones no reconocidas (ignoradas): "
                      + ", ".join(resp.descartados))
    if resp.diagnosticos:
        lineas.append("Diagnósticos (de mayor a menor prioridad):")
        for i, d in enumerate(resp.diagnosticos, start=1):
            lineas.append(f"  {i}. {d.nombre}  |  severidad: {d.severidad}  |  "
                          f"certeza: {d.certeza}  |  prioridad: {d.prioridad}  |  "
                          f"evidencia: {d.cobertura}%")
            lineas.append(f"     Acción: {d.accion}")
    elif resp.sospechosos:
        lineas.append("Componentes sospechosos (de más a menos indicios):")
        for comp, cantidad in resp.sospechosos:
            lineas.append(f"  - {comp} ({cantidad} indicio(s))")
        lineas.append("Sugerencia: realice más pruebas y vuelva a consultar.")
    return "\n".join(lineas)

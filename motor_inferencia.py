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
import json
import re
import tempfile
import unicodedata
from threading import RLock
from dataclasses import dataclass, field
from typing import Iterable

from pyswip import Prolog

RUTA_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "base_conocimiento.pl")
RUTA_ALIAS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "aliases_aprendidos.json")


# --------------------------------------------------------------------------- #
#  Estructuras de datos (solo transportan lo que devuelve Prolog)
# --------------------------------------------------------------------------- #
@dataclass
class Diagnostico:
    """Un diagnóstico tal como lo entrega Prolog."""
    nombre: str
    certeza: str
    severidad: str
    nivel_danio: str
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
    explicaciones: list[ExplicacionDiagnostico] = field(default_factory=list)
    sugerencias: list[Sugerencia] = field(default_factory=list)


@dataclass
class ExplicacionDiagnostico:
    """Traza de reglas, hechos y exclusiones devuelta por Prolog."""
    nombre: str
    certeza: str
    severidad: str
    nivel_danio: str
    prioridad: int
    cobertura: int
    accion: str
    reglas: list[str] = field(default_factory=list)
    hechos: list[str] = field(default_factory=list)
    negaciones: list[str] = field(default_factory=list)
    alternativas_descartadas: list[str] = field(default_factory=list)


@dataclass
class Sugerencia:
    """Dato o prueba priorizada por Prolog para completar el caso."""
    dato: str
    razon: str
    hipotesis: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
#  Motor
# --------------------------------------------------------------------------- #
class MotorInferencia:
    """Carga la base de conocimiento y expone funciones que consultan Prolog."""

    def __init__(self, ruta_base: str = RUTA_BASE) -> None:
        if not os.path.isfile(ruta_base):
            raise FileNotFoundError(f"No se encontró la base de conocimiento: {ruta_base}")
        self._prolog = Prolog()
        self._lock = RLock()
        self._ruta_alias = RUTA_ALIAS
        self._aliases_aprendidos: list[tuple[str, str]] = []
        # PySwip espera rutas con "/" aunque el sistema operativo sea Windows.
        list(self._prolog.query(f"consult('{ruta_base.replace(os.sep, '/')}')"))
        self._cargar_aliases_aprendidos()

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
        with self._lock:
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
                Diagnostico(str(d[0]), str(d[1]), str(d[2]), str(d[3]),
                            int(d[4]), int(d[5]), str(d[6]))
                for d in diagnosticos
            ],
            sospechosos=[(str(s[0]), int(s[1])) for s in sospechosos],
            descartados=[str(x) for x in descartados],
        )

    # -- consultas a Prolog ------------------------------------------------- #
    def consultar_texto(self, texto: str) -> Respuesta:
        """Procesa texto libre con alias dinámicos y preserva elementos inválidos."""
        if texto is None or not str(texto).strip():
            return Respuesta("entrada_vacia")

        partes = self._split_top_level(str(texto))
        if not partes:
            return Respuesta("entrada_vacia")

        es_texto_libre = any(" " in parte and "(" not in parte for parte in partes)
        if es_texto_libre:
            lista = self._parsear_texto_natural(str(texto))
            if not lista:
                return Respuesta("entrada_invalida")
            return self.consultar_lista(lista)

        return self.consultar_lista(partes)

    def _parsear_texto_natural(self, texto: str) -> list[str]:
        """Convierte frases normales a síntomas del catálogo usando aliases dinámicos."""
        if not texto or not texto.strip():
            return []

        texto_limpio = texto.strip()
        partes = self._split_top_level(texto_limpio)
        if not partes:
            return []

        validos = {valor for valor, _ in self.listar_sintomas()}
        alias_map = {self._normalizar_alias(frase): sintoma for sintoma, frase in self.listar_aliases()}

        if any("(" in parte or parte.startswith("temp_cpu") or parte.startswith("pitidos(") or parte.startswith("prueba(") or parte.startswith("equipo(") for parte in partes):
            entrada: list[str] = []
            for parte in partes:
                parte_limpia = parte.strip()
                if not parte_limpia:
                    continue
                if parte_limpia in validos:
                    entrada.append(parte_limpia)
                elif parte_limpia.startswith("temp_cpu(") or parte_limpia.startswith("pitidos(") or parte_limpia.startswith("prueba(") or parte_limpia.startswith("equipo("):
                    entrada.append(parte_limpia)
                else:
                    for alias, sintoma in sorted(alias_map.items(), key=lambda item: len(item[0]), reverse=True):
                        if alias in self._normalizar_alias(parte_limpia) and sintoma not in entrada:
                            entrada.append(sintoma)
                            break
            return entrada

        encontrado: list[str] = []
        for parte in partes:
            bloque = self._normalizar_alias(parte)
            if not bloque:
                continue
            bloque_compacto = bloque.replace(" ", "_")
            if bloque_compacto in validos and bloque_compacto not in encontrado:
                encontrado.append(bloque_compacto)
                continue
            for alias, sintoma in sorted(alias_map.items(), key=lambda item: len(item[0]), reverse=True):
                if alias in bloque and sintoma not in encontrado:
                    encontrado.append(sintoma)

        if not encontrado:
            texto_norm = re.sub(r"[^a-z0-9\s]+", " ", texto.lower())
            texto_norm = re.sub(r"\s+", " ", texto_norm).strip()
            for nombre in validos:
                if nombre.replace("_", " ") in texto_norm and nombre not in encontrado:
                    encontrado.append(nombre)

        return encontrado

    @staticmethod
    def _split_top_level(texto: str) -> list[str]:
        """Divide entradas por comas que estén fuera de paréntesis."""
        partes: list[str] = []
        actual: list[str] = []
        profundidad = 0
        for caracter in texto:
            if caracter == "(":
                profundidad += 1
            elif caracter == ")" and profundidad > 0:
                profundidad -= 1
            elif caracter == "," and profundidad == 0:
                valor = "".join(actual).strip()
                if valor:
                    partes.append(valor)
                actual = []
                continue
            actual.append(caracter)
        valor = "".join(actual).strip()
        if valor:
            partes.append(valor)
        return partes

    @staticmethod
    def _normalizar_alias(texto: str) -> str:
        """Normaliza una frase para comparar alias sin distinguir mayúsculas."""
        texto_norm = unicodedata.normalize("NFKD", texto.lower())
        texto_norm = "".join(
            caracter for caracter in texto_norm
            if not unicodedata.combining(caracter)
        )
        texto_norm = re.sub(r"[^a-z0-9\s]+", " ", texto_norm)
        return re.sub(r"\s+", " ", texto_norm).strip()

    def consultar_lista(self, items: Iterable[str]) -> Respuesta:
        """Invoca ``consultar_caso(+Entrada, -Respuesta)`` con una lista."""
        consulta = f"consultar_caso({self._lista_prolog(items)}, R)"
        return self._a_respuesta(self._una_solucion(consulta)["R"])

    def analizar_caso(self, items: Iterable[str]) -> Respuesta:
        """Consulta el diagnóstico, la traza y datos faltantes en Prolog."""
        consulta = f"analizar_caso({self._lista_prolog(items)}, R)"
        crudo = self._una_solucion(consulta)["R"]
        estado, diagnosticos, sospechosos, descartados, explicaciones, sugerencias = crudo
        respuesta = self._a_respuesta(
            [estado, diagnosticos, sospechosos, descartados]
        )
        respuesta.explicaciones = [
            ExplicacionDiagnostico(
                nombre=str(item[0]),
                certeza=str(item[1]),
                severidad=str(item[2]),
                nivel_danio=str(item[3]),
                prioridad=int(item[4]),
                cobertura=int(item[5]),
                accion=str(item[6]),
                reglas=[str(regla) for regla in item[7]],
                hechos=[str(hecho) for hecho in item[8]],
                negaciones=[str(negacion) for negacion in item[9]],
                alternativas_descartadas=[str(alt) for alt in item[10]],
            )
            for item in explicaciones
        ]
        respuesta.sugerencias = [
            Sugerencia(
                dato=str(item[0]),
                razon=str(item[1]),
                hipotesis=[str(hipotesis) for hipotesis in item[2]],
            )
            for item in sugerencias
        ]
        return respuesta

    def diagnosticar_todos(self, items: Iterable[str]) -> tuple[str, list[Diagnostico]]:
        """Invoca ``diagnosticar_todos(+Entrada, -Estado, -Diagnosticos)``."""
        consulta = f"diagnosticar_todos({self._lista_prolog(items)}, E, D)"
        sol = self._una_solucion(consulta)
        diagnosticos = [Diagnostico(str(d[0]), str(d[1]), str(d[2]), str(d[3]),
                                    int(d[4]), int(d[5]), str(d[6]))
                        for d in sol["D"]]
        return str(sol["E"]), diagnosticos

    def listar_sintomas(self) -> list[tuple[str, str]]:
        """Invoca ``listar_sintomas(-Lista)``."""
        sol = self._una_solucion("listar_sintomas(L)")
        return [(str(s[0]), str(s[1])) for s in sol["L"]]

    def listar_aliases(self) -> list[tuple[str, str]]:
        """Lista los aliases dinámicos aprendidos por el usuario experto."""
        with self._lock:
            sol = self._una_solucion("listar_aliases(L)")
        return [(str(item[0]), str(item[1])) for item in sol["L"]]

    def aprender_alias(self, frase: str, sintoma: str) -> bool:
        """Guarda de forma persistente un alias vinculado a un síntoma conocido."""
        frase = " ".join(frase.split())
        sintoma = sintoma.strip()
        if not frase or len(frase) > 120 or not re.fullmatch(r"[a-z][a-z0-9_]*", sintoma):
            return False

        with self._lock:
            if not list(self._prolog.query(f"sintoma_catalogo({sintoma}, _)")):
                return False

            normalizada = self._normalizar_alias(frase)
            existentes = self.listar_aliases()
            coincidencias = [
                (nombre, alias)
                for nombre, alias in existentes
                if self._normalizar_alias(alias) == normalizada
            ]
            if coincidencias:
                return all(nombre == sintoma for nombre, _ in coincidencias)

            consulta = f"agregar_alias({self._atomo(frase)}, {sintoma})"
            if not list(self._prolog.query(consulta)):
                return False

            self._aliases_aprendidos.append((sintoma, frase))
            try:
                self._guardar_aliases_aprendidos()
            except OSError:
                self._prolog.query(
                    f"retract(alias_sintoma({sintoma}, {self._atomo(frase)}))"
                )
                self._aliases_aprendidos.pop()
                raise
        return True

    def listar_aliases_aprendidos(self) -> list[tuple[str, str]]:
        """Devuelve solo las asociaciones personalizadas persistidas por el experto."""
        with self._lock:
            return list(self._aliases_aprendidos)

    def eliminar_alias_aprendido(self, frase: str) -> bool:
        """Elimina un alias personalizado de Prolog y de su archivo persistente."""
        normalizada = self._normalizar_alias(frase)
        if not normalizada:
            return False

        with self._lock:
            indice = next(
                (
                    i for i, (_, alias) in enumerate(self._aliases_aprendidos)
                    if self._normalizar_alias(alias) == normalizada
                ),
                None,
            )
            if indice is None:
                return False

            sintoma, alias = self._aliases_aprendidos[indice]
            consulta = f"retract(alias_sintoma({sintoma}, {self._atomo(alias)}))"
            if not list(self._prolog.query(consulta)):
                return False

            self._aliases_aprendidos.pop(indice)
            try:
                self._guardar_aliases_aprendidos()
            except OSError:
                self._aliases_aprendidos.insert(indice, (sintoma, alias))
                self._prolog.query(
                    f"assertz(alias_sintoma({sintoma}, {self._atomo(alias)}))"
                )
                raise
        return True

    def _cargar_aliases_aprendidos(self) -> None:
        if not os.path.exists(self._ruta_alias):
            return
        try:
            with open(self._ruta_alias, encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"No se pudieron cargar los alias aprendidos ({self._ruta_alias}): {error}"
            ) from error
        if not isinstance(datos, list):
            raise RuntimeError(
                f"El archivo de alias aprendidos no contiene una lista: {self._ruta_alias}"
            )

        for item in datos:
            if not isinstance(item, dict):
                raise RuntimeError(f"Registro inválido en {self._ruta_alias}")
            frase = item.get("frase")
            sintoma = item.get("sintoma")
            if not isinstance(frase, str) or not isinstance(sintoma, str):
                raise RuntimeError(f"Registro inválido en {self._ruta_alias}")
            frase = " ".join(frase.split())
            sintoma = sintoma.strip()
            if (
                not frase
                or len(frase) > 120
                or not re.fullmatch(r"[a-z][a-z0-9_]*", sintoma)
            ):
                raise RuntimeError(f"Alias inválido en {self._ruta_alias}: {frase!r}")

            with self._lock:
                if not list(self._prolog.query(f"sintoma_catalogo({sintoma}, _)")):
                    raise RuntimeError(
                        f"El alias {frase!r} referencia un síntoma inexistente: {sintoma}"
                    )
                existentes = self.listar_aliases()
                if any(
                    self._normalizar_alias(alias) == self._normalizar_alias(frase)
                    and nombre != sintoma
                    for nombre, alias in existentes
                ):
                    raise RuntimeError(
                        f"El alias {frase!r} está asociado a síntomas incompatibles"
                    )
                if not any(
                    self._normalizar_alias(alias) == self._normalizar_alias(frase)
                    and nombre == sintoma
                    for nombre, alias in existentes
                ):
                    self._prolog.query(
                        f"agregar_alias({self._atomo(frase)}, {sintoma})"
                    )
                self._aliases_aprendidos.append((sintoma, frase))

    def _guardar_aliases_aprendidos(self) -> None:
        carpeta = os.path.dirname(self._ruta_alias)
        archivo_temporal = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=carpeta,
                prefix=".aliases-",
                suffix=".tmp",
                delete=False,
            ) as archivo:
                archivo_temporal = archivo.name
                json.dump(
                    [
                        {"sintoma": sintoma, "frase": frase}
                        for sintoma, frase in self._aliases_aprendidos
                    ],
                    archivo,
                    ensure_ascii=False,
                    indent=2,
                )
                archivo.write("\n")
            os.replace(archivo_temporal, self._ruta_alias)
        except OSError:
            if archivo_temporal and os.path.exists(archivo_temporal):
                os.remove(archivo_temporal)
            raise

    def listar_hechos_base(self) -> dict[str, list[str]]:
        """Devuelve los hechos y elementos de catálogos definidos en Prolog."""
        consultas = [
            ("Componentes", "componente(Id, Descripcion)",
             lambda r: f"componente({r['Id']}, {r['Descripcion']})"),
            ("Síntomas reportables", "sintoma_catalogo(Sintoma, Descripcion)",
             lambda r: f"sintoma_catalogo({r['Sintoma']}, {r['Descripcion']})"),
            ("Relaciones síntoma-componente", "sintoma_componente(Sintoma, Componente)",
             lambda r: f"sintoma_componente({r['Sintoma']}, {r['Componente']})"),
            ("Patrones de pitidos", "codigo_pitido(Patron, Componente)",
             lambda r: f"codigo_pitido({r['Patron']}, {r['Componente']})"),
            ("Pruebas", "prueba_catalogo(Nombre, Descripcion)",
             lambda r: f"prueba_catalogo({r['Nombre']}, {r['Descripcion']})"),
            ("Resultados de pruebas", "resultado_prueba(Resultado, Descripcion)",
             lambda r: f"resultado_prueba({r['Resultado']}, {r['Descripcion']})"),
            ("Tipos de equipo", "tipo_equipo(Tipo, Descripcion)",
             lambda r: f"tipo_equipo({r['Tipo']}, {r['Descripcion']})"),
            ("Umbrales", "umbral(Parametro, Valor)",
             lambda r: f"umbral({r['Parametro']}, {r['Valor']})"),
            ("Gravedad base por diagnóstico", "gravedad(Diagnostico, Nivel)",
             lambda r: f"gravedad({r['Diagnostico']}, {r['Nivel']})"),
            ("Pesos de severidad", "peso_gravedad(Nivel, Peso)",
             lambda r: f"peso_gravedad({r['Nivel']}, {r['Peso']})"),
            ("Acciones recomendadas", "accion(Diagnostico, Accion)",
             lambda r: f"accion({r['Diagnostico']}, {r['Accion']})"),
            ("Evidencia típica por diagnóstico", "evidencia_tipica(Diagnostico, Evidencia)",
             lambda r: f"evidencia_tipica({r['Diagnostico']}, "
                       f"[{', '.join(map(str, r['Evidencia']))}])"),
            ("Casos de ejemplo", "caso_ejemplo(Nombre, Entrada)",
             lambda r: f"caso_ejemplo({r['Nombre']}, "
                       f"[{', '.join(map(str, r['Entrada']))}])"),
        ]
        with self._lock:
            return {
                seccion: [formatear(fila) for fila in self._prolog.query(consulta)]
                for seccion, consulta, formatear in consultas
            }


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
            lineas.append(f"  {i}. {d.nombre}  |  nivel de daño: {d.nivel_danio}  |  "
                          f"severidad: {d.severidad}  |  "
                          f"certeza: {d.certeza}  |  prioridad: {d.prioridad}  |  "
                          f"evidencia: {d.cobertura}%")
            lineas.append(f"     Acción: {d.accion}")
    elif resp.sospechosos:
        lineas.append("Componentes sospechosos (de más a menos indicios):")
        for comp, cantidad in resp.sospechosos:
            lineas.append(f"  - {comp} ({cantidad} indicio(s))")
        lineas.append("Sugerencia: realice más pruebas y vuelva a consultar.")
    return "\n".join(lineas)

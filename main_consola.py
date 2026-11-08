"""Interfaz de consola original de HardDiag."""

import re
import unicodedata

from motor_inferencia import MotorInferencia, formatear_respuesta

ALIASES_SINTOMAS = [
    ("no enciende", "no_enciende"),
    ("no prende", "no_enciende"),
    ("no arranca", "no_enciende"),
    ("olor a quemado", "olor_quemado"),
    ("pantalla negra", "pantalla_negra"),
    ("pantalla azul", "pantalla_azul"),
    ("se apaga", "apagados_repentinos"),
    ("se congela", "bloqueos"),
    ("va lento", "lentitud"),
    ("se reinicia solo", "reinicios_aleatorios"),
    ("ventilador ruidoso", "ventilador_ruidoso"),
    ("ventilador no gira", "ventilador_detenido"),
    ("disco hace clic", "ruido_clic"),
    ("pantalla con rayas", "lineas_en_pantalla"),
    ("artefactos en pantalla", "artefactos_video"),
    ("se calienta", "ventilador_ruidoso"),
]


def normalizar_texto_libre(texto: str) -> str:
    texto_normal = unicodedata.normalize("NFKD", texto.lower())
    texto_normal = "".join(ch for ch in texto_normal if not unicodedata.combining(ch))
    texto_normal = re.sub(r"[^a-z0-9°\s]+", " ", texto_normal)
    return re.sub(r"\s+", " ", texto_normal).strip()


def convertir_entrada_libre(texto: str) -> str:
    texto_normal = normalizar_texto_libre(texto)
    if not texto_normal:
        return ""
    condiciones = []
    for patron, sintoma in ALIASES_SINTOMAS:
        if patron in texto_normal and sintoma not in condiciones:
            condiciones.append(sintoma)
    if not condiciones:
        return texto.strip()
    return ", ".join(condiciones)


AYUDA = """
Escriba las condiciones separadas por comas o describa el daño en lenguaje natural.
Formatos aceptados:
  sintoma                     ej.  no_enciende, pantalla_negra
  texto libre                ej.  no prende, pantalla negra, olor a quemado
  temp_cpu(Grados)            ej.  temp_cpu(92)
  pitidos(Patron)             ej.  pitidos(tres_cortos)
  prueba(Nombre, Resultado)   ej.  prueba(reasentar_ram, resuelve)
  equipo(Tipo, Anios)         ej.  equipo(escritorio, 7)

Comandos:  sintomas  (lista de síntomas)   ayuda   salir
"""


def main() -> None:
    motor = MotorInferencia()
    print("=" * 62)
    print(" SISTEMA EXPERTO DE DIAGNÓSTICO DE HARDWARE")
    print("=" * 62)
    print(AYUDA)
    while True:
        try:
            texto = input("Condiciones> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if texto.lower() in ("salir", "exit", "quit"):
            break
        if texto.lower() == "ayuda":
            print(AYUDA)
            continue
        if texto.lower() == "sintomas":
            for sintoma, descripcion in motor.listar_sintomas():
                print(f"  {sintoma:<22} {descripcion}")
            continue
        texto_procesado = convertir_entrada_libre(texto)
        if texto_procesado:
            texto = texto_procesado
        print()
        print(formatear_respuesta(motor.consultar_texto(texto)))
        print()
    print("Hasta pronto.")


if __name__ == "__main__":
    main()

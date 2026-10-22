"""
main.py
=======
Interfaz de consola del Sistema Experto de Diagnóstico de Hardware.

Python solo recibe lo que escribe el usuario, lo envía a Prolog y muestra el
resultado. Toda la lógica está en base_conocimiento.pl.

Ejecución:  python main.py
"""

from motor_inferencia import MotorInferencia, formatear_respuesta

AYUDA = """
Escriba las condiciones separadas por comas. Formatos aceptados:
  sintoma                     ej.  no_enciende, pantalla_negra
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
        print()
        print(formatear_respuesta(motor.consultar_texto(texto)))
        print()
    print("Hasta pronto.")


if __name__ == "__main__":
    main()

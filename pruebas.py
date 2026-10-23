"""
pruebas.py
==========
Script de pruebas por consola del Sistema Experto de Diagnóstico de Hardware.

Ejecuta nueve casos base y cinco verificaciones de integración para diagnóstico,
explicabilidad y sugerencias de datos faltantes. Guarda la salida en
``evidencia_pruebas.txt``.

Ejecución:  python pruebas.py
Código de salida: 0 si todos los casos pasan, 1 si alguno falla.

Python solo envía la entrada, invoca Prolog y compara/presenta resultados.
"""

import os
import sys

from motor_inferencia import MotorInferencia, formatear_respuesta

ARCHIVO_EVIDENCIA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "evidencia_pruebas.txt")

# Cada caso: tipo, objetivo, entrada (texto enviado a Prolog) y esperado.
CASOS = [
    {
        "id": 1,
        "tipo": "Normal 1 (diagnóstico único claro)",
        "objetivo": "Un solo diagnóstico claro, con severidad elevada por olor a quemado.",
        "entrada": "no_enciende, olor_quemado, prueba(fuente_con_probador, falla)",
        "esperado": {"estado": "ok",
                     "diagnosticos": [("fuente_poder_defectuosa", "critica")]},
    },
    {
        "id": 2,
        "tipo": "Normal 2 (múltiples diagnósticos / recolección)",
        "objetivo": "Recolectar dos diagnósticos distintos, sin duplicados y "
                    "ordenados por prioridad (el de mayor severidad primero).",
        "entrada": "pantalla_azul, bloqueos, pitidos(tres_cortos), "
                   "prueba(reasentar_ram, no_resuelve), arranque_lento, "
                   "ruido_clic, prueba(smart_disco, falla)",
        "esperado": {"estado": "ok",
                     "diagnosticos": [("disco_fallando", "alta"),
                                      ("ram_defectuosa", "media")]},
    },
    {
        "id": 3,
        "tipo": "Normal 3 (severidad crítica por temperatura)",
        "objetivo": "Elevar a 'critica' la severidad cuando la temperatura "
                    "del procesador supera el umbral crítico.",
        "entrada": "temp_cpu(97), ventilador_ruidoso",
        "esperado": {"estado": "ok",
                     "diagnosticos": [("refrigeracion_deficiente", "critica")]},
    },
    {
        "id": 4,
        "tipo": "Exclusión 1 (\\+)",
        "objetivo": "Descartar la falla de fuente aunque haya síntomas, porque "
                    "la fuente pasó la prueba (\\+ descartado). Debe quedar solo "
                    "la batería CMOS.",
        "entrada": "no_enciende, olor_quemado, prueba(fuente_con_probador, ok), "
                   "hora_incorrecta, equipo(escritorio, 7)",
        "esperado": {"estado": "ok",
                     "diagnosticos": [("bateria_cmos_agotada", "baja")]},
    },
    {
        "id": 5,
        "tipo": "Exclusión 2 (! reglas mutuamente excluyentes)",
        "objetivo": "RAM mal asentada y RAM defectuosa son excluyentes: si "
                    "reasentar resuelve, solo debe salir 'ram_mal_asentada'.",
        "entrada": "pantalla_azul, prueba(reasentar_ram, resuelve)",
        "esperado": {"estado": "ok",
                     "diagnosticos": [("ram_mal_asentada", "baja")]},
    },
    {
        "id": 6,
        "tipo": "Borde 1 (datos insuficientes / lista parcial)",
        "objetivo": "Con un solo síntoma ninguna regla se cumple: debe indicar "
                    "datos insuficientes y sugerir el componente sospechoso.",
        "entrada": "pantalla_negra",
        "esperado": {"estado": "datos_insuficientes", "diagnosticos": [],
                     "sospechosos": ["tarjeta_video"]},
    },
    {
        "id": 7,
        "tipo": "Borde 1b (lista con elementos inválidos)",
        "objetivo": "Ignorar elementos no reconocidos sin romper la consulta y "
                    "reportarlos como descartados.",
        "entrada": "xyz, temp_cpu(abc), pantalla_negra",
        "esperado": {"estado": "datos_insuficientes", "diagnosticos": [],
                     "descartados": ["xyz", "temp_cpu(abc)"]},
    },
    {
        "id": 8,
        "tipo": "Borde 2 (lista vacía / caso por defecto)",
        "objetivo": "Una lista vacía no debe producir errores en Python: "
                    "Prolog responde con el caso por defecto 'entrada_vacia'.",
        "entrada": "",
        "esperado": {"estado": "entrada_vacia", "diagnosticos": []},
    },
    {
        "id": 9,
        "tipo": "Placa base (nuevas reglas de inferencia)",
        "objetivo": "Diagnosticar la placa base cuando no hay energía, "
                    "la fuente pasa la prueba y el patrón BIOS apunta a la placa.",
        "entrada": "no_enciende, prueba(fuente_con_probador, ok), "
                   "pitidos(un_largo_tres_cortos)",
        "esperado": {"estado": "ok",
                     "diagnosticos": [("placa_base_defectuosa", "alta")]},
    },
]


class Tee:
    """Escribe a la vez en la consola y en el archivo de evidencia."""

    def __init__(self, *flujos):
        self.flujos = flujos

    def write(self, texto):
        for flujo in self.flujos:
            flujo.write(texto)

    def flush(self):
        for flujo in self.flujos:
            flujo.flush()


def evaluar(resp, esperado):
    """Compara lo obtenido con lo esperado; devuelve (ok, lista_de_diferencias)."""
    diferencias = []
    if resp.estado != esperado["estado"]:
        diferencias.append(f"estado: esperado {esperado['estado']}, obtenido {resp.estado}")
    obtenidos = [(d.nombre, d.severidad) for d in resp.diagnosticos]
    if obtenidos != esperado["diagnosticos"]:
        diferencias.append(f"diagnósticos: esperado {esperado['diagnosticos']}, obtenido {obtenidos}")
    if "sospechosos" in esperado:
        comps = [c for c, _ in resp.sospechosos]
        if comps != esperado["sospechosos"]:
            diferencias.append(f"sospechosos: esperado {esperado['sospechosos']}, obtenido {comps}")
    if "descartados" in esperado and resp.descartados != esperado["descartados"]:
        diferencias.append(f"descartados: esperado {esperado['descartados']}, obtenido {resp.descartados}")
    return not diferencias, diferencias


def describir_esperado(esperado):
    partes = [f"estado = {esperado['estado']}"]
    if esperado["diagnosticos"]:
        partes.append("diagnósticos = " + ", ".join(
            f"{n} ({s})" for n, s in esperado["diagnosticos"]))
    else:
        partes.append("diagnósticos = ninguno")
    if "sospechosos" in esperado:
        partes.append("sospechoso principal = " + esperado["sospechosos"][0])
    if "descartados" in esperado:
        partes.append("ignorados = " + ", ".join(esperado["descartados"]))
    return "; ".join(partes)


def main():
    with open(ARCHIVO_EVIDENCIA, "w", encoding="utf-8") as archivo:
        sys.stdout = Tee(sys.__stdout__, archivo)
        try:
            ejecutar()
        finally:
            sys.stdout = sys.__stdout__
    return 0


def ejecutar():
    motor = MotorInferencia()
    print("=" * 72)
    print(" PRUEBAS DEL SISTEMA EXPERTO DE DIAGNÓSTICO DE HARDWARE")
    print("=" * 72)
    aprobados = 0
    for caso in CASOS:
        resp = motor.consultar_texto(caso["entrada"])
        ok, diferencias = evaluar(resp, caso["esperado"])
        aprobados += ok
        entrada_mostrada = caso["entrada"] if caso["entrada"] else "(texto vacío)"
        print(f"\nCaso {caso['id']}: {caso['tipo']}")
        print("-" * 72)
        print(f"Objetivo : {caso['objetivo']}")
        print(f"Entrada  : {entrada_mostrada}")
        print(f"Consulta : consultar_texto('{caso['entrada']}', Respuesta).")
        print(f"Esperado : {describir_esperado(caso['esperado'])}")
        print("Obtenido :")
        for linea in formatear_respuesta(resp).splitlines():
            print("    " + linea)
        print(f"Resultado: {'APROBADO' if ok else 'FALLIDO'}")
        for d in diferencias:
            print(f"    ! {d}")
    print("\n" + "=" * 72)
    integraciones_aprobadas = evaluar_integraciones(motor)
    aprobados += integraciones_aprobadas
    total_casos = len(CASOS) + 5
    print(f" INTEGRACIÓN: {integraciones_aprobadas} de 5 casos aprobados")
    print(f" RESUMEN: {aprobados} de {total_casos} casos aprobados")
    print("=" * 72)
    if aprobados != total_casos:
        sys.exit(1)


def evaluar_integraciones(motor):
    """Comprueba los cinco escenarios del entregable Streamlit/explicabilidad."""
    casos = [
        (
            "Diagnóstico con explicación",
            lambda: _caso_diagnostico_explicable(motor),
        ),
        (
            "Síntomas insuficientes y sugerencia",
            lambda: _caso_informacion_insuficiente(motor),
        ),
        (
            "Varias hipótesis posibles",
            lambda: _caso_hipotesis_ambiguas(motor),
        ),
        (
            "Prueba recomendada para RAM",
            lambda: _caso_sugerencia_ram(motor),
        ),
        (
            "Entrada válida sin diagnóstico",
            lambda: _caso_sin_diagnostico(motor),
        ),
    ]
    aprobados = 0
    for nombre, comprobar in casos:
        try:
            ok = comprobar()
        except Exception as error:
            ok = False
            print(f"  Error en {nombre}: {error}")
        aprobados += ok
        print(f"  {nombre}: {'APROBADO' if ok else 'FALLIDO'}")
    return aprobados


def _caso_diagnostico_explicable(motor):
    respuesta = motor.analizar_caso([
        "no_enciende",
        "olor_quemado",
        "prueba(fuente_con_probador, falla)",
    ])
    if respuesta.estado != "ok" or not respuesta.diagnosticos:
        return False
    explicacion = respuesta.explicaciones[0]
    return (
        respuesta.diagnosticos[0].nombre == "fuente_poder_defectuosa"
        and {"R1", "R9", "R21"}.issubset(explicacion.reglas)
        and any("prueba(fuente_con_probador, falla)" in hecho for hecho in explicacion.hechos)
        and any("\\+" in negacion for negacion in explicacion.negaciones)
    )


def _caso_informacion_insuficiente(motor):
    respuesta = motor.analizar_caso(["pantalla_negra"])
    return (
        respuesta.estado == "datos_insuficientes"
        and not respuesta.diagnosticos
        and bool(respuesta.sugerencias)
    )


def _caso_hipotesis_ambiguas(motor):
    respuesta = motor.analizar_caso(["pantalla_negra", "ventiladores_giran"])
    hipotesis = {
        nombre
        for sugerencia in respuesta.sugerencias
        for nombre in sugerencia.hipotesis
    }
    return (
        respuesta.estado == "datos_insuficientes"
        and {"cable_o_monitor_defectuoso", "gpu_defectuosa"}.issubset(hipotesis)
    )


def _caso_sugerencia_ram(motor):
    respuesta = motor.analizar_caso(["pantalla_azul"])
    return (
        bool(respuesta.sugerencias)
        and any("RAM" in sugerencia.dato for sugerencia in respuesta.sugerencias)
        and any("R14" in sugerencia.razon or "R15" in sugerencia.razon
                for sugerencia in respuesta.sugerencias)
    )


def _caso_sin_diagnostico(motor):
    respuesta = motor.analizar_caso(["led_encendido"])
    return (
        respuesta.estado == "datos_insuficientes"
        and not respuesta.diagnosticos
        and any(
            explicacion.nombre == "sin_diagnostico"
            and "R25" in explicacion.reglas
            for explicacion in respuesta.explicaciones
        )
    )


if __name__ == "__main__":
    sys.exit(main())

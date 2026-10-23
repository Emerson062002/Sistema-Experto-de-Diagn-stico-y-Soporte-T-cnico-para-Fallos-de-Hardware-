"""Interfaz Streamlit de HardDiag. La inferencia y sus explicaciones viven en Prolog."""

from __future__ import annotations

import streamlit as st
from pyswip.prolog import PrologError

from motor_inferencia import MotorInferencia, Respuesta


@st.cache_resource
def obtener_motor() -> MotorInferencia:
    """Mantiene una única instancia del motor Prolog entre recargas de Streamlit."""
    return MotorInferencia()


NOMBRES_DIAGNOSTICO = {
    "fuente_poder_defectuosa": "Fuente de poder defectuosa",
    "cable_o_monitor_defectuoso": "Cable o monitor defectuoso",
    "gpu_defectuosa": "Tarjeta gráfica defectuosa",
    "placa_base_defectuosa": "Placa base defectuosa",
    "refrigeracion_deficiente": "Refrigeración deficiente",
    "ram_mal_asentada": "Memoria RAM mal asentada",
    "ram_defectuosa": "Memoria RAM defectuosa",
    "disco_fallando": "Disco de almacenamiento fallando",
    "bateria_cmos_agotada": "Batería CMOS agotada",
}
NOMBRES_COMPONENTE = {
    "fuente_poder": "Fuente de poder",
    "placa_base": "Placa base",
    "procesador": "Procesador y refrigeración",
    "memoria_ram": "Memoria RAM",
    "almacenamiento": "Almacenamiento",
    "tarjeta_video": "Tarjeta gráfica y video",
}
NOMBRES_PRUEBA = {
    "fuente_con_probador": "Probar la fuente con un probador",
    "cambio_cable": "Cambiar el cable de video",
    "otro_monitor": "Conectar otro monitor",
    "gpu_en_otro_equipo": "Probar la tarjeta gráfica en otro equipo",
    "reasentar_ram": "Reasentar la memoria RAM",
    "smart_disco": "Revisar el estado SMART del disco",
    "cambio_bateria": "Cambiar la batería CMOS",
}
NOMBRES_RESULTADO = {
    "falla": "La prueba detectó una falla",
    "ok": "El componente pasó la prueba",
    "resuelve": "La acción resolvió el problema",
    "no_resuelve": "La acción no resolvió el problema",
}
PATRONES_PITIDOS = {
    "Tres pitidos cortos": "tres_cortos",
    "Uno largo y dos cortos": "un_largo_dos_cortos",
    "Pitidos cortos repetidos": "cortos_repetidos",
    "Uno largo y tres cortos": "un_largo_tres_cortos",
}
RESULTADOS_PRUEBA = {
    "La prueba detectó una falla": "falla",
    "El componente pasó la prueba": "ok",
    "La acción resolvió el problema": "resuelve",
    "La acción no resolvió el problema": "no_resuelve",
}
ESTADOS = {
    "ok": "Diagnóstico generado.",
    "datos_insuficientes": "La información no basta para confirmar un diagnóstico.",
    "entrada_vacia": "No se proporcionaron datos para analizar.",
    "entrada_invalida": "No se encontraron condiciones válidas.",
}


def preparar_entrada(
    sintomas: list[str],
    adicionales: str,
    temperatura: int | None,
    pitidos: str | None,
    tipo_equipo: str | None,
    antiguedad: int | None,
    pruebas: list[tuple[str, str]],
) -> list[str]:
    """Limpia y convierte los controles del formulario en términos Prolog permitidos."""
    sintomas_validos = {nombre for nombre, _ in obtener_motor().listar_sintomas()}
    sintomas_extra = [elemento.strip() for elemento in adicionales.split(",") if elemento.strip()]
    desconocidos = sorted(set(sintomas + sintomas_extra) - sintomas_validos)
    if desconocidos:
        raise ValueError(
            "Síntoma(s) no reconocido(s): "
            + ", ".join(desconocidos)
            + ". Usa los nombres del catálogo."
        )

    entrada = list(dict.fromkeys(sintomas + sintomas_extra))
    if temperatura is not None:
        entrada.append(f"temp_cpu({temperatura})")
    if pitidos:
        entrada.append(f"pitidos({pitidos})")
    for nombre, resultado in pruebas:
        entrada.append(f"prueba({nombre}, {resultado})")
    if tipo_equipo and antiguedad is not None:
        entrada.append(f"equipo({tipo_equipo}, {antiguedad})")
    return entrada


def mostrar_resultado(respuesta: Respuesta) -> None:
    """Presenta únicamente los diagnósticos, trazas y sugerencias devueltos por Prolog."""
    st.subheader("Resultado")
    st.info(ESTADOS.get(respuesta.estado, respuesta.estado))

    if respuesta.diagnosticos:
        if len(respuesta.diagnosticos) > 1:
            st.caption(
                "Prolog ordenó las hipótesis por prioridad: primero severidad y luego "
                "porcentaje de evidencia."
            )
        for indice, diagnostico in enumerate(respuesta.diagnosticos, start=1):
            nombre = NOMBRES_DIAGNOSTICO.get(diagnostico.nombre, diagnostico.nombre)
            st.markdown(f"### {indice}. {nombre}")
            st.write(
                f"**Severidad:** {diagnostico.severidad} · "
                f"**Certeza:** {diagnostico.certeza} · "
                f"**Prioridad:** {diagnostico.prioridad} · "
                f"**Evidencia:** {diagnostico.cobertura}%"
            )
            st.write(f"**Recomendación:** {diagnostico.accion}")
            explicacion = next(
                (e for e in respuesta.explicaciones if e.nombre == diagnostico.nombre),
                None,
            )
            if explicacion:
                with st.expander(f"¿Por qué? — {nombre}"):
                    st.markdown("**Reglas de Prolog que sustentan el resultado**")
                    st.write(", ".join(explicacion.reglas) or "Sin traza de reglas.")
                    st.markdown("**Hechos comprobados en este caso**")
                    if explicacion.hechos:
                        for hecho in explicacion.hechos:
                            st.write(f"- `{hecho}`")
                    else:
                        st.write("No se registraron hechos positivos.")
                    if explicacion.negaciones:
                        st.markdown("**Exclusiones comprobadas mediante negación por fallo (`\\+`)**")
                        for negacion in explicacion.negaciones:
                            st.write(f"- {negacion}")
                    if explicacion.alternativas_descartadas:
                        st.markdown("**Hipótesis alternativas descartadas por pruebas**")
                        for alternativa in explicacion.alternativas_descartadas:
                            st.write(f"- {alternativa}")
                    st.caption(
                        "La lista de reglas se obtiene de la ruta de inferencia que Prolog "
                        "comprobó para este diagnóstico."
                    )
    elif respuesta.sospechosos:
        st.warning("Todavía no hay evidencia suficiente para confirmar una falla.")
        st.markdown("**Componentes con síntomas relacionados:**")
        for componente, indicios in respuesta.sospechosos:
            st.write(
                f"- {NOMBRES_COMPONENTE.get(componente, componente)} "
                f"({indicios} indicio(s))"
            )

    if respuesta.descartados:
        st.caption("Condiciones desconocidas ignoradas: " + ", ".join(respuesta.descartados))

    if respuesta.sugerencias:
        st.subheader("¿Qué falta?")
        for sugerencia in respuesta.sugerencias:
            st.markdown(f"**{sugerencia.dato}**")
            st.write(sugerencia.razon)
            if sugerencia.hipotesis:
                hipotesis = [
                    NOMBRES_DIAGNOSTICO.get(nombre, nombre)
                    for nombre in sugerencia.hipotesis
                ]
                st.caption("Ayuda a diferenciar: " + ", ".join(hipotesis))


def main() -> None:
    st.set_page_config(
        page_title="HardDiag | Diagnóstico de hardware",
        page_icon="🖥️",
        layout="wide",
    )
    st.title("HardDiag")
    st.subheader("Sistema experto de diagnóstico de hardware")
    st.write(
        "Selecciona los síntomas que observas. La inferencia, las explicaciones y "
        "las sugerencias de información faltante se calculan en Prolog."
    )
    st.warning(
        "Herramienta educativa de orientación. Ante olor a quemado, apaga y "
        "desconecta el computador. No abras la fuente de poder."
    )

    try:
        motor = obtener_motor()
        sintomas_catalogo = motor.listar_sintomas()
    except (FileNotFoundError, OSError, PrologError, RuntimeError) as error:
        st.error(f"No se pudo iniciar SWI-Prolog o cargar la base de conocimiento: {error}")
        st.info(
            "Instala SWI-Prolog, verifica que esté disponible para PySwip y ejecuta "
            "`py -m pip install -r requirements.txt`."
        )
        return

    opciones_sintomas = {nombre: descripcion for nombre, descripcion in sintomas_catalogo}
    with st.form("formulario_diagnostico"):
        elegidos = st.multiselect(
            "Síntomas observados",
            options=list(opciones_sintomas),
            format_func=lambda nombre: opciones_sintomas[nombre],
        )
        adicionales = st.text_input(
            "Otros síntomas del catálogo (opcional)",
            placeholder="Escribe nombres separados por coma, por ejemplo: no_enciende",
            help="Usa los identificadores del catálogo mostrado arriba; no escribas términos Prolog.",
        )

        st.markdown("#### Detalles opcionales")
        col_temp, col_beep = st.columns(2)
        with col_temp:
            conoce_temperatura = st.checkbox("Conozco la temperatura del procesador")
            temperatura = (
                st.number_input(
                    "Temperatura del procesador (°C)",
                    min_value=0,
                    max_value=150,
                    step=1,
                    value=None,
                    placeholder="Ingresa los grados Celsius",
                )
                if conoce_temperatura
                else None
            )
        with col_beep:
            patron_label = st.selectbox(
                "Patrón de pitidos",
                options=["No lo conozco / no aplica", *PATRONES_PITIDOS],
            )
            patron = PATRONES_PITIDOS.get(patron_label)

        incluir_equipo = st.checkbox("Indicar tipo y antigüedad del computador")
        tipo_equipo = None
        antiguedad = None
        if incluir_equipo:
            col_tipo, col_edad = st.columns(2)
            with col_tipo:
                tipo_equipo = st.selectbox(
                    "Tipo de equipo",
                    options=["escritorio", "portatil"],
                    format_func=lambda valor: (
                        "Computador de escritorio"
                        if valor == "escritorio"
                        else "Computador portátil"
                    ),
                )
            with col_edad:
                antiguedad = st.number_input(
                    "Antigüedad (años)", min_value=0, max_value=100, step=1, value=5
                )

        st.markdown("#### Pruebas realizadas")
        no_hizo_pruebas = st.checkbox("No hice ninguna prueba", value=True)
        pruebas_seleccionadas: list[tuple[str, str]] = []
        resultados_pendientes: list[str] = []
        if not no_hizo_pruebas:
            nombres_pruebas = st.multiselect(
                "Selecciona las pruebas realizadas",
                options=list(NOMBRES_PRUEBA),
                format_func=lambda nombre: NOMBRES_PRUEBA[nombre],
            )
            for nombre in nombres_pruebas:
                resultado_label = st.selectbox(
                    f"Resultado: {NOMBRES_PRUEBA[nombre]}",
                    options=["Selecciona el resultado", *RESULTADOS_PRUEBA],
                    key=f"resultado_{nombre}",
                )
                resultado = RESULTADOS_PRUEBA.get(resultado_label)
                if resultado:
                    pruebas_seleccionadas.append((nombre, resultado))
                else:
                    resultados_pendientes.append(NOMBRES_PRUEBA[nombre])

        enviar = st.form_submit_button("Analizar síntomas", type="primary")

    if enviar:
        try:
            if resultados_pendientes:
                raise ValueError(
                    "Selecciona el resultado de cada prueba realizada: "
                    + ", ".join(resultados_pendientes)
                    + "."
                )
            entrada = preparar_entrada(
                elegidos,
                adicionales,
                temperatura,
                patron,
                tipo_equipo,
                antiguedad,
                pruebas_seleccionadas,
            )
            respuesta = motor.analizar_caso(entrada)
            st.session_state["harddiag_ultima_respuesta"] = respuesta
        except ValueError as error:
            st.error(str(error))
        except (PrologError, RuntimeError, OSError) as error:
            st.error(f"Falló la consulta entre Python y Prolog: {error}")

    respuesta = st.session_state.get("harddiag_ultima_respuesta")
    if respuesta is not None:
        mostrar_resultado(respuesta)


if __name__ == "__main__":
    main()

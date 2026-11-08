"""Interfaz Streamlit de HardDiag. La inferencia y sus explicaciones viven en Prolog."""

from __future__ import annotations

import re
import unicodedata

import streamlit as st
from pyswip.prolog import PrologError

from motor_inferencia import MotorInferencia, Respuesta

ALIASES_SINTOMAS = [
    ("no enciende", "no_enciende"),
    ("no prende", "no_enciende"),
    ("no arranca", "no_enciende"),
    ("equipo no enciende", "no_enciende"),
    ("olor a quemado", "olor_quemado"),
    ("olor quemado", "olor_quemado"),
    ("pantalla negra", "pantalla_negra"),
    ("pantalla en negro", "pantalla_negra"),
    ("monitor negro", "pantalla_negra"),
    ("pantalla azul", "pantalla_azul"),
    ("pantalla en azul", "pantalla_azul"),
    ("monitor azul", "pantalla_azul"),
    ("se apaga solo", "apagados_repentinos"),
    ("se apaga de repente", "apagados_repentinos"),
    ("apaga solo", "apagados_repentinos"),
    ("pantalla azul", "pantalla_azul"),
    ("bloquea", "bloqueos"),
    ("se congela", "bloqueos"),
    ("quedarse pegado", "bloqueos"),
    ("va lento", "lentitud"),
    ("muy lento", "lentitud"),
    ("arranque lento", "arranque_lento"),
    ("se reinicia solo", "reinicios_aleatorios"),
    ("reinicios aleatorios", "reinicios_aleatorios"),
    ("ventilador hace ruido", "ventilador_ruidoso"),
    ("ventilador ruidoso", "ventilador_ruidoso"),
    ("ventilador no gira", "ventilador_detenido"),
    ("ventiladores no giran", "ventilador_detenido"),
    ("ventiladores giran", "ventiladores_giran"),
    ("disco hace clic", "ruido_clic"),
    ("hace clic", "ruido_clic"),
    ("disco no encontrado", "disco_no_encontrado"),
    ("lineas en la pantalla", "lineas_en_pantalla"),
    ("rayas en la pantalla", "lineas_en_pantalla"),
    ("artefactos en pantalla", "artefactos_video"),
    ("artefactos en la imagen", "artefactos_video"),
    ("calienta demasiado", "ventilador_ruidoso"),
    ("se calienta", "ventilador_ruidoso"),
    ("sobrecalienta", "ventilador_ruidoso"),
    ("no da imagen", "pantalla_negra"),
    ("pantalla sin imagen", "pantalla_negra"),
]

PATRONES_PITIDOS_LIBRES = {
    "3 pitidos cortos": "tres_cortos",
    "tres pitidos cortos": "tres_cortos",
    "1 largo y 2 cortos": "un_largo_dos_cortos",
    "uno largo y dos cortos": "un_largo_dos_cortos",
    "1 largo y 3 cortos": "un_largo_tres_cortos",
    "uno largo y tres cortos": "un_largo_tres_cortos",
    "pitidos cortos repetidos": "cortos_repetidos",
    "pitidos repetidos": "cortos_repetidos",
}


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
DESCRIPCIONES_SINTOMA = {
    "no_enciende": "El equipo no enciende",
    "led_encendido": "Alguna luz indicadora está encendida",
    "apagados_repentinos": "El equipo se apaga de repente",
    "olor_quemado": "Hay olor a quemado",
    "pitidos_arranque": "Se oyen pitidos al arrancar",
    "hora_incorrecta": "La fecha y la hora se pierden",
    "reinicios_aleatorios": "El equipo se reinicia solo",
    "ventilador_ruidoso": "El ventilador hace ruido excesivo",
    "ventilador_detenido": "El ventilador no gira",
    "ventiladores_giran": "Los ventiladores giran al encender",
    "lentitud": "El equipo funciona muy lento",
    "pantalla_azul": "Aparece una pantalla azul",
    "bloqueos": "El equipo se congela",
    "arranque_lento": "El inicio tarda demasiado",
    "ruido_clic": "El disco hace clics",
    "disco_no_encontrado": "Aparece el aviso «disco no encontrado»",
    "pantalla_negra": "La pantalla queda en negro",
    "lineas_en_pantalla": "Aparecen líneas en la pantalla",
    "artefactos_video": "Aparecen artefactos en la imagen",
}
NOMBRES_PATRON_PITIDOS = {
    "tres_cortos": "tres pitidos cortos",
    "un_largo_dos_cortos": "un pitido largo y dos cortos",
    "cortos_repetidos": "pitidos cortos repetidos",
    "un_largo_tres_cortos": "un pitido largo y tres cortos",
}
NOMBRES_TIPO_EQUIPO = {
    "escritorio": "computador de escritorio",
    "portatil": "computador portátil",
}
GUIAS_SOLUCION = {
    "fuente_poder_defectuosa": {
        "pasos": [
            "Apaga el computador y desconéctalo de la corriente.",
            "No abras la fuente de poder: puede conservar voltaje peligroso.",
            "Solicita a un técnico que confirme la falla y reemplace la fuente.",
        ],
        "ayuda": "La fuente de poder debe ser reemplazada por una compatible con el equipo.",
    },
    "cable_o_monitor_defectuoso": {
        "pasos": [
            "Apaga el equipo y vuelve a conectar firmemente el cable de video.",
            "Prueba con otro cable o monitor compatible para identificar cuál falla.",
            "Reemplaza únicamente el elemento que no funcione.",
        ],
        "ayuda": "No fuerces conectores; verifica que el cable corresponda al puerto del equipo.",
    },
    "gpu_defectuosa": {
        "pasos": [
            "Apaga y desconecta el computador antes de moverlo o llevarlo a revisión.",
            "Pide una prueba de la tarjeta gráfica y sus conexiones.",
            "Si se confirma la falla, solicita reemplazo o reparación compatible.",
        ],
        "ayuda": "La instalación o reparación interna es mejor dejarla a un técnico si no tienes experiencia.",
    },
    "placa_base_defectuosa": {
        "pasos": [
            "Apaga y desconecta el equipo.",
            "Lleva el computador a un técnico para revisar la placa y sus conexiones.",
            "Confirma el costo de reparación frente al reemplazo antes de autorizar el trabajo.",
        ],
        "ayuda": "La placa base requiere diagnóstico y reparación especializados.",
    },
    "refrigeracion_deficiente": {
        "pasos": [
            "Apaga el equipo y deja que se enfríe completamente.",
            "Mantén libres las rejillas de ventilación; en un portátil, úsalo sobre una superficie firme.",
            "Solicita limpieza interna y revisión del ventilador y la pasta térmica.",
        ],
        "ayuda": "Si el equipo sigue muy caliente, no continúes usándolo: un técnico debe revisar la refrigeración.",
    },
    "ram_mal_asentada": {
        "pasos": [
            "Apaga y desconecta el equipo antes de cualquier intervención.",
            "Solicita que vuelvan a colocar la memoria RAM y comprueben que quede bien fijada.",
            "Reinicia y observa si el problema vuelve a presentarse.",
        ],
        "ayuda": "Si no tienes experiencia abriendo el equipo, pide ayuda a un técnico.",
    },
    "ram_defectuosa": {
        "pasos": [
            "Solicita una prueba de memoria para identificar el módulo que falla.",
            "Reemplaza el módulo defectuoso por uno compatible con el equipo.",
            "Comprueba después que el sistema arranque y funcione con normalidad.",
        ],
        "ayuda": "La compatibilidad depende del modelo del computador y de su placa base.",
    },
    "disco_fallando": {
        "pasos": [
            "Respalda de inmediato tus archivos importantes si el disco todavía responde.",
            "Evita seguir usando el disco si hace ruidos extraños o los archivos dejan de abrir.",
            "Solicita la sustitución del disco y la recuperación o reinstalación del sistema.",
        ],
        "ayuda": "No guardes el respaldo en el mismo disco que presenta la falla.",
    },
    "bateria_cmos_agotada": {
        "pasos": [
            "Guarda la fecha y hora actuales y confirma si se pierden al apagar el equipo.",
            "Solicita el cambio de la batería CMOS por una del tipo compatible.",
            "Al encender de nuevo, ajusta la fecha y hora si es necesario.",
        ],
        "ayuda": "En algunos portátiles la batería no es de fácil acceso; consulta el manual o a un técnico.",
    },
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
    "smart_disco": "Revisar el estado de salud del disco",
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
PREGUNTAS_LENTITUD = [
    (
        "¿La demora se nota principalmente cuando enciendes el computador?",
        "arranque_lento",
    ),
    (
        "¿El computador también se congela o deja de responder?",
        "bloqueos",
    ),
    (
        "¿Escuchas clics repetidos o ruidos inusuales del disco?",
        "ruido_clic",
    ),
]
ESTADOS = {
    "ok": "Diagnóstico generado.",
    "datos_insuficientes": "La información no basta para confirmar un diagnóstico.",
    "entrada_vacia": "No se proporcionaron datos para analizar.",
    "entrada_invalida": "No se encontraron condiciones válidas.",
}


def normalizar_texto_libre(texto: str) -> str:
    """Reduce texto libre a una versión normalizada para comparar patrones."""
    texto_normal = unicodedata.normalize("NFKD", texto.lower())
    texto_normal = "".join(ch for ch in texto_normal if not unicodedata.combining(ch))
    texto_normal = re.sub(r"[^a-z0-9°\s]+", " ", texto_normal)
    return re.sub(r"\s+", " ", texto_normal).strip()


def detectar_equipo_desde_texto(texto: str) -> str | None:
    """Detecta si el usuario describió un portátil o un PC de escritorio."""
    texto_normal = normalizar_texto_libre(texto)
    if any(pat in texto_normal for pat in ("portatil", "laptop", "notebook", "portable")):
        return "portatil"
    if any(
        pat in texto_normal
        for pat in ("escritorio", "desktop", "torre", "pc de mesa", "computador de mesa", "computadora de mesa")
    ):
        return "escritorio"
    return None


def detectar_temperatura_desde_texto(texto: str) -> int | None:
    """Extrae temperatura en grados Celsius si la menciona el usuario."""
    texto_normal = normalizar_texto_libre(texto)
    coincidencia = re.search(r"(\d{2,3})\s*(?:grados|celsius|centigrados|°)", texto_normal)
    if coincidencia:
        return int(coincidencia.group(1))
    return None


def detectar_pitidos_desde_texto(texto: str) -> str | None:
    """Detecta patrones de pitidos en lenguaje natural."""
    texto_normal = normalizar_texto_libre(texto)
    for patron, valor in PATRONES_PITIDOS_LIBRES.items():
        if patron in texto_normal:
            return valor
    return None


def extraer_sintomas_libres(texto: str) -> list[str]:
    """Convierte frases normales de hardware a síntomas del catálogo conocido."""
    resultado: list[str] = []
    texto_normal = normalizar_texto_libre(texto)
    if not texto_normal:
        return resultado
    for patron, sintoma in ALIASES_SINTOMAS:
        if patron in texto_normal and sintoma not in resultado:
            resultado.append(sintoma)
    return resultado


def nombre_dato(codigo: str, nombres: dict[str, str]) -> str:
    return nombres.get(codigo, codigo.replace("_", " "))


def presentar_hecho(hecho: str) -> str:
    """Muestra en español los datos internos usados para justificar el resultado."""
    coincidencia = re.fullmatch(r"observado\(([^)]+)\)", hecho)
    if coincidencia:
        return nombre_dato(coincidencia.group(1), DESCRIPCIONES_SINTOMA)

    coincidencia = re.fullmatch(r"temp_cpu\((\d+)\s*°C\)", hecho)
    if coincidencia:
        return f"Temperatura del procesador: {coincidencia.group(1)} °C"

    coincidencia = re.fullmatch(r"pitidos\(([^)]+)\)", hecho)
    if coincidencia:
        patron = nombre_dato(coincidencia.group(1), NOMBRES_PATRON_PITIDOS)
        return f"Patrón de pitidos: {patron}"

    coincidencia = re.fullmatch(r"prueba\(([^,]+),\s*([^)]+)\)", hecho)
    if coincidencia:
        prueba, resultado = coincidencia.groups()
        return (
            f"Prueba realizada: {nombre_dato(prueba, NOMBRES_PRUEBA)}. "
            f"Resultado: {nombre_dato(resultado, NOMBRES_RESULTADO)}."
        )

    coincidencia = re.fullmatch(r"equipo\(([^,]+),\s*(\d+) años\)", hecho)
    if coincidencia:
        tipo, antiguedad = coincidencia.groups()
        return (
            f"Equipo: {nombre_dato(tipo, NOMBRES_TIPO_EQUIPO)}, "
            f"{antiguedad} años de antigüedad."
        )

    coincidencia = re.fullmatch(r"sintoma_componente\(([^,]+),\s*([^)]+)\)", hecho)
    if coincidencia:
        sintoma, componente = coincidencia.groups()
        descripcion = nombre_dato(sintoma, DESCRIPCIONES_SINTOMA)
        nombre = nombre_dato(componente, NOMBRES_COMPONENTE).lower()
        return f"El síntoma «{descripcion}» puede relacionarse con {nombre}."

    coincidencia = re.fullmatch(r"codigo_pitido\(([^,]+),\s*([^)]+)\)", hecho)
    if coincidencia:
        patron, componente = coincidencia.groups()
        nombre_patron = nombre_dato(patron, NOMBRES_PATRON_PITIDOS)
        nombre_componente = nombre_dato(componente, NOMBRES_COMPONENTE).lower()
        return f"El patrón «{nombre_patron}» puede relacionarse con {nombre_componente}."

    coincidencia = re.fullmatch(r"umbral\(temp_cpu_max_celsius,\s*(\d+)\)", hecho)
    if coincidencia:
        return f"Umbral de temperatura utilizado: {coincidencia.group(1)} °C."

    coincidencia = re.fullmatch(r"umbral\(antiguedad_critica_anios,\s*(\d+)\)", hecho)
    if coincidencia:
        return f"Umbral de antigüedad utilizado: {coincidencia.group(1)} años."

    return hecho.replace("_", " ").capitalize()


def presentar_negacion(texto: str) -> str:
    """Traduce las comprobaciones lógicas a una explicación clara en español."""
    if texto.startswith("R21:"):
        return "No se encontró una prueba que descarte este posible diagnóstico."
    if texto.startswith("R1:"):
        return "No se reportaron luces indicadoras encendidas."
    if texto.startswith("R9b:"):
        return "La prueba no confirmó una falla de la fuente de poder."
    if texto.startswith("R13:"):
        return (
            "No se detectó un patrón de pitidos que indique una falla de memoria; "
            "la sospecha se basa en la inestabilidad y los síntomas observados."
        )
    if texto.startswith("R25:"):
        return "Con los datos ingresados no se pudo obtener una conclusión final."
    return texto.replace("\\+", "no").replace("_", " ")


def presentar_alternativa(texto: str) -> str:
    diagnostico, separador, razon = texto.partition(": ")
    if not separador:
        return texto
    nombre = nombre_dato(diagnostico, NOMBRES_DIAGNOSTICO)
    return f"{nombre}: {razon}"


def sintomas_seguimiento_lentitud(respuestas: dict[int, str]) -> list[str]:
    """Convierte únicamente respuestas afirmativas del asistente en síntomas."""
    return [
        sintoma
        for indice, (_, sintoma) in enumerate(PREGUNTAS_LENTITUD)
        if respuestas.get(indice) == "Sí"
    ]


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
    sintomas_libres = []
    for elemento in sintomas_extra:
        sintomas_libres.extend(extraer_sintomas_libres(elemento))

    equipo_detectado = detectar_equipo_desde_texto(adicionales)
    temperatura_detectada = detectar_temperatura_desde_texto(adicionales)
    pitidos_detectado = detectar_pitidos_desde_texto(adicionales)

    if temperatura is None and temperatura_detectada is not None:
        temperatura = temperatura_detectada
    if pitidos is None and pitidos_detectado is not None:
        pitidos = pitidos_detectado
    if tipo_equipo is None and equipo_detectado is not None:
        tipo_equipo = equipo_detectado

    entrada_refinada = []
    for item in sintomas + sintomas_extra + sintomas_libres:
        valor = item.strip()
        if valor and valor not in entrada_refinada:
            entrada_refinada.append(valor)

    desconocidos = sorted({valor for valor in entrada_refinada if valor not in sintomas_validos})
    if desconocidos:
        entrada_refinada = [valor for valor in entrada_refinada if valor in sintomas_validos]

    entrada = list(dict.fromkeys(entrada_refinada))
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
    st.markdown("## Resultado del análisis")
    marca = st.session_state.get("harddiag_marca")
    if marca:
        st.caption(f"Equipo: {marca}")

    mensajes_estado = {
        "ok": ("✅", "Se encontraron posibles diagnósticos"),
        "datos_insuficientes": ("🔎", "Hace falta información para confirmar una falla"),
        "entrada_vacia": ("ℹ️", "Aún no hay información para analizar"),
        "entrada_invalida": ("⚠️", "No se encontraron datos válidos"),
    }
    icono, mensaje = mensajes_estado.get(
        respuesta.estado, ("ℹ️", ESTADOS.get(respuesta.estado, respuesta.estado))
    )
    st.info(f"{icono} **{mensaje}.**")

    if respuesta.diagnosticos:
        if len(respuesta.diagnosticos) > 1:
            st.caption("Las hipótesis están ordenadas por prioridad y evidencia.")
        for indice, diagnostico in enumerate(respuesta.diagnosticos, start=1):
            nombre = NOMBRES_DIAGNOSTICO.get(diagnostico.nombre, diagnostico.nombre)
            with st.container(border=True):
                st.markdown(f"### {indice}. {nombre}")
                col_danio, col_severidad, col_certeza, col_prioridad = st.columns(4)
                col_danio.metric("Nivel de daño", diagnostico.nivel_danio.capitalize())
                col_severidad.metric("Severidad", diagnostico.severidad.capitalize())
                col_certeza.metric("Certeza", diagnostico.certeza.capitalize())
                col_prioridad.metric("Prioridad", diagnostico.prioridad)
                st.progress(
                    max(0, min(diagnostico.cobertura, 100)) / 100,
                    text=f"Evidencia relacionada: {diagnostico.cobertura}%",
                )
                st.markdown("#### Solución recomendada")
                st.success(diagnostico.accion)
                guia = GUIAS_SOLUCION.get(diagnostico.nombre)
                if guia:
                    st.markdown("**Pasos sugeridos**")
                    for paso in guia["pasos"]:
                        st.markdown(f"- {paso}")
                    st.caption(f"Ten en cuenta: {guia['ayuda']}")
                else:
                    st.caption(
                        "Sigue la recomendación indicada y consulta a un técnico si no "
                        "tienes experiencia con reparaciones de hardware."
                    )

                explicacion = next(
                    (e for e in respuesta.explicaciones if e.nombre == diagnostico.nombre),
                    None,
                )
                if explicacion:
                    with st.expander("Ver explicación del diagnóstico"):
                        col_reglas, col_hechos = st.columns(2)
                        with col_reglas:
                            st.markdown("**Reglas aplicadas**")
                            if explicacion.reglas:
                                for regla in explicacion.reglas:
                                    st.write(f"- Regla {regla}")
                            else:
                                st.caption("No hay reglas registradas.")
                        with col_hechos:
                            st.markdown("**Datos que respaldan el resultado**")
                            if explicacion.hechos:
                                for hecho in explicacion.hechos:
                                    st.write(f"- {presentar_hecho(hecho)}")
                            else:
                                st.caption("No se registraron hechos positivos.")
                        if explicacion.negaciones:
                            st.markdown("**Comprobaciones que descartaron fallas**")
                            for negacion in explicacion.negaciones:
                                st.write(f"- {presentar_negacion(negacion)}")
                        if explicacion.alternativas_descartadas:
                            st.markdown("**Otras hipótesis descartadas**")
                            for alternativa in explicacion.alternativas_descartadas:
                                st.write(f"- {presentar_alternativa(alternativa)}")
                        st.caption(
                            "La explicación corresponde a las reglas y pruebas que Prolog "
                            "comprobó para este resultado."
                        )
    elif respuesta.sospechosos:
        st.markdown("### Componentes que conviene revisar")
        st.caption("Estos componentes tienen relación con los síntomas indicados; no son un diagnóstico confirmado.")
        columnas = st.columns(min(len(respuesta.sospechosos), 3))
        for indice, (componente, indicios) in enumerate(respuesta.sospechosos):
            with columnas[indice % len(columnas)]:
                st.metric(
                    NOMBRES_COMPONENTE.get(componente, componente),
                    f"{indicios} indicio(s)",
                )

    if respuesta.descartados:
        with st.expander("Datos que no se pudieron reconocer"):
            st.write(", ".join(respuesta.descartados))

    if respuesta.sugerencias:
        st.markdown("## ¿Qué falta?")
        st.caption(
            "Completar estas comprobaciones puede ayudar a distinguir las posibles causas. "
            "Empieza por la primera sugerencia."
        )
        for indice, sugerencia in enumerate(respuesta.sugerencias, start=1):
            with st.container(border=True):
                st.markdown(f"### {indice}. {sugerencia.dato}")
                st.write(sugerencia.razon)
                if sugerencia.hipotesis:
                    hipotesis = [
                        NOMBRES_DIAGNOSTICO.get(nombre, nombre)
                        for nombre in sugerencia.hipotesis
                    ]
                    st.caption("Esta comprobación ayuda a diferenciar: " + " · ".join(hipotesis))
    elif respuesta.estado == "datos_insuficientes":
        st.info(
            "Prueba a agregar más síntomas observados o completar los detalles del equipo "
            "y vuelve a analizar."
        )


def main() -> None:
    st.set_page_config(
        page_title="HardDiag | Diagnóstico de hardware",
        page_icon="🖥️",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        #MainMenu, header[data-testid="stHeader"], footer {visibility: hidden;}
        :root {
            --hd-cyan: #40d9ff;
            --hd-blue: #648bff;
            --hd-line: rgba(91, 183, 255, .2);
            --hd-muted: #9ab0c9;
        }
        .stApp {
            background:
                radial-gradient(ellipse at 12% 0%, rgba(32, 131, 220, .2), transparent 33%),
                radial-gradient(ellipse at 95% 24%, rgba(38, 224, 224, .09), transparent 27%),
                linear-gradient(145deg, #07111f 0%, #091728 48%, #07101d 100%);
        }
        .block-container {
            max-width: 1120px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3 { letter-spacing: -0.025em; }
        .hero {
            position: relative;
            overflow: hidden;
            padding: 2rem 2.2rem;
            margin: 0 0 1.2rem;
            border: 1px solid rgba(64, 217, 255, .3);
            border-radius: 20px;
            background:
                radial-gradient(ellipse at 85% 50%, rgba(64, 217, 255, .13), transparent 38%),
                linear-gradient(120deg, rgba(17, 36, 59, .98), rgba(11, 25, 43, .96));
            box-shadow: 0 16px 48px rgba(0, 0, 0, .28), inset 0 1px rgba(255, 255, 255, .04);
        }
        .hero-kicker {
            color: var(--hd-cyan);
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        .hero h1 {
            margin: .35rem 0 .4rem;
            color: #f0f8ff;
            font-size: clamp(2rem, 5vw, 3rem);
            text-shadow: 0 0 28px rgba(64, 217, 255, .24);
        }
        .hero p {
            margin: 0;
            max-width: 720px;
            color: #aec2d8;
            font-size: 1.05rem;
            line-height: 1.65;
        }
        .hero-status {
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            margin-top: 1.1rem;
            padding: .38rem .72rem;
            border: 1px solid rgba(64, 217, 255, .25);
            border-radius: 999px;
            background: rgba(64, 217, 255, .07);
            color: #bdefff;
            font-size: .78rem;
            letter-spacing: .02em;
        }
        .hero-status::before {
            width: .48rem;
            height: .48rem;
            border-radius: 50%;
            background: var(--hd-cyan);
            box-shadow: 0 0 12px var(--hd-cyan);
            content: "";
        }
        .stMarkdown p, .stCaption, label, [data-testid="stWidgetLabel"] p {
            color: #d5e4f3;
        }
        h2, h3, h4 { color: #edf7ff; }
        div[data-testid="stForm"] {
            padding: 1.4rem 1.5rem;
            border: 1px solid var(--hd-line);
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(16, 31, 50, .94), rgba(10, 23, 39, .96));
            box-shadow: 0 16px 42px rgba(0, 0, 0, .2), inset 0 1px rgba(255, 255, 255, .035);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 16px;
            border-color: var(--hd-line);
            background: linear-gradient(145deg, rgba(16, 31, 50, .93), rgba(10, 23, 39, .95));
            box-shadow: 0 12px 32px rgba(0, 0, 0, .16);
        }
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
            min-height: 2.8rem;
            border: 1px solid rgba(64, 217, 255, .45);
            border-radius: 10px;
            background: linear-gradient(100deg, #126f9d, #315bd1);
            color: white;
            font-weight: 700;
            box-shadow: 0 0 20px rgba(51, 160, 255, .18);
            transition: transform .18s ease, box-shadow .18s ease;
        }
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: var(--hd-cyan);
            box-shadow: 0 0 24px rgba(64, 217, 255, .3);
            transform: translateY(-1px);
        }
        div[data-testid="stAlert"] {
            border: 1px solid var(--hd-line);
            border-radius: 12px;
            background: rgba(16, 35, 54, .82);
        }
        div[data-testid="stMetric"] {
            padding: .8rem;
            border: 1px solid var(--hd-line);
            border-radius: 12px;
            background: rgba(8, 22, 38, .82);
        }
        div[data-testid="stMetricLabel"] p { color: var(--hd-muted); }
        div[data-testid="stMetricValue"] { color: #ecf8ff; }
        [data-baseweb="select"] > div, [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div {
            border-color: rgba(100, 160, 210, .28);
            background-color: rgba(7, 18, 32, .85);
        }
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="textarea"] > div:focus-within {
            border-color: var(--hd-cyan);
            box-shadow: 0 0 0 1px var(--hd-cyan), 0 0 14px rgba(64, 217, 255, .15);
        }
        [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #318bff, var(--hd-cyan));
            box-shadow: 0 0 12px rgba(64, 217, 255, .35);
        }
        @media (max-width: 640px) {
            .block-container { padding: 1rem 1rem 3rem; }
            .hero { padding: 1.3rem; border-radius: 16px; }
            div[data-testid="stForm"] { padding: 1rem; }
        }
        </style>
        <section class="hero">
            <div class="hero-kicker">Asistente de soporte técnico</div>
            <h1>HardDiag</h1>
            <p>Describe las fallas de tu computador y recibe posibles causas,
            recomendaciones y pasos seguros para continuar.</p>
            <div class="hero-status">Sistema experto · Análisis de hardware</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.write(
        "Elige los síntomas observados o descríbelos con tus propias palabras. "
        "El sistema analiza computadores de escritorio y portátiles."
    )
    st.warning(
        "Herramienta educativa de orientación. Ante olor a quemado, apaga y "
        "desconecta el computador. No abras la fuente de poder."
    )

    try:
        motor = obtener_motor()
        sintomas_catalogo = motor.listar_sintomas()
        hechos_por_seccion = motor.listar_hechos_base()
    except (FileNotFoundError, OSError, PrologError, RuntimeError) as error:
        st.error(f"No se pudo iniciar SWI-Prolog o cargar la base de conocimiento: {error}")
        st.info(
            "Instala SWI-Prolog, verifica que esté disponible para PySwip y ejecuta "
            "`py -m pip install -r requirements.txt`."
        )
        return

    cantidad_hechos_visibles = sum(map(len, hechos_por_seccion.values()))
    with st.expander(
        f"Explorar todos los hechos y catálogos de la base ({cantidad_hechos_visibles} elementos)"
    ):
        st.caption(
            "La base Prolog contiene hechos, relaciones y catálogos. Aquí se muestran "
            "todos sus elementos; los datos de cada caso se ingresan en los controles "
            "de síntomas, pitidos, pruebas y detalles del equipo."
        )
        for seccion, hechos in hechos_por_seccion.items():
            st.markdown(f"#### {seccion} ({len(hechos)})")
            st.code("\n".join(hechos), language="prolog")

    opciones_sintomas = {nombre: descripcion for nombre, descripcion in sintomas_catalogo}
    st.markdown("#### Detalles opcionales del equipo")
    st.caption(
        "Cada casilla funciona de forma independiente y muestra únicamente sus propios campos."
    )
    columna_temperatura, columna_equipo = st.columns(2)
    with columna_temperatura:
        conoce_temperatura = st.checkbox(
            "Conozco la temperatura del procesador",
            key="opcion_temperatura_independiente",
        )
    with columna_equipo:
        incluir_equipo = st.checkbox(
            "Indicar tipo y antigüedad del computador",
            key="opcion_equipo_independiente",
        )

    with st.container(border=True):
        columna_temperatura, columna_equipo = st.columns(2)
        with columna_temperatura:
            if st.session_state["opcion_temperatura_independiente"]:
                temperatura = st.number_input(
                    "Temperatura del procesador (°C)",
                    min_value=0,
                    max_value=150,
                    step=1,
                    value=None,
                    placeholder="Ingresa los grados Celsius",
                )
            else:
                temperatura = None
        with columna_equipo:
            if st.session_state["opcion_equipo_independiente"]:
                tipo_equipo = st.selectbox(
                    "Tipo de equipo",
                    options=["escritorio", "portatil"],
                    format_func=lambda valor: (
                        "Computador de escritorio"
                        if valor == "escritorio"
                        else "Computador portátil"
                    ),
                )
                antiguedad = st.number_input(
                    "Antigüedad (años)", min_value=0, max_value=100, step=1, value=5
                )
            else:
                tipo_equipo = None
                antiguedad = None

    with st.container(border=True):
        elegidos = st.multiselect(
            "Síntomas observados",
            options=list(opciones_sintomas),
            format_func=lambda nombre: opciones_sintomas[nombre],
            placeholder="Selecciona uno o varios síntomas",
        )
        adicionales = st.text_input(
            "Otros síntomas o fallas (opcional)",
            placeholder="Ejemplo: no prende, pantalla negra, portátil se calienta, olor a quemado",
            help="Puedes escribir descripciones normales del problema para equipos de escritorio o portátiles; el sistema intenta convertirlas a síntomas válidos.",
        )
        sintomas_libres = extraer_sintomas_libres(adicionales)
        presenta_lentitud = "lentitud" in elegidos or "lentitud" in sintomas_libres
        if presenta_lentitud:
            st.markdown("#### Revisemos por qué va lento")
            st.caption(
                "Te haré unas preguntas breves, una por una. Solo las respuestas afirmativas "
                "se agregarán como síntomas para el análisis."
            )
            paso_lentitud = st.session_state.get("harddiag_lentitud_paso", 0)
            respuestas_lentitud = st.session_state.get("harddiag_lentitud_respuestas", {})

            if paso_lentitud < len(PREGUNTAS_LENTITUD):
                pregunta, _ = PREGUNTAS_LENTITUD[paso_lentitud]
                st.progress(
                    (paso_lentitud + 1) / len(PREGUNTAS_LENTITUD),
                    text=f"Pregunta {paso_lentitud + 1} de {len(PREGUNTAS_LENTITUD)}",
                )
                respuesta_lentitud = st.radio(
                    pregunta,
                    options=["Sí", "No", "No estoy seguro"],
                    index=None,
                    key=f"harddiag_lentitud_respuesta_{paso_lentitud}",
                    horizontal=True,
                )
                columna_anterior, columna_siguiente = st.columns(2)
                with columna_anterior:
                    if paso_lentitud > 0 and st.button(
                        "Pregunta anterior",
                        key=f"harddiag_lentitud_anterior_{paso_lentitud}",
                    ):
                        st.session_state["harddiag_lentitud_paso"] = paso_lentitud - 1
                        st.rerun()
                with columna_siguiente:
                    texto_boton = (
                        "Ver resumen"
                        if paso_lentitud == len(PREGUNTAS_LENTITUD) - 1
                        else "Siguiente pregunta"
                    )
                    if st.button(
                        texto_boton,
                        key=f"harddiag_lentitud_siguiente_{paso_lentitud}",
                    ):
                        if respuesta_lentitud is None:
                            st.warning("Elige «Sí», «No» o «No estoy seguro» para continuar.")
                        else:
                            respuestas_lentitud[paso_lentitud] = respuesta_lentitud
                            for indice in range(paso_lentitud + 1, len(PREGUNTAS_LENTITUD)):
                                respuestas_lentitud.pop(indice, None)
                            st.session_state["harddiag_lentitud_respuestas"] = respuestas_lentitud
                            st.session_state["harddiag_lentitud_paso"] = paso_lentitud + 1
                            st.rerun()
            else:
                sintomas_seguimiento = sintomas_seguimiento_lentitud(respuestas_lentitud)
                if sintomas_seguimiento:
                    st.success(
                        "Síntomas adicionales identificados: "
                        + ", ".join(
                            DESCRIPCIONES_SINTOMA.get(sintoma, sintoma)
                            for sintoma in sintomas_seguimiento
                        )
                    )
                else:
                    st.info(
                        "No se identificaron síntomas adicionales en estas preguntas. "
                        "El síntoma general de lentitud se incluirá de todas formas."
                    )
                if st.button("Volver a revisar las respuestas", key="harddiag_lentitud_reiniciar"):
                    st.session_state["harddiag_lentitud_paso"] = 0
                    st.session_state["harddiag_lentitud_respuestas"] = {}
                    st.rerun()
        else:
            st.session_state["harddiag_lentitud_paso"] = 0
            st.session_state["harddiag_lentitud_respuestas"] = {}

        marca = st.text_input(
            "Marca del computador",
            placeholder="Ejemplo: Dell, HP, Lenovo, ASUS",
            help="Dato informativo para identificar el equipo; no cambia el diagnóstico.",
        ).strip()

        st.markdown("#### Otros datos")
        patron_label = st.selectbox(
            "Patrón de pitidos",
            options=["No lo conozco / no aplica", *PATRONES_PITIDOS],
        )
        patron = PATRONES_PITIDOS.get(patron_label)

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

        enviar = st.button("Analizar síntomas", type="primary")

    if enviar:
        try:
            if resultados_pendientes:
                raise ValueError(
                    "Selecciona el resultado de cada prueba realizada: "
                    + ", ".join(resultados_pendientes)
                    + "."
                )
            entrada = preparar_entrada(
                list(
                    dict.fromkeys(
                        elegidos
                        + (
                            sintomas_seguimiento_lentitud(
                                st.session_state.get("harddiag_lentitud_respuestas", {})
                            )
                            if presenta_lentitud
                            else []
                        )
                    )
                ),
                adicionales,
                temperatura,
                patron,
                tipo_equipo,
                antiguedad,
                pruebas_seleccionadas,
            )
            respuesta = motor.analizar_caso(entrada)
            st.session_state["harddiag_ultima_respuesta"] = respuesta
            st.session_state["harddiag_marca"] = marca
        except ValueError as error:
            st.error(str(error))
        except (PrologError, RuntimeError, OSError) as error:
            st.error(f"Falló la consulta entre Python y Prolog: {error}")

    respuesta = st.session_state.get("harddiag_ultima_respuesta")
    if respuesta is not None:
        mostrar_resultado(respuesta)


if __name__ == "__main__":
    main()

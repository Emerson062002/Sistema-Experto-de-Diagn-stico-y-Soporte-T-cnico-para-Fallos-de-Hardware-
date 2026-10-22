# Ficha de Definición del Proyecto y Pareja

**Fundación Escuela Tecnológica de Neiva – Jesús Oviedo Pérez**

## 1. Integrantes

| Nombre completo | Código estudiantil | Correo institucional |
| --- | --- | --- |
| Johan Sebastian Camacho Aragones | [completar] | [completar] |
| Luis Emerson Moncada Carvajal | [completar] | [completar] |
| Brayan Stiven Trujillo Ramon | [completar] | [completar] |

## 2. Tema seleccionado

**Título:** Sistema Experto de Diagnóstico y Soporte Técnico para Fallos de Hardware en Computadores Personales (de escritorio y portátiles). Nombre corto: *HardDiag*.

### Descripción del problema

El sistema resuelve un problema de **diagnóstico**: identificar qué componente de hardware de un computador está fallando a partir de los síntomas que observa el usuario, y recomendar la acción correcta.

Hoy, usuarios no especializados y soporte técnico de nivel básico suelen diagnosticar a prueba y error. Un mismo síntoma tiene varias causas posibles: una pantalla negra puede venir de la tarjeta gráfica, el cable de video o el monitor. Esto genera reemplazos innecesarios de piezas, tiempo perdido y costos evitables.

### Justificación: ¿por qué un sistema basado en reglas?

- El conocimiento de un técnico experimentado es **heurístico** y se expresa naturalmente como reglas «si… entonces…» (por ejemplo: si no hay video, los ventiladores giran y cambiar el cable no lo resuelve, entonces probable falla de la tarjeta gráfica).
- Las conclusiones se **encadenan**: los síntomas validan estados intermedios y estos llevan al diagnóstico final.
- El dominio es **acotado y estable**: 6 componentes y un conjunto finito de síntomas y pruebas.
- Permite **descartar** diagnósticos con pruebas (negación por fallo) y **explicar** de dónde sale cada conclusión.
- No hace falta un conjunto grande de datos históricos, que es lo que exigiría un enfoque de aprendizaje automático.

### Alcance

- **Cubre:** fuente de poder, placa base, procesador y refrigeración, memoria RAM, almacenamiento (HDD/SSD) y tarjeta gráfica y video, en equipos de escritorio y portátiles.
- **No cubre:** fallas de software, sistema operativo o virus; redes, impresoras, servidores, teléfonos y consolas; reparación a nivel de componentes de la placa; daño físico evidente por líquidos o golpes.
- **Entradas (lista enviada desde Python):** síntomas, temperatura del procesador `temp_cpu(Grados)`, patrón de pitidos `pitidos(Patron)`, pruebas realizadas `prueba(Nombre, Resultado)` y tipo y antigüedad del equipo `equipo(Tipo, Anios)`.
- **Salidas:** lista de diagnósticos con certeza (alta o media), severidad (baja, media, alta o crítica), prioridad, porcentaje de evidencia y acción recomendada. Si faltan datos, devuelve los componentes sospechosos.

### Listado preliminar de diagnósticos esperados

| Diagnóstico | Gravedad base | Acción recomendada |
| --- | --- | --- |
| `fuente_poder_defectuosa` | alta | Desconectar el equipo y reemplazar la fuente de poder. |
| `cable_o_monitor_defectuoso` | baja | Reemplazar el cable de video o el monitor que falló. |
| `gpu_defectuosa` | alta | Reemplazar la tarjeta gráfica o llevar el equipo a un técnico. |
| `placa_base_defectuosa` | alta | Llevar el equipo a un técnico para revisar y reparar la placa base. |
| `refrigeracion_deficiente` | media | Limpiar el polvo, cambiar la pasta térmica y reemplazar el ventilador. |
| `ram_mal_asentada` | baja | Reasentar el módulo de RAM y limpiar los contactos. |
| `ram_defectuosa` | media | Reemplazar el módulo de memoria RAM defectuoso. |
| `disco_fallando` | alta | Respaldar la información de inmediato y reemplazar el disco. |
| `bateria_cmos_agotada` | baja | Cambiar la batería CMOS (CR2032). |

Estados posibles de una consulta: `ok`, `datos_insuficientes`, `entrada_vacia` y `entrada_invalida`.

## 3. Contenido de la entrega

| Archivo | Contenido |
| --- | --- |
| `ficha_proyecto.md` | Esta ficha. |
| `base_conocimiento.pl` | Exactamente 45 hechos y 25 reglas de inferencia numeradas (R1–R25), con inferencia en 3 niveles, listas, cortes, negación, `findall` y severidad. |
| `motor_inferencia.py` | Puente Python–Prolog (PySwip). |
| `main.py` | Consola interactiva. |
| `web_app.py` | Servidor local para la interfaz web. |
| `index.html` | Interfaz web del sistema experto. |
| `pruebas.py` | 9 casos de prueba hacia Prolog. |
| `evidencia_pruebas.txt` | Salida de la ejecución de `pruebas.py`. |
| `diccionario_predicados.md` | Diccionario de predicados. |

## 4. Cómo ejecutar

1. Instalar SWI-Prolog y las dependencias de Python: `pip install -r requirements.txt`.
2. Interfaz web: `py web_app.py` y abrir `http://127.0.0.1:8000` en el navegador.
3. Consola interactiva: `py main.py`.
4. Pruebas: `py pruebas.py` (genera `evidencia_pruebas.txt`).

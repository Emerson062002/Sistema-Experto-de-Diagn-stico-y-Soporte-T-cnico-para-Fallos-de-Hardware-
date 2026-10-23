# HardDiag

Sistema experto universitario para orientar el diagnóstico de fallas de hardware en computadores. La interfaz Streamlit recibe y valida los datos; el motor SWI-Prolog aplica las reglas, explica las conclusiones y recomienda la información adicional que ayudaría a distinguir hipótesis.

> HardDiag es un proyecto educativo, no sustituye una revisión profesional. Si hay olor a quemado, apaga y desconecta el computador. No abras la fuente de poder.

## Requisitos

- Windows 10/11.
- Python 3.10 o posterior.
- SWI-Prolog instalado y disponible para PySwip.
- Navegador web moderno.

## Instalación

### 1. Instalar SWI-Prolog

Descárgalo e instálalo desde [swi-prolog.org](https://www.swi-prolog.org/download/stable). En el instalador de Windows, habilita la opción para agregar SWI-Prolog al `PATH` si está disponible. Abre una terminal nueva y verifica:

```powershell
swipl --version
```

PySwip utiliza la biblioteca compartida de SWI-Prolog. Si Python no logra localizarla, configura `PATH` para incluir la carpeta `bin` de SWI-Prolog y verifica la arquitectura compatible (Python y SWI-Prolog deben ser ambos de 64 bits o ambos de 32 bits). Después de modificar `PATH`, cierra y abre de nuevo Visual Studio Code.

### 2. Instalar dependencias Python

Abre la terminal integrada de VS Code en la carpeta del repositorio:

```powershell
py --version
py -m pip install -r requirements.txt
```

La instalación directa equivalente solicitada es:

```powershell
py -m pip install pyswip streamlit
```

`requirements.txt` declara PySwip y Streamlit para repetir la instalación del proyecto. No se necesita Node.js.

## Ejecutar la interfaz Streamlit

Desde la carpeta que contiene `main.py` y `base_conocimiento.pl`:

```powershell
py -m streamlit run main.py
```

Streamlit muestra la dirección local en la terminal y abre el navegador. Normalmente es:

```text
http://localhost:8501
```

Para detener la aplicación, vuelve a la terminal y presiona **Ctrl+C**. No ejecutes `py main.py` para iniciar la interfaz; usa `streamlit run` como se indica.

## Uso

1. Selecciona síntomas del catálogo. También puedes escribir identificadores adicionales separados por coma; Python comprueba que existan en el catálogo antes de enviarlos.
2. Si conoces la temperatura, indícala; de lo contrario, déjala vacía. El patrón de pitidos es opcional.
3. El tipo y la antigüedad del equipo también son opcionales.
4. Deja marcada **«No hice ninguna prueba»** si corresponde. Si desmarcas esa opción, selecciona las pruebas realizadas y su resultado. Las pruebas sin resultado no se envían como evidencia.
5. Pulsa **«Analizar síntomas»**.

El resultado contiene los diagnósticos calculados por Prolog (certeza, severidad, prioridad, evidencia y recomendación). Si faltan datos, muestra componentes sospechosos y el panel **«¿Qué falta?»** con pruebas o datos priorizados por las hipótesis compatibles. Abre **«¿Por qué?»** para ver las reglas comprobadas, los hechos del caso, las negaciones por fallo y las alternativas descartadas mediante pruebas.

Los ejemplos de identificadores de síntomas incluyen:

```text
no_enciende
pantalla_negra
ventiladores_giran
pantalla_azul
olor_quemado
```

Al ingresar síntomas en el campo de texto, utiliza sus identificadores de Prolog, no frases libres.

## ¿Qué contiene el proyecto?

| Archivo | Descripción |
| --- | --- |
| `base_conocimiento.pl` | Base Prolog con 45 hechos, reglas R1–R25, diagnósticos, trazas y sugerencias de información faltante. |
| `motor_inferencia.py` | Adaptador PySwip: carga Prolog, envía entradas y convierte respuestas, explicaciones y sugerencias. |
| `main.py` | Interfaz Streamlit principal. |
| `main_consola.py` | Conserva la interfaz interactiva original por consola. |
| `pruebas.py` | Nueve pruebas del motor y cinco verificaciones de integración, trazas y sugerencias. |
| `evidencia_pruebas.txt` | Salida guardada por `pruebas.py`. |
| `requirements.txt` | Dependencias Python del proyecto. |
| `web_app.py`, `index.html` | Interfaz web HTTP anterior; se conserva como alternativa, pero el entregable Streamlit se ejecuta con `main.py`. |
| `ficha_proyecto.md` | Ficha académica, alcance e integrantes. |
| `diccionario_predicados.md` | Referencia de predicados Prolog. |

## Arquitectura

```text
Formulario Streamlit (main.py)
        ↓ datos limpios y validados
Adaptador PySwip (motor_inferencia.py)
        ↓ analizar_caso/2
Base SWI-Prolog (base_conocimiento.pl)
        ↓ diagnóstico, traza, exclusiones y sugerencias
Presentación en Streamlit
```

La inferencia, la explicación de las reglas y la priorización de datos faltantes se realizan en Prolog. Python se ocupa de la interfaz, la validación básica de los valores del formulario y la presentación de la respuesta.

## Base de conocimiento: hechos y reglas

La base mantiene **exactamente 45 hechos** y las **25 reglas de inferencia identificadas como R1–R25**. Los catálogos relacionados están almacenados como hechos compactos para cumplir el conteo; reglas auxiliares permiten consultarlos. La traza informa reglas solo cuando la ruta Prolog correspondiente tuvo éxito. El panel de información faltante se basa en catálogos, evidencias típicas y pruebas que existen en la propia base.

Los componentes cubiertos son fuente de poder, placa base, procesador/refrigeración, memoria RAM, almacenamiento y tarjeta gráfica/video. Los diagnósticos incluyen fallas de fuente, video, placa base, refrigeración, RAM, disco y batería CMOS.

## Ejecutar pruebas

```powershell
py pruebas.py
```

El script conserva los nueve casos anteriores y agrega cinco comprobaciones de integración:

1. Diagnóstico suficiente con explicación de reglas y hechos.
2. Síntomas insuficientes.
3. Más de una hipótesis compatible.
4. Recomendación de datos/prueba faltante.
5. Entrada válida sin diagnóstico final.

El comando debe terminar con código 0 e informar todas las verificaciones aprobadas. También actualiza `evidencia_pruebas.txt`.

## Ejecutar la consola original

La consola anterior se conserva en:

```powershell
py main_consola.py
```

## Solución de problemas

### `swipl` no se reconoce

Instala SWI-Prolog, comprueba su carpeta `bin` en `PATH`, reinicia VS Code y vuelve a comprobar:

```powershell
swipl --version
```

### PySwip no encuentra SWI-Prolog

Verifica que SWI-Prolog está instalado, que `PATH` incluye su carpeta `bin`, que Python y SWI-Prolog tienen la misma arquitectura y que reiniciaste la terminal después del cambio. Reinstala dependencias si hace falta:

```powershell
py -m pip install -r requirements.txt
```

### Streamlit no se reconoce

Ejecuta el módulo con el intérprete de Python:

```powershell
py -m streamlit run main.py
```

### Error al abrir `base_conocimiento.pl`

Ejecuta el comando desde la carpeta del proyecto. El motor también localiza la base respecto a `motor_inferencia.py`, por lo que no es necesario codificar una ruta absoluta.

## Alcance y limitaciones

El sistema orienta sobre fallas de hardware de computadores personales. No diagnostica fallas de software, sistema operativo, virus, redes, impresoras, teléfonos o consolas, y no reemplaza pruebas físicas ni la evaluación de un técnico. Los códigos de pitidos pueden variar según el fabricante del BIOS.

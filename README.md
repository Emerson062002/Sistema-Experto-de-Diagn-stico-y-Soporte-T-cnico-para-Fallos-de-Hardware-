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

La interfaz utiliza un tema oscuro con acentos luminosos. Para detener la aplicación, vuelve a la terminal y presiona **Ctrl+C**. La recarga automática de archivos está desactivada para que no aparezca el aviso en inglés de Streamlit; después de cambiar el código, reinicia la aplicación y actualiza la página del navegador. No ejecutes `py main.py` para iniciar la interfaz; usa `streamlit run` como se indica.

## Uso

1. Empieza en **«¿Qué le sucede al computador?»**: selecciona síntomas o escribe libremente una descripción en el campo multilínea (por ejemplo: "no prende", "pantalla negra", "la pantalla parpadea y se apaga jugando"). El sistema intenta asociar el texto con síntomas conocidos. Si no reconoce una frase, la conserva y avisa que todavía no puede inferir un diagnóstico a partir de ella; un experto puede enseñarle una asociación. Si indicas lentitud, aparece una guía para precisar si tarda al iniciar, se congela o el disco hace clic.
2. También puedes ingresar identificadores adicionales separados por coma; Python comprueba que existan en el catálogo antes de enviarlos.
3. En **«Datos que pueden afinar el resultado»** puedes abrir las secciones opcionales para agregar temperatura, antigüedad, pitidos o pruebas. No es necesario completar estos datos para analizar.
4. Si necesitas gestionar el vocabulario, pulsa **«Ir al modo experto»**. Allí puedes agregar frases personalizadas, consultar las existentes y eliminar las que ya no uses. **«Volver al diagnóstico normal»** retorna al formulario.
5. Puedes registrar la marca del computador; se muestra como dato informativo y no modifica las reglas de diagnóstico.
6. Deja marcada **«No he realizado pruebas»** si corresponde. Si desmarcas esa opción, selecciona las pruebas realizadas y su resultado. Las pruebas sin resultado no se envían como evidencia.
7. Pulsa **«Analizar mi computador»** y revisa las hipótesis, la evidencia y las recomendaciones.

### Modos de uso

- **Normal:** formulario de síntomas, descripción libre, datos opcionales y resultados del diagnóstico. No muestra herramientas de administración del conocimiento.
- **Experto:** se abre con el botón **«Ir al modo experto»**. Permite agregar, consultar y eliminar alias persistentes vinculados a los síntomas conocidos. Usa **«Volver al diagnóstico normal»** para salir.

El modo experto administra las frases reconocidas, no crea diagnósticos ni reglas Prolog nuevas.

## Entrega 3: procesamiento del lenguaje natural y aprendizaje dinámico

Este proyecto incluye la funcionalidad solicitada para la entrega académica de procesamiento del lenguaje natural, con integración de DCG y aprendizaje dinámico en cliente:

- Conversión de frases naturales y sus variantes comunes a síntomas del dominio, con integración del parser y el catálogo Prolog.
- Mapeo de alias aprendidos por el usuario experto: por ejemplo, si se define que "se ven rayas" equivale a `lineas_en_pantalla`, el sistema lo guardará para futuras consultas.
- El campo acepta cualquier descripción; solo se generan diagnósticos a partir de síntomas que el sistema conoce. El texto no reconocido se indica al usuario en vez de inventar una causa.
- Compatibilidad con la entrada formal anterior del proyecto (identificadores tipo `no_enciende`, `pitidos(tres_cortos)`, `temp_cpu(97)` y pruebas como `prueba(fuente_con_probador, falla)`).

La interfaz, los resultados y las explicaciones se presentan en español. El resultado contiene los diagnósticos calculados por Prolog (nivel de daño según el tipo de falla, certeza, severidad, prioridad y evidencia), una solución recomendada y pasos orientativos para cada daño reconocido. El nivel de daño se clasifica como leve, moderado o grave a partir de la gravedad base de cada diagnóstico; la severidad puede aumentar por los factores de riesgo del caso. Si faltan datos, muestra componentes sospechosos y el panel **«¿Qué falta?»** con pruebas o datos priorizados por las hipótesis compatibles. Abre **«¿Por qué?»** para ver las reglas comprobadas, los hechos del caso, las negaciones por fallo y las alternativas descartadas mediante pruebas. Las guías son educativas; si no tienes experiencia en reparaciones internas, consulta a un técnico.

Los ejemplos de identificadores de síntomas incluyen:

```text
no_enciende
pantalla_negra
ventiladores_giran
pantalla_azul
olor_quemado
```

En el campo de descripción puedes escribir frases normales; el sistema intenta relacionarlas con los síntomas que conoce.

## ¿Qué contiene el proyecto?

| Archivo | Descripción |
| --- | --- |
| `base_conocimiento.pl` | Base Prolog con hechos, reglas R1–R25, diagnóstico, trazas, sugerencias y nuevas reglas para alias y procesamiento de lenguaje natural. |
| `motor_inferencia.py` | Adaptador PySwip: carga Prolog, normaliza entradas, interpreta texto libre, aplica y persiste alias dinámicos y convierte respuestas, explicaciones y sugerencias. |
| `main.py` | Interfaz Streamlit con vistas separadas para diagnóstico normal y administración del modo experto. |
| `aliases_aprendidos.json` | Archivo creado automáticamente para conservar los alias personalizados del modo experto. |
| `main_consola.py` | Conserva la interfaz interactiva original por consola. |
| `pruebas.py` | Casos del motor y verificaciones del sistema experto, incluidas pruebas de integración y compatibilidad. |
| `evidencia_pruebas.txt` | Salida guardada por `pruebas.py`. |
| `requirements.txt` | Dependencias Python del proyecto. |
| `web_app.py`, `index.html` | Interfaz web HTTP anterior; se conserva como alternativa, pero el entregable principal es la interfaz Streamlit. |
| `ficha_proyecto.md` | Ficha académica, alcance e integrantes. |
| `diccionario_predicados.md` | Referencia de predicados Prolog. |

## Arquitectura

```text
Formulario Streamlit (main.py)
        ↓ texto libre / entrada formal / modo experto
Adaptador PySwip (motor_inferencia.py)
        ↓ normalización, alias dinámicos y parseo de lenguaje natural
Base SWI-Prolog (base_conocimiento.pl)
        ↓ diagnóstico, traza, exclusiones, sugerencias y DCG
Presentación en Streamlit
```

La inferencia, la explicación de las reglas y la priorización de datos faltantes se realizan en Prolog. Python se ocupa de la interfaz, la validación básica del formulario, la interpretación del lenguaje natural, el aprendizaje dinámico de aliases y la presentación de la respuesta.

## Base de conocimiento: hechos y reglas

La base mantiene los hechos del dominio, los catálogos de síntomas y pruebas, y las reglas de inferencia responsables del diagnóstico. Además, incluye el soporte para la entrega 3 con alias dinámicos y un parser mínimo de lenguaje natural mediante DCG.

Los catálogos relacionados están almacenados como hechos compactos para consultar información de componentes, pruebas, resultados, umbrales, diagnósticos y acciones recomendadas. La traza informa reglas solo cuando la ruta Prolog correspondiente tuvo éxito. El panel de información faltante se basa en catálogos, evidencias típicas y pruebas que existen en la propia base.

Los componentes cubiertos son fuente de poder, placa base, procesador/refrigeración, memoria RAM, almacenamiento y tarjeta gráfica/video. Los diagnósticos incluyen fallas de fuente, video, placa base, refrigeración, RAM, disco y batería CMOS.

## Ejecutar pruebas

```powershell
py pruebas.py
```

El script ejecuta once casos base y siete comprobaciones de integración:

1. Diagnóstico suficiente con explicación de reglas y hechos.
2. Síntomas insuficientes.
3. Más de una hipótesis compatible.
4. Recomendación de datos/prueba faltante.
5. Entrada válida sin diagnóstico final.
6. Reconocimiento de descripciones naturales adicionales.

El comando debe terminar con código 0 e informar todas las verificaciones aprobadas. También actualiza `evidencia_pruebas.txt`.

## Ejecutar la consola original

La consola anterior se conserva en:

```powershell
py main_consola.py
```

## Modo experto y aprendizaje dinámico

El modo experto del proyecto permite que el usuario registre frases comunes que luego se convertirán automáticamente en síntomas del dominio. Por ejemplo:

```text
Frase: "pantalla con rayas"
Se guarda como alias de: lineas_en_pantalla
```

Esto hace que el sistema aprenda dinámicamente variantes del lenguaje natural sin alterar la lógica de inferencia ni la validación del catálogo. La relación se conserva para futuras consultas en la misma sesión y puede reutilizarse en nuevas entradas.

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

# HardDiag

Sistema experto para orientar el diagnóstico de fallas de hardware en computadores de escritorio y portátiles. El usuario informa síntomas y, si los conoce, mediciones y resultados de pruebas; el motor de inferencia en SWI-Prolog aplica reglas y devuelve diagnósticos ordenados por prioridad.

> HardDiag es una herramienta educativa de orientación. No reemplaza una revisión profesional. Ante olor a quemado, apaga y desconecta el equipo; no abras la fuente de poder.

## Contenido

- [Funciones](#funciones)
- [Tecnologías y requisitos](#tecnologías-y-requisitos)
- [Instalación en Windows](#instalación-en-windows)
- [Ejecutar la interfaz web](#ejecutar-la-interfaz-web)
- [Usar el diagnóstico web](#usar-el-diagnóstico-web)
- [Ejecutar la consola](#ejecutar-la-consola)
- [Ejecutar las pruebas](#ejecutar-las-pruebas)
- [Arquitectura y archivos](#arquitectura-y-archivos)
- [Base de conocimiento](#base-de-conocimiento)
- [Solución de problemas](#solución-de-problemas)
- [Alcance y limitaciones](#alcance-y-limitaciones)

## Funciones

- Interfaz web en español adaptable a computadores y celulares.
- Diagnósticos basados en exactamente 45 hechos y 25 reglas de inferencia, organizadas en tres niveles.
- Resultados con certeza, severidad, prioridad, cobertura de evidencia y acción recomendada.
- Lista de componentes sospechosos cuando faltan datos para confirmar un diagnóstico.
- La temperatura del procesador y el patrón de pitidos son opcionales.
- La persona puede marcar **«No hice ninguna prueba»** y consultar sin registrar pruebas.
- Consola interactiva como alternativa a la página web.
- Nueve casos de prueba que ejercitan diagnósticos, exclusiones y entradas incompletas.

## Tecnologías y requisitos

- Python 3.
- SWI-Prolog instalado y disponible en el sistema.
- PySwip, instalado desde `requirements.txt`.
- Navegador web moderno para la interfaz web.

No se necesita Node.js ni instalar dependencias de JavaScript.

## Instalación en Windows

Abre PowerShell en la carpeta del proyecto. Si ya estás en otra carpeta, cambia a la ruta correspondiente:

```powershell
cd "C:\Users\EMERSON\OneDrive\Escritorio\proyecto de sistemas expertos\sistema_experto_hardware"
```

Comprueba que Python y SWI-Prolog estén disponibles:

```powershell
py --version
swipl --version
```

Si SWI-Prolog no está instalado, instálalo desde [swi-prolog.org](https://www.swi-prolog.org/download/stable). Luego instala las dependencias Python:

```powershell
py -m pip install -r requirements.txt
```

En otros sistemas operativos, usa `python3` en lugar de `py` si ese es el comando de Python disponible.

## Ejecutar la interfaz web

Desde la carpeta del proyecto:

```powershell
py web_app.py
```

Abre esta dirección en el navegador:

```text
http://127.0.0.1:8000
```

La aplicación funciona localmente en el computador donde se ejecuta el servidor. Mantén abierta la ventana de PowerShell mientras la usas. Para detenerla, presiona **Ctrl+C**.

## Usar el diagnóstico web

1. Selecciona los síntomas observados.
2. En **Detalles adicionales**, proporciona la temperatura o el patrón de pitidos solo si los conoces. Las casillas para indicar que no conoces o no deseas proporcionar esos datos vienen seleccionadas; desmárcalas para habilitar los campos.
3. Indica el tipo y la antigüedad del equipo si deseas. Estos campos también son opcionales.
4. En **Pruebas realizadas**, deja seleccionada **«No hice ninguna prueba»** si no realizaste pruebas. Para añadir una, desmarca esa opción y pulsa **«Agregar una prueba»**.
5. Pulsa **«Analizar síntomas»** para consultar el motor experto.

El resultado muestra explícitamente si no se realizaron pruebas o, si se hicieron, cada prueba con el resultado indicado. También puede mostrar uno o más diagnósticos ordenados por prioridad. Si la evidencia no basta, mostrará los componentes sospechosos en lugar de afirmar una causa.

### Datos que se pueden ingresar

**Síntomas:** no enciende, apagados repentinos, olor a quemado, fecha u hora incorrecta, reinicios, problemas de ventilación, lentitud, pantalla azul, bloqueos, problemas de arranque o disco, pantalla negra y defectos de imagen, entre otros. La lista completa se carga directamente desde la base de conocimiento.

**Temperatura:** un valor entero en grados Celsius, entre 0 y 150.

**Patrones de pitidos:** tres cortos; uno largo y dos cortos; pitidos cortos repetidos; uno largo y tres cortos. Los códigos de pitidos son orientativos y pueden variar según el fabricante del BIOS.

**Pruebas disponibles:** probador de fuente, cambio de cable, otro monitor, tarjeta gráfica en otro equipo, reasentar RAM, estado SMART del disco y cambio de batería CMOS. Cada prueba debe incluir uno de los resultados disponibles: falla, ok, resuelve o no_resuelve.

## Ejecutar la consola

Como alternativa a la web:

```powershell
py main.py
```

Escribe las condiciones separadas por comas. Por ejemplo:

```text
no_enciende, olor_quemado, prueba(fuente_con_probador, falla)
```

Otros ejemplos:

```text
temp_cpu(97), ventilador_ruidoso
```

```text
pantalla_azul, prueba(reasentar_ram, resuelve)
```

En la consola también puedes escribir:

- `sintomas`: mostrar el catálogo de síntomas.
- `ayuda`: volver a mostrar los formatos de entrada.
- `salir`: cerrar el programa.

## Ejecutar las pruebas

Desde PowerShell:

```powershell
py pruebas.py
```

El comando ejecuta nueve casos y muestra cuántos fueron aprobados. También crea o actualiza `evidencia_pruebas.txt` con el detalle. El programa termina con código 0 si todas las pruebas pasan y con código 1 si alguna falla.

Los casos cubren, entre otros:

- Diagnóstico de fuente y severidad crítica.
- Diagnósticos múltiples de almacenamiento y RAM.
- Sobrecalentamiento.
- Exclusión de causas mediante resultados de pruebas.
- Datos insuficientes y condiciones desconocidas.
- Entrada vacía.
- Diagnóstico de placa base.

## Arquitectura y archivos

| Archivo | Responsabilidad |
| --- | --- |
| `base_conocimiento.pl` | Hechos del dominio, casos de ejemplo, reglas de inferencia, validación y predicados de consulta. |
| `motor_inferencia.py` | Puente PySwip entre Python y SWI-Prolog; convierte las respuestas para su presentación. |
| `web_app.py` | Servidor HTTP local y API de la interfaz web; valida los datos recibidos antes de enviarlos a Prolog. |
| `index.html` | Interfaz web, formulario y presentación de resultados. |
| `main.py` | Interfaz interactiva por consola. |
| `pruebas.py` | Casos automatizados que comprueban las respuestas del sistema. |
| `evidencia_pruebas.txt` | Evidencia generada por la última ejecución de las pruebas. |
| `diccionario_predicados.md` | Referencia de predicados, reglas y hechos de Prolog. |
| `ficha_proyecto.md` | Definición, alcance e información de la entrega académica. |
| `requirements.txt` | Dependencias Python. |

Flujo de una consulta web:

```text
Formulario HTML → web_app.py → motor_inferencia.py / PySwip
               → base_conocimiento.pl → resultado mostrado en la página
```

## Base de conocimiento

La base cuenta con **exactamente 45 hechos** y **25 reglas de inferencia numeradas (R1–R25)**. Para conservar el catálogo completo dentro del límite, los datos relacionados (códigos de pitidos, pruebas, gravedades, acciones y evidencias) se guardan en hechos compactos de listas; las reglas auxiliares permiten consultar cada elemento. También hay ocho casos de ejemplo reutilizables con `caso_ejemplo/2`.

Las reglas de inferencia se organizan en tres niveles:

1. **Validación preliminar:** reconoce condiciones como falta de energía, ausencia de video, sobrecalentamiento, inestabilidad y señales de pitidos.
2. **Inferencia intermedia:** combina síntomas y pruebas para determinar fallas probables, y descarta hipótesis contradichas por pruebas.
3. **Conclusión final:** genera diagnósticos, recomendaciones y acciones de escalamiento.

El sistema considera estos componentes: fuente de poder, placa base, procesador y refrigeración, memoria RAM, almacenamiento y tarjeta gráfica y video.

Diagnósticos contemplados: fuente defectuosa, cable o monitor defectuoso, tarjeta gráfica defectuosa, placa base defectuosa, refrigeración deficiente, RAM mal asentada o defectuosa, disco fallando y batería CMOS agotada.

Para ver las definiciones y consultas disponibles, revisa [diccionario_predicados.md](diccionario_predicados.md).

## Solución de problemas

### `swipl` no se reconoce como comando

Instala SWI-Prolog y comprueba que su carpeta esté agregada a `PATH`. Cierra y vuelve a abrir PowerShell después de instalarlo y ejecuta:

```powershell
swipl --version
```

### No se encuentra PySwip

Instala las dependencias desde la carpeta del proyecto:

```powershell
py -m pip install -r requirements.txt
```

### El puerto 8000 ya está ocupado

Cierra la instancia anterior de `py web_app.py` con **Ctrl+C**. Si otra aplicación está usando el puerto, detén esa aplicación o cambia la constante `PORT` en `web_app.py` y abre el nuevo puerto en el navegador.

### No se puede abrir la página

Confirma que `py web_app.py` sigue ejecutándose y que abriste `http://127.0.0.1:8000` en el mismo computador.

## Alcance y limitaciones

HardDiag orienta sobre fallas de hardware de computadores personales. No diagnostica problemas de software, sistemas operativos, virus, redes, impresoras, servidores, teléfonos o consolas. Tampoco determina daños por líquidos o golpes ni reemplaza una evaluación técnica presencial.

Las conclusiones dependen de los síntomas y pruebas que informe la persona. Un resultado es una orientación basada en reglas, no una garantía de que el componente indicado sea la causa real.

:- encoding(utf8).
%% =============================================================================
%%  base_conocimiento.pl
%%  Sistema Experto de Diagnóstico y Soporte Técnico para Fallos de Hardware
%%  Fundación Escuela Tecnológica de Neiva – Jesús Oviedo Pérez
%%
%%  ESTRUCTURA DEL ARCHIVO
%%    PARTE A. HECHOS     (conocimiento del dominio + casos de ejemplo)
%%    PARTE B. REGLAS     (3.1) encadenamiento en tres niveles
%%                        Nivel 1: validación preliminar (solo hechos base)
%%                        Nivel 2: inferencia intermedia (nivel 1 + hechos)
%%                        Nivel 3: conclusión final (nivel 2 + nivel 1 + hechos)
%%    PARTE C. LISTAS Y CONTROL DE FLUJO (3.2) listas, corte (!) y negación (\+)
%%    PARTE D. RECOLECCIÓN Y SEVERIDAD   (3.3) findall/3, sort/2 y severidad
%%    PARTE E. INTERFAZ PARA PYTHON      predicados que invoca el puente
%%
%%  PREVENCIÓN DE CICLOS
%%    Las reglas están estratificadas: un predicado solo llama a predicados de
%%    un nivel inferior (N3 -> N2 -> N1 -> hechos). No hay recursión sobre el
%%    mismo predicado salvo en listas, y allí SIEMPRE se consume la cabeza
%%    antes de la llamada recursiva (recursión por la derecha, sobre la cola).
%%    No existe recursión izquierda. La meta que liga la variable del equipo
%%    (un hecho o una regla de nivel inferior) va siempre primero, y \+ solo
%%    se aplica con todas sus variables ya instanciadas.
%%
%%  USO RÁPIDO (SWI-Prolog):
%%    ?- consult('base_conocimiento.pl').
%%    ?- consultar_texto('no_enciende, olor_quemado', Respuesta).
%%
%%  La base contiene exactamente 45 hechos: componentes, síntomas, catálogos
%%  compactos, umbrales y ocho casos de ejemplo. Los predicados de acceso a
%%  esos catálogos son reglas auxiliares; las reglas de inferencia son R1-R25.
%% =============================================================================

% Los datos de un caso son dinámicos: la parte C los carga desde una lista
% enviada por Python y los elimina al terminar (ver cargar_caso/2).
:- dynamic equipo/3, observado/2, medicion/3, pitidos/2, prueba/3.


%% =============================================================================
%%  PARTE A. HECHOS
%% =============================================================================

%% -----------------------------------------------------------------------------
%%  A.1 Componentes de hardware cubiertos
%%      componente(Id, Descripcion)
%% -----------------------------------------------------------------------------
componente(fuente_poder,   'Fuente de poder').
componente(placa_base,     'Placa base').
componente(procesador,     'Procesador y refrigeración').
componente(memoria_ram,    'Memoria RAM').
componente(almacenamiento, 'Almacenamiento (HDD/SSD)').
componente(tarjeta_video,  'Tarjeta gráfica y video').

%% -----------------------------------------------------------------------------
%%  A.2 Catálogo de síntomas que el usuario puede reportar
%%      sintoma_catalogo(Sintoma, Descripcion)
%% -----------------------------------------------------------------------------
sintoma_catalogo(no_enciende,          'El equipo no enciende').
sintoma_catalogo(led_encendido,        'Algún LED del equipo está encendido').
sintoma_catalogo(apagados_repentinos,  'El equipo se apaga de repente').
sintoma_catalogo(olor_quemado,         'Hay olor a quemado').
sintoma_catalogo(pitidos_arranque,     'Se oyen pitidos al arrancar').
sintoma_catalogo(hora_incorrecta,      'La fecha y hora se pierden').
sintoma_catalogo(reinicios_aleatorios, 'El equipo se reinicia solo').
sintoma_catalogo(ventilador_ruidoso,   'El ventilador hace ruido excesivo').
sintoma_catalogo(ventilador_detenido,  'El ventilador no gira').
sintoma_catalogo(ventiladores_giran,   'Los ventiladores giran al encender').
sintoma_catalogo(lentitud,             'El equipo va muy lento').
sintoma_catalogo(pantalla_azul,        'Aparece pantalla azul').
sintoma_catalogo(bloqueos,             'El equipo se congela').
sintoma_catalogo(arranque_lento,       'El arranque tarda demasiado').
sintoma_catalogo(ruido_clic,           'El disco hace clics').
sintoma_catalogo(disco_no_encontrado,  'Aparece "disco no encontrado"').
sintoma_catalogo(pantalla_negra,       'La pantalla queda en negro').
sintoma_catalogo(lineas_en_pantalla,   'Aparecen líneas en la pantalla').
sintoma_catalogo(artefactos_video,     'Aparecen artefactos en la imagen').

%% -----------------------------------------------------------------------------
%%  A.3 Síntomas y componentes con los que se asocian
%%      sintoma_componente(Sintoma, ComponenteAsociado)
%% -----------------------------------------------------------------------------
relaciones_sintoma([
    no_enciende-fuente_poder,
    no_enciende-placa_base,
    apagados_repentinos-fuente_poder,
    olor_quemado-fuente_poder,
    pitidos_arranque-memoria_ram,
    pitidos_arranque-placa_base,
    hora_incorrecta-placa_base,
    reinicios_aleatorios-procesador,
    reinicios_aleatorios-fuente_poder,
    ventilador_ruidoso-procesador,
    ventilador_detenido-procesador,
    lentitud-procesador,
    lentitud-almacenamiento,
    pantalla_azul-memoria_ram,
    bloqueos-memoria_ram,
    bloqueos-almacenamiento,
    arranque_lento-almacenamiento,
    ruido_clic-almacenamiento,
    disco_no_encontrado-almacenamiento,
    pantalla_negra-tarjeta_video,
    lineas_en_pantalla-tarjeta_video,
    artefactos_video-tarjeta_video
]).

%% -----------------------------------------------------------------------------
%%  A.4 Códigos de pitidos de la BIOS (referenciales: varían según fabricante)
%%      codigo_pitido(Patron, ComponenteIndicado)
%% -----------------------------------------------------------------------------
catalogo_pitidos([
    tres_cortos-memoria_ram,
    un_largo_dos_cortos-tarjeta_video,
    cortos_repetidos-fuente_poder,
    un_largo_tres_cortos-placa_base
]).

%% -----------------------------------------------------------------------------
%%  A.5 Pruebas simples que el usuario puede realizar
%%      prueba_catalogo(Nombre, Descripcion)
%% -----------------------------------------------------------------------------
catalogo_pruebas([
    fuente_con_probador-'Probar la fuente con un probador de fuentes',
    cambio_cable-'Cambiar el cable de video',
    otro_monitor-'Conectar otro monitor',
    gpu_en_otro_equipo-'Probar la tarjeta gráfica en otro equipo',
    reasentar_ram-'Sacar y volver a colocar la memoria RAM',
    smart_disco-'Revisar el estado SMART del disco',
    cambio_bateria-'Cambiar la batería CMOS'
]).

%% -----------------------------------------------------------------------------
%%  A.6 Resultados válidos de una prueba
%%      resultado_prueba(Resultado, Descripcion)
%% -----------------------------------------------------------------------------
catalogo_resultados([
    falla-'La prueba detectó una falla',
    ok-'El componente pasó la prueba',
    resuelve-'La acción resolvió el problema',
    no_resuelve-'La acción no resolvió el problema'
]).

%% -----------------------------------------------------------------------------
%%  A.7 Tipos de equipo aceptados
%%      tipo_equipo(Tipo, Descripcion)
%% -----------------------------------------------------------------------------
catalogo_tipos_equipo([
    escritorio-'Computador de escritorio',
    portatil-'Computador portátil'
]).

%% -----------------------------------------------------------------------------
%%  A.8 Umbrales de decisión
%%      umbral(Parametro, Valor)
%% -----------------------------------------------------------------------------
umbral(temp_cpu_max_celsius,     85).
umbral(temp_cpu_critica_celsius, 95).
umbral(antiguedad_critica_anios, 5).

%% -----------------------------------------------------------------------------
%%  A.9 Gravedad base de cada diagnóstico posible
%%      gravedad(Diagnostico, Nivel)         Nivel: baja | media | alta
%% -----------------------------------------------------------------------------
catalogo_gravedades([
    fuente_poder_defectuosa-alta,
    cable_o_monitor_defectuoso-baja,
    gpu_defectuosa-alta,
    placa_base_defectuosa-alta,
    refrigeracion_deficiente-media,
    ram_mal_asentada-baja,
    ram_defectuosa-media,
    disco_fallando-alta,
    bateria_cmos_agotada-baja
]).

%% -----------------------------------------------------------------------------
%%  A.10 Peso numérico de cada nivel de severidad
%%       peso_gravedad(Nivel, Peso)
%% -----------------------------------------------------------------------------
catalogo_pesos([
    baja-1,
    media-2,
    alta-3,
    critica-4
]).

%% -----------------------------------------------------------------------------
%%  A.11 Acción recomendada para cada diagnóstico
%%       accion(Diagnostico, TextoDeLaAccion)
%% -----------------------------------------------------------------------------
catalogo_acciones([
    fuente_poder_defectuosa-'Desconectar el equipo y reemplazar la fuente de poder.',
    cable_o_monitor_defectuoso-'Reemplazar el cable de video o el monitor que falló en la prueba.',
    gpu_defectuosa-'Reemplazar la tarjeta gráfica o llevar el equipo a un técnico.',
    placa_base_defectuosa-'Llevar el equipo a un técnico para revisar y reparar la placa base.',
    refrigeracion_deficiente-'Limpiar el polvo, cambiar la pasta térmica y reemplazar el ventilador.',
    ram_mal_asentada-'Reasentar el módulo de RAM y limpiar los contactos.',
    ram_defectuosa-'Reemplazar el módulo de memoria RAM defectuoso.',
    disco_fallando-'Respaldar la información de inmediato y reemplazar el disco.',
    bateria_cmos_agotada-'Cambiar la batería CMOS (CR2032) de la placa base.'
]).

%% -----------------------------------------------------------------------------
%%  A.12 Evidencia típica de cada diagnóstico (lista de condiciones)
%%       evidencia_tipica(Diagnostico, ListaDeCondiciones)
%%       Condiciones especiales: temp_cpu_alta y equipo_antiguo (ver C.2).
%% -----------------------------------------------------------------------------
catalogo_evidencia([
    fuente_poder_defectuosa-[no_enciende, olor_quemado, prueba(fuente_con_probador, falla)],
    cable_o_monitor_defectuoso-[pantalla_negra, ventiladores_giran, prueba(cambio_cable, resuelve)],
    gpu_defectuosa-[pantalla_negra, ventiladores_giran,
                    prueba(cambio_cable, no_resuelve), prueba(otro_monitor, no_resuelve)],
    placa_base_defectuosa-[no_enciende, prueba(fuente_con_probador, ok),
                           pitidos(un_largo_tres_cortos)],
    refrigeracion_deficiente-[temp_cpu_alta, ventilador_ruidoso],
    ram_mal_asentada-[pantalla_azul, prueba(reasentar_ram, resuelve)],
    ram_defectuosa-[pitidos(tres_cortos), pantalla_azul,
                    prueba(reasentar_ram, no_resuelve)],
    disco_fallando-[arranque_lento, ruido_clic, prueba(smart_disco, falla)],
    bateria_cmos_agotada-[hora_incorrecta, equipo_antiguo]
]).

%% -----------------------------------------------------------------------------
%%  A.13 Ocho casos de ejemplo para consultas manuales
%% -----------------------------------------------------------------------------
caso_ejemplo(fuente, [no_enciende, olor_quemado,
                      prueba(fuente_con_probador, falla)]).
caso_ejemplo(cable_video, [pantalla_negra, ventiladores_giran,
                           prueba(cambio_cable, resuelve)]).
caso_ejemplo(grafica, [pantalla_negra, ventiladores_giran,
                       prueba(cambio_cable, no_resuelve),
                       prueba(otro_monitor, no_resuelve)]).
caso_ejemplo(placa_base, [no_enciende, prueba(fuente_con_probador, ok),
                          pitidos(un_largo_tres_cortos)]).
caso_ejemplo(refrigeracion, [temp_cpu(97), ventilador_ruidoso]).
caso_ejemplo(memoria_ram, [pantalla_azul, prueba(reasentar_ram, resuelve)]).
caso_ejemplo(disco, [arranque_lento, ruido_clic,
                     prueba(smart_disco, falla)]).
caso_ejemplo(bateria_cmos, [hora_incorrecta, equipo(escritorio, 7)]).

%% -----------------------------------------------------------------------------
%%  A.14 Reglas auxiliares para consultar los catálogos compactos.
%%       Estos accesores mantienen la interfaz usada por las reglas de R1-R25.
%% -----------------------------------------------------------------------------
sintoma_componente(Sintoma, Componente) :-
    relaciones_sintoma(Relaciones),
    member(Sintoma-Componente, Relaciones).

codigo_pitido(Patron, Componente) :-
    catalogo_pitidos(Codigos),
    member(Patron-Componente, Codigos).

prueba_catalogo(Nombre, Descripcion) :-
    catalogo_pruebas(Pruebas),
    member(Nombre-Descripcion, Pruebas).

resultado_prueba(Resultado, Descripcion) :-
    catalogo_resultados(Resultados),
    member(Resultado-Descripcion, Resultados).

tipo_equipo(Tipo, Descripcion) :-
    catalogo_tipos_equipo(Tipos),
    member(Tipo-Descripcion, Tipos).

gravedad(Diagnostico, Nivel) :-
    catalogo_gravedades(Gravedades),
    member(Diagnostico-Nivel, Gravedades).

peso_gravedad(Nivel, Peso) :-
    catalogo_pesos(Pesos),
    member(Nivel-Peso, Pesos).

accion(Diagnostico, Accion) :-
    catalogo_acciones(Acciones),
    member(Diagnostico-Accion, Acciones).

evidencia_tipica(Diagnostico, Evidencia) :-
    catalogo_evidencia(Evidencias),
    member(Diagnostico-Evidencia, Evidencias).


%% =============================================================================
%%  PARTE B. REGLAS DE INFERENCIA CON ENCADENAMIENTO (3.1)
%% =============================================================================

%% -----------------------------------------------------------------------------
%%  NIVEL 1 – VALIDACIÓN PRELIMINAR
%%  Clasifican datos de entrada o verifican condiciones elementales.
%%  Solo consultan hechos base.
%% -----------------------------------------------------------------------------

% R1. El equipo no recibe energía: no enciende y no muestra ningún LED.
%     \+ se justifica porque "no hay LED" es ausencia de información: se
%     verifica por fallo. E ya está ligada por la meta anterior.
sin_energia(E) :-
    observado(E, no_enciende),
    \+ observado(E, led_encendido).

% R2. El equipo arranca (ventiladores giran) pero no entrega imagen.
sin_video(E) :-
    observado(E, pantalla_negra),
    observado(E, ventiladores_giran).

% R3. La temperatura medida del procesador supera el umbral permitido.
sobrecalentamiento(E) :-
    medicion(E, temp_cpu, T),
    umbral(temp_cpu_max_celsius, Max),
    T > Max.

% R4. Los pitidos de la BIOS apuntan a un componente determinado.
pitidos_error(E, Componente) :-
    pitidos(E, Patron),
    codigo_pitido(Patron, Componente).

% R5. El equipo muestra inestabilidad general (tres formas de manifestarse).
inestabilidad(E) :-
    observado(E, reinicios_aleatorios).
inestabilidad(E) :-
    observado(E, pantalla_azul).
inestabilidad(E) :-
    observado(E, bloqueos).

% R6. Un síntoma observado en el equipo se asocia a un componente.
sintoma_de(E, Componente) :-
    observado(E, Sintoma),
    sintoma_componente(Sintoma, Componente).

% R7. El equipo supera la antigüedad crítica.
equipo_antiguo(E) :-
    equipo(E, _Tipo, Anios),
    umbral(antiguedad_critica_anios, Limite),
    Anios >= Limite.

% R8. Factor de riesgo inmediato: olor a quemado o temperatura crítica.
factor_riesgo(E) :-
    observado(E, olor_quemado).
factor_riesgo(E) :-
    medicion(E, temp_cpu, T),
    umbral(temp_cpu_critica_celsius, Critica),
    T >= Critica.

%% -----------------------------------------------------------------------------
%%  NIVEL 2 – INFERENCIA INTERMEDIA
%%  Combinan reglas de nivel 1 con hechos para deducir estados intermedios.
%% -----------------------------------------------------------------------------

% R9. Falla de alimentación: sin energía y la fuente falla al probarla.
falla_energia(E) :-
    sin_energia(E),
    prueba(E, fuente_con_probador, falla).
% R9b. Sin energía y con olor a quemado, sin prueba de fuente que lo contradiga.
%      \+ evita que las dos cláusulas den la misma conclusión dos veces.
falla_energia(E) :-
    sin_energia(E),
    observado(E, olor_quemado),
    \+ prueba(E, fuente_con_probador, falla).

% R10. Falla externa de video: se corrige cambiando cable o monitor.
falla_cable_o_monitor(E) :-
    sin_video(E),
    prueba(E, cambio_cable, resuelve).
falla_cable_o_monitor(E) :-
    sin_video(E),
    prueba(E, otro_monitor, resuelve).

% R11. Falla interna de video: sin imagen y las pruebas externas no la corrigen.
%      once/1 basta con un síntoma de video: no importa cuántos haya.
falla_video_interno(E) :-
    sin_video(E),
    once(sintoma_de(E, tarjeta_video)),
    prueba(E, cambio_cable, no_resuelve),
    prueba(E, otro_monitor, no_resuelve).

% R12. Refrigeración deficiente: sobrecalentamiento con ventilador anómalo.
falla_refrigeracion(E) :-
    sobrecalentamiento(E),
    observado(E, ventilador_ruidoso).
falla_refrigeracion(E) :-
    sobrecalentamiento(E),
    observado(E, ventilador_detenido).

% R13. Memoria sospechosa: los pitidos la señalan, o hay inestabilidad
%      asociada a la RAM (y los pitidos no lo habían concluido ya).
memoria_sospechosa(E) :-
    pitidos_error(E, memoria_ram).
memoria_sospechosa(E) :-
    once(inestabilidad(E)),
    once(sintoma_de(E, memoria_ram)),
    \+ pitidos_error(E, memoria_ram).

% R14. Memoria mal asentada: sospechosa y reasentarla resuelve el problema.
memoria_mal_asentada(E) :-
    memoria_sospechosa(E),
    prueba(E, reasentar_ram, resuelve).

% R15. Memoria defectuosa: sospechosa y reasentarla no resuelve el problema.
memoria_defectuosa(E) :-
    memoria_sospechosa(E),
    prueba(E, reasentar_ram, no_resuelve).

% R16. Almacenamiento degradado: síntomas de disco y la prueba SMART falla.
almacenamiento_degradado(E) :-
    once(sintoma_de(E, almacenamiento)),
    prueba(E, smart_disco, falla).

% R17. Batería CMOS agotada: la hora se pierde en un equipo antiguo.
bateria_cmos_agotada(E) :-
    observado(E, hora_incorrecta),
    equipo_antiguo(E).

% R18. Diagnósticos DESCARTADOS por una prueba que los contradice.
%      Se usan con \+ en el nivel 3 (criterio de exclusión).
descartado(E, fuente_poder_defectuosa) :-
    prueba(E, fuente_con_probador, ok).
descartado(E, gpu_defectuosa) :-
    prueba(E, gpu_en_otro_equipo, ok).
descartado(E, disco_fallando) :-
    prueba(E, smart_disco, ok).
descartado(E, bateria_cmos_agotada) :-
    prueba(E, cambio_bateria, no_resuelve).

% R19. La placa base es sospechosa si no hay energía, la fuente pasó la prueba
%      y los pitidos de BIOS apuntan a la placa.
placa_base_sospechosa(E) :-
    sin_energia(E),
    prueba(E, fuente_con_probador, ok),
    pitidos_error(E, placa_base).

% R20. La combinación de señales de R19 permite diagnosticar la placa base.
placa_base_defectuosa(E) :-
    placa_base_sospechosa(E).

%% -----------------------------------------------------------------------------
%%  NIVEL 3 – CONCLUSIÓN FINAL
%%  Determinan el diagnóstico o la recomendación integrando las reglas
%%  intermedias.
%%  diagnostico(Equipo, Diagnostico, Certeza)         Certeza: alta | media
%%
%%  Cada cláusula exige la regla de nivel 2 y NO estar descartada (\+). E y el
%%  diagnóstico ya están ligados cuando se evalúa \+ descartado/2.
%% -----------------------------------------------------------------------------

% R21. Diagnósticos (una cláusula por conclusión posible).
diagnostico(E, fuente_poder_defectuosa, alta) :-
    falla_energia(E),
    \+ descartado(E, fuente_poder_defectuosa).
diagnostico(E, cable_o_monitor_defectuoso, alta) :-
    falla_cable_o_monitor(E),
    \+ descartado(E, cable_o_monitor_defectuoso).
diagnostico(E, gpu_defectuosa, media) :-
    falla_video_interno(E),
    \+ descartado(E, gpu_defectuosa).
diagnostico(E, placa_base_defectuosa, alta) :-
    placa_base_defectuosa(E),
    \+ descartado(E, placa_base_defectuosa).
diagnostico(E, refrigeracion_deficiente, alta) :-
    falla_refrigeracion(E),
    \+ descartado(E, refrigeracion_deficiente).
diagnostico(E, ram_mal_asentada, alta) :-
    memoria_mal_asentada(E),
    \+ descartado(E, ram_mal_asentada).
diagnostico(E, ram_defectuosa, alta) :-
    memoria_defectuosa(E),
    \+ descartado(E, ram_defectuosa).
diagnostico(E, disco_fallando, alta) :-
    almacenamiento_degradado(E),
    \+ descartado(E, disco_fallando).
diagnostico(E, bateria_cmos_agotada, alta) :-
    bateria_cmos_agotada(E),
    \+ descartado(E, bateria_cmos_agotada).

% R22. Recomendación: la acción asociada a cada diagnóstico del equipo.
recomendacion(E, Accion) :-
    diagnostico(E, Diagnostico, _Certeza),
    accion(Diagnostico, Accion).

% R23. Se debe escalar a un técnico si algún diagnóstico es de gravedad alta
%      o si su certeza es solo media.
requiere_tecnico(E) :-
    diagnostico(E, Diagnostico, _Certeza),
    gravedad(Diagnostico, alta).
requiere_tecnico(E) :-
    diagnostico(E, _Diagnostico, media).

% R24. Un diagnóstico de refrigeración con un factor de riesgo requiere atención
%      técnica, especialmente cuando la temperatura es crítica.
requiere_tecnico(E) :-
    diagnostico(E, refrigeracion_deficiente, _Certeza),
    factor_riesgo(E).

% R25. Caso sin conclusión: el equipo está registrado pero ninguna regla aplica.
sin_diagnostico(E) :-
    equipo(E, _Tipo, _Anios),
    \+ diagnostico(E, _Diagnostico, _Certeza).


%% =============================================================================
%%  PARTE C. PROCESAMIENTO DE LISTAS Y CONTROL DE FLUJO (3.2)
%%
%%  Python envía una LISTA de condiciones. Formatos aceptados:
%%      sintoma                     p. ej. no_enciende, pantalla_negra
%%      temp_cpu(Grados)            medición numérica
%%      pitidos(Patron)             patrón de pitidos de la BIOS
%%      prueba(Nombre, Resultado)   prueba simple realizada
%%      equipo(Tipo, Anios)         tipo y antigüedad del equipo
%% =============================================================================

%% -----------------------------------------------------------------------------
%%  C.1 Clasificación y filtrado de la lista de entrada
%% -----------------------------------------------------------------------------

% clasificar_item(+Item, -Tipo)
% Las cláusulas son MUTUAMENTE EXCLUYENTES: el corte (!) confirma la primera
% que aplica y evita que el backtracking pruebe las demás. La última cláusula
% es el VALOR POR DEFECTO (fallback): todo lo no reconocido es 'desconocido'.
clasificar_item(Item, desconocido) :-
    \+ ground(Item), !.                      % variables sueltas no se aceptan
clasificar_item(temp_cpu(V), medicion) :-
    number(V), !.
clasificar_item(pitidos(P), pitidos) :-
    codigo_pitido(P, _), !.
clasificar_item(prueba(N, R), prueba) :-
    prueba_catalogo(N, _),
    resultado_prueba(R, _), !.
clasificar_item(equipo(T, A), equipo) :-
    tipo_equipo(T, _),
    integer(A), A >= 0, !.
clasificar_item(S, sintoma) :-
    atom(S),
    sintoma_catalogo(S, _), !.
clasificar_item(_, desconocido).             % fallback por defecto

% validar_entrada(+Entrada, -Validos, -Descartados)
% Recorre la lista (recursión por la cola) separando elementos válidos de
% elementos no reconocidos.
validar_entrada([], [], []).
validar_entrada([Item|Resto], [Item|Validos], Descartados) :-
    clasificar_item(Item, Tipo),
    Tipo \== desconocido, !,                 % corte: cláusulas excluyentes
    validar_entrada(Resto, Validos, Descartados).
validar_entrada([Item|Resto], Validos, [Item|Descartados]) :-
    validar_entrada(Resto, Validos, Descartados).

%% -----------------------------------------------------------------------------
%%  C.2 Subconjuntos y conteo de condiciones cumplidas
%% -----------------------------------------------------------------------------

% evidencia_presente(+Condicion, +Lista)
% Dos condiciones especiales se evalúan contra los datos; el resto debe
% aparecer literalmente en la lista. Los cortes hacen excluyentes las cláusulas.
evidencia_presente(temp_cpu_alta, Lista) :-
    !,
    member(temp_cpu(V), Lista),
    umbral(temp_cpu_max_celsius, Max),
    V > Max, !.
evidencia_presente(equipo_antiguo, Lista) :-
    !,
    member(equipo(_, A), Lista),
    umbral(antiguedad_critica_anios, Limite),
    A >= Limite, !.
evidencia_presente(Condicion, Lista) :-
    memberchk(Condicion, Lista).

% contiene_todos(+Requisitos, +Lista)
% Verdadero si la lista contiene TODOS los requisitos (subconjunto).
contiene_todos([], _).
contiene_todos([Req|Resto], Lista) :-
    evidencia_presente(Req, Lista),
    contiene_todos(Resto, Lista).

% contar_presentes(+Requisitos, +Lista, -N)
% Cuenta cuántos requisitos de la primera lista están presentes en la segunda.
contar_presentes([], _, 0).
contar_presentes([Req|Resto], Lista, N) :-
    evidencia_presente(Req, Lista), !,       % corte: presente -> suma 1
    contar_presentes(Resto, Lista, N0),
    N is N0 + 1.
contar_presentes([_|Resto], Lista, N) :-
    contar_presentes(Resto, Lista, N).

% contar_ocurrencias(+Elemento, +Lista, -N)
contar_ocurrencias(_, [], 0).
contar_ocurrencias(X, [X|Resto], N) :- !,
    contar_ocurrencias(X, Resto, N0),
    N is N0 + 1.
contar_ocurrencias(X, [_|Resto], N) :-
    contar_ocurrencias(X, Resto, N).

% cobertura(+Validos, +Diagnostico, -Porcentaje)
% Porcentaje (0-100) de la evidencia típica del diagnóstico que está presente.
cobertura(Validos, Diagnostico, 100) :-
    evidencia_tipica(Diagnostico, Evidencia),
    contiene_todos(Evidencia, Validos), !.   % corte: ya está completa
cobertura(Validos, Diagnostico, Porcentaje) :-
    evidencia_tipica(Diagnostico, Evidencia),
    contar_presentes(Evidencia, Validos, N),
    length(Evidencia, Total),
    Total > 0,
    Porcentaje is round(100 * N / Total).

%% -----------------------------------------------------------------------------
%%  C.3 Carga temporal de un caso a partir de la lista
%%      Reutiliza las reglas de la parte B sobre un caso identificado por Id.
%% -----------------------------------------------------------------------------

% cargar_caso(+Id, +Validos)
cargar_caso(Id, Validos) :-
    limpiar_caso(Id),
    cargar_items(Id, Validos),
    registrar_equipo_por_defecto(Id).

cargar_items(_, []).
cargar_items(Id, [Item|Resto]) :-
    cargar_item(Id, Item),
    cargar_items(Id, Resto).

% cargar_item(+Id, +Item): una cláusula por tipo de dato, excluyentes con (!).
cargar_item(Id, temp_cpu(V))    :- !, assertz(medicion(Id, temp_cpu, V)).
cargar_item(Id, pitidos(P))     :- !, assertz(pitidos(Id, P)).
cargar_item(Id, prueba(N, R))   :- !, assertz(prueba(Id, N, R)).
cargar_item(Id, equipo(T, A))   :- !, assertz(equipo(Id, T, A)).
cargar_item(Id, Sintoma)        :- assertz(observado(Id, Sintoma)).

% Si la lista no trae el equipo, se registra con tipo desconocido y 0 años.
% \+ equipo(Id,_,_): Id está instanciado, por lo que la negación es segura.
registrar_equipo_por_defecto(Id) :-
    \+ equipo(Id, _, _), !,
    assertz(equipo(Id, desconocido, 0)).
registrar_equipo_por_defecto(_).

% limpiar_caso(+Id)
limpiar_caso(Id) :-
    retractall(equipo(Id, _, _)),
    retractall(observado(Id, _)),
    retractall(medicion(Id, _, _)),
    retractall(pitidos(Id, _)),
    retractall(prueba(Id, _, _)).


%% =============================================================================
%%  PARTE D. RECOLECCIÓN Y SEVERIDAD (3.3)
%% =============================================================================

%% -----------------------------------------------------------------------------
%%  D.1 Severidad y prioridad
%% -----------------------------------------------------------------------------

% severidad(+Id, +Diagnostico, -Nivel, -Peso)
% Reglas excluyentes ordenadas de la más específica a la más general.
% Un factor de riesgo eleva a 'critica' cualquier diagnóstico que no sea de
% gravedad baja. \== se evalúa con G ya instanciada por gravedad/2.
severidad(Id, Diagnostico, critica, Peso) :-
    factor_riesgo(Id),
    gravedad(Diagnostico, Gravedad),
    Gravedad \== baja, !,
    peso_gravedad(critica, Peso).
severidad(_, Diagnostico, Nivel, Peso) :-
    gravedad(Diagnostico, Nivel),
    peso_gravedad(Nivel, Peso), !.
severidad(_, _, media, 2).                   % fallback: severidad por defecto

% prioridad(+Peso, +Cobertura, -Prioridad)
% La severidad domina (centenas); la cobertura de evidencia desempata.
prioridad(Peso, Cobertura, Prioridad) :-
    Prioridad is Peso * 100 + Cobertura.

%% -----------------------------------------------------------------------------
%%  D.2 Recolección de todos los diagnósticos de un caso
%% -----------------------------------------------------------------------------

% diagnosticar_todos(+Entrada, -Estado, -Diagnosticos)
% Agrupa en UNA lista, sin duplicados y ordenada por prioridad, todos los
% diagnósticos del caso. Cada elemento es una lista:
%     [Diagnostico, Certeza, Severidad, Prioridad, Cobertura, Accion]
% Estado: ok | datos_insuficientes | entrada_vacia | entrada_invalida
diagnosticar_todos(Entrada, entrada_invalida, []) :-
    \+ is_list(Entrada), !.
diagnosticar_todos([], entrada_vacia, []) :- !.
diagnosticar_todos(Entrada, Estado, Diagnosticos) :-
    validar_entrada(Entrada, Validos, _Descartados),
    evaluar_validos(Validos, Estado, Diagnosticos).

evaluar_validos([], entrada_invalida, []) :- !.
evaluar_validos(Validos, Estado, Diagnosticos) :-
    setup_call_cleanup(
        cargar_caso(caso_tmp, Validos),
        recolectar_diagnosticos(caso_tmp, Validos, Diagnosticos),
        limpiar_caso(caso_tmp)),
    estado_caso(Diagnosticos, Estado).

% estado_caso(+Diagnosticos, -Estado)  (cláusulas excluyentes con corte)
estado_caso([], datos_insuficientes) :- !.
estado_caso(_, ok).

% recolectar_diagnosticos(+Id, +Validos, -Ordenados)
recolectar_diagnosticos(Id, Validos, Ordenados) :-
    findall(D-C, diagnostico(Id, D, C), Crudos),
    sort(Crudos, Unicos),                    % sort/2 elimina duplicados
    findall(P-Fila,
            ( member(D-C, Unicos),
              fila_diagnostico(Id, Validos, D, C, P, Fila) ),
            Pares),
    sort(1, @>=, Pares, Descendente),        % mayor prioridad primero
    pairs_values(Descendente, Ordenados).

fila_diagnostico(Id, Validos, D, C, Prioridad, [D, C, Sev, Prioridad, Cob, Accion]) :-
    severidad(Id, D, Sev, Peso),
    cobertura(Validos, D, Cob),
    prioridad(Peso, Cob, Prioridad),
    accion(D, Accion).

%% -----------------------------------------------------------------------------
%%  D.3 Componentes sospechosos (útil cuando faltan datos)
%% -----------------------------------------------------------------------------

% componentes_sospechosos(+Entrada, -Sospechosos)
% Lista [[Componente, Cantidad], ...] ordenada de mayor a menor cantidad de
% indicios (síntomas y pitidos que apuntan a ese componente).
componentes_sospechosos(Entrada, []) :-
    \+ is_list(Entrada), !.
componentes_sospechosos(Entrada, Sospechosos) :-
    validar_entrada(Entrada, Validos, _),
    setup_call_cleanup(
        cargar_caso(caso_tmp, Validos),
        recolectar_sospechas(caso_tmp, Sospechosos),
        limpiar_caso(caso_tmp)).

recolectar_sospechas(Id, Sospechosos) :-
    findall(C, ( sintoma_de(Id, C) ; pitidos_error(Id, C) ), Todos),
    sort(Todos, Unicos),
    findall(N-C, ( member(C, Unicos), contar_ocurrencias(C, Todos, N) ), Pares),
    sort(0, @>=, Pares, Descendente),
    findall([C, N], member(N-C, Descendente), Sospechosos).


%% =============================================================================
%%  PARTE E. INTERFAZ PARA PYTHON
%%  Python solo invoca estos predicados y presenta lo que devuelven.
%% =============================================================================

% consultar_caso(+Entrada, -Respuesta)
% Respuesta = [Estado, Diagnosticos, Sospechosos, Descartados]
consultar_caso(Entrada, [Estado, Diagnosticos, Sospechosos, Descartados]) :-
    diagnosticar_todos(Entrada, Estado, Diagnosticos),
    componentes_sospechosos(Entrada, Sospechosos),
    descartados_como_texto(Entrada, Descartados).

% descartados_como_texto(+Entrada, -ListaDeAtomos)
descartados_como_texto(Entrada, []) :-
    \+ is_list(Entrada), !.
descartados_como_texto(Entrada, Textos) :-
    validar_entrada(Entrada, _Validos, Descartados),
    findall(Texto,
            ( member(Item, Descartados), format(atom(Texto), '~w', [Item]) ),
            Textos).

% consultar_texto(+Texto, -Respuesta)
% Igual que consultar_caso/2, pero recibe texto separado por comas, por
% ejemplo 'no_enciende, olor_quemado, temp_cpu(90)'.
consultar_texto(Texto, Respuesta) :-
    texto_a_lista(Texto, Lista), !,
    consultar_caso(Lista, Respuesta).
consultar_texto(_, [entrada_invalida, [], [], []]).   % fallback: sintaxis inválida

% texto_a_lista(+Texto, -Lista)
texto_a_lista(Texto, Lista) :-
    atomic_list_concat(['[', Texto, ']'], Atomo),
    catch(term_to_atom(Lista, Atomo), _, fail),
    is_list(Lista).

% listar_sintomas(-Lista)  ->  [[Sintoma, Descripcion], ...]
listar_sintomas(Lista) :-
    findall([S, D], sintoma_catalogo(S, D), Lista).

%% -----------------------------------------------------------------------------
%%  F. EXPLICABILIDAD Y DATOS FALTANTES
%%  Las trazas solo se producen después de que diagnostico/3 tuvo éxito. Cada
%%  ruta vuelve a comprobar las reglas intermedias que justifican el diagnóstico.
%% -----------------------------------------------------------------------------

% analizar_caso(+Entrada, -Reporte)
% Reporte = [Estado, Diagnosticos, Sospechosos, Descartados,
%            Explicaciones, Sugerencias]
analizar_caso(Entrada, [entrada_invalida, [], [], [], [], []]) :-
    \+ is_list(Entrada), !.
analizar_caso([], [entrada_vacia, [], [], [], [], Sugerencias]) :-
    !,
    sugerencia_entrada_vacia(Sugerencias).
analizar_caso(Entrada, Reporte) :-
    validar_entrada(Entrada, Validos, Descartados),
    setup_call_cleanup(
        cargar_caso(caso_tmp, Validos),
        reporte_cargado(caso_tmp, Validos, Descartados, Reporte),
        limpiar_caso(caso_tmp)).

reporte_cargado(Id, Validos, Descartados,
                [Estado, Diagnosticos, Sospechosos, DescartadosTexto,
                 Explicaciones, Sugerencias]) :-
    ( Validos = []
    -> Estado = entrada_invalida,
       Diagnosticos = [],
       Sospechosos = [],
       Explicaciones = [],
       Sugerencias = []
    ; recolectar_diagnosticos(Id, Validos, Diagnosticos),
      estado_caso(Diagnosticos, Estado),
      recolectar_sospechas(Id, Sospechosos),
      ( Diagnosticos = []
      -> explicacion_sin_diagnostico(Id, Validos, Explicaciones),
         sugerencias_faltantes(Id, Validos, Sugerencias)
      ; explicar_diagnosticos(Id, Validos, Diagnosticos, Explicaciones),
        sugerencias_para_hipotesis(Id, Validos, Diagnosticos, Sugerencias)
      )
    ),
    atomizar_descartados(Descartados, DescartadosTexto).

atomizar_descartados(Items, Textos) :-
    findall(Texto,
            ( member(Item, Items), format(atom(Texto), '~w', [Item]) ),
            Textos).

explicar_diagnosticos(_, _, [], []).
explicar_diagnosticos(Id, Validos, [[D, C, Sev, Prioridad, Cob, Accion]|Resto],
                      [[D, C, Sev, Prioridad, Cob, Accion,
                        Reglas, Hechos, Negaciones, Alternativas]|Explicaciones]) :-
    traza_diagnostico(Id, D, Reglas),
    hechos_comprobados(Id, Reglas, Hechos),
    negaciones_comprobadas(Id, D, Reglas, Negaciones),
    alternativas_descartadas(Id, Alternativas),
    explicar_diagnosticos(Id, Validos, Resto, Explicaciones).

traza_diagnostico(Id, fuente_poder_defectuosa, Reglas) :-
    sin_energia(Id),
    falla_energia(Id),
    ( prueba(Id, fuente_con_probador, falla)
    -> Reglas = ['R1', 'R9', 'R21']
    ; Reglas = ['R1', 'R9b', 'R21']
    ).
traza_diagnostico(Id, cable_o_monitor_defectuoso, ['R2', 'R10', 'R21']) :-
    falla_cable_o_monitor(Id).
traza_diagnostico(Id, gpu_defectuosa, ['R2', 'R6', 'R11', 'R21']) :-
    falla_video_interno(Id).
traza_diagnostico(Id, placa_base_defectuosa,
                  ['R1', 'R4', 'R19', 'R20', 'R21']) :-
    placa_base_defectuosa(Id).
traza_diagnostico(Id, refrigeracion_deficiente, Reglas) :-
    falla_refrigeracion(Id),
    ( factor_riesgo(Id)
    -> Reglas = ['R3', 'R8', 'R12', 'R21']
    ; Reglas = ['R3', 'R12', 'R21']
    ).
traza_diagnostico(Id, ram_mal_asentada, Reglas) :-
    memoria_mal_asentada(Id),
    traza_memoria(Id, Reglas, ['R14', 'R21']).
traza_diagnostico(Id, ram_defectuosa, Reglas) :-
    memoria_defectuosa(Id),
    traza_memoria(Id, Reglas, ['R15', 'R21']).
traza_diagnostico(Id, disco_fallando, ['R6', 'R16', 'R21']) :-
    almacenamiento_degradado(Id).
traza_diagnostico(Id, bateria_cmos_agotada, ['R7', 'R17', 'R21']) :-
    bateria_cmos_agotada(Id).

traza_memoria(Id, Reglas, ReglasFinales) :-
    ( pitidos_error(Id, memoria_ram)
    -> Reglas = ['R4', 'R13'|ReglasFinales]
    ; inestabilidad(Id),
      sintoma_de(Id, memoria_ram),
      \+ pitidos_error(Id, memoria_ram),
      Reglas = ['R5', 'R6', 'R13'|ReglasFinales]
    ).

hechos_comprobados(Id, Reglas, Hechos) :-
    findall(Texto, hecho_observado(Id, Texto), Observados),
    findall(Texto, hecho_medicion(Id, Texto), Mediciones),
    findall(Texto, hecho_pitido(Id, Texto), Pitidos),
    findall(Texto, hecho_prueba(Id, Texto), Pruebas),
    findall(Texto, hecho_equipo(Id, Texto), Equipos),
    findall(Texto,
            ( member(Regla, ['R6', 'R11', 'R13', 'R16']),
              memberchk(Regla, Reglas),
              hecho_asociacion_sintoma(Id, Texto)
            ),
            Asociaciones),
    findall(Texto,
            ( memberchk('R4', Reglas), hecho_asociacion_pitido(Id, Texto) ),
            Codigos),
    findall(Texto, umbral_traza(Reglas, Id, Texto), Umbrales),
    append([Observados, Mediciones, Pitidos, Pruebas, Equipos,
            Asociaciones, Codigos, Umbrales], Hechos).

hecho_observado(Id, Texto) :-
    observado(Id, Sintoma),
    format(atom(Texto), 'observado(~w)', [Sintoma]).
hecho_medicion(Id, Texto) :-
    medicion(Id, temp_cpu, Valor),
    format(atom(Texto), 'temp_cpu(~w °C)', [Valor]).
hecho_pitido(Id, Texto) :-
    pitidos(Id, Patron),
    format(atom(Texto), 'pitidos(~w)', [Patron]).
hecho_prueba(Id, Texto) :-
    prueba(Id, Nombre, Resultado),
    format(atom(Texto), 'prueba(~w, ~w)', [Nombre, Resultado]).
hecho_equipo(Id, Texto) :-
    equipo(Id, Tipo, Anios),
    Tipo \== desconocido,
    format(atom(Texto), 'equipo(~w, ~w años)', [Tipo, Anios]).
hecho_asociacion_sintoma(Id, Texto) :-
    observado(Id, Sintoma),
    sintoma_componente(Sintoma, Componente),
    format(atom(Texto), 'sintoma_componente(~w, ~w)', [Sintoma, Componente]).
hecho_asociacion_pitido(Id, Texto) :-
    pitidos(Id, Patron),
    codigo_pitido(Patron, Componente),
    format(atom(Texto), 'codigo_pitido(~w, ~w)', [Patron, Componente]).
umbral_traza(Reglas, Id, Texto) :-
    memberchk('R3', Reglas),
    medicion(Id, temp_cpu, _),
    umbral(temp_cpu_max_celsius, Umbral),
    format(atom(Texto), 'umbral(temp_cpu_max_celsius, ~w)', [Umbral]).
umbral_traza(Reglas, Id, Texto) :-
    memberchk('R7', Reglas),
    equipo(Id, _, Anios),
    Anios > 0,
    umbral(antiguedad_critica_anios, Umbral),
    format(atom(Texto), 'umbral(antiguedad_critica_anios, ~w)', [Umbral]).

negaciones_comprobadas(Id, Diagnostico, Reglas, Negaciones) :-
    findall(Texto, negacion_traza(Id, Diagnostico, Reglas, Texto), Negaciones).

negacion_traza(Id, Diagnostico, Reglas, Texto) :-
    memberchk('R21', Reglas),
    \+ descartado(Id, Diagnostico),
    format(atom(Texto),
           'R21: \\+ descartado(~w) tuvo éxito; no se encontró una prueba contradictoria.',
           [Diagnostico]).
negacion_traza(Id, _, Reglas, Texto) :-
    memberchk('R1', Reglas),
    \+ observado(Id, led_encendido),
    format(atom(Texto),
           'R1: \\+ observado(led_encendido) tuvo éxito; no se reportó un LED encendido.',
           []).
negacion_traza(Id, fuente_poder_defectuosa, Reglas, Texto) :-
    memberchk('R9b', Reglas),
    \+ prueba(Id, fuente_con_probador, falla),
    format(atom(Texto),
           'R9b: \\+ prueba(fuente_con_probador, falla) tuvo éxito.',
           []).
negacion_traza(Id, ram_defectuosa, Reglas, Texto) :-
    memberchk('R13', Reglas),
    \+ pitidos_error(Id, memoria_ram),
    format(atom(Texto),
           'R13: \\+ pitidos_error(memoria_ram) tuvo éxito; la sospecha provino de inestabilidad y síntomas de RAM.',
           []).
negacion_traza(Id, ram_mal_asentada, Reglas, Texto) :-
    memberchk('R13', Reglas),
    \+ pitidos_error(Id, memoria_ram),
    format(atom(Texto),
           'R13: \\+ pitidos_error(memoria_ram) tuvo éxito; la sospecha provino de inestabilidad y síntomas de RAM.',
           []).

alternativas_descartadas(Id, Alternativas) :-
    findall(Texto,
            ( descartado(Id, Diagnostico),
              prueba(Id, Nombre, Resultado),
              razon_descartado(Diagnostico, Nombre, Resultado, Razon),
              format(atom(Texto), '~w: ~w', [Diagnostico, Razon])
            ),
            Alternativas).

razon_descartado(fuente_poder_defectuosa, fuente_con_probador, ok,
                 'la prueba del probador indicó que la fuente pasó').
razon_descartado(gpu_defectuosa, gpu_en_otro_equipo, ok,
                 'la tarjeta gráfica funcionó en otro equipo').
razon_descartado(disco_fallando, smart_disco, ok,
                 'la revisión SMART no detectó falla').
razon_descartado(bateria_cmos_agotada, cambio_bateria, no_resuelve,
                 'cambiar la batería no resolvió el problema').

explicacion_sin_diagnostico(Id, Validos,
    [[sin_diagnostico, '', '', 0, 0, '', ['R25'], Hechos, [Negacion], []]]) :-
    sin_diagnostico(Id),
    hechos_comprobados(Id, ['R25'], Hechos),
    format(atom(Negacion),
           'R25: \\+ diagnostico(~w, _, _) tuvo éxito; ninguna conclusión final se derivó.',
           [Id]),
    Validos = [_|_].

sugerencias_faltantes(Id, Validos, Sugerencias) :-
    findall(D,
            ( candidato_diagnostico(Id, Validos, D),
              \+ diagnostico(Id, D, _),
              \+ descartado(Id, D)
            ),
            CandidatosDuplicados),
    sort(CandidatosDuplicados, Candidatos),
    ( Candidatos = []
    -> sugerencias_generales(Validos, Sugerencias)
    ; construir_sugerencias(Candidatos, Validos, Sugerencias)
    ).

sugerencias_para_hipotesis(Id, Validos, Diagnosticos, Sugerencias) :-
    ( Diagnosticos = [_,_|_]
    -> findall(D,
               ( candidato_diagnostico(Id, Validos, D),
                 \+ descartado(Id, D)
               ),
               CandidatosDuplicados),
       sort(CandidatosDuplicados, Candidatos),
       construir_sugerencias(Candidatos, Validos, Sugerencias)
    ; Sugerencias = []
    ).

candidato_diagnostico(Id, Validos, Diagnostico) :-
    componente_diagnostico(Diagnostico, Componente),
    sintoma_de(Id, Componente),
    Validos \= [].
candidato_diagnostico(_, Validos, Diagnostico) :-
    evidencia_tipica(Diagnostico, Evidencias),
    member(Evidencia, Evidencias),
    evidencia_presente(Evidencia, Validos).

componente_diagnostico(fuente_poder_defectuosa, fuente_poder).
componente_diagnostico(cable_o_monitor_defectuoso, tarjeta_video).
componente_diagnostico(gpu_defectuosa, tarjeta_video).
componente_diagnostico(placa_base_defectuosa, placa_base).
componente_diagnostico(refrigeracion_deficiente, procesador).
componente_diagnostico(ram_mal_asentada, memoria_ram).
componente_diagnostico(ram_defectuosa, memoria_ram).
componente_diagnostico(disco_fallando, almacenamiento).
componente_diagnostico(bateria_cmos_agotada, placa_base).

construir_sugerencias([], _, []).
construir_sugerencias(Candidatos, Validos, Sugerencias) :-
    findall(Clave, (member(D, Candidatos), dato_recomendado(D, Clave, _, _, _),
                    \+ dato_ya_informado(Clave, Validos)), ClavesDuplicadas),
    sort(ClavesDuplicadas, Claves),
    findall(Prioridad-[Descripcion, Razon, Hipotesis],
            ( member(Clave, Claves),
              findall(D, (member(D, Candidatos),
                          dato_recomendado(D, Clave, _, _, _)), Hipotesis),
              once(dato_recomendado(Dato, Clave, Descripcion, Razon, Base)),
              memberchk(Dato, Hipotesis),
              length(Hipotesis, Cantidad),
              Prioridad is Base + Cantidad * 10
            ),
            Pares),
    sort(1, @>=, Pares, Ordenadas),
    tomar_sugerencias(Ordenadas, 5, Sugerencias).

tomar_sugerencias([], _, []).
tomar_sugerencias(_, 0, []) :- !.
tomar_sugerencias([_-Sugerencia|Resto], N, [Sugerencia|Sugerencias]) :-
    N > 0,
    N1 is N - 1,
    tomar_sugerencias(Resto, N1, Sugerencias).

dato_ya_informado(cambio_cable, Validos) :-
    member(prueba(cambio_cable, _), Validos).
dato_ya_informado(otro_monitor, Validos) :-
    member(prueba(otro_monitor, _), Validos).
dato_ya_informado(fuente_con_probador, Validos) :-
    member(prueba(fuente_con_probador, _), Validos).
dato_ya_informado(gpu_en_otro_equipo, Validos) :-
    member(prueba(gpu_en_otro_equipo, _), Validos).
dato_ya_informado(reasentar_ram, Validos) :-
    member(prueba(reasentar_ram, _), Validos).
dato_ya_informado(smart_disco, Validos) :-
    member(prueba(smart_disco, _), Validos).
dato_ya_informado(cambio_bateria, Validos) :-
    member(prueba(cambio_bateria, _), Validos).
dato_ya_informado(temperatura, Validos) :-
    member(temp_cpu(_), Validos).
dato_ya_informado(patron_pitidos, Validos) :-
    member(pitidos(_), Validos).
dato_ya_informado(antiguedad, Validos) :-
    member(equipo(_, _), Validos).

dato_recomendado(cable_o_monitor_defectuoso, cambio_cable,
    'Prueba: cambia el cable de video y registra si resuelve el problema.',
    'R10 utiliza esta prueba para confirmar una falla externa; si no resuelve, ayuda a diferenciarla de una falla interna de video.',
    100).
dato_recomendado(gpu_defectuosa, cambio_cable,
    'Prueba: cambia el cable de video y registra si resuelve el problema.',
    'R10 y R11 distinguen entre una falla externa y una posible falla interna de video.',
    100).
dato_recomendado(gpu_defectuosa, otro_monitor,
    'Prueba: conecta otro monitor y registra el resultado.',
    'R11 requiere que el cambio de monitor tampoco resuelva la falta de imagen.',
    75).
dato_recomendado(fuente_poder_defectuosa, fuente_con_probador,
    'Prueba: revisa la fuente con un probador y registra si falla o pasa.',
    'R9 evalúa la falla de la fuente; si pasa la prueba, evita ese diagnóstico.',
    95).
dato_recomendado(placa_base_defectuosa, fuente_con_probador,
    'Prueba: revisa la fuente con un probador y registra si falla o pasa.',
    'R19 solo considera la placa base en esta ruta cuando la fuente pasó la prueba.',
    95).
dato_recomendado(placa_base_defectuosa, patron_pitidos,
    'Dato: indica el patrón de pitidos al encender, si lo escuchas.',
    'R4 y R19 relacionan el código de pitidos con una posible falla de placa base.',
    80).
dato_recomendado(ram_mal_asentada, reasentar_ram,
    'Prueba: vuelve a colocar la RAM y registra si el problema se resuelve.',
    'R14 y R15 distinguen una RAM mal asentada de una RAM posiblemente defectuosa.',
    95).
dato_recomendado(ram_defectuosa, reasentar_ram,
    'Prueba: vuelve a colocar la RAM y registra si el problema se resuelve.',
    'R14 y R15 distinguen una RAM mal asentada de una RAM posiblemente defectuosa.',
    95).
dato_recomendado(disco_fallando, smart_disco,
    'Prueba: consulta el estado SMART del disco y registra si indica falla.',
    'R16 usa el resultado SMART junto con síntomas de almacenamiento.',
    95).
dato_recomendado(refrigeracion_deficiente, temperatura,
    'Dato: proporciona la temperatura del procesador en °C, si puedes consultarla.',
    'R3 y R12 necesitan comprobar sobrecalentamiento y una anomalía de ventilación.',
    85).
dato_recomendado(refrigeracion_deficiente, ventilador,
    'Dato: indica si el ventilador hace ruido o dejó de girar.',
    'R12 combina sobrecalentamiento con un ventilador ruidoso o detenido.',
    80).
dato_recomendado(bateria_cmos_agotada, antiguedad,
    'Dato: indica el tipo y la antigüedad aproximada del equipo.',
    'R7 y R17 necesitan comprobar que el equipo alcanzó el umbral de antigüedad.',
    75).

sugerencias_generales(Validos, [[Descripcion, Razon, []]]) :-
    memberchk(led_encendido, Validos), !,
    Descripcion = 'Añade cualquier otro síntoma observable del catálogo.',
    Razon = 'R6 relaciona síntomas observados con componentes; el LED por sí solo no identifica una causa en las reglas actuales.'.
sugerencias_generales(_, [[Descripcion, Razon, []]]) :-
    Descripcion = 'Selecciona uno o más síntomas observables del catálogo.',
    Razon = 'La base de conocimiento necesita síntomas u otros datos de entrada para evaluar sus reglas de diagnóstico.'.

sugerencia_entrada_vacia([[Descripcion, Razon, []]]) :-
    Descripcion = 'Selecciona al menos un síntoma observable para iniciar el diagnóstico.',
    Razon = 'Sin condiciones de entrada, Prolog no puede comprobar ninguna regla de diagnóstico.'.

# ScopeProof 0.3.4 — candidato de publicación

**Evidencia antes de preparar la factura.** Prototipo local para relacionar alcance acordado, informe de entrega, aceptación expresa de una versión y borrador de factura. La IA ayuda a revisar; una persona decide si acepta el trabajo.

Estado al 16 de octubre de 2026: **0.3.4 supera 202 pruebas Python, cinco escenarios HTTP locales, 21 comprobaciones del controlador JavaScript y una reproducción de 16 peticiones HTTP con respuestas históricas**. El registro está en `VERIFICATION_0_3_4.txt`. Son pruebas internas con proveedores simulados; no acreditan integración real con PayPal. Los resultados anteriores de 0.3.3 se conservan como historia. La inscripción en Devpost está realizada y ScopeProof está guardado como borrador; **la candidatura aún no está enviada**.

La suite integrada incluye diez regresiones nuevas del backend. Las 21 comprobaciones de interfaz usan el JavaScript real con adaptadores DOM/HTTP; también pasó la comprobación de sintaxis. Estas revisiones no realizaron llamadas reales a PayPal ni acreditan renderizado en un navegador.

## Abrir la aplicación

Se necesita un ordenador con Python 3.11 o posterior. Clona o descarga [el repositorio](https://github.com/carlosjunquerovila-afk/scopeproof), abre una terminal en su carpeta principal y ejecuta el comando siguiente. No hace falta un instalador separado. La aplicación no se ejecuta directamente en el navegador del iPhone.

```sh
python app.py
```

La aplicación abre una sesión privada en `127.0.0.1` y guarda el estado en `~/.scopeproof-local/`. Ctrl+C la detiene. No instala un servicio permanente ni descarga modelos o dependencias.

El modo inicial muestra **LOCAL SIMULATOR · NOT PAYPAL**. Los informes de ejemplo son sintéticos y los identificadores `INV2-MOCK-*` pertenecen al simulador. No se envía una factura ni se mueve dinero.

## Recorrido recomendado

1. Lee el hito, el importe acordado y los criterios.
2. Revisa el informe incompleto y utiliza la búsqueda local o importa un análisis de tu herramienta de IA.
3. Carga el ejemplo completo y pulsa **Save new version**. Los cambios sin guardar quedan señalados: guarda o descarta expresamente antes de analizar, refrescar o abrir una revisión.
4. Abre la sesión separada y acepta explícitamente cada criterio de la versión actual después de comprobarlo.
5. Vuelve a la sesión del responsable, refresca y confirma por separado la creación del borrador simulado.

Una versión nueva invalida la aceptación anterior. Los enlaces privados autorizan acceso local, pero no verifican la identidad del cliente ni constituyen una firma legal. No los publiques ni muestres sus tokens en el vídeo.

Las tarjetas de revisión de 0.3.4 muestran juntos el criterio, el estado y motivo del análisis, su cita y la decisión humana. El resumen del análisis está separado de la aceptación: importar una respuesta no marca las casillas ni aprueba el hito.

La corrección de 0.3.3 protege los cambios sin guardar del informe y del alcance, incluidos nombre, importe, moneda y criterios. Conserva lo escrito durante respuestas tardías y serializa las acciones. No es autoguardado; confirmar expresamente una recarga todavía puede descartar ediciones pendientes.

## IA: resultado nuevo y límites precisos

Se realizó una prueba con **dos respuestas nuevas de un agente ChatGPT externo**, generadas a partir de prompts exportados por el servidor HTTP real de ScopeProof. La aplicación importó y validó las respuestas. En el caso incompleto, el formulario no probado y la accesibilidad pendiente quedaron marcados como ausentes; en el completo, encontró apoyo textual para los tres criterios.

La prueba registró 16 peticiones HTTP: la IA no aprobó automáticamente; un operador local simulado aceptó la versión; la creación y repetición dejaron un único borrador simulado. Cambiar el informe revocó la aceptación y bloqueó el análisis y enlace de revisión antiguos. El registro está en `demo_evidence/fresh_run.json`.

La ejecución original usó el runtime `0.3.2-evidence-limits`. La reproducción guardada sobre `0.3.3-edit-safety` también pasó las 16 peticiones HTTP. Esa repetición no generó análisis nuevo. **No hubo llamadas de la aplicación a una API de modelos, llamadas reales a PayPal ni clientes participantes.** No se afirma que exista vídeo de esa prueba.

En 0.3.4 también pasaron las 16 peticiones usando explícitamente la identidad histórica dentro de un espacio temporal del simulador. El registro nuevo está en `demo_evidence/replay_0_3_4.json`. Los espacios nuevos normales tienen otra identidad: las respuestas guardadas no corresponden a su prompt. Obtén un análisis nuevo para ese prompt o usa el comando de reproducción histórica; no cambies la huella de una respuesta para forzar su aceptación.

Puedes exportar el prompt de la versión actual, obtener una respuesta en tu herramienta de IA e importar el JSON. ScopeProof comprueba versión, esquema, criterios y citas; no autentica al autor ni demuestra que el informe sea verdadero. Los archivos de `examples/` son respuestas guardadas: importarlas no ejecuta una inferencia nueva.

La búsqueda local no es un LLM. El adaptador opcional de Ollama necesita un modelo ya instalado; no lo descarga. La IA no puede aceptar el hito, fijar su precio ni ejecutar pagos.

## PayPal Sandbox

```sh
python app.py --sandbox --workspace ./scopeproof-sandbox
```

Introduce credenciales de prueba autorizadas únicamente en el panel privado del ordenador que ejecuta la aplicación. No las pegues en el chat, el repositorio o el vídeo. Consulta `README.md` para los dominios de cuentas de prueba admitidos.

Lista de ejecución:

1. Comprueba que dispones de la aplicación **Sandbox**, sus credenciales y las cuentas de prueba de vendedor y comprador, y que ese ordenador puede alcanzar la API Sandbox de PayPal.
2. Arranca el comando anterior con un espacio de trabajo Sandbox separado. Conserva ese mismo espacio durante la creación y cualquier recuperación.
3. Conecta desde el panel privado y comprueba el entorno y las direcciones de prueba. La autenticación no crea una factura.
4. Guarda el alcance y el informe, revisa la versión actual con IA y acepta expresamente los criterios y esa versión en la sesión de revisión.
5. Confirma una sola creación del borrador desde la sesión del responsable. Verifica la lectura directa: importe, moneda, partes, descripción y número. Ante un resultado incierto, reconcilia leyendo el borrador existente.
6. Conserva el registro de forma privada. Si preparas evidencia pública, elimina credenciales y capacidades de sesión y mantén visible que corresponde a Sandbox. Detén el servidor con Ctrl+C.

Autenticarse es distinto de crear el borrador. La integración requiere creación real en Sandbox y lectura directa coincidente. Tener la sesión de PayPal abierta o un borrador simulado no acredita ese recorrido, que sigue pendiente.

Las credenciales se mantienen en el proceso; no se guardan en el registro o informe de la aplicación. La máquina y el sistema operativo siguen siendo de confianza. No se implementan envío de facturas, cobro, captura, reembolso ni conexión de producción.

Si una creación queda incierta, **no borres la base de datos para repetirla**. El flujo conserva la intención y reconcilia por lectura. Un caso sin registro remoto identificable puede requerir investigación manual.

En 0.3.4 cada espacio nuevo obtiene una identidad distinta que se conserva al reiniciar; los espacios existentes conservan la anterior. La petición incluye un `PayPal-Request-Id` estable derivado del borrador persistido, pero todavía no se ha comprobado su efecto con el proveedor real. Un rechazo HTTP explícito admitido queda registrado como `CREATE_REJECTED`; errores ambiguos, límites de frecuencia, fallos del servidor o de red quedan como `UNKNOWN`. Ninguno inicia otra creación automáticamente. El registro se conserva para su revisión.

## Comprobar el paquete

```sh
python run_tests.py
```

Con Node.js instalado:

```sh
node test_ui_unsaved.js
```

El segundo grupo usa adaptadores DOM/HTTP y el JavaScript real; no prueba renderizado visual ni el recorrido del navegador a PayPal. El README en inglés detalla cada límite.

Para reproducir las respuestas IA guardadas desde este repositorio:

```sh
python demo_evidence/run_demo.py --app . --replay --output ../scopeproof-local-replay.json
```

La reproducción usa un espacio temporal y guarda un resultado nuevo fuera del código. No genera otra inferencia, no llama a PayPal y no modifica la evidencia original. El resultado identifica la versión ejecutada.

## Qué publicar

Publica código, recursos de interfaz, pruebas, documentación, licencia y la evidencia sintética preparada. No publiques espacios de trabajo, bases de datos, credenciales, enlaces privados de sesión ni exportaciones sin revisar. `.gitignore` ayuda a excluir archivos locales, pero no sustituye revisar el contenido. `.env.example` contiene únicamente campos vacíos de documentación; la aplicación no lo carga automáticamente.

## Monetización y pendientes

La hipótesis actual es **99 € por piloto supervisado**, para un proyecto y hasta tres revisiones. Sustituye al anterior importe de planificación de 49 €; no es un precio validado ni hay ventas acreditadas. Se proponen diez prospectos, tres sesiones de uso y dos pilotos pagados, manteniendo la facturación de producción en el sistema habitual del estudio.

Quedan la integración Sandbox real, el vídeo con interacción IA mostrada, la publicación verificada del código y el envío definitivo. Licencia MIT, autoría pública Carlosjv, con asistencia de ChatGPT. Los documentos de versiones anteriores se conservan como historia, no como estado vigente. Consulta `RELEASE_0_3_4.md` para el estado de esta versión.

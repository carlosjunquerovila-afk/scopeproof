# ScopeProof 0.3.1 — revisión limitada y recuperación de operaciones

Esta versión deriva del paquete 0.3.0 recuperado, no sustituye su historia por resultados inventados.

## Correcciones comprobadas

1. Un enlace de revisión anterior ya no puede leer evidencias ni condiciones de una nueva versión. Antes se bloqueaba la aprobación obsoleta, pero no la lectura del estado.
2. Al reiniciar después de una interrupción, la interfaz recupera la intención desde el registro duradero. No depende de que el resultado hubiera llegado a guardarse en la pantalla.
3. Un resultado recuperado se muestra como histórico hasta una consulta explícita posterior. Reconstruir el registro no contacta con PayPal ni acredita que su estado remoto siga igual.

## Reproducción

`python run_tests.py` ejecuta 188 pruebas (168 heredadas + 20 nuevas) y los cinco escenarios HTTP locales heredados. Usa Python 3.11 o posterior; no hace llamadas a proveedores externos.

Las 20 pruebas nuevas incluyen interrupciones reales de un proceso separado mediante os._exit(73) en cinco puntos. El proveedor sigue siendo un simulador SQLite: no son fallos observados en PayPal. Después de crear un registro en ese simulador se conserva uno y se reconcilia sin otro POST. Si la interrupción ocurre antes de la creación, el resultado permanece incierto y no se habilita un reintento a ciegas.

## Ejecución

`python app.py` abre el simulador. `python app.py --sandbox` abre el panel privado de conexión. Requiere un ordenador con Python, no se ejecuta directamente en Safari de iPhone.

Las credenciales Sandbox no están incluidas. No se copian de la cuenta del usuario ni se publican en el código. La aplicación sigue sin una autenticación PayPal realizada en esta sesión, sin inferencia externa nueva, sin repositorio público ni presentación al hackathon.

## Límite de seguridad

Los enlaces de revisión son capacidades temporales; no verifican por sí solos una identidad de cliente. El sistema de archivos y el operador local siguen siendo de confianza. No es una aplicación lista para producción ni una certificación de seguridad externa.

No se envían facturas, no se capturan pagos y no se ejecutan reembolsos. Para la candidatura faltan la integración real de Sandbox, la evaluación de IA, la demostración completa y la publicación.

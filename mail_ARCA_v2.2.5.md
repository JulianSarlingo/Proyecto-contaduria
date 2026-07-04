[ACTUALIZACIÓN 8] v2.2.5

⚙️ OPTIMIZACIÓN:

* Tiempos de Carga: Se optimizó el tiempo de carga de datos al momento de la ejecución del programa. Esta mejora se aplica siempre y cuando el archivo Excel no haya sufrido modificaciones; en caso de que sea modificado, el proceso mantendrá su tiempo de carga habitual.

🐛 CORRECCIÓN CRÍTICA:

* Parámetro de Fechas en Mis Comprobantes: Se solucionó un error en la asignación de fechas para ciertos usuarios, el cual provocaba que el sistema procesara un rango incorrecto y generara la descarga de archivos Excel vacíos.

⚠️ CAMBIO ESTRUCTURAL REQUERIDO:

* Base de Datos de Licencias: Se modificó la estructura de la base de datos de las licencias para reforzar la seguridad de las autorizaciones por equipo. Debido a esta actualización, es necesario que el programa vuelva a ser autorizado para restablecer su correcto funcionamiento.

🚨 MANTENIMIENTO Y DIAGNÓSTICO (WIP):

* Módulo Mis Retenciones: Actualmente, esta sección no está respondiendo. Ya me encuentro trabajando de forma prioritaria en la resolución de este inconveniente para restablecer su funcionamiento óptimo.

📋 PROYECTO EN EVALUACIÓN:

* Paralelización de Procesos: Se sigue trabajando en la arquitectura que permitirá la ejecución simultánea de varios clientes para optimizar los tiempos de procesamiento.

📌 NOTA IMPORTANTE: El archivo config.txt sigue siendo funcional y necesario, y no ha sufrido modificaciones en esta versión.

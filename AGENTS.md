\# AGENTS.md - Proyecto UESVALLE



\## Contexto general



Este repositorio contiene el portal de tableros UESVALLE publicado mediante GitHub Pages.



Ruta local principal:



`G:\\Mi unidad\\8.UES\\PAGINA INDICADORES\\UESVALLE`



URL institucional esperada:



`https://uesvalle.github.io/`



El proyecto combina tableros HTML, archivos CSV/JSON, scripts Python, procesos de normalización de datos, análisis SIG y publicación en GitHub.



Antes de trabajar en cualquier tarea, revisar también:



`docs/MEMORIA\_CHATGPT\_UESVALLE.md`



Ese archivo resume la memoria histórica del trabajo realizado con ChatGPT sobre UESVALLE.



\## Entorno de trabajo



Sistema operativo: Windows.



Terminal preferida: PowerShell.



Python oficial del proyecto:



`C:\\Users\\Javier\\miniconda3\\envs\\analitica\\python.exe`



No usar `python` genérico si se puede usar la ruta anterior.



Carpeta principal del proyecto:



`G:\\Mi unidad\\8.UES\\PAGINA INDICADORES\\UESVALLE`



\## Estructura del repositorio



\* `dashboards/`: tableros HTML.

\* `data/`: datos por módulo.

\* `scripts/`: scripts Python y BAT por módulo.

\* `docs/`: documentación técnica y memoria del proyecto.

\* `archive/`: respaldos o versiones antiguas.



\## Reglas críticas



\* No modificar archivos `raw` sin autorización expresa.

\* No borrar datos, scripts o dashboards sin autorización.

\* No hacer cambios masivos sin explicar el alcance.

\* No usar `git add .` salvo que el usuario lo apruebe explícitamente.

\* No hacer `git push` sin aprobación explícita.

\* No hacer `git reset --hard`, `git clean -fd` ni eliminación de carpetas sin aprobación.

\* Trabajar por módulo y por archivo específico.

\* Antes de modificar un tablero, identificar qué archivos CSV/JSON consume.

\* Antes de modificar un script Python, identificar entradas, salidas y validaciones.

\* Después de modificar un normalizador, validar que genere correctamente los archivos esperados en `data/<modulo>/current`.



\## Flujo de trabajo obligatorio



1\. Revisar `git status`.

2\. Identificar archivos relacionados con la tarea.

3\. Leer `docs/MEMORIA\_CHATGPT\_UESVALLE.md` cuando la tarea toque UESVALLE.

4\. Proponer plan antes de editar.

5\. Modificar solo archivos necesarios.

6\. Ejecutar validaciones razonables.

7\. Mostrar diferencias.

8\. Sugerir commit específico, sin publicarlo automáticamente.



\## Módulos principales



\* Seguimiento ACH.

\* MPR.

\* Resultados de Agua.

\* IRCAS.

\* Sedes Educativas.

\* Filtros.

\* Piscinas.

\* Empresas Plaguicidas.

\* Dosificación Cloro.

\* Muestras.



\## Criterio de trabajo terminado



Una tarea se considera terminada cuando:



\* Los archivos modificados son los estrictamente necesarios.

\* El tablero o script funciona localmente.

\* Los datos generados conservan estructura esperada.

\* `git status` queda entendido y explicado.

\* Se informa qué se debe subir a GitHub y qué no.




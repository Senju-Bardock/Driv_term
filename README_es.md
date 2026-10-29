# Driv_term

**Google Drive en tu terminal.** Explora, visualiza, descarga, sube y organiza tus archivos de Google Drive desde una consola de texto, en Windows, Linux y macOS.

Driv_term es un único script de Python que usa **solo la biblioteca estándar de Python**. No hay nada que instalar con `pip`, ni SDK, ni servicios en segundo plano. Habla directamente con la API oficial de Google Drive v3 por HTTPS y está pensado para ser rápido: transferencias en paralelo, conexiones persistentes, descargas por trozos y subidas reanudables.

---

## Índice

1. [Características](#características)
2. [Contenido del repositorio](#contenido-del-repositorio)
3. [Requisitos](#requisitos)
4. [Instalación](#instalación)
5. [Configuración inicial: obtener las credenciales OAuth de Google](#configuración-inicial-obtener-las-credenciales-oauth-de-google)
6. [Ejecutar la aplicación](#ejecutar-la-aplicación)
7. [Inicio de sesión (flujo OAuth)](#inicio-de-sesión-flujo-oauth)
8. [La pantalla principal](#la-pantalla-principal)
9. [Referencia de comandos](#referencia-de-comandos)
10. [Seleccionar varios elementos](#seleccionar-varios-elementos)
11. [Trabajar con archivos](#trabajar-con-archivos)
12. [Descargas](#descargas)
13. [Subidas](#subidas)
14. [Mover a la papelera](#mover-a-la-papelera)
15. [Documentos, Hojas de cálculo y Presentaciones de Google](#documentos-hojas-de-cálculo-y-presentaciones-de-google)
16. [Ajuste del rendimiento](#ajuste-del-rendimiento)
17. [Dónde se guardan tus datos](#dónde-se-guardan-tus-datos)
18. [Seguridad y privacidad](#seguridad-y-privacidad)
19. [Opciones de línea de comandos](#opciones-de-línea-de-comandos)
20. [Cómo funciona por dentro](#cómo-funciona-por-dentro)
21. [Limitaciones](#limitaciones)
22. [Solución de problemas](#solución-de-problemas)
23. [Preguntas frecuentes](#preguntas-frecuentes)

---

## Características

- **Navegación completa por Drive** desde el teclado: carpetas, "Compartidos conmigo" y búsqueda por nombre.
- **Transferencias en paralelo.** Se descargan o suben varios archivos a la vez mediante un grupo de hilos (8 por defecto, configurable).
- **Conexiones HTTPS persistentes.** No se repite la consulta DNS, la conexión TCP ni el handshake TLS en cada petición, lo que marca una gran diferencia con muchos archivos pequeños.
- **Descargas por trozos en paralelo.** Los archivos grandes se dividen en partes de 16 MiB que se descargan simultáneamente con peticiones HTTP `Range`.
- **Descarga recursiva rápida de carpetas.** El árbol de carpetas se lista por lotes y en paralelo, en lugar de una petición por carpeta.
- **Subidas inteligentes.** Los archivos pequeños (hasta 5 MiB) van en una sola petición multipart. Los grandes usan el protocolo de subida reanudable de Drive con trozos de 16 MiB y recuperación automática ante fallos de red.
- **Subida y descarga de carpetas completas**, conservando la estructura de directorios.
- **Explorador amigable para subir.** Pulsa `u` y elige archivos y carpetas con la ventana de archivos de tu sistema (varios a la vez). Se acabó escribir rutas largas. Sin interfaz gráfica (SSH, servidores) pasa automáticamente a rutas escritas.
- **Descarga y borra varios elementos a la vez.** `d 1-3,5` descarga archivos y carpetas en un solo lote con una barra de progreso, y `t 2,4-6` los mueve a la papelera. `all` selecciona todo.
- **Una barra de progreso global** con tamaño total, porcentaje, velocidad actual y tiempo estimado restante.
- **Visor integrado.** Lee archivos de texto, Documentos, Presentaciones y la primera hoja de una Hoja de cálculo de Google directamente en la terminal, con paginación. El resto de archivos se abren con la aplicación predeterminada de tu sistema.
- **Exportación automática** de los archivos nativos de Google (Documentos, Hojas de cálculo, Presentaciones, Dibujos) a formatos Office/PDF/PNG.
- **Inicio de sesión seguro con OAuth 2.0** mediante el flujo de bucle local (loopback) con PKCE. Tu contraseña de Google nunca se escribe en el programa ni la ve.
- **Red robusta.** Reintentos automáticos con espera exponencial, renovación transparente del token y cancelación con `Ctrl+C`.
- **Multiplataforma.** Windows, Linux y macOS.
- **Bilingüe.** Se incluyen versiones en inglés y en español.

---

## Contenido del repositorio

| Ruta | Descripción |
| --- | --- |
| `code/Driv_term_en.py` | Código fuente en Python, interfaz en **inglés**. |
| `code/Driv_term_es.py` | Código fuente en Python, interfaz en **español**. |
| `Driv_term_en.exe` | Ejecutable de Windows listo para usar, interfaz en **inglés**. |
| `Driv_term_es.exe` | Ejecutable de Windows listo para usar, interfaz en **español**. |
| `README.md` | Este documento en inglés. |
| `README_es.md` | Este documento en español. |

> Si prefieres no ejecutar un binario ya compilado, ejecuta el código fuente de Python que está en la carpeta `code/`. Es un único archivo legible y puedes revisar todo lo que hace.

---

## Requisitos

### Usando el código fuente de Python

- **Python 3.8 o superior.**
- Acceso a internet.
- Un navegador web en el mismo equipo (se necesita una vez para autorizar la aplicación).
- Tus propias credenciales OAuth de Google (gratuitas, ver [más abajo](#configuración-inicial-obtener-las-credenciales-oauth-de-google)).

No hacen falta paquetes de terceros.

### Usando los archivos `.exe`

- Windows.
- Un navegador web, acceso a internet y tus propias credenciales OAuth de Google.
- **No** necesitas tener Python instalado.

---

## Instalación

### Opción A: código fuente de Python (todas las plataformas)

```bash
git clone https://github.com/Senju-Bardock/Driv_term.git
cd Driv_term/code
python3 Driv_term_es.py
```

En Windows usa `python` en lugar de `python3`. Usa `Driv_term_en.py` para la interfaz en inglés.

### Opción B: ejecutable de Windows

1. Descarga `Driv_term_es.exe` (español) o `Driv_term_en.exe` (inglés) de este repositorio.
2. Haz doble clic, o ejecútalo desde `cmd` / PowerShell:

```powershell
.\Driv_term_es.exe
```

Windows SmartScreen o tu antivirus pueden avisar sobre ejecutables sin firmar descargados de internet. Es habitual en herramientas pequeñas e independientes. Si tienes dudas, compila y ejecuta desde el código fuente de Python.

---

## Configuración inicial: obtener las credenciales OAuth de Google

Google no permite que programas de terceros usen usuario y contraseña. En su lugar, cada usuario crea su **propio** cliente OAuth gratuito, de modo que la aplicación solo puede acceder a **tu** Drive y al de nadie más. Esto se hace **una sola vez**.

1. Abre la [Consola de Google Cloud](https://console.cloud.google.com/) y **crea un proyecto** (con el nombre que quieras).
2. Ve a **APIs y servicios → Biblioteca**, busca **Google Drive API** y pulsa **Habilitar**.
3. Ve a **APIs y servicios → Pantalla de consentimiento de OAuth**:
   - Elige el tipo de usuario **Externo**.
   - Rellena los datos obligatorios de la aplicación (nombre, tu correo).
   - En **Usuarios de prueba**, **añade tu propia dirección de correo de Google**.
4. Ve a **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**:
   - Tipo de aplicación: **Aplicación de escritorio**.
5. **Descarga el archivo JSON** (o copia el *ID de cliente* y el *secreto de cliente*).

La primera vez que inicies Driv_term, te pedirá estas credenciales:

```
Ruta del JSON descargado (o Enter para pegar ID y secreto a mano):
```

- Escribe la ruta del archivo JSON descargado, **o**
- pulsa Enter y pega a mano el `client_id` y el `client_secret`.

Se guardan localmente en `~/.drive_terminal/config.json` y no se volverán a pedir.

---

## Ejecutar la aplicación

Inicia el programa e introduce el correo de la cuenta de Google que quieras usar:

```
=== Google Drive en la terminal ===

email: tu@gmail.com
```

Si todo va bien verás:

```
Conectado como tu@gmail.com
Espacio usado: 12.3 GB de 15.0 GB
Transferencias en paralelo: 8 hilos (DRIVE_WORKERS para cambiarlo)
```

y se abre la pantalla principal del explorador.

---

## Inicio de sesión (flujo OAuth)

La primera vez que uses una cuenta (o cuando caduque la sesión guardada), Driv_term inicia el proceso de autorización:

1. Arranca un pequeño servidor web en `127.0.0.1` con un puerto libre aleatorio. Solo escucha en tu propio equipo.
2. Abre tu navegador predeterminado en la página de consentimiento de Google. Si el navegador no se abre, el programa imprime un enlace que puedes pegar en cualquier navegador **del mismo equipo**.
3. Inicias sesión y concedes el acceso.
4. Google redirige el navegador al servidor local, la página muestra **"Listo. Ya puedes cerrar esta pestana y volver a la terminal"** y el programa continúa.
5. Se guarda un token de actualización (refresh token) para que los próximos inicios sean automáticos.

Detalles:

- El programa espera hasta **5 minutos** a que autorices. Pulsa `Ctrl+C` para cancelar.
- El flujo usa **PKCE** (S256) y un valor `state` aleatorio para protegerse contra interceptaciones y falsificaciones.
- Si inicias sesión con una cuenta de Google distinta al correo que escribiste, el programa te avisa y usa la cuenta con la que realmente iniciaste sesión.
- Mientras tu aplicación esté en modo "Testing" (pruebas), Google muestra una pantalla de aviso indicando que la app no está verificada. Es normal porque es *mi propia* aplicación: pulsa **Avanzado** y continúa.

---

## La pantalla principal

```
=== Drive: tu@gmail.com ===
Ruta: Mi unidad / Proyectos

   #  Tipo  Nombre                            Tamano  Modificado
------------------------------------------------------------
   1  DIR   Copias de seguridad                    -   2026-10-01
   2  DIR   Fotos                                  -   2026-09-14
   3  GDOC  Notas de la reunion                    -   2026-10-20
   4  FILE  informe.pdf                       2.4 MB   2026-10-18
   5  LNK   Acceso directo a archivo               -   2026-08-02

Pagina 1/1 - 5 elementos
  [numero] abrir | b atras | h inicio | n/p pagina | s buscar | c compartidos conmigo
  d SEL descargar | t SEL papelera | u subir | m nueva carpeta   (SEL: 3 | 1-4 | 1,3,7 | all)
  r recargar | x cerrar sesion | q salir   (Ctrl+C cancela una transferencia)

>
```

**Columnas**

| Columna | Significado |
| --- | --- |
| `#` | El número que escribes para abrir un elemento o para usar con `d` y `t`. |
| `Tipo` | `DIR` carpeta, `FILE` archivo normal, `GDOC` archivo nativo de Google (Documentos/Hojas/Presentaciones/Dibujos), `LNK` acceso directo. |
| `Nombre` | Nombre del elemento (se recorta con `~` si es demasiado largo para el ancho de tu terminal). |
| `Tamano` | Tamaño legible (`-` para carpetas y archivos nativos de Google). |
| `Modificado` | Fecha de la última modificación (`AAAA-MM-DD`). |

Las carpetas se listan primero y luego los archivos, ambos ordenados por nombre. La lista está paginada con **15 elementos por página**. El formato se adapta al ancho de tu terminal.

---

## Referencia de comandos

Escribe un comando en el prompt `>` y pulsa Enter.

| Comando | Acción |
| --- | --- |
| `<número>` | Abre una carpeta, o abre el menú de archivo si es un archivo. Los accesos directos se siguen hasta su destino. |
| `b` | Vuelve un nivel atrás. |
| `h` | Vuelve a la raíz ("Mi unidad"). |
| `n` / `p` | Página siguiente / anterior. |
| `s` | Busca por nombre (elementos cuyo nombre *contiene* el texto que escribas). |
| `c` | Muestra los archivos **compartidos contigo**. |
| `d SEL` | Descarga uno o **varios** elementos (archivos y/o carpetas), por ejemplo `d 3`, `d 1-4`, `d 1,3,7`, `d all`. Ver [Seleccionar varios elementos](#seleccionar-varios-elementos). |
| `t SEL` | Mueve uno o **varios** elementos a la papelera de Drive (tras confirmar). Misma sintaxis de selección que `d`. |
| `u` | Sube archivos y/o carpetas a la carpeta actual usando el explorador de archivos del sistema. |
| `m` | Crea una nueva carpeta en la carpeta actual. |
| `r` | Recarga el listado actual. |
| `x` | Cierra sesión y borra de este equipo el token guardado de esta cuenta. |
| `q` | Salir. |
| `Ctrl+C` | Cancela la transferencia en curso (los archivos parciales se limpian). |

Notas:

- `u` y `m` solo funcionan **dentro de una carpeta**, no dentro de resultados de búsqueda ni de "Compartidos conmigo". Entra primero en una carpeta.
- Tras una subida, la creación de una carpeta o mover elementos a la papelera, el listado se actualiza automáticamente.

---

## Seleccionar varios elementos

Los comandos `d` (descargar) y `t` (mover a la papelera) aceptan **uno o varios elementos** a la vez. Escribe el comando seguido de los números de la columna `#`:

| Escribes | Selecciona |
| --- | --- |
| `d 3` | El elemento 3. |
| `d 1-4` | Los elementos 1, 2, 3 y 4. |
| `d 1,3,7` | Los elementos 1, 3 y 7. |
| `d 2-5 9` | Del 2 al 5, y el 9. Sirven comas y espacios, y puedes mezclar rangos y números sueltos. |
| `d all` (o `d todo`) | **Todos** los elementos del listado actual (todas las páginas, no solo la que ves). |

La misma sintaxis funciona con `t`. Si la entrada no es válida (`d 0`, `t 99`, `d abc`...) se rechaza con un mensaje y **no se hace nada**. Si escribes solo `d` o `t`, se muestra un recordatorio breve de la sintaxis.

---

## Trabajar con archivos

Escribe el número de un archivo para abrir su menú:

```
Archivo : informe.pdf
Tipo    : application/pdf
Tamano  : 2.4 MB

  1) Ver      2) Descargar      3) Informacion
  4) Mover a la papelera           0) Volver
```

### 1) Ver

- Los **archivos de texto** (texto plano, código fuente, registros, JSON, CSV, Markdown y muchos más) se muestran en un paginador. Solo se carga el primer **1 MiB**; si el archivo es mayor, un aviso te indica que lo descargues para ver el contenido completo.
- Los **Documentos y Presentaciones de Google** se exportan como texto plano y se muestran en el paginador.
- Las **Hojas de cálculo de Google** se exportan como CSV y se muestran en el paginador (**solo la primera hoja**).
- Los **Dibujos de Google** se exportan a PNG y se abren con el visor de imágenes de tu sistema.
- **Cualquier otro archivo** (imágenes, PDF, vídeos, archivos comprimidos, etc.) se descarga a una carpeta temporal y se abre con la **aplicación predeterminada del sistema** (`os.startfile` en Windows, `open` en macOS, `xdg-open` en Linux). Para archivos de más de **100 MB** el programa pide confirmación antes.

El paginador muestra una pantalla cada vez: pulsa **Enter** para seguir o **q** para salir.

### 2) Descargar

Pide una carpeta de destino (por defecto, tu carpeta `Downloads`) y guarda el archivo. En los archivos nativos de Google puedes elegir el formato de exportación.

### 3) Información

Muestra metadatos: ID, nombre, tipo MIME, tamaño, fechas de creación y modificación, enlace web y propietarios.

### 4) Mover a la papelera

Tras confirmar (`s`), mueve el archivo a la **papelera de Drive**. **No** es un borrado permanente: puedes restaurar el archivo desde la papelera en Google Drive. Para enviar varios elementos a la vez a la papelera, usa `t` en la pantalla principal (ver [Mover a la papelera](#mover-a-la-papelera)).

---

## Descargas

Usa `d SEL` en la pantalla principal (uno o varios elementos, ver [Seleccionar varios elementos](#seleccionar-varios-elementos)), o la opción **Descargar** del menú de un archivo.

### Destino

Se te pide una carpeta de destino. Pulsa Enter para usar la predeterminada (`~/Downloads`, o el directorio actual si no existe), o escribe `?` para elegir la carpeta con la ventana del sistema.

### Colisiones de nombres

Driv_term **nunca sobrescribe** archivos existentes. Si ya existe `informe.pdf`, el nuevo se guarda como `informe (1).pdf`, luego `informe (2).pdf`, y así sucesivamente. Los caracteres no válidos en nombres de archivo (`< > : " / \ | ? *`) se sustituyen por `_`, lo que además protege contra el path traversal.

### Archivos grandes

Los archivos de **32 MiB o más** se dividen en **partes de 16 MiB** que se descargan en paralelo y se escriben en la posición correcta de un archivo temporal `.part`. Cuando todas las partes terminan, el archivo se renombra a su nombre final. Si algo falla o cancelas, el archivo `.part` se elimina, de modo que nunca te quedas con un archivo corrupto que parezca completo.

### Carpetas enteras

`d 3` sobre una carpeta la descarga de forma **recursiva**:

1. La estructura se lee nivel a nivel, listando hasta 30 carpetas por consulta a la API y ejecutando las consultas en paralelo.
2. Se crean carpetas locales que replican la estructura de Drive.
3. Todos los archivos se descargan en paralelo (primero los más grandes).

Conviene saber que:

- Los **accesos directos** dentro de las carpetas se **omiten** (evita bucles infinitos y datos duplicados).
- Los archivos nativos de Google dentro de la carpeta se exportan usando el **primer** formato de cada tipo (ver la tabla más abajo).
- Al final se muestra un resumen: número de archivos, número de errores y el motivo del primer fallo.

### Varios archivos y carpetas a la vez

`d` acepta una selección (ver [Seleccionar varios elementos](#seleccionar-varios-elementos)), así que puedes mezclar archivos y carpetas en un solo comando:

```
> d 1-3,6
Carpeta destino [C:\Users\tu_usuario\Downloads]  (Enter = esa, ? = abrir explorador):
  Leyendo estructura... 142 archivos.
  Descargando 142/142 archivos  1.2 GB / 1.2 GB  100%  38.4 MB/s
  Terminado en 00:31 (media 38.1 MB/s)
```

- Todo va en **un único lote**: una barra de progreso y un solo grupo de hilos compartido, de modo que los archivos pequeños de carpetas distintas no esperan unos a otros.
- Las colisiones de nombres se resuelven en **toda la selección** (dos elementos llamados `informe.pdf` quedan como `informe.pdf` e `informe (1).pdf`), y nunca se sobrescriben archivos existentes.
- Cada carpeta seleccionada se descarga de forma recursiva, como se explicó antes. Los archivos nativos de Google se exportan al primer formato de su tipo.
- Si seleccionas un **acceso directo**, se sigue y se descarga su destino.
- En la pregunta del destino puedes escribir `?` para abrir el explorador de carpetas del sistema en lugar de escribir la ruta.
- Al terminar se muestra un resumen (`Descarga completada en <carpeta>: N archivos`) con el número de errores y el motivo del primer fallo, si lo hay.

---

## Subidas

Pulsa `u` dentro de una carpeta. Driv_term abre una pantalla de subida donde construyes una lista de **archivos y carpetas** locales (mezclados, todos los que quieras) y después sube toda la lista de una vez:

```
Subir a: Mi unidad / Proyectos

Seleccionado (3):
   DIR   C:\Users\tu_usuario\Fotos
   FILE  C:\Users\tu_usuario\informe.pdf
   FILE  C:\Users\tu_usuario\notas.txt

  1) Elegir archivos (varios a la vez)   2) Elegir carpeta(s) (repite para anadir mas)
  3) Escribir / pegar rutas              c) Vaciar la lista
  s) SUBIR lo elegido                    0) Cancelar

>
```

| Tecla | Acción |
| --- | --- |
| `1` | Abre el **explorador de archivos** del sistema. Selecciona uno o varios archivos a la vez. |
| `2` | Abre el **explorador de carpetas** del sistema. En la tabla de abajo se indica cuántas carpetas puedes elegir por ventana; siempre puedes repetir la opción para añadir más. |
| `3` | Escribe o pega rutas a mano (una por línea, línea vacía para terminar). Arrastrar un archivo o carpeta a la terminal pega su ruta. |
| `c` | Vacía la lista. |
| `s` | Empieza a subir todo lo que hay en la lista. |
| `0` | Cancela y vuelve al explorador sin subir nada. |

Puedes usar `1`, `2` y `3` tantas veces como quieras antes de pulsar `s`. La lista muestra lo que llevas seleccionado.

> Solo se puede subir **dentro de una carpeta** (no en resultados de búsqueda ni en "Compartidos conmigo"). Entra primero en la carpeta de destino; su ruta aparece arriba en la pantalla de subida.

### El explorador de archivos local

El explorador es una **comodidad, no un requisito**: Driv_term elige la mejor opción disponible en tu equipo.

| Sistema | Qué se usa | Varias carpetas en una ventana |
| --- | --- | --- |
| Windows | Ventana nativa de Windows (incluida con Python para Windows) | No, una carpeta por ventana (repite `2`) |
| macOS | Ventana nativa de macOS | Sí |
| Linux con escritorio | `zenity` si está instalado, si no `python3-tk` | Sí con `zenity`; una por ventana con `python3-tk` |
| Linux sin escritorio, SSH, servidores | Sin explorador: modo de rutas escritas | Escribes todas las rutas que quieras |

En Linux puedes instalar el explorador gráfico con `sudo apt install zenity` (o `sudo apt install python3-tk`).

### Sin interfaz gráfica (solo CLI)

Si no se puede abrir ningún explorador (sesión SSH, servidor sin pantalla, sin `zenity`/`tkinter`), Driv_term lo **detecta automáticamente** y pasa al modo de rutas escritas. Al pulsar `1` o `2` muestra un aviso breve y pide las rutas una por línea:

```
  No hay explorador grafico disponible (SSH o sin pantalla).
  En Linux puedes instalarlo con: sudo apt install zenity   (o python3-tk)
  Escribe o arrastra aqui cada ruta (una por linea). Linea vacia para terminar.
  > /home/tu_usuario/copia.tar
  > /home/tu_usuario/fotos
  >
```

Todo lo demás (la lista, `s` para subir, `c`, `0`) funciona exactamente igual, así que la experiencia es la misma en un entorno solo de terminal.

> El inicio de sesión sigue necesitando un navegador en el mismo equipo la primera vez (ver [Inicio de sesión](#inicio-de-sesión-flujo-oauth)). En un servidor sin pantalla, autoriza desde una máquina con navegador o usa reenvío de puertos por SSH.

### Qué pasa con la selección

- Se eliminan los duplicados y se **descarta todo lo que ya está dentro de una carpeta seleccionada**, para que nada se suba dos veces.
- Las rutas que no existen se avisan (`No existe: ...`) y se ignoran.
- Archivos y carpetas se suben en **un único lote** con una sola barra de progreso.

### Archivos individuales

- Los archivos de hasta **5 MiB** se envían en **una sola** petición multipart (metadatos y contenido juntos), lo que reduce a la mitad los viajes de red y es mucho más rápido con muchos archivos pequeños.
- Los archivos más grandes usan la **subida reanudable** de Drive: el archivo se envía en **trozos de 16 MiB**. Si se corta la conexión o el servidor devuelve un error transitorio, el programa pregunta a Drive cuántos bytes ya tiene y **continúa desde ahí**, con hasta 6 reintentos y esperas crecientes.

### Carpetas

Por cada carpeta seleccionada, Driv_term primero crea el árbol de carpetas remoto (nivel a nivel, en paralelo) y después sube todos los archivos simultáneamente (primero los más grandes). Los elementos ilegibles se omiten y se indican en el resumen final ("Omitidos (sin permiso/ilegibles)").

### Resumen del resultado

```
Subida completada: 128 archivos, 2 con error
   Fallaron: a.bin, b.iso
   Motivo del primero: [403] ...
```

---

## Mover a la papelera

Hay dos formas de borrar, y ambas mueven los elementos a la **papelera de Drive** (nada se elimina de forma permanente):

- **Un archivo:** abre su menú y elige `4) Mover a la papelera`.
- **Varios archivos y/o carpetas:** usa `t` con una selección en la pantalla principal.

```
> t 2,4-6
Mover a la papelera (se puede recuperar) (4):
   - Copias antiguas/
   - borrador.docx
   - foto1.jpg
   - foto2.jpg
Confirmar [s/N]: s
  Moviendo a la papelera 4/4
Movidos a la papelera: 4
```

Cómo funciona:

- Muestra lo que está a punto de enviar a la papelera (hasta 10 nombres; las carpetas terminan en `/`) y pide confirmación. **Cualquier respuesta distinta de `s` cancela** y no se toca nada.
- Los elementos se procesan en paralelo, con un contador en vivo.
- Mover una **carpeta** a la papelera también envía todo lo que contiene.
- Los elementos quedan en la papelera de Drive, desde donde puedes restaurarlos en Google Drive (Google conserva los elementos de la papelera unos 30 días antes de eliminarlos definitivamente).
- Si seleccionas un **acceso directo**, solo se envía a la papelera el acceso directo, **nunca** el archivo o carpeta al que apunta.
- Si algún elemento falla (por ejemplo, archivos compartidos contigo que no son tuyos), el resto se procesa igualmente y el resumen indica cuáles fallaron y por qué.
- `t all` envía a la papelera **todo** el listado actual. Revisa la lista de confirmación antes de responder `s`.

---

## Documentos, Hojas de cálculo y Presentaciones de Google

Los archivos nativos de Google no tienen un tamaño real y no se pueden descargar tal cual, así que se **exportan**. Al descargar un archivo individual eliges el formato. Al descargar una **carpeta**, se usa el primer formato de cada lista.

| Tipo de archivo de Google | Formatos de exportación disponibles (el primero es el predeterminado en carpetas) |
| --- | --- |
| Documento | `docx`, `pdf`, `txt` |
| Hoja de cálculo | `xlsx`, `csv`, `pdf` |
| Presentación | `pptx`, `pdf`, `txt` |
| Dibujo | `png`, `pdf` |
| Otros tipos de Google | `pdf` |

La extensión correcta se añade automáticamente al nombre del archivo. Ten en cuenta que Google limita el tamaño del contenido exportado (unos 10 MB por exportación a través de la API).

---

## Ajuste del rendimiento

El número de transferencias simultáneas se controla con la variable de entorno `DRIVE_WORKERS` (por defecto **8**, rango permitido **de 1 a 32**). Se aplica a descargas, subidas y al mover elementos a la papelera.

**Linux / macOS**

```bash
DRIVE_WORKERS=12 python3 Driv_term_es.py
```

**Windows PowerShell**

```powershell
$env:DRIVE_WORKERS=12; python Driv_term_es.py
```

**Windows cmd**

```bat
set DRIVE_WORKERS=12
Driv_term_es.exe
```

Recomendaciones:

- Muchos archivos pequeños: prueba con **12 a 16** hilos.
- Pocos archivos enormes: el valor por defecto ya es bueno gracias a las partes en paralelo.
- Si ves muchos reintentos por `429` / límite de peticiones, **baja** el número. Google puede limitar el exceso de paralelismo.

El programa muestra al arrancar el número de hilos activo.

---

## Dónde se guardan tus datos

Todo vive en una carpeta oculta de tu directorio personal:

| Archivo | Contenido |
| --- | --- |
| `~/.drive_terminal/config.json` | Tu `client_id` y `client_secret` de OAuth. |
| `~/.drive_terminal/tokens.json` | El token de actualización de cada cuenta con la que iniciaste sesión. |

En Linux y macOS estos archivos se crean con permisos **`600`** (solo tú puedes leerlos y escribirlos). En Windows, `~` es tu perfil de usuario (`C:\Users\<tu_usuario>`).

Los archivos descargados van donde tú elijas. Los archivos abiertos con **Ver** (los que no son de texto) van a una carpeta temporal llamada `drive_term_*` dentro del directorio temporal de tu sistema.

---

## Seguridad y privacidad

- **Sin manejo de contraseñas.** La autenticación se hace en tu navegador con Google. El programa solo recibe un código de autorización en una dirección local `127.0.0.1`.
- **PKCE y validación de `state`** protegen el flujo OAuth.
- **Tus propias credenciales.** No se envía nada a ningún servidor que no sea de Google. No hay telemetría, ni analíticas, ni backend de terceros.
- **Redirecciones seguras.** La capa HTTP solo sigue redirecciones a dominios de Google (`*.googleapis.com`, `*.googleusercontent.com`, `*.google.com`) y rechaza cualquier otra.
- **Acceso completo a Drive.** La aplicación solicita `https://www.googleapis.com/auth/drive`, que le da acceso de lectura y escritura a tu Drive. Es necesario para explorar todo, subir y enviar archivos a la papelera. Puedes revocarlo en cualquier momento en <https://myaccount.google.com/permissions>.
- **Protege tu archivo de tokens.** Cualquiera que pueda leer `tokens.json` junto con `config.json` puede acceder a tu Drive. No compartas ni subas a un repositorio la carpeta `~/.drive_terminal`.
- **Cierra sesión** con `x` para borrar el token guardado de la cuenta.
- **La papelera es reversible.** El programa nunca elimina archivos de forma permanente.

---

## Opciones de línea de comandos

| Opción | Descripción |
| --- | --- |
| `--reset-config` | Borra las credenciales OAuth y los tokens guardados (`config.json` y `tokens.json`) y termina. Úsala para cambiar a otro cliente OAuth o para borrar todas las credenciales locales. |

---

## Cómo funciona por dentro

Esta sección es para los curiosos y para quienes quieran contribuir.

**Arquitectura**

| Componente | Responsabilidad |
| --- | --- |
| `Auth` | Inicio de sesión OAuth 2.0 loopback + PKCE, renovación de tokens (segura entre hilos), almacenamiento de tokens. |
| `Http` | Capa HTTPS con una conexión persistente **por hilo y host**, reintentos automáticos con espera exponencial y jitter, renovación del token ante un 401 y gestión segura de redirecciones. |
| `Drive` | Llamadas a la API de Drive v3: listado, búsqueda, listado por lotes, descargas (individual, de carpeta y por lotes con varias selecciones), exportaciones, subidas (archivos y carpetas en un solo lote), creación de carpetas y mover a la papelera. |
| `FileJob` | Un archivo a descargar, que puede constar de varias partes. |
| `Progress` | Una barra de progreso global segura entre hilos, con velocidad suavizada y tiempo estimado. |
| `browse()` / `file_menu()` | La interfaz interactiva de terminal. |
| `pick_local()` / `choose_uploads()` | El explorador de archivos local (ventana nativa o respaldo con rutas escritas) y la pantalla de selección para subir. |
| `parse_selection()` | Interpreta selecciones como `1-4,7` o `all` para `d` y `t`. |

**Detalles de red**

- Las peticiones se reintentan (hasta 6 veces) ante errores de conexión y ante las respuestas HTTP `429`, `500`, `502`, `503`, `504`, y las respuestas `403` por límite de peticiones, con espera exponencial (máx. 20 s) más un jitter aleatorio.
- Un `401` provoca una renovación transparente del token de acceso y un reintento.
- Las respuestas se piden con `Accept-Encoding: identity` para que los rangos de bytes y los tamaños sean exactos.
- Las descargas de partes verifican que el servidor haya respetado la petición `Range`; si no lo hizo, se reinicia la conexión y se lanza un error en lugar de corromper datos en silencio.
- Las exportaciones verifican `Content-Length` cuando está presente y reintentan si la descarga está incompleta.

**Flujo de descarga**

1. Se preasigna un archivo `.part` del tamaño final.
2. Se divide en rangos de 16 MiB (para archivos de 32 MiB o más).
3. Los hilos obtienen los rangos y los escriben en el desplazamiento correcto (cada hilo tiene su propio manejador de archivo).
4. Cuando termina la última parte de un archivo, el `.part` se renombra de forma atómica (`os.replace`).
5. Si se cancela o hay un error, se borran los `.part` sobrantes.

**Flujo de subida**

- Pequeños: una petición `multipart/related` con los metadatos en JSON y el contenido del archivo.
- Grandes: se inicia una sesión reanudable y después se envían trozos de 16 MiB con `PUT` y `Content-Range`. Si falla, se consulta la sesión (`Content-Range: bytes */tamaño`) para conocer el desplazamiento confirmado y continuar desde ahí.

**Listados**

- El contenido de las carpetas usa `orderBy=folder,name`, `pageSize=1000` y sigue `nextPageToken`.
- Las descargas recursivas usan consultas como `('id1' in parents or 'id2' in parents ...)` en lotes de 30 carpetas y asignan los resultados a sus carpetas padre.
- Las unidades compartidas (Shared Drives) están soportadas mediante `supportsAllDrives` e `includeItemsFromAllDrives`.

---

## Limitaciones

- Los **accesos directos se omiten** al descargar carpetas.
- La exportación de archivos nativos de Google está sujeta al límite de tamaño de exportación de Google (alrededor de 10 MB).
- El visor muestra como máximo el **primer 1 MiB** de un archivo de texto y solo la **primera hoja** de una hoja de cálculo.
- No hay sincronización: Driv_term es una herramienta interactiva de exploración y transferencia, no un cliente de sincronización.
- No hay operaciones de renombrar, mover, copiar ni borrado permanente (solo crear carpeta, subir, descargar y mover a la papelera). Mover a la papelera es la única forma de borrar, y siempre es reversible.
- En Windows (y en Linux con `python3-tk`) la ventana del sistema selecciona **una carpeta cada vez**; repite la opción para añadir más. Los archivos sí se pueden seleccionar varios a la vez.
- Los elementos que no son tuyos (por ejemplo algunos archivos de "Compartidos conmigo") no se pueden mover a la papelera; se indican como errores mientras se procesa el resto de la selección.
- Los archivos subidos se guardan tal cual: **no** se convierten en Documentos/Hojas/Presentaciones nativos de Google.
- La búsqueda por nombre encuentra nombres que *contienen* el texto; no busca en el contenido de los archivos.
- Las transferencias no se reanudan entre reinicios del programa (la reanudación solo funciona dentro de una misma ejecución, en las subidas).
- No se verifica la integridad de los archivos con sumas de comprobación tras la transferencia.

---

## Solución de problemas

**Aviso "Google no ha verificado esta aplicación"**
Es lo esperado en clientes OAuth personales. Comprueba que tu correo esté en **Usuarios de prueba** de la pantalla de consentimiento de OAuth, luego pulsa *Avanzado* y continúa.

**`Error 403: access_denied`**
Tu cuenta de Google no está en la lista de **Usuarios de prueba** de tu pantalla de consentimiento de OAuth. Añádela y vuelve a intentarlo.

**Tengo que autorizar de nuevo cada semana**
Mientras la pantalla de consentimiento de OAuth esté en estado **Testing** (pruebas), Google caduca los tokens de actualización a los 7 días aproximadamente. Puedes volver a autorizar sin más, o publicar tu aplicación desde la configuración de la pantalla de consentimiento para evitarlo.

**"La sesion guardada caduco; hay que autorizar de nuevo."**
El token de actualización fue revocado o caducó. Autoriza de nuevo cuando se abra el navegador. Usa `--reset-config` si quieres empezar completamente desde cero.

**El navegador no se abrió / estoy en un servidor remoto (SSH)**
Abre el enlace impreso en un navegador **del mismo equipo donde se ejecuta el programa**, porque la redirección va a `127.0.0.1` de esa máquina. En un servidor sin interfaz gráfica, usa reenvío de puertos por SSH o ejecuta la aplicación en un equipo con navegador.

**`Tiempo de espera agotado.` durante la autorización**
Tienes 5 minutos para completar el inicio de sesión. Vuelve a ejecutar el programa.

**`[403] ... Drive API has not been used in project ...`**
Olvidaste habilitar la **Google Drive API** en tu proyecto de Cloud. Habilítala y espera un minuto.

**Mensajes de `[429]` / límite de peticiones o transferencias lentas**
Reduce `DRIVE_WORKERS` (prueba con 4). El programa reintenta automáticamente con espera.

**`Descarga interrumpida` / `Conexion cortada por el servidor.`**
Problema temporal de red. El programa ya reintenta varias veces; vuelve a lanzar la transferencia si sigue fallando.

**Caracteres extraños en la terminal**
Usa una terminal con soporte UTF-8 (en Windows se recomienda Windows Terminal). El programa sustituye los caracteres no imprimibles en lugar de fallar.

**La pantalla se ve mal en consolas antiguas de Windows**
Usa Windows Terminal o PowerShell en una versión reciente de Windows. El programa activa automáticamente el soporte ANSI en Windows.

**Windows SmartScreen / el antivirus marca el `.exe`**
Los ejecutables sin firmar suelen provocar avisos. Ejecuta mejor el código fuente de Python, que puedes leer y verificar.

**El explorador de archivos/carpetas no se abre**
Pasa por SSH, en servidores sin pantalla o en Linux sin `zenity` ni `python3-tk`. Driv_term te pide entonces que escribas las rutas (una por línea), así que puedes subir igualmente. Para tener el explorador gráfico en Linux, instálalo con `sudo apt install zenity` (o `python3-tk`).

**`Numero fuera de rango` / `Seleccion no valida`**
Los números después de `d` o `t` deben estar en la columna `#` del listado actual. Ejemplos válidos: `d 3`, `d 1-4`, `t 1,3,7`, `d all`. Si la selección no es válida, no se descarga ni se envía nada a la papelera.

**Algunos elementos no se pudieron mover a la papelera**
El resumen indica cuáles fallaron y el motivo del primero. La causa habitual es un `[403]` en archivos que no son tuyos (por ejemplo, compartidos contigo). El resto de la selección se procesa igualmente.

---

## Preguntas frecuentes

**¿Es un producto oficial de Google?**
No. Es una herramienta independiente de código abierto que usa la API pública de Google Drive.

**¿Tengo que pagar algo?**
No. Crear un proyecto de Google Cloud y credenciales OAuth para uso personal es gratis.

**¿Puedo usar varias cuentas de Google?**
Sí. Introduce un correo distinto al arrancar. Los tokens se guardan por cuenta. Usa `x` para cerrar sesión en una de ellas.

**¿Puedo ver las unidades compartidas?**
Los elementos de las unidades compartidas aparecen en los listados y búsquedas. Usa `c` para los archivos compartidos directamente contigo.

**¿Borra mis archivos?**
Solo si eliges explícitamente *Mover a la papelera* (desde el menú de un archivo, o con `t` para varios elementos), tras una confirmación, y aun así los archivos se pueden restaurar desde la papelera de Drive. Nunca borra de forma permanente.

**¿Puedo descargar o borrar más de un archivo o carpeta a la vez?**
Sí. Usa una selección: `d 1-3,5` para descargar, `t 2,4-6` para mover a la papelera, o `all` para todo el listado. Se pueden mezclar archivos y carpetas. Ver [Seleccionar varios elementos](#seleccionar-varios-elementos).

**¿Puedo subir varios archivos y carpetas a la vez?**
Sí. Pulsa `u`, elige archivos y carpetas con el explorador tantas veces como quieras y pulsa `s` para subirlos todos en un solo lote.

**¿Funciona sin interfaz gráfica (SSH, servidores, consola de Linux)?**
Sí. El explorador es opcional: si no se puede abrir ninguna ventana, Driv_term te pide que escribas o pegues las rutas. Todo lo demás es terminal pura. Solo el primer inicio de sesión necesita un navegador en el mismo equipo.

**¿Dónde están los archivos temporales?**
Los archivos que no son de texto abiertos con *Ver* se guardan en una carpeta `drive_term_*` del directorio temporal de tu sistema.

**¿Cómo elimino todo por completo?**
Ejecuta con `--reset-config`, borra la carpeta `~/.drive_terminal` y revoca el acceso en <https://myaccount.google.com/permissions>.

---

## Contribuir

Los issues y pull requests son bienvenidos. Si encuentras un error, incluye tu sistema operativo, la versión de Python (o qué `.exe` usaste), el mensaje de error exacto y los pasos para reproducirlo. **Nunca** pegues tu `client_secret`, tokens o nombres de archivos privados en issues públicos.

## Licencia

Todavía no se ha especificado ninguna licencia.

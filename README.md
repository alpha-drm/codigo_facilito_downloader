<!-- markdownlint-disable MD033 MD036 MD041 MD045 MD046 -->
<div align="center">
    <img width="100" src="https://i.imgur.com/dca7pcI.png" alt="Coco Logo">
</div>
<div align="center">
    <img width="250" src="https://i.imgur.com/tZhUf6Y.png" alt="Coco Logo">
</div>
<div align="center">

<h1 style="border-bottom: none">
    <b><a href="https://github.com/ivansaul/codigo_facilito_downloader">Codigo Facilito Downloader</a></b>
</h1>

Descarga automatizada de los cursos de **_`Codigo Facilito`_**<br />
con un script creado con **_`Python`_** y **_`Playwright`_**.

![GitHub repo size](https://img.shields.io/github/repo-size/ivansaul/codigo_facilito_downloader)
![GitHub stars](https://img.shields.io/github/stars/ivansaul/codigo_facilito_downloader)
![GitHub forks](https://img.shields.io/github/forks/ivansaul/codigo_facilito_downloader)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://discord.gg/tDvybtJ7y9">
    <img alt="Discord Server" height="50" src="https://cdn.jsdelivr.net/npm/@intergrav/devins-badges@3/assets/cozy/social/discord-plural_vector.svg">
</a>

</div>

---

<div align="center">
    
![demo](https://github.com/user-attachments/assets/21255d4e-24b4-407a-bcc6-252d7a0b2d56)

</div>

## Características Principales

- Interfaz de Terminal Moderna: Visualización en tiempo real con barras de progreso, tablas y paneles informativos.
- Descarga Estructurada: Organización automática del contenido por módulos y lecciones.
- Caché Inteligente: Reanudación de descargas mediante almacenamiento de la estructura en .json.
- Ejecución Concurrente: Descargas más rápidas usando múltiples hilos.
- Calidad de Video Configurable: Soporte para 1080p, 720p, 480p y 360p.
- Formatos Estándar: Exportación en .mp4 y .mhtml para uso offline.
- Autenticación Flexible: Inicio de sesión por credenciales o cookies.

## Dependencias del sistema (requeridas)

Este proyecto usa herramientas externas para descargar y procesar los videos.
Asegúrate de tener **`yt-dlp`** y **`ffmpeg`** instalados y disponibles en tu `PATH`.

### yt-dlp Instalación

#### Windows

Puedes descargar la versión de `yt-dlp` para Windows desde [aquí](https://github.com/yt-dlp/yt-dlp/releases). o algún gestor de paquetes como [`Scoop`][scoop] o [`Chocolatey`][chocolatey].

```console
scoop install yt-dlp
```

```console
choco install yt-dlp
```

#### Linux / macOS (pipx / pip)

```console
pipx install yt-dlp
# o, si no usas pipx:
pip install -U yt-dlp
```

Mientras el comando `yt-dlp` esté disponible en tu `PATH`, el downloader podrá usarlo sin problemas.

### FFmpeg Instalación

#### Windows [[Tutorial]][ffmpeg-youtube]

Puedes descargar la versión de `ffmpeg` para Windows desde [aquí][ffmpeg]. o algún gestor de paquetes como [`Scoop`][scoop] o [`Chocolatey`][chocolatey].

```console
scoop install ffmpeg
```

#### Ubuntu / Debian

```console
sudo apt install ffmpeg -y
```

#### Arch Linux

```console
sudo pacman -S ffmpeg
```

## Instalación | Actualización

### Con **`poetry`** **(recomendado)**

> [!TIP]
> La forma recomendada y moderna de instalar Poetry es usando **`pipx`**. Si no lo tienes, instálalo de acuerdo a tu sistema [aquí](https://pipx.pypa.io/stable/installation/)

<details>

<summary>Instrucciones</summary>

### Instalación

1. Instala `poetry` en tu sistema:

   ```console
   pipx install poetry
   ```

2. Clona el repositorio:

   ```console
   git clone https://github.com/ivansaul/codigo_facilito_downloader.git
   ```

3. Entra al directorio del repositorio:

   ```console
   cd codigo_facilito_downloader
   ```

4. Instala el paquete:

   ```console
   poetry install
   ```

5. Instala las dependencias de `playwright`:

   ```console
   poetry run playwright install chromium
   ```

### Actualización

1. Entra al directorio del repositorio:

   ```console
   cd codigo_facilito_downloader
   ```

2. Actualiza el repositorio:

   ```console
   git reset --hard HEAD
   git pull
   ```

3. Actualiza el paquete:

   ```console
   poetry install
   ```

4. Actualiza las dependencias de `playwright`:

   ```console
   poetry run playwright install chromium
   ```

</details>

### Con **`pip`**

<details>

<summary>Instrucciones</summary>

## Instalación y actualización

1. Instala el paquete:

   ```console
   pip install -U git+https://github.com/ivansaul/codigo_facilito_downloader.git
   ```

2. Instala las dependencias de `playwright`:

   ```console
   playwright install chromium
   ```

</details>

<br>

## Guía de uso

El `CLI` proporciona los siguientes comandos:

### Login

Puedes iniciar sesión de dos formas:

#### Email | Google

```console
facilito login
```

#### Cookies

Este método solo se recomienda si tienes problemas de autenticación mediante el método anterior.

```console
facilito set-cookies path/to/cookies.json
```

<details>

<summary>Tips & Tricks</summary>

## Exportar las cookies

1. Inicia sesión en tu navegador de tu preferencia.
2. Instala alguna extensión como **_`GetCookies`_** o **_`Cookie-Editor`_**
3. Recarga la página.
4. Exporta las cookies en formato `json` desde la extensión.

</details>

### Logout

Elimina la sesión almacenada localmente de Código Facilito.

```console
facilito logout
```

### Descargar

> [!IMPORTANT]
> Asegúrate de estar logueado antes de intentar descargar los cursos.

Descarga un **curso** o **bootcamp** completo.

```console
facilito download <url> [OPCIONES]
```

Opciones:

- `--quality`, `-q`: Especifica la calidad del video (por defecto: `1080`). Opciones disponibles: `[best|1080|720|480|360|worst]`.
- `--override`, `-w`: Sobrescribe el archivo existente si existe (por defecto: `False`).
- `--threads`, `-t`: Número de hilos a utilizar (por defecto: `10`).

> [!TIP]
> Para visualizar todas las opciones disponibles, ejecuta `facilito download --help`.

Ejemplos:

**Descargar un curso:**

```console
facilito download https://codigofacilito.com/cursos/docker
```

**Descargar un bootcamp:**

```console
facilito download https://codigofacilito.com/programas/ingles-conversacional
```

**Descargar con opciones personalizadas:**

```console
facilito download URL -q 720 -t 5
```

<br>

> [!TIP]
> Si por algún motivo se cancela la descarga, vuelve a ejecutar `facilito download <url>` para retomar la descarga.

> [!NOTE]
> Para **cursos** y **bootcamps**, el downloader guarda la estructura de los mismos en un archivo `.json`. En ejecuciones posteriores,
> si detecta un **cache hit**, puede saltarse el scraping web y continuar usando el JSON local.

## Estructura de salida

Dependiendo del tipo de recurso, la estructura de carpetas generada será similar a:

### Cursos

```text
Facilito/
└── Nombre del Curso/
    ├── Nombre del Curso.json
    ├── source.mhtml
    ├── 01 - Módulo 1/
    │   ├── 01 - Introducción.mhtml
    │   ├── 02 - Bienvenida.mp4
    │   └── ...
    ├── 02 - Módulo 2/
    │   └── ...
    └── ...
```

### Bootcamps

```text
Facilito/
└── Nombre del Bootcamp/
    ├── Nombre del Bootcamp.json
    ├── source.mhtml
    ├── 01 - Módulo 1/
    │   ├── 1.1 Introducción.mp4
    │   ├── 1.2 Presentación.mhtml
    │   └── ...
    ├── 02 - Módulo 2/
    │   └── ...
    └── ...
```

Los nombres de carpetas y archivos se limpian automáticamente para evitar caracteres inválidos en el sistema de archivos.

## TODO

¡Contribuciones son bienvenidas!

- [ ] Improve documentation
- [x] Implement rich progress bar for downloads
- [ ] Improve error handling
- [ ] Write tests

## Cómo contribuir

¡Todas las contribuciones son bienvenidas!. Antes de enviar cambios, revisa la guía [CONTRIBUTING.md](./CONTRIBUTING.md) para conocer las pautas del proyecto.

## Contribuidores

<a href="https://github.com/ivansaul/codigo_facilito_downloader/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ivansaul/codigo_facilito_downloader" />
</a>

## License

Distribuido bajo la Licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más información.

## **Aviso de Uso**

Este proyecto se realiza con fines exclusivamente educativos y de aprendizaje. El código proporcionado se ofrece "tal cual" sin ninguna garantía de su funcionamiento o idoneidad para ningún propósito específico.

No me hago responsable por cualquier mal uso, daño o consecuencia que pueda surgir del uso de este proyecto. Es responsabilidad del usuario utilizarlo de manera adecuada y dentro de los límites legales y éticos.

## Descubre Más

Aquí tienes una lista de algunos de mis otros repositorios. ¡Échales un vistazo!

[![Bookmark Style Card](https://svg.bookmark.style/api?url=https://github.com/ivansaul/codigo_facilito_downloader&mode=light&style=horizontal)](https://github.com/ivansaul/codigo_facilito_downloader)
[![Bookmark Style Card](https://svg.bookmark.style/api?url=https://github.com/ivansaul/platzi-downloader&mode=light&style=horizontal)](https://github.com/ivansaul/platzi-downloader)
[![Bookmark Style Card](https://svg.bookmark.style/api?url=https://github.com/ivansaul/terabox_downloader&mode=light&style=horizontal)](https://github.com/ivansaul/terabox_downloader)
[![Bookmark Style Card](https://svg.bookmark.style/api?url=https://github.com/ivansaul/personal-portfolio&mode=light&style=horizontal)](https://github.com/ivansaul/personal-portfolio)
[![Bookmark Style Card](https://svg.bookmark.style/api?url=https://github.com/ivansaul/flutter_todo_app&mode=light&style=horizontal)](https://github.com/ivansaul/flutter_todo_app)
[![Bookmark Style Card](https://svg.bookmark.style/api?url=https://github.com/ivansaul/Flutter-UI-Kit&mode=light&style=horizontal)](https://github.com/ivansaul/Flutter-UI-Kit)

[scoop]: https://scoop.sh/
[ffmpeg]: https://ffmpeg.org
[chocolatey]: https://community.chocolatey.org
[ffmpeg-youtube]: https://youtu.be/JR36oH35Fgg?si=Gerco7SP8WlZVaKM
[previous-version]: https://github.com/ivansaul/codigo_facilito_downloader/tree/e39524cf4a925fb036c903b5d82306f9e2088ca6
[cookies-extension]: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

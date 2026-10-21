# OpenAnime

**OpenAnime** es una aplicación de escritorio desarrollada en Python y PySide6 para explorar y reproducir anime desde una interfaz propia.

## 📺 Canal de YouTube

**[Kyuutb Tech ☑️](https://www.youtube.com/@kyuutbtech)**

Visita el canal para ver contenido relacionado con tecnología y proyectos.

## ✨ Características

- 🎬 **Reproductor integrado:** carga servidores compatibles dentro de OpenAnime mediante `QWebEngineView`, sin abrir un navegador externo.
- 🌐 **Reproducción en línea:** permite reproducir desde servidores compatibles; la disponibilidad depende de cada fuente.
- 📥 **Descarga de capítulos:** permite descargar episodios para reproducirlos localmente.
- ▶️ **Alternativa cuando falla la reproducción:** si un servidor no reproduce un capítulo, puedes descargarlo y reproducir el archivo descargado desde OpenAnime, siempre que la fuente permita obtenerlo.
- 📦 **Ejecutable para Windows:** compilación en un único archivo `.exe`.
- 🎨 **Icono personalizado:** admite el icono `OpenAnime.ico` durante la compilación.
- 🔄 **Versiones y publicaciones:** compilación y publicación de versiones mediante GitHub Actions y GitHub Releases.
- 🔐 **Verificación de integridad:** generación de un hash SHA-256 para el ejecutable publicado.
- 🧩 **Integración con `yt-dlp`:** para las funciones compatibles del programa.

## 📥 Descarga

Descarga la versión publicada desde la sección **Releases**:

**[Descargar OpenAnime](https://github.com/JGRyuuTB/OpenAnime/releases)**

1. Abre la página de Releases.
2. Descarga `OpenAnime.exe` de la versión que quieras utilizar.
3. Ejecuta el archivo en Windows.

La versión compilada está pensada para ejecutarse sin iniciar manualmente el código Python.

## ⚙️ Requisitos

### Para usuarios

- Windows compatible con la versión publicada.
- Conexión a Internet para explorar contenido, reproducir en línea o descargar capítulos.

### Para desarrolladores

- Python.
- Las dependencias indicadas en `requirements.txt`.
- Git, si deseas clonar el repositorio.

## 💻 Ejecutar desde el código fuente

Clona el repositorio:

```bash
git clone https://github.com/JGRyuuTB/OpenAnime.git
cd OpenAnime
```

Instala las dependencias:

```bash
python -m pip install -r requirements.txt
```

Inicia la aplicación:

```bash
python main.py
```

## 🏗️ Compilar para Windows

Instala las dependencias:

```bash
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

Coloca `OpenAnime.ico` en la raíz del proyecto y ejecuta:

```bash
pyinstaller --noconfirm --clean --onefile --windowed --icon=OpenAnime.ico --name OpenAnime --collect-submodules yt_dlp main.py
```

El ejecutable se generará en:

```text
dist/OpenAnime.exe
```

### Compilación automatizada

El flujo de GitHub Actions puede:

- Establecer la versión de la aplicación.
- Compilar OpenAnime para Windows.
- Incluir el icono personalizado.
- Calcular el hash SHA-256.
- Publicar el ejecutable y su hash en GitHub Releases.

## ▶️ Reproducción y descarga de capítulos

OpenAnime ofrece reproducción en línea mediante servidores compatibles y funciones de descarga de capítulos.

Si un servidor no reproduce un episodio, una alternativa es **descargar el capítulo y reproducir el archivo localmente** desde OpenAnime. Esta alternativa depende de que la fuente permita descargar el contenido y de que el archivo resultante sea compatible con el reproductor.

La descarga local puede evitar los problemas de reproducción en línea causados por un servidor temporalmente caído o por ciertas limitaciones del reproductor web. No garantiza que todos los episodios estén disponibles para descargar.

## 🔄 Actualizaciones

Las versiones que incluyen el mecanismo de actualización pueden consultar las publicaciones de GitHub Releases para detectar nuevas versiones. El funcionamiento depende de la versión instalada y de la configuración del proyecto.

Se recomienda descargar los ejecutables desde una publicación de confianza y comprobar el hash SHA-256 cuando esté disponible.

## 🐛 Solución de problemas

### El vídeo no se reproduce en línea

- Comprueba tu conexión a Internet.
- Prueba otro servidor compatible.
- Si la fuente lo permite, descarga el capítulo y reprodúcelo localmente.
- El servidor puede estar fuera de servicio o imponer restricciones que OpenAnime no puede resolver.

### La descarga no funciona

- Comprueba la conexión a Internet.
- Verifica que el servidor o la fuente todavía estén disponibles.
- No todos los servidores permiten descargar episodios.

### La aplicación no inicia

- Descarga nuevamente el ejecutable desde Releases.
- Comprueba si Windows o el antivirus han bloqueado el archivo.
- Si ejecutas desde el código fuente, verifica que las dependencias estén instaladas.

### El icono no cambia

Comprueba que `OpenAnime.ico` esté presente durante la compilación y que estés ejecutando el `.exe` recién generado. Windows puede conservar iconos antiguos temporalmente en caché.

## 📝 Reportar errores

Al informar de un problema, incluye:

- La versión de OpenAnime.
- La versión de Windows.
- Los pasos para reproducir el error.
- El servidor utilizado, si corresponde.
- El mensaje de error o una captura de pantalla.

No compartas contraseñas, tokens ni otros datos privados.

## ⚖️ Aviso legal

La disponibilidad de los contenidos y las opciones de reproducción o descarga dependen de las fuentes utilizadas. El usuario es responsable de respetar las leyes aplicables, los derechos de autor y las condiciones de los servicios de terceros.

## 🙏 Créditos

- **Python** — lenguaje de programación.
- **PySide6 / Qt** — interfaz gráfica y vista web integrada.
- **PyInstaller** — generación del ejecutable.
- **yt-dlp** — funciones compatibles de extracción y gestión de medios.
- Autores y mantenedores de las bibliotecas utilizadas.

---

**OpenAnime** · Explora, descarga y reproduce capítulos desde una aplicación de escritorio.

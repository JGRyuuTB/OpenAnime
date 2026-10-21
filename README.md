# OpenAnime

Aplicación de código abierto y gratuita para ver y descargar anime. **Nadie tiene derecho a cobrarte por ella.**

## Ejecutar
```
pip install -r requirements.txt
python main.py
```

## Compilar (.exe)
- Local: ejecuta `build.bat` (resultado en `dist/OpenAnime/`).
- Automático: sube un tag y GitHub Actions publica la release.

## Publicar una actualización
1. Cambia `VERSION` en `main.py` (por ejemplo `1.0.1`).
2. `git add . && git commit -m "v1.0.1" && git tag v1.0.1 && git push && git push --tags`
3. GitHub Actions compila y crea la release con `OpenAnime-Windows.zip`.
4. La app avisa a los usuarios cuando hay una versión nueva.

## Licencia
GNU GPL v3.0 o posterior. Consulta el archivo `LICENSE`.
Cualquier versión modificada o redistribuida debe seguir siendo de código abierto bajo la misma licencia.

Creado por Kyuu TB Tech — https://youtube.com/@kyuutbtech

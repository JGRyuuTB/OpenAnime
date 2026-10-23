; ============================================================
; SETUP STUDIO - PLANTILLA BASE INNO SETUP (MODO OSCURO)
; Plantilla corregida para Inno Setup 6.6 o posterior.
; Edita la sección CONFIGURACIÓN y compila con Inno Setup.
; ============================================================

#define MyAppName "OpenAnime"
#define MyAppVersion "1.2.6"
#define MyAppPublisher "RyUU"
#define MyAppExeName "OpenAnime.exe"

; ---- CONFIGURACIÓN: EDITA ESTA RUTA ----
; Debe ser una carpeta que EXISTE y que contiene OpenAnime.exe
; junto con los archivos y carpetas que necesita la aplicación.
#define MyAppSourceDir "C:\Users\lozad\Downloads\Output"

; Icono opcional del instalador. Descomenta si tienes un .ico.
; #define MySetupIconFile "C:\Ruta\A\mi-icono.ico"

; Clave opcional de compilación. No es una clave de licencia.
; #define MyOutputPassword "cambia-esta-clave"

[Setup]
; Conserva este AppId para actualizar/desinstalar esta misma aplicación.
AppId={{A7C29F2B-0B0D-4D7C-9D15-8E2C6B95A421}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Instalación por usuario, sin solicitar permisos de administrador.
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

; Salida del compilador
OutputDir=Output
OutputBaseFilename={#MyAppName}-Setup
Compression=lzma2
SolidCompression=yes

; Apariencia oscura moderna (Inno Setup 6.6+)
WizardStyle=modern dark
WizardSizePercent=100
SetupLogging=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; Descomenta si definiste un icono personalizado:
; SetupIconFile={#MySetupIconFile}

; Descomenta ambas líneas si definiste una contraseña:
; Password={#MyOutputPassword}
; Encryption=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
; Incluye todos los archivos y subcarpetas de la carpeta indicada arriba.
; IMPORTANTE: esta carpeta debe existir y contener OpenAnime.exe.
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: postinstall nowait skipifsilent

; ============================================================
; CÓMO USAR
; 1. Verifica que MyAppSourceDir apunta a una carpeta existente.
; 2. Esa carpeta debe contener OpenAnime.exe y sus recursos.
; 3. Si tu EXE está en otra carpeta, cambia MyAppSourceDir.
; 4. Abre este archivo .iss en Inno Setup y pulsa Compile.
; 5. El instalador se creará en la subcarpeta Output junto al .iss.
;
; Nota: no apuntes MyAppSourceDir a la carpeta de salida del
; instalador salvo que ahí estén realmente los archivos de la app.
; ============================================================

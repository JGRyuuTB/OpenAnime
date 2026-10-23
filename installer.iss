; ============================================================
; OpenAnime - instalador Inno Setup en modo oscuro
; Este archivo se compila automáticamente desde GitHub Actions.
; No usa rutas locales del ordenador del desarrollador.
; ============================================================

#define MyAppName "OpenAnime"
#ifndef MyAppVersion
  #define MyAppVersion "1.2.6"
#endif
#define MyAppPublisher "RyUU"
#define MyAppExeName "OpenAnime.exe"

[Setup]
AppId={{A7C29F2B-0B0D-4D7C-9D15-8E2C6B95A421}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=OpenAnime-Setup
SetupIconFile=OpenAnime.ico
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern dark
WizardSizePercent=100
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
; El workflow compila OpenAnime.exe con PyInstaller antes de ejecutar ISCC.
; No cambies esta ruta por una ruta local como C:\Users\...
Source: "dist\OpenAnime.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: postinstall nowait skipifsilent

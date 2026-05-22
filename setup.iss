
[Setup]
AppName=Secretary Assistant
AppVersion=4.0.0
AppPublisher=Emil
DefaultDirName={autopf}\Secretary Assistant
DefaultGroupName=Secretary Assistant
UninstallDisplayIcon={app}\main.exe
OutputDir=.\installer_output
OutputBaseFilename=Secretary Assistant Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=icon.ico
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
; Копируем всё из папки Nuitka в папку установки
Source: "build\main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
; Ярлык в меню Пуск
Name: "{group}\Secretary Assistant"; Filename: "{app}\main.exe"; IconFilename: "{app}\icon.ico"
; Ярлык на рабочем столе
Name: "{userdesktop}\Secretary Assistant"; Filename: "{app}\main.exe"; IconFilename: "{app}\icon.ico"

[Run]
; Запуск программы после установки
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,Secretary Assistant}"; Flags: nowait postinstall skipifsilent
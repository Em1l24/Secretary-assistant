[Setup]
AppName=Secretary assistant
AppVersion=3.0
DefaultDirName={autopf}\Secretary assistant
DefaultGroupName=Secretary assistant
OutputDir=InstallerOutput
OutputBaseFilename=Secretary assistant
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\Secretary assistant.exe

[Files]
Source: "dist\Secretary assistant.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\Secretary assistant"; Filename: "{app}\Secretary assistant.exe"
Name: "{group}\Secretary assistant"; Filename: "{app}\Secretary assistant.exe"

[Run]
Filename: "{app}\Secretary assistant.exe"; Description: "Запустить приложение"; Flags: nowait postinstall skipifsilent
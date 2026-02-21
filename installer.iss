[Setup]
AppName=Taylan
AppVersion=1.0.0
AppPublisher=Taylan
DefaultDirName={commonpf}\Taylan
DefaultGroupName=Taylan
DisableProgramGroupPage=yes
OutputBaseFilename=setup_taylan
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
WizardResizable=yes
SetupIconFile=C:\Users\aonur\Desktop\my_lang\logo.ico
UninstallDisplayIcon={app}\taylan_editor.exe
CloseApplications=yes
RestartApplications=no

[Files]
Source: "C:\Users\aonur\Desktop\my_lang\dist\taylan_editor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\aonur\Desktop\my_lang\dist\taylan.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\aonur\Desktop\my_lang\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{commondesktop}\Taylan Editor"; Filename: "{app}\taylan_editor.exe"

[Registry]
Root: HKCR; Subkey: ".taylan"; ValueType: string; ValueName: ""; ValueData: "TaylanFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "TaylanFile"; ValueType: string; ValueName: ""; ValueData: "Taylan Source File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "TaylanFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\taylan_editor.exe"" ""%1"""; Flags: uninsdeletekey

[Run]
Filename: "{app}\taylan_editor.exe"; Description: "Taylan Editor aç"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\taylan_packages"

[Dirs]
Name: "{app}\taylan_packages"

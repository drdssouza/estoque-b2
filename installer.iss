; ============================================================
;  Controle B2 — Script de instalacao (Inno Setup 6)
;  Nao requer permissao de administrador.
;  Instala em %LocalAppData%\Controle-B2\
;  A pasta "data\" e preservada na desinstalacao.
; ============================================================

[Setup]
AppName=Controle B2
AppVersion=1.2.0
AppVerName=Controle B2 v1.2.0
AppPublisher=Eduardo Souza
AppPublisherURL=https://github.com/drdssouza/estoque-b2
AppSupportURL=https://github.com/drdssouza/estoque-b2
AppUpdatesURL=https://github.com/drdssouza/estoque-b2/releases

; Instala sem precisar de admin (cada usuario instala na propria conta)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

DefaultDirName={localappdata}\Controle-B2
DefaultGroupName=Controle B2
DisableProgramGroupPage=yes

; Sobrescreve instalacao anterior sem perguntar
AllowNoIcons=yes
; Nao apaga arquivos que nao eram da instalacao anterior (protege a pasta data)
DontMergeDuplicateFiles=no

OutputDir=dist_installer
OutputBaseFilename=Controle-B2-Setup-1.2.0
SetupIconFile=icon.ico

Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Requer Windows 10 ou superior (64 bits)
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
; Mensagens personalizadas em portugues
WelcomeLabel2=Este assistente instalara o [name/ver] no seu computador.%n%nRecomendamos que feche todos os outros programas antes de continuar.

[Tasks]
Name: "desktopicon"; Description: "Criar icone na Area de Trabalho"; GroupDescription: "Icones adicionais:"; Flags: unchecked

[Files]
; Copia todos os arquivos gerados pelo PyInstaller (pasta dist\estoque-b2\)
Source: "dist\estoque-b2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\Controle B2"; Filename: "{app}\estoque-b2.exe"; WorkingDir: "{app}"

; Atalho na Area de Trabalho (opcional, marcada na tela de tarefas)
Name: "{userdesktop}\Controle B2"; Filename: "{app}\estoque-b2.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Oferecer abrir o programa ao final da instalacao
Filename: "{app}\estoque-b2.exe"; Description: "Abrir Controle B2 agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; INTENCIONAL: a pasta "data\" NAO esta aqui — os dados do usuario sao preservados.
; Apenas remove a pasta de instalacao (arquivos rastreados pelo Inno Setup).
Type: filesandordirs; Name: "{app}\_internal"

[Code]
// Avisa o usuario que os dados serao preservados na desinstalacao
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: string;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataPath := ExpandConstant('{app}\data');
    if DirExists(DataPath) then
      MsgBox(
        'Seus dados (comandas, produtos, etc.) foram preservados em:' + #13#10 +
        DataPath + #13#10#13#10 +
        'Voce pode fazer backup dessa pasta antes de desinstalar.',
        mbInformation, MB_OK
      );
  end;
end;

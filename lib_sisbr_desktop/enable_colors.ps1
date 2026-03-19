# Script para habilitar cores ANSI no PowerShell
Write-Host "Habilitando cores ANSI no PowerShell..." -ForegroundColor Green

# Habilita cores ANSI
$Host.UI.RawUI.ForegroundColor = "White"
$Host.UI.RawUI.BackgroundColor = "Black"

# Configura o console para suportar cores ANSI
if ($Host.Name -eq "ConsoleHost") {
    Import-Module PSReadLine
    Set-PSReadLineOption -Colors @{
        Command            = 'Magenta'
        Parameter          = 'Green'
        Operator           = 'Yellow'
        Variable           = 'Cyan'
        String             = 'Red'
        Number             = 'Blue'
        Member             = 'Gray'
        Type               = 'DarkYellow'
        Default            = 'White'
    }
}

Write-Host "Cores ANSI habilitadas!" -ForegroundColor Green
Write-Host "Agora execute o script Python novamente." -ForegroundColor Yellow

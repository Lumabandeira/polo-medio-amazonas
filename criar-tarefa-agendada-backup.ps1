$python  = 'C:\Users\Defensoria\AppData\Local\Microsoft\WindowsApps\python.exe'
$script  = 'C:\Users\Defensoria\Desktop\5° versão\polo-medio-amazonas\backup-firestore.py'
$dir     = 'C:\Users\Defensoria\Desktop\5° versão\polo-medio-amazonas'
$tarefa  = 'BackupFirestorePoloMedioAmazonas'

$action   = New-ScheduledTaskAction -Execute $python -Argument "`"$script`"" -WorkingDirectory $dir
$trigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '07:00AM'
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName   $tarefa `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -Description 'Faz backup do Firestore (polo-medio-as) para backups/firestore/' `
    -Force

Write-Host "Tarefa '$tarefa' criada com sucesso. Executa semanalmente aos domingos às 07:00."

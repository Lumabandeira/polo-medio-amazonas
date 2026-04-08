$python  = 'C:\Users\lucia\AppData\Local\Python\bin\python.exe'
$script  = 'C:\Users\lucia\Desktop\5° versão\verificar-diario-oficial.py'
$dir     = 'C:\Users\lucia\Desktop\5° versão'
$tarefa  = 'VerificarDiarioOficialDPE'

$action   = New-ScheduledTaskAction -Execute $python -Argument "`"$script`"" -WorkingDirectory $dir
$trigger  = New-ScheduledTaskTrigger -Daily -At '06:00AM'
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName   $tarefa `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -Description 'Verifica Diário Oficial DPE/AM e atualiza site Polo Médio Amazonas' `
    -Force

Write-Host "Tarefa '$tarefa' criada com sucesso. Executa diariamente às 06:00."

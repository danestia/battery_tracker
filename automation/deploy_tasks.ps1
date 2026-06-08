# Define absolute paths to ensure the SYSTEM account never gets lost
$TargetDir  = "C:\battery-tracker"
$AutomationDir = "C:\battery-tracker\automation"
$Controller = "C:\battery-tracker\automation\controller.ps1"

# Define the SYSTEM execution principal
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Clean out old tasks cleanly before rebuilding
foreach ($name in @("BatteryTracker_Start", "BatteryTracker_Stop", "BatteryTracker_Delivery")) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
}

# --- 1. START TASK ---
$startAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$Controller`" -Mode Start" `
    -WorkingDirectory $TargetDir

$startTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 09:00

$startSettings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 9)

Register-ScheduledTask `
    -TaskName "BatteryTracker_Start" `
    -Action $startAction `
    -Trigger $startTrigger `
    -Settings $startSettings `
    -Principal $principal `
    -Force

# --- 2. STOP TASK ---
$stopAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$Controller`" -Mode Stop" `
    -WorkingDirectory $TargetDir

$stopTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 18:00

$stopSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName "BatteryTracker_Stop" `
    -Action $stopAction `
    -Trigger $stopTrigger `
    -Settings $stopSettings `
    -Principal $principal `
    -Force

# --- 3. DELIVERY TASK ---
$deliveryAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$Controller`" -Mode Deliver" `
    -WorkingDirectory $TargetDir

$deliveryTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At 17:50

$deliverySettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName "BatteryTracker_Delivery" `
    -Action $deliveryAction `
    -Trigger $deliveryTrigger `
    -Settings $deliverySettings `
    -Principal $principal `
    -Force

Write-Host "✅ All 3 BatteryTracker tasks registered successfully with explicit working directories." -ForegroundColor Green
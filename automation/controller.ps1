param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Start", "Stop", "Deliver", IgnoreCase = $true)]
    [string]$Mode
)

if (-not $Mode) { $Mode = $args[0] }

# Environment Setup (100% Dynamic & Portable)
$ScriptDir  = $PSScriptRoot
$RootDir    = Split-Path -Parent $ScriptDir
$PythonExe  = Join-Path $RootDir ".venv\Scripts\python.exe"
$TrackerPy  = Join-Path $RootDir "run_tracker.py"
$DeliveryPy = Join-Path $RootDir "delivery.py"
$LogFile    = Join-Path $ScriptDir "controller.log"
$LockFile   = Join-Path $RootDir "data\tracker.lock"

function Write-Log($msg) {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "$timestamp [$Mode] $msg" | Out-File $LogFile -Append
}

function Get-TrackerProcess {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*run_tracker.py*" }
}

# Ensure an action mode was passed
if ($Mode -notin @("Start", "Stop", "Deliver")) {
    Write-Log "Error: Invalid or missing Mode parameter ($Mode)."
    exit 1
}

Write-Log "Controller invoked."

# =============================================================================
# CONTROLLER MODE SWITCH
# =============================================================================
switch($Mode.ToLower()) {
    "start" {
        $now = Get-Date
        $currentHour = $now.Hour

        # Strict Time Gate: Do not start if it's outside 08:00 - 18:00
        if ($currentHour -lt 8 -or $currentHour -ge 18) {
            Write-Log "Start aborted: Outside operational hours (08:00 - 18:00)."
            exit 0
        }

        # Weekend Gate
        if ($now.DayOfWeek -in @("Saturday", "Sunday")) {
            Write-Log "Start aborted: Weekend detected."
            exit 0
        }

        # Check process states
        $running = Get-TrackerProcess
        if ($running) {
            Write-Log "Tracker already running (PID: $($running.ProcessId))."
            $running.ProcessId | Out-File $LockFile -Force
            exit 0
        }

        # Clean up stale locks
        if (Test-Path $LockFile) {
            Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
        }

        Write-Log "Launching run_tracker.py..."
        $proc = Start-Process $PythonExe `
            -ArgumentList "`"$TrackerPy`"" `
            -WorkingDirectory $RootDir `
            -WindowStyle Hidden `
            -PassThru

        Start-Sleep -Milliseconds 500
        $proc.Id | Out-File $LockFile -Force
        Write-Log "Tracker started successfully (PID: $($proc.Id))."    
    }

    "stop" {
        
        $running = Get-TrackerProcess

        if (-not $running) {
            Write-Log "Stop requested: No tracker process found."
            Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
            exit 0
        }

        foreach ($proc in $running) {
            Write-Log "Terminating process PID $($proc.ProcessId)..."
            Stop-Process -Id $proc.ProcessId -Force
        }

        Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
        Write-Log "Tracker stopped completely."
    }

    "deliver" {
        $now = Get-Date
        if ($now.Hour -ge 18) {
            Write-Log "Delivery skipped: Past 18:00 operational boundary."
            exit 0
        }

        Write-Log "Executing delivery payload routine..."
        Start-Process $PythonExe `
            -ArgumentList "`"$DeliveryPy`"" `
            -WorkingDirectory $RootDir `
            -Wait `
            -NoNewWindow

        Write-Log "Delivery routine finished execution loop."
    }
}

exit 0
#This script get a list of servers from a csv file and then uninstalls the Marimba service is installed
#Sham Ramchandani - March 2018

# Get the List of Servers that have Marimba Install on them
$Marimbaservers = Import-Csv C:\temp\marimba.csv
$servers = $Marimbaservers.MachineName

#Setup log file
$logTime = get-date -format yyyyMMdd-HHmmss
$logName = ".\Marimba_Uninstall-$logTime.txt"
out-file -filepath $logName -inputobject "$logTime Log file for Uninstall_Marimba.ps1 script"

function logFile([string]$logText) {
    # Function for writing text to screen and appending log file. Log file must be pre-created
      $logTime = get-date -format yyyyMMdd-HHmmss
      out-file -filepath $logName -append -inputobject "$logTime $logText"
      Write-Host $logText
    }

function pingCheck([string]$server) {
    if (Test-Connection -ComputerName $server -Count 2 -ErrorAction SilentlyContinue) {         
        return $true }
      else {
        return $false }

}

function serviceStatus([string]$service, [string]$server) {
    # Function to return status of specified service on a computer
      $serviceStatus = (get-service $service -ComputerName $server -ErrorAction SilentlyContinue).Status 
      if ($serviceStatus.length -eq 0) {
        $serviceStatus = "Not Installed" }
      return $serviceStatus
    }

foreach ($server in $servers) {
    
    if (!(pingCheck $server)) {
       Continue
    }

    $MarimbaAgent = serviceStatus FTServerWindows $server
    if ($MarimbaAgent -eq "Running" -or $MarimbaAgent -eq "Stopped") {
        $script = { 
            invoke-expression "msiexec /QN /X '{4759F5DE-D90C-AEAE-026C-2036F5D5A262}' "
            Start-Sleep -Seconds 15
        }

        Invoke-Command -ComputerName $server -ScriptBlock $script
        logfile "$server - Marimba has been uninstalled"
        
    }

    else {
        logfile "$server does not have Marimba Installed"
    }
}







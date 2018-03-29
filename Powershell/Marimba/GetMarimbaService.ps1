#This Script gets the list servers from AD that have logged in in the last 30 days and then checks to see if it has the Marimba Service Installed
#Sham Ramchandani - March 2018

# Gets time stamps for all computers in the domain that have NOT logged in since after specified date 
import-module activedirectory  
$DaysInactive = 30  
$time = (Get-Date).Adddays(-($DaysInactive))
  
# Get all AD computers with lastLogonTimestamp less than our time 
$servers = Get-ADComputer -Filter {LastLogonTimeStamp -gt $time} -Properties LastLogonTimeStamp -searchbase "OU=Windows Servers,DC=ad,DC=ft,DC=com"
  
function pingCheck([string]$server) {
    if (Test-Connection -ComputerName $server -Count 2 -ErrorAction SilentlyContinue) {         
        return $true }
      else {
        return $false }

}

foreach ($server in $servers) {
    $Name = $server.Name

    if (!(pingCheck $Name)) {
       Continue
    }

    get-service -Name "FT_Server_Windows" -ComputerName $Name | Select-Object -Property MachineName, Status, DisplayName, StartType | Export-Csv -path c:\temp\marimba.csv -Append -NoTypeInformation

}
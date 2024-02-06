# Define default values or set to $null if you require them to be provided
$imageName = $null
$containerName = $null
$env:MITTA_TOKEN = $null
$env:MITTA_PIPELINE = $null
$env:MITTA_DEV = "True"

$configFilePath = ".\config.json"

Write-Host "Starting management of dreams-service..."

# Check if config file exists
if (Test-Path -Path $configFilePath) {
    Write-Host "Config file found. Reading configuration..."
    $configContent = Get-Content -Path $configFilePath | ConvertFrom-Json
    
    # Assign values from config file
    $imageName = $configContent.imageName
    $containerName = $configContent.containerName
    $env:MITTA_TOKEN = $configContent.MITTA_TOKEN
    $env:MITTA_DEV = $configContent.MITTA_DEV
    $env:MITTA_PIPELINE = $configContent.MITTA_PIPELINE
}
else {
    Write-Host "Config file not found. Copy the sample config (`config.sample.json`), save it as `config.json`, and restart the script."
    exit
}


# Function to get the most recent modification time of files
function Get-LatestModificationTime {
    return (Get-ChildItem -Recurse | Where-Object { -not $_.PSIsContainer } | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
}

# Infinite loop to ensure the container is always running and updated
while ($true) {
    # Get the most recent modification time
    $currentModificationTime = Get-LatestModificationTime

    # Check if there's any file changed since last check
    if ($currentModificationTime -gt $lastCheckTime) {
        Write-Host "File changes detected. Rebuilding and restarting the container..."

        # Update the last check time
        $lastCheckTime = Get-Date

        # Stop and remove existing container if it exists
        $existingContainer = docker ps -a | Select-String $containerName
        if ($existingContainer) {
            docker stop $containerName
            docker rm $containerName
        }

        # Rebuild the Docker image
        docker build -t $imageName .

        # Run the Docker container with a restart policy and port mapping
        # Run the Docker container with environment variables, a restart policy, and port mapping
        docker run --name $containerName -d --restart=on-failure:5 -p 5000:5000 -e MITTA_TOKEN=$env:MITTA_TOKEN -e MITTA_PIPELINE=$env:MITTA_PIPELINE -e MITTA_DEV=$env:MITTA_DEV $imageName

        Write-Host "Container rebuilt and restarted with port 5000 exposed."
    }

    # Check if the container is running
    $containerRunning = docker ps | Select-String $containerName

    # If the container is not running, restart it
    if (-not $containerRunning) {
        Write-Host "Container not running. Attempting to restart..."
        docker start $containerName
        Write-Host "Container restarted."
    }

    # Display the latest logs
    Write-Host "Displaying latest container logs:"
    docker logs $containerName --tail 50

    # Wait for 5 seconds before checking again
    Start-Sleep -Seconds 5
}

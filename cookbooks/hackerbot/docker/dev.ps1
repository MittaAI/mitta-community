# Define variables
$imageName = "convert-service"
$containerName = "convert-container"
$lastCheckTime = Get-Date

Write-Host "Starting management of convert-service..."

# Define environment variables
$env:MITTA_TOKEN = "wMM80IZMYhuagK96ggdLc6as2x6R5VEVYTlq_ivY"
$env:NEWS_PIPELINE = "4bogW07SUcIVg"

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
        docker run --name $containerName -d --restart=on-failure:5 -p 5000:5000 -e MITTA_TOKEN=$env:MITTA_TOKEN -e NEWS_PIPELINE=$env:NEWS_PIPELINE $imageName

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

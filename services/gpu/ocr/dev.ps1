# Define variables
$imageName = "ocr-service"
$containerName = "ocr-container"
$envVar = "OCR_TOKEN=f00bar"

Write-Host "Starting management of ocr-service..."

# Function to get the most recent modification time of files
function Get-LatestModificationTime {
    return (Get-ChildItem -Recurse | Where-Object { -not $_.PSIsContainer } | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
}


# Infinite loop to ensure the container is always running
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

    # If the container is not running, rebuild and restart it
    if (-not $containerRunning) {
        Write-Host "Container not running. Attempting to rebuild and restart..."

        # Stop and remove existing container if it exists
        $existingContainer = docker ps -a | Select-String $containerName
        if ($existingContainer) {
            docker stop $containerName
            docker rm $containerName
        }

        # Rebuild the Docker image
        docker build -t $imageName .

        # Run the Docker container with a restart policy, port mapping, and environment variable
        docker run --name $containerName -d --restart=on-failure:5 -p 5000:5000 -v "${PWD}:/app" -e $envVar $imageName

        Write-Host "Container restarted with port 5000 exposed and OCR_TOKEN set."
    }

    # Display the latest logs after checking the container status
    Write-Host "Displaying latest container logs:"
    docker logs $containerName --tail 50

    # Wait for 5 seconds before checking again
    Start-Sleep -Seconds 5
}
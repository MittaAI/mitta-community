# Define variables
$imageName = "ffmpeg-service"
$containerName = "ffmpeg-container"
$envVar = "FFMPEG_TOKEN=f00bar"

Write-Host "Starting management of ffmpeg-service..."

# Infinite loop to ensure the container is always running
while ($true) {
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

        Write-Host "Container restarted with port 5000 exposed and FFMPEG_TOKEN set."
    }

    # Display the latest logs after checking the container status
    Write-Host "Displaying latest container logs:"
    docker logs $containerName --tail 50

    # Wait for 5 seconds before checking again
    Start-Sleep -Seconds 5
}


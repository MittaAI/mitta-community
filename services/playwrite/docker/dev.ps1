# Define variables
$imageName = "playwright-python"
$containerName = "playwright-container"
$grubToken = "f00bar" # Read GRUB_TOKEN

Write-Host "Starting management of $imageName..."

# Infinite loop to ensure the container is always running
while ($true) {
    Start-Sleep -Seconds 

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

        # Run the Docker container with a restart policy, port mapping, and volume mounting
        docker run --name $containerName -d --restart=on-failure:5 -p 5000:5000 -v "${PWD}:/app" -e GRUB_TOKEN=$grubToken $imageName

        Write-Host "Container restarted with port 5000 exposed and directory synced."
    }

    # Display the latest logs after checking the container status
    Write-Host "Displaying latest container logs:"
    docker logs $containerName --tail 50

    # Execute commands inside the container
    # Write-Host "Executing command inside the container..."
    # docker exec -it $containerName bash
}
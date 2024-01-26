# Define variables
$imageName = "convert-service"
$containerName = "convert-container"

# Infinite loop to ensure the container is always running
while ($true) {
    # Check if the container is running
    $containerRunning = docker ps | Select-String $containerName

    # If the container is not running, rebuild and restart it
    if (-not $containerRunning) {
        Write-Host "Container not running. Attempting to rebuild and restart..."

        # Stop and remove existing container if it exists
        docker ps -a | Select-String $containerName | ForEach-Object {
            docker stop $containerName
            docker rm $containerName
        }

        # Rebuild the Docker image
        docker build -t $imageName .

        # Run the Docker container with a restart policy and port mapping
        docker run --name $containerName -d --restart=on-failure:5 -p 5000:5000 $imageName

        Write-Host "Container restarted with port 5000 exposed."
    }

    # Wait for 5 seconds before checking again
    Start-Sleep -Seconds 5
}

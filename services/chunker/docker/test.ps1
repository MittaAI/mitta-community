# Define the API endpoint
$apiUrl = "http://localhost:5000/chunk"

# Define the request body
$body = @{
    texts = @(
        @(
            "This is a sample text to be chunked. It will be split into smaller pieces based on the specified parameters. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
        )
    )
    filenames = @("sample.txt")
    length = 50
    min_length = 20
    start_page = 1
    overlap = 0
    flatten_output = $true
} | ConvertTo-Json

# Set the content type to JSON
$headers = @{
    "Content-Type" = "application/json"
}

try {
    # Make the API call
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -Headers $headers

    # Display the response
    Write-Host "API Response:"
    $response | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "An error occurred while calling the API:"
    Write-Host $_.Exception.Message
}
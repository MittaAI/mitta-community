$credentialsFilePath = "./credentials.json"

$pipelineID = Read-Host -Prompt "Enter your pipeline ID"
$token = Read-Host -Prompt "Enter your token"

# Construct the URL
$url = "https://mitta.ai/pipeline/$pipelineID/task?token=$token"
$fileToUpload = "../kord/code/mitta-community/documents/edward.pdf"  # Adjust the path as necessary

# Prepare the file content
$fileContent = [System.IO.File]::ReadAllBytes($fileToUpload)

# Prepare JSON data
$jsonData = @{
    filename = "edward.pdf"
    content_type = "application/pdf"
} | ConvertTo-Json

# Create multipart/form-data boundary
$boundary = [System.Guid]::NewGuid().ToString()

# Construct headers
$headers = @{
    "Content-Type" = "multipart/form-data; boundary=$boundary"
}

# Construct the request body
$bodyLines = (
    "--$boundary",
    'Content-Disposition: form-data; name="file"; filename="edward.pdf"',
    "Content-Type: application/pdf",
    "",
    [System.Text.Encoding]::Default.GetString($fileContent),
    "--$boundary",
    'Content-Disposition: form-data; name="json"',
    'Content-Type: application/json',
    "",
    $jsonData,
    "--$boundary--"
) -join "`r`n"

# Convert body to bytes
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyLines)

# Send the request
Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $bodyBytes



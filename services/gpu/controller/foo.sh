# Get the current remote URL for 'origin'
remote_url=$(git remote get-url origin)

# Check if the URL is an SSH URL and convert it to HTTPS
if [[ "$remote_url" =~ ^git@github.com:(.+)/(.+).git$ ]]; then
    user="${BASH_REMATCH[1]}"
    repo="${BASH_REMATCH[2]}"
    https_url="https://github.com/${user}/${repo}.git"
    echo $https_url
# Else, assume it's already an HTTPS URL, just remove the authentication part if present
else
    https_url=$(echo $remote_url | sed -E 's/https:\/\/[^@]+@/https:\/\//')
    echo $https_url
fi

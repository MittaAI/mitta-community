document.addEventListener('DOMContentLoaded', function() {
    // This function fetches stored values and populates the form fields
    function populateStoredValues() {
        chrome.storage.local.get(['pipelineId', 'token'], (data) => {
            console.log(data);
            if (data.pipelineId) {
                document.getElementById('pipelineId').value = data.pipelineId;
            }
            if (data.token) {
                document.getElementById('token').value = data.token;
            }
        });
    }

    // Call populateStoredValues when the popup is opened to fill the form with existing values
    populateStoredValues(); // Removed redundant DOMContentLoaded listener

    document.getElementById('save').addEventListener('click', () => {
        const pipelineId = document.getElementById('pipelineId').value;
        const token = document.getElementById('token').value;
        console.log('Attempting to save:', pipelineId, token); // Log what we're about to save

        chrome.storage.local.set({pipelineId, token}, () => {
            console.log('Settings saved:', pipelineId, token);
            chrome.storage.local.get(['pipelineId', 'token'], (result) => {
                console.log('Verify saved data:', result); // Verify what was saved
            });
        });
    });

    document.getElementById('takeScreenshot').addEventListener('click', () => {
        console.log("screenshot clicked");
        // First, get the current tab's URL
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            const currentTab = tabs[0]; // Assuming there's at least one tab
            const pageUrl = currentTab.url; // Get the URL of the current tab

            chrome.tabs.captureVisibleTab(null, {format: 'png'}, (dataUrl) => {
                if (!dataUrl) {
                    console.log('Failed to capture screenshot.');
                    return;
                }
                chrome.storage.local.get(['pipelineId', 'token'], (data) => {
                    if (!data.pipelineId || !data.token) {
                        console.log('Pipeline ID or Token not configured.');
                        return; // Stop if the pipeline ID or token is not set
                    }
                    const blob = dataUrltoBlob(dataUrl);
                    const formData = new FormData();
                    formData.append('file', blob, 'screenshot.png');
                    formData.append('page_url', pageUrl); // Add the current page's URL to the FormData

                    const endpoint = `https://mitta.ai/pipeline/${data.pipelineId}/task?token=${data.token}`;
                    fetch(endpoint, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(result => console.log('Upload successful', result))
                    .then(result => {
					    console.log('Upload successful', result);
					    window.close(); // Correctly placed inside a then() to ensure proper sequencing
					})
                    .catch(error => console.error('Upload failed', error));
                });
            });
        });
    });

    // Utility function to convert dataURL to Blob object
    function dataUrltoBlob(dataUrl) {
        var byteString = atob(dataUrl.split(',')[1]);
        var mimeString = dataUrl.split(',')[0].split(':')[1].split(';')[0];
        var ab = new ArrayBuffer(byteString.length);
        var ia = new Uint8Array(ab);
        for (var i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
        }
        return new Blob([ia], {type: mimeString});
    }
});

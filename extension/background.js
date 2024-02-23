chrome.runtime.onInstalled.addListener(() => {
  // Initially disable the icon
  chrome.action.disable();
  // Check if the credentials are stored and enable the icon accordingly
  chrome.storage.local.get(['pipelineId', 'token'], (data) => {
    if (data.pipelineId && data.token) {
      chrome.action.enable(); // Enable the icon if credentials are stored
      console.log("Extension icon enabled.");
    } else {
      console.log("Extension icon not enabled due to missing credentials.");
    }
  });
});

chrome.storage.onChanged.addListener((changes, namespace) => {
  for (let [key, { oldValue, newValue }] of Object.entries(changes)) {
    console.log(
      `Storage key "${key}" in namespace "${namespace}" changed.`,
      `Old value was "${oldValue}", new value is "${newValue}".`
    );
  }
});


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "checkCredentials") {
    chrome.storage.local.get(['pipelineId', 'token'], (data) => {
      const isConfigured = data.pipelineId && data.token;
      sendResponse({configured: isConfigured});
    });
    return true; // Return true to indicate you wish to send a response asynchronously
  }
  // Handle other messages or commands as needed
});

// In background.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "checkCredentialsAndUpdateIcon") {
        chrome.storage.local.get(['pipelineId', 'token'], (data) => {
            if (data.pipelineId && data.token) {
                chrome.action.enable(); // Enable the icon if credentials are stored
                sendResponse({message: "Icon enabled."});
            } else {
                chrome.action.disable(); // Keep the icon disabled if credentials are missing
                sendResponse({message: "Icon disabled due to missing credentials."});
            }
        });
        return true; // This ensures the message channel is kept open for the asynchronous response
    }
    // Handle other types of messages as needed
});


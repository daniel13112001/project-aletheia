const API_ENDPOINT = 'http://localhost:8080/search';

// Initialize storage on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    factCheckResults: [],
    pendingChecks: 0
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'checkFact') {
    handleFactCheck(message.query);
    sendResponse({ success: true });
  } else if (message.action === 'clearResults') {
    clearResults();
    sendResponse({ success: true });
  }
  return true;
});

async function handleFactCheck(query) {
  // Increment pending checks
  const storage = await chrome.storage.local.get(['pendingChecks', 'factCheckResults']);
  const pendingChecks = (storage.pendingChecks || 0) + 1;
  await chrome.storage.local.set({ pendingChecks });

  // Update badge to show pending
  updateBadge(storage.factCheckResults?.length || 0, pendingChecks);

  try {
    const response = await fetch(`${API_ENDPOINT}?q=${encodeURIComponent(query)}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const results = await response.json();

    // Get current storage state
    const currentStorage = await chrome.storage.local.get(['factCheckResults', 'pendingChecks']);
    const existingResults = currentStorage.factCheckResults || [];
    const currentPending = currentStorage.pendingChecks || 1;

    // Add new results with the original query for context
    const newResults = results.map(result => ({
      ...result,
      originalQuery: query,
      checkedAt: new Date().toISOString()
    }));

    // Append to existing results
    const allResults = [...newResults, ...existingResults];
    const newPending = Math.max(0, currentPending - 1);

    await chrome.storage.local.set({
      factCheckResults: allResults,
      pendingChecks: newPending
    });

    // Update badge with total results count
    updateBadge(allResults.length, newPending);

    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" fill="#4a90e2"/><path d="M20 24l4 4 8-8" stroke="white" stroke-width="3" fill="none"/></svg>'),
      title: 'Fact Check Complete',
      message: `Found ${results.length} result${results.length !== 1 ? 's' : ''} for: "${query.substring(0, 50)}${query.length > 50 ? '...' : ''}"`
    });

    // Notify popup if open
    chrome.runtime.sendMessage({
      action: 'resultsUpdated',
      results: allResults,
      pendingChecks: newPending
    }).catch(() => {});

  } catch (error) {
    console.error('Fact check error:', error);

    // Decrement pending on error
    const currentStorage = await chrome.storage.local.get(['factCheckResults', 'pendingChecks']);
    const newPending = Math.max(0, (currentStorage.pendingChecks || 1) - 1);
    await chrome.storage.local.set({ pendingChecks: newPending });

    updateBadge(currentStorage.factCheckResults?.length || 0, newPending);

    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" fill="#f44336"/><path d="M18 18l12 12M30 18l-12 12" stroke="white" stroke-width="3"/></svg>'),
      title: 'Fact Check Failed',
      message: `Could not check: "${query.substring(0, 50)}${query.length > 50 ? '...' : ''}"`
    });
  }
}

function updateBadge(resultsCount, pendingCount) {
  if (pendingCount > 0) {
    // Show spinner-like indicator when checks are pending
    chrome.action.setBadgeText({ text: '...' });
    chrome.action.setBadgeBackgroundColor({ color: '#4a90e2' });
  } else if (resultsCount > 0) {
    chrome.action.setBadgeText({ text: resultsCount.toString() });
    chrome.action.setBadgeBackgroundColor({ color: '#4caf50' });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
}

async function clearResults() {
  await chrome.storage.local.set({
    factCheckResults: [],
    pendingChecks: 0
  });
  chrome.action.setBadgeText({ text: '' });

  chrome.runtime.sendMessage({
    action: 'resultsCleared'
  }).catch(() => {});
}

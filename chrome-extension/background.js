// Mock API - simulates API delay and returns dummy data
// Replace this with real API call when backend is ready
const USE_DUMMY_API = true;

// Dummy API function that simulates network delay
async function mockApiCall(query, k) {
  // Simulate ~2 second API delay
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Return dummy fact-check results
  return [
    {
      statement: query.substring(0, 100) + (query.length > 100 ? '...' : ''),
      verdict: "True",
      factchecker: "PolitiFact",
      statement_originator: "Public Figure",
      statement_date: "2024-01-15",
      factcheck_analysis_link: "https://www.politifact.com/factchecks/2024/jan/15/example/"
    },
    {
      statement: "Related claim about " + query.substring(0, 50),
      verdict: "False",
      factchecker: "Snopes",
      statement_originator: "Social Media",
      statement_date: "2024-01-10",
      factcheck_analysis_link: "https://www.snopes.com/fact-check/example/"
    },
    {
      statement: "Another related statement regarding " + query.substring(0, 40),
      verdict: "Mixed",
      factchecker: "FactCheck.org",
      statement_originator: "News Article",
      statement_date: "2024-01-05",
      factcheck_analysis_link: "https://www.factcheck.org/2024/01/example/"
    }
  ];
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'checkFact') {
    handleFactCheck(message.query);
    sendResponse({ success: true });
  }
  return true; // Keep channel open for async response
});

async function handleFactCheck(query) {
  // Update badge to show processing
  chrome.action.setBadgeText({ text: '...' });
  chrome.action.setBadgeBackgroundColor({ color: '#4a90e2' });

  try {
    let results = [];
    
    if (USE_DUMMY_API) {
      // Use mock API
      results = await mockApiCall(query, 5);
    } else {
      // Real API call (uncomment when backend is ready)
      // const API_ENDPOINT = 'http://localhost:8080/api/search';
      // const response = await fetch(API_ENDPOINT, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({
      //     query: query,
      //     k: 5
      //   })
      // });
      // 
      // if (!response.ok) {
      //   throw new Error(`API error: ${response.status}`);
      // }
      // 
      // const data = await response.json();
      // 
      // // Handle different possible response formats
      // if (Array.isArray(data)) {
      //   results = data;
      // } else if (data.results && Array.isArray(data.results)) {
      //   results = data.results;
      // } else if (data.data && Array.isArray(data.data)) {
      //   results = data.data;
      // }
    }
    
    // Store results
    await chrome.storage.local.set({ factCheckResults: results });

    // Update badge with result count
    const count = results.length;
    chrome.action.setBadgeText({ text: count > 0 ? count.toString() : '0' });
    chrome.action.setBadgeBackgroundColor({ color: count > 0 ? '#4caf50' : '#f44336' });

    // Show notification
    chrome.notifications.create({
      type: 'basic',
      title: 'Fact Check Complete',
      message: `Found ${count} result${count !== 1 ? 's' : ''}`
    });

    // Notify popup if it's open
    chrome.runtime.sendMessage({
      action: 'showResults',
      results: results
    }).catch(() => {
      // Popup might be closed, ignore error
    });

  } catch (error) {
    console.error('Fact check error:', error);
    
    // Update badge to show error
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#f44336' });

    // Show error notification
    chrome.notifications.create({
      type: 'basic',
      title: 'Fact Check Failed',
      message: 'Unable to complete fact check. Please try again.'
    });
  }
}

// Configuration - update this to match your API endpoint
const API_ENDPOINT = 'http://localhost:8080/api/search';

document.addEventListener('DOMContentLoaded', async () => {
  const queryInput = document.getElementById('query-input');
  const checkBtn = document.getElementById('check-btn');
  const statusMessage = document.getElementById('status-message');
  const inputView = document.getElementById('input-view');
  const resultsView = document.getElementById('results-view');
  const resultsContainer = document.getElementById('results-container');
  const newCheckBtn = document.getElementById('new-check-btn');

  // Check if there are existing results
  const storedResults = await chrome.storage.local.get('factCheckResults');
  if (storedResults.factCheckResults) {
    showResults(storedResults.factCheckResults);
  } else {
    // Try to get selected text from the current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab.id) {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: getSelectedText
      }, (results) => {
        if (results && results[0] && results[0].result) {
          queryInput.value = results[0].result;
        }
      });
    }
  }

  checkBtn.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    
    if (!query) {
      showStatus('Please enter text to fact-check', 'error');
      return;
    }

    // Disable button and show status
    checkBtn.disabled = true;
    showStatus('Fact check started! You can close this and continue browsing', 'success');

    // Send message to background script
    chrome.runtime.sendMessage({
      action: 'checkFact',
      query: query
    });

    // Auto-close after 1.5 seconds
    setTimeout(() => {
      window.close();
    }, 1500);
  });

  newCheckBtn.addEventListener('click', () => {
    chrome.storage.local.remove('factCheckResults');
    inputView.classList.remove('hidden');
    resultsView.classList.add('hidden');
    queryInput.value = '';
    statusMessage.textContent = '';
    chrome.action.setBadgeText({ text: '' });
  });
});

function getSelectedText() {
  return window.getSelection().toString();
}

function showStatus(message, type) {
  const statusMessage = document.getElementById('status-message');
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
}

function showResults(results) {
  inputView.classList.add('hidden');
  resultsView.classList.remove('hidden');
  resultsContainer.innerHTML = '';

  if (results.length === 0) {
    resultsContainer.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No results found</p>';
    return;
  }

  results.forEach(result => {
    const resultDiv = document.createElement('div');
    resultDiv.className = 'result-item';

    const statement = document.createElement('div');
    statement.className = 'result-statement';
    statement.textContent = result.statement || 'No statement available';
    resultDiv.appendChild(statement);

    if (result.verdict) {
      const verdict = document.createElement('div');
      verdict.className = `result-verdict ${result.verdict.toLowerCase()}`;
      verdict.textContent = `Verdict: ${result.verdict}`;
      resultDiv.appendChild(verdict);
    }

    const meta = document.createElement('div');
    meta.className = 'result-meta';
    const metaParts = [];
    if (result.factchecker) metaParts.push(`Fact-checked by: ${result.factchecker}`);
    if (result.statement_originator) metaParts.push(`Source: ${result.statement_originator}`);
    if (result.statement_date) metaParts.push(`Date: ${result.statement_date}`);
    meta.textContent = metaParts.join(' • ');
    resultDiv.appendChild(meta);

    if (result.factcheck_analysis_link) {
      const link = document.createElement('div');
      link.className = 'result-link';
      const a = document.createElement('a');
      a.href = result.factcheck_analysis_link;
      a.target = '_blank';
      a.textContent = 'View full analysis →';
      link.appendChild(a);
      resultDiv.appendChild(link);
    }

    resultsContainer.appendChild(resultDiv);
  });
}

// Listen for results from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'showResults') {
    showResults(message.results);
  }
});

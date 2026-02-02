document.addEventListener('DOMContentLoaded', async () => {
  const queryInput = document.getElementById('query-input');
  const checkBtn = document.getElementById('check-btn');
  const statusMessage = document.getElementById('status-message');
  const inputSection = document.getElementById('input-section');
  const resultsSection = document.getElementById('results-section');
  const resultsContainer = document.getElementById('results-container');
  const clearAllBtn = document.getElementById('clear-all-btn');
  const resultsCount = document.getElementById('results-count');
  const pendingIndicator = document.getElementById('pending-indicator');

  // Load current state
  await loadState();

  // Try to get selected text from the current tab
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab.id && !tab.url.startsWith('chrome://')) {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: () => window.getSelection().toString()
      });
      if (results && results[0] && results[0].result) {
        queryInput.value = results[0].result;
      }
    }
  } catch (e) {
    // Ignore errors from restricted pages
  }

  checkBtn.addEventListener('click', async () => {
    const query = queryInput.value.trim();

    if (!query) {
      showStatus('Please enter text to fact-check', 'error');
      return;
    }

    // Send to background for processing
    chrome.runtime.sendMessage({
      action: 'checkFact',
      query: query
    });

    // Clear input and show confirmation
    queryInput.value = '';
    showStatus('Checking in background...', 'success');

    // Update pending indicator
    const storage = await chrome.storage.local.get('pendingChecks');
    updatePendingIndicator((storage.pendingChecks || 0) + 1);

    // Clear status after delay
    setTimeout(() => {
      statusMessage.textContent = '';
      statusMessage.className = 'status-message';
    }, 2000);
  });

  clearAllBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'clearResults' });
    resultsContainer.innerHTML = '';
    resultsCount.textContent = '0 results';
    updatePendingIndicator(0);
  });

  // Listen for updates from background
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'resultsUpdated') {
      renderResults(message.results);
      updateResultsCount(message.results.length);
      updatePendingIndicator(message.pendingChecks);
    } else if (message.action === 'resultsCleared') {
      resultsContainer.innerHTML = '';
      resultsCount.textContent = '0 results';
      updatePendingIndicator(0);
    }
  });

  async function loadState() {
    const storage = await chrome.storage.local.get(['factCheckResults', 'pendingChecks']);
    const results = storage.factCheckResults || [];
    const pending = storage.pendingChecks || 0;

    renderResults(results);
    updateResultsCount(results.length);
    updatePendingIndicator(pending);
  }

  function renderResults(results) {
    resultsContainer.innerHTML = '';

    if (results.length === 0) {
      resultsContainer.innerHTML = '<p class="no-results">No fact-checks yet. Highlight text on any page and check it!</p>';
      return;
    }

    results.forEach((result, index) => {
      const resultDiv = document.createElement('div');
      resultDiv.className = 'result-item';

      // Original query section
      if (result.originalQuery) {
        const queryDiv = document.createElement('div');
        queryDiv.className = 'result-query';
        queryDiv.textContent = `Checked: "${result.originalQuery.substring(0, 80)}${result.originalQuery.length > 80 ? '...' : ''}"`;
        resultDiv.appendChild(queryDiv);
      }

      // Statement
      const statement = document.createElement('div');
      statement.className = 'result-statement';
      statement.textContent = result.statement || 'No statement available';
      resultDiv.appendChild(statement);

      // Verdict badge
      if (result.verdict) {
        const verdict = document.createElement('span');
        const verdictLower = result.verdict.toLowerCase();
        verdict.className = `result-verdict ${verdictLower}`;
        verdict.textContent = result.verdict;
        resultDiv.appendChild(verdict);
      }

      // Metadata
      const meta = document.createElement('div');
      meta.className = 'result-meta';
      const metaParts = [];
      if (result.factchecker) metaParts.push(`by ${result.factchecker}`);
      if (result.statement_originator) metaParts.push(`Source: ${result.statement_originator}`);
      if (result.statement_date) metaParts.push(result.statement_date);
      meta.textContent = metaParts.join(' · ');
      resultDiv.appendChild(meta);

      // Link to full analysis
      if (result.factcheck_analysis_link) {
        const link = document.createElement('a');
        link.className = 'result-link';
        link.href = result.factcheck_analysis_link;
        link.target = '_blank';
        link.textContent = 'View full analysis';
        resultDiv.appendChild(link);
      }

      resultsContainer.appendChild(resultDiv);
    });
  }

  function updateResultsCount(count) {
    resultsCount.textContent = `${count} result${count !== 1 ? 's' : ''}`;
  }

  function updatePendingIndicator(count) {
    if (count > 0) {
      pendingIndicator.textContent = `${count} check${count !== 1 ? 's' : ''} in progress...`;
      pendingIndicator.classList.remove('hidden');
    } else {
      pendingIndicator.classList.add('hidden');
    }
  }

  function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
  }
});

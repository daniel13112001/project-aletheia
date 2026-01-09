# Aletheia Fact Checker Chrome Extension

A Chrome extension for fact-checking highlighted text on any webpage.

## Setup

1. **Load the extension in Chrome:**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `chrome-extension` folder


## API Configuration

**Currently using dummy/mock API for testing.**

To switch to a real API endpoint:
1. Open `background.js`
2. Set `USE_DUMMY_API = false`
3. Uncomment the real API code and update `API_ENDPOINT`

**Expected API Format:**

**Endpoint:** `POST /api/search`

**Request Body:**
```json
{
  "query": "text to fact-check",
  "k": 5
}
```

**Response:** Array of fact-check results
```json
[
  {
    "statement": "The claim text",
    "verdict": "True|False|Mixed",
    "factchecker": "Fact checker name",
    "statement_originator": "Source",
    "statement_date": "Date",
    "factcheck_analysis_link": "URL to full analysis"
  }
]
```

The endpoint should:
1. Call your gRPC VectorSearchService with the query
2. Get metadata for the returned UIDs from your metadata store
3. Return the metadata as JSON array

## Usage

1. Highlight text on any webpage
2. Click the extension icon
3. The selected text will appear in the textarea (or type manually)
4. Click "Check Fact"
5. The popup will close automatically
6. A notification will appear when results are ready
7. Click the extension icon again to view results

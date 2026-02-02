# Aletheia Fact Checker Chrome Extension

A Chrome extension that allows users to fact-check highlighted text on any webpage. Select text, click the extension, and instantly see if the claim has been fact-checked.

## Features

- Highlight text on any webpage and fact-check it
- Automatic text selection detection
- Color-coded verdict badges (green/red/yellow)
- Desktop notifications when results are ready
- Links to full fact-check analyses
- Works offline with mock API for testing

## Installation

### Development Installation

1. Clone the repository and navigate to the extension folder:
   ```bash
   cd chrome-extension
   ```

2. Open Chrome and go to `chrome://extensions/`

3. Enable **Developer mode** (toggle in the top right)

4. Click **Load unpacked**

5. Select the `chrome-extension` folder

The extension icon will appear in your Chrome toolbar.

### Production Build

For distribution, package the extension:
1. Go to `chrome://extensions/`
2. Click **Pack extension**
3. Select the `chrome-extension` folder
4. This creates a `.crx` file for distribution

## Usage

1. **Highlight text** on any webpage that you want to fact-check

2. **Click the extension icon** in the Chrome toolbar

3. The selected text will automatically appear in the textarea
   - You can also type or paste text manually

4. **Click "Check Fact"**

5. The popup closes automatically and a **notification** appears when results are ready

6. **Click the extension icon again** to view the results:
   - Statement text
   - Verdict badge (True/False/Mixed)
   - Fact-checker information
   - Link to full analysis

7. Click **"New Check"** to start over

## Configuration

### Switching to Real API

By default, the extension uses a mock API for testing. To connect to the real API:

1. Open `background.js`

2. Change `USE_DUMMY_API` to `false`:
   ```javascript
   const USE_DUMMY_API = false;
   ```

3. Update the API endpoint if needed:
   ```javascript
   const API_ENDPOINT = 'http://localhost:8080/search';
   ```

4. Reload the extension in `chrome://extensions/`

### API Endpoint Configuration

The extension calls:
```
GET http://localhost:8080/search?q=<query>
```

**Expected Response Format:**
```json
[
  {
    "statement": "The claim text",
    "verdict": "True|False|Mixed",
    "factchecker": "Organization name",
    "statement_originator": "Who made the claim",
    "statement_date": "2024-01-15",
    "factcheck_analysis_link": "https://..."
  }
]
```

## Permissions

| Permission | Purpose |
|------------|---------|
| `storage` | Store fact-check results locally |
| `notifications` | Show desktop notifications when results are ready |
| `activeTab` | Access the current tab to extract selected text |
| `scripting` | Execute scripts to get selected text from pages |

### Host Permissions

```json
"host_permissions": ["http://localhost/*"]
```

The extension only connects to localhost by default. For production, update this to your API server's domain.

## Files

| File | Description |
|------|-------------|
| `manifest.json` | Extension configuration (Manifest V3) |
| `background.js` | Service worker for API calls and state management |
| `popup.html` | Popup UI markup |
| `popup.js` | Popup UI controller and event handling |
| `popup.css` | Popup styling |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Chrome Extension                   │
│                                                      │
│  ┌────────────────┐      ┌─────────────────────┐    │
│  │   popup.html   │      │   background.js     │    │
│  │   popup.js     │◄────►│   (Service Worker)  │    │
│  │   popup.css    │      │                     │    │
│  └────────────────┘      └──────────┬──────────┘    │
│                                     │               │
│  ┌──────────────────────────────────┼───────────┐   │
│  │           chrome.storage          │           │   │
│  │  ┌─────────────────────────────┐  │           │   │
│  │  │     lastResults: [...]      │◄─┘           │   │
│  │  └─────────────────────────────┘              │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
                          │
                          │ HTTP GET
                          ▼
                 ┌─────────────────┐
                 │   API Gateway   │
                 │  :8080/search   │
                 └─────────────────┘
```

## Data Flow

1. **User opens popup** → `popup.js` checks for existing results in `chrome.storage.local`
2. **User clicks "Check Fact"** → Message sent to `background.js`
3. **Background processes** → Calls API, stores results, shows notification
4. **User reopens popup** → Results loaded from storage and displayed

## Verdict Display

Results are displayed with color-coded badges:

| Verdict | Color | Badge |
|---------|-------|-------|
| True | Green | `#27ae60` |
| False | Red | `#e74c3c` |
| Mixed | Yellow | `#f1c40f` |

## Development

### Debugging

1. Open `chrome://extensions/`
2. Click **"Inspect views: service worker"** to debug `background.js`
3. Right-click the popup and select **"Inspect"** to debug popup scripts

### Testing with Mock API

The mock API (`USE_DUMMY_API = true`) returns sample data after a 2-second delay:

```javascript
{
  statement: "This is a sample fact-checked statement",
  verdict: "True",
  factchecker: "PolitiFact",
  statement_originator: "Sample Source",
  statement_date: "2024-01-01",
  factcheck_analysis_link: "https://example.com/analysis"
}
```

### Reloading Changes

After modifying files:
1. Go to `chrome://extensions/`
2. Click the refresh icon on the Aletheia extension
3. Close and reopen any popup windows

## Troubleshooting

**Popup shows "No results yet":**
- Ensure you've clicked "Check Fact" and waited for the notification
- Check the service worker console for errors

**API errors:**
- Verify the API Gateway is running on port 8080
- Check that `USE_DUMMY_API` matches your setup
- Ensure the API endpoint is correct in `background.js`

**Selected text not appearing:**
- The page must be fully loaded
- Some pages (like chrome:// URLs) don't allow script injection
- Try manually typing the text instead

# Aletheia Fact Checker Chrome Extension

A Chrome extension that allows users to fact-check highlighted text on any webpage. Select text, click the extension, and instantly queue a fact-check. Results accumulate in the background, letting you check multiple claims while browsing.

## Features

- Highlight text on any webpage and fact-check it
- **Queue multiple checks** - check several claims without waiting
- Background processing - continue browsing while checks complete
- Badge counter shows total results found
- Desktop notifications when each check completes
- Color-coded verdict badges (True/False/Mixed)
- Links to full fact-check analyses
- Persistent results until cleared

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

## Usage

### Basic Workflow

1. **Highlight text** on any webpage that you want to fact-check

2. **Click the extension icon** - the popup opens with highlighted text pre-filled

3. **Click "Check Fact"** - the check starts in the background

4. **Continue browsing** - repeat steps 1-3 for other claims you want to check

5. **Watch the badge** - it shows "..." while checks are pending, then updates to show the total result count

6. **View results** - click the extension icon anytime to see all accumulated results

7. **Clear results** - click "Clear All" to start fresh

### Multiple Checks

You can queue multiple fact-checks at once:
- Each check runs independently in the background
- The pending indicator shows how many checks are in progress
- Results accumulate as each check completes
- Badge counter increases with each new result

## Configuration

### API Endpoint

The extension connects to the Aletheia API Gateway at:
```
http://localhost:8080/search
```

To change the endpoint, edit `background.js`:
```javascript
const API_ENDPOINT = 'http://localhost:8080/search';
```

### Permissions

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

For production deployment, update this to your API server's domain.

## Files

| File | Description |
|------|-------------|
| `manifest.json` | Extension configuration (Manifest V3) |
| `background.js` | Service worker - handles API calls, manages state, sends notifications |
| `popup.html` | Popup UI markup |
| `popup.js` | Popup UI controller - renders results, handles user input |
| `popup.css` | Popup styling |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Chrome Extension                         │
│                                                              │
│  ┌─────────────────┐         ┌──────────────────────────┐   │
│  │     Popup       │◄───────►│   Background Service     │   │
│  │  (popup.js)     │ message │      Worker              │   │
│  │                 │         │   (background.js)        │   │
│  └─────────────────┘         └────────────┬─────────────┘   │
│                                           │                  │
│                              ┌────────────┴─────────────┐   │
│                              │    chrome.storage.local  │   │
│                              │  ┌────────────────────┐  │   │
│                              │  │ factCheckResults[] │  │   │
│                              │  │ pendingChecks: n   │  │   │
│                              │  └────────────────────┘  │   │
│                              └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    │ GET /search?q=...
                                    ▼
                           ┌─────────────────┐
                           │   API Gateway   │
                           │     :8080       │
                           └─────────────────┘
```

## Data Flow

1. **User opens popup** → loads state from `chrome.storage.local`
2. **User submits query** → sends message to background worker
3. **Background worker**:
   - Increments pending counter
   - Updates badge to show "..."
   - Calls `GET /search?q=<query>`
   - On success: appends results, decrements pending, updates badge
   - Shows desktop notification
4. **Popup receives update** → re-renders results list

## Verdict Display

Results show color-coded verdict badges:

| Verdict | Color |
|---------|-------|
| True | Green |
| Mostly True | Green |
| Half True | Yellow |
| Mixed | Yellow |
| Barely True | Orange |
| Mostly False | Orange |
| False | Red |
| Pants on Fire | Red |

## Development

### Debugging

1. Open `chrome://extensions/`
2. Click **"Inspect views: service worker"** to debug `background.js`
3. Right-click the popup and select **"Inspect"** to debug popup scripts

### Reloading Changes

After modifying files:
1. Go to `chrome://extensions/`
2. Click the refresh icon on the Aletheia extension
3. Close and reopen any popup windows

## Troubleshooting

**Badge shows "..." but never updates:**
- Check that the API Gateway is running on port 8080
- Open the service worker console to check for errors

**Selected text not appearing:**
- The page must be fully loaded
- Some pages (chrome://, file://) don't allow script injection
- Try manually pasting text instead

**"Fact Check Failed" notification:**
- Verify the API Gateway is running
- Check network connectivity
- Look at the service worker console for detailed errors

**Results not persisting:**
- Chrome storage is cleared on extension reinstall
- Results are stored per browser profile

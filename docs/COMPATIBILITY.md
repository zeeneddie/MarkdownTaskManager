# Compatibility

> **[Back to README](../README.md)**

Browser and system compatibility information for Markdown Task Manager.

---

## Supported Browsers

| Browser | Minimum version | Support | Notes |
|---------|----------------|---------|-------|
| Chrome  | 86+            | Full | Recommended |
| Edge    | 86+            | Full | Recommended |
| Opera   | 72+            | Full | OK |
| Brave   | 1.17+          | Full | OK |
| Firefox | -              | Not supported | API not available |
| Safari  | -              | Not supported | API not available |

**Note:** File System Access API is required. It is not available on Firefox and Safari.

---

## Operating Systems

| OS | Support | Notes |
|----|---------|-------|
| **Windows** 10/11 | Full | All supported browsers work |
| **macOS** 10.15+ | Full | With Chrome/Edge |
| **Linux** | Full | All distributions with Chrome/Edge/Opera |
| **Chrome OS** | Full | Native support |
| iOS/iPadOS | Not supported | Safari only |
| Android | Limited | Limited browser support |

---

## Performance

| Metric | Value |
|--------|-------|
| **HTML file size** | ~144 KB (everything included, no dependencies) |
| **Loading time** | Instant (< 100ms) |
| **Parsing** | < 50ms for 1000 tasks |
| **Memory usage** | ~10 MB (for 500 tasks) |

---

## Security and Privacy

- **100% local data**: Nothing is sent to the Internet
- **No tracking**: No telemetry, no analytics
- **No account**: No authentication required
- **Explicit permissions**: User controls file access
- **Open code**: All JavaScript code is readable in HTML file
- **No CDN**: No external resources loaded
- **Offline**: Works without Internet connection

### Required permissions

The application only requests:
- **File Read/Write**: To access your Markdown files
- **IndexedDB**: To remember recent projects (local to browser)

No network, webcam, microphone or other permissions are required.

---

## Troubleshooting

### "File System Access API not supported"
- Use Chrome 86+, Edge 86+, or Opera 72+
- Firefox and Safari are not supported

### "Permission denied"
- The browser needs explicit permission to access folders
- Click "Allow" when prompted
- Some corporate policies may block this API

### Files not syncing
- Check if you're looking at the correct folder
- Try refreshing the page
- Verify the files exist on disk

---

**[Back to README](../README.md)** | **[Use Cases](./USE_CASES.md)** | **[Installation](./INSTALLATION.md)**

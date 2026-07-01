# @auris/web-sdk

Official Web SDK and drop-in embeddable widget for the **Auris Voice AI Platform**. Connect browser clients directly to real-time conversational voice agents over low-latency WebSocket / WebRTC audio streaming.

---

## 📦 Installation

Install via npm:

```bash
npm install @auris/web-sdk
```

Or import directly via CDN / script tag:

```html
<script type="module" src="https://unpkg.com/@auris/web-sdk/src/widget.js"></script>
```

---

## 🚀 Drop-In Embed Widget (`<auris-voice-widget>`)

Add the floating voice widget to any HTML page with a single custom element tag:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>My Website</title>
  <script type="module" src="./node_modules/@auris/web-sdk/src/widget.js"></script>
</head>
<body>

  <!-- Drop-In Voice Widget -->
  <auris-voice-widget
    base-url="https://api.auris.ai"
    agent-id="1"
    token="YOUR_USER_JWT_TOKEN"
    agent-name="Customer Support Assistant">
  </auris-voice-widget>

</body>
</html>
```

### Attributes
- `base-url`: Your Auris API domain (defaults to `window.location.origin`).
- `agent-id`: The numeric ID of the virtual agent.
- `token`: Valid authentication token for API access.
- `agent-name`: Human-readable title displayed inside the floating call panel.

---

## 🛠️ Programmatic Client SDK (`AurisVoiceClient`)

If you want custom UI or need precise control over call lifecycle, use the programmatic client:

```javascript
import { AurisVoiceClient } from '@auris/web-sdk';

const client = new AurisVoiceClient({
  baseUrl: 'https://api.auris.ai',
  agentId: 1,
  token: 'YOUR_USER_JWT_TOKEN',
  callerNumber: '+1234567890' // optional identifier
});

// Event Listeners
client.on('start', ({ agentId }) => {
  console.log('Call connected with agent:', agentId);
});

client.on('volume', ({ level }) => {
  // Update your custom audio visualizer (0.0 to 1.0)
  updateVisualizer(level);
});

client.on('transcript', ({ text, final }) => {
  console.log(`[Transcript ${final ? 'Final' : 'Partial'}]: ${text}`);
});

client.on('interrupted', () => {
  console.log('User interrupted agent speaking.');
});

client.on('end', () => {
  console.log('Call ended.');
});

client.on('error', ({ message }) => {
  console.error('Call error:', message);
});

// Start Call (requests mic access)
await client.start({ customContext: 'page_checkout' });

// Toggle Mute
client.setMuted(true);

// Send DTMF Digit
client.sendDTMF('1');

// Hang Up
client.stop();
```

---

## 📄 License
MIT License © Auris Voice AI Platform

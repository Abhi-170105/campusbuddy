# CampusBuddy as a phone app (PWA)

CampusBuddy is a Progressive Web App: open it in a phone browser and install it.
It gets its own home-screen icon, opens full screen, and still opens without internet.

## Files
| File | What it does |
|---|---|
| `manifest.webmanifest` | The app's "ID card": name, icons, colours, opens full screen (`display: standalone`) |
| `sw.js` | Service worker: a background script that saves the app shell so it opens offline. API data (profiles, events, chatbot) is never cached, it is always live |
| `offline.html` | Shown if the app was never opened before and there is no internet |
| `icons/` | App icons (192, 512, a maskable 512 for Android, 180 for iPhone) |
| `index.html` | Adds the manifest, iPhone tags, the "Install app" button and service worker registration |
| `backend/main.py` | Serves these files from the site root (`/sw.js`, `/manifest.webmanifest`, `/icons/...`) |

## Run it on a phone
Phones can only install over HTTPS, and they cannot open the laptop's `127.0.0.1`.
Use a free Cloudflare tunnel (no account needed):

1. Start the app: `python run.py`
2. In a second terminal (first time only: `winget install Cloudflare.cloudflared`):
   `cloudflared tunnel --url http://localhost:8000`
3. It prints a link like `https://something.trycloudflare.com`. Open it on the phone.
   The link works only while both terminals keep running, and it changes each time.

## Install
- **Android (Chrome):** tap **Install app** in the header, or menu (three dots) > **Install app**.
- **iPhone (Safari):** tap **Share** > **Add to Home Screen**. (Tapping **Install app** shows this tip.)

## Updating
After changing `index.html`, change `VERSION` in `sw.js` (for example `campusbuddy-v2`)
so phones drop the old saved copy.

## Viva in one breath
"The manifest tells the phone how to install it, the service worker caches the app shell so it
opens offline, and API data is always fetched live so attendee lists and privacy settings are
never stale. It is one codebase for laptop and phone, served by the same FastAPI backend."

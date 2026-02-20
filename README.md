# SonosPlay

A simple Python GUI app to play local MP3 files through Sonos speakers on your network.

## Requirements

- Python 3.10+
- Your computer and Sonos speakers must be on the same Wi-Fi network

## Installation

```bash
pip install soco
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 sonosplay.py
```

1. **Select an MP3** — Click "Browse…" to pick a file from your computer
2. **Pick a speaker** — Choose from the list of discovered Sonos speakers (click "Refresh Speakers" to re-scan)
3. **Play** — Click "▶ Play" to start playback
4. **Stop** — Click "■ Stop" to stop playback

## How it works

Sonos speakers can only play audio from a URL, not directly from a local file. When you hit Play, the app:

1. Starts a lightweight HTTP server on your machine
2. Serves the selected MP3 on a random port
3. Tells the Sonos speaker to stream from that URL

The server runs only while playback is active and shuts down when you stop.

## Troubleshooting

- **No speakers found** — Make sure your computer is on the same network as your Sonos speakers and that no firewall is blocking UDP port 1400.
- **Playback doesn't start** — Check that your firewall allows incoming connections on random high ports (the local HTTP server needs to be reachable by the speaker).

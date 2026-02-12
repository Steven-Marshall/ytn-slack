# YTN Slack Bot

Summarize YouTube videos in Slack with `/ytsummary`.

## How It Works

```
User → Slack → n8n webhook → transcript-service → Ollama → Slack response
                   ↓
            immediate "processing" ack
```

1. User types `/ytsummary` in any Slack channel
2. n8n receives webhook, immediately acknowledges with "Summarizing video..."
3. Transcript service fetches video metadata and transcript from YouTube
4. Ollama runs 2-stage summarization (extract key info → format for Slack)
5. Summary posted back to the channel

## Usage

```
/ytsummary                              # Short summary of most recent YouTube video in channel
/ytsummary <https://youtube.com/...>    # Short summary of specific video
/ytsummary <https://youtube.com/...> medium   # Medium-detail summary
/ytsummary <https://youtube.com/...> long     # Comprehensive section-by-section breakdown
/ytsummary medium                       # Medium summary of most recent video in channel
/ytsummary long                         # Long summary of most recent video in channel
```

### Summary Levels

| Level | Output | Details |
|-------|--------|---------|
| `short` (default) | TLDR + 3-4 bullets | Under 300 words. Uses first 15k chars of transcript. |
| `medium` | TLDR + 5-8 detailed bullets | 300-800 words. Uses up to 50% of transcript (cap 40k chars). |
| `long` | TLDR + sectioned breakdown | 500-1500 words. Uses full transcript (cap 80k chars). |

**Note:** Slack unfurls (expands) URLs automatically. To pass a URL directly, wrap it in angle brackets `<url>` to prevent unfurling.

## Components

| File | Purpose |
|------|---------|
| `app.py` | Flask API - fetches transcripts/metadata from YouTube |
| `Dockerfile` | Python container with youtube_transcript_api |
| `docker-compose.yml` | Container config |
| `n8n-workflow.json` | n8n workflow to import |
| `slack-app-manifest.yml` | Slack app configuration template |

---

## Setup Guide

### Prerequisites

- Docker and docker-compose
- n8n instance (self-hosted or cloud)
- Ollama with a model installed (default: `gpt-oss:20b-128k`)
- Slack workspace admin access

### Step 1: Deploy Transcript Service

```bash
cd slack-bot

# If using Docker networking, ensure your n8n network exists
# Edit docker-compose.yml to match your network name

# Start the service
docker-compose up -d

# Verify it's running
curl http://localhost:5001/health
# Should return: {"status":"ok"}
```

**Network configuration:**

The `docker-compose.yml` connects to an external Docker network so n8n can reach it. Update the network name to match your setup:

```yaml
networks:
  your-n8n-network:
    external: true
```

### Step 2: Import n8n Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `n8n-workflow.json`

**Configure the workflow:**

1. **Ollama nodes** - Update the URL if Ollama is on a different host:
   - `http://localhost:11434` - Ollama on same host
   - `http://172.17.0.1:11434` - Ollama on Docker host (from container)
   - `http://host.docker.internal:11434` - Docker Desktop

2. **Transcript service** - Update URL if using different hostname:
   - Default: `http://ytn-transcript:5001` (Docker network name)

3. **Create Slack credential:**
   - Go to n8n **Credentials** → **Add** → **Header Auth**
   - Name: `Slack YTN Bot Token`
   - Header Name: `Authorization`
   - Header Value: `Bearer xoxb-your-slack-bot-token`

4. **Activate** the workflow

### Step 3: Create Slack App

**Option A: Use manifest (recommended)**

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From an app manifest**
3. Select your workspace
4. Paste contents of `slack-app-manifest.yml`
5. **Update the webhook URL** to your n8n host
6. Click **Create**
7. Go to **Install App** → **Install to Workspace**
8. Copy the **Bot User OAuth Token** (starts with `xoxb-`) for the n8n credential

**Option B: Manual setup**

1. Create app at https://api.slack.com/apps → **From scratch**
2. Add slash command `/ytsummary` pointing to `https://YOUR-N8N-HOST/webhook/slack-ytn`
3. Add bot scopes: `commands`, `chat:write`, `channels:history`
4. Install to workspace

### Step 4: Test

In any Slack channel:
```
/ytsummary
```
(With a YouTube URL posted recently in the channel)

---

## Troubleshooting

### "No YouTube URL found" error
- Post a YouTube URL in the channel first, then run `/ytsummary`
- Or use angle brackets: `/ytsummary <https://youtube.com/watch?v=...>`

### Summary never arrives
1. Check n8n execution history for errors
2. Verify transcript service is reachable from n8n
3. Check Ollama is running: `curl http://localhost:11434/api/tags`

### Transcript service not starting
```bash
docker logs ytn-transcript
```

---

## Customization

### Change Ollama model

Edit the "Prepare Stage 1 Request" and "Prepare Stage 2 Request" nodes in n8n:
```javascript
model: "your-model-name"
```

### Adjust summary prompts

Edit the prompt text in the same nodes to customize:
- What information is extracted (Stage 1)
- How the Slack message is formatted (Stage 2)

---

## API Reference

### GET /transcript

| Param | Description |
|-------|-------------|
| `v` | Video ID or full URL (required) |
| `timestamps` | `true` for `[M:SS]` format (optional) |

### GET /metadata

| Param | Description |
|-------|-------------|
| `v` | Video ID or full URL (required) |

### GET /health

Returns `{"status":"ok"}` if service is running.

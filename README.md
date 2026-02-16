# App Store Connect API Skill

An opencode skill for interacting with App Store Connect API.

## Features

- **getappid**: Get numeric app ID from bundle ID
- **reviews**: Fetch App Store reviews
- **response**: Submit responses to reviews

## Setup

1. Clone this skill to your opencode skills directory:
   ```bash
   cp -r appstore ~/.config/opencode/skills/
   ```

2. Configure your App Store Connect API credentials:
   ```bash
   cd ~/.config/opencode/skills/appstore
   python setup_config.py
   ```

   Or copy `config.example.json` to `config.json` and fill in your credentials:
   ```json
   {
     "key_id": "YOUR_KEY_ID",
     "issuer_id": "YOUR_ISSUER_ID",
     "private_key_path": "~/path/to/your/cs.p8"
   }
   ```

3. Get your API credentials from [App Store Connect](https://appstoreconnect.apple.com):
   - Create an API key with "Customer Reviews" access
   - Download the .p8 file
   - Note your Key ID and Issuer ID

## Usage

### Get App ID

Find numeric app ID from bundle ID:
```bash
python appstore.py getappid com.example.yourapp
```

### Fetch Reviews

```bash
python fetch_reviews.py reviews 1234567890
python fetch_reviews.py reviews 1234567890 5  # 5 reviews
```

### Respond to Review

```bash
python submit_response.py 00000046-ea46-3002-cf40-2d5b00000000 "Thank you for your feedback!"
```

## With opencode

If using with opencode agent, just describe what you want:

```
Get latest App Store reviews for my app
```

The agent will use this skill automatically.

## Important Notes

- **Response attribute**: When submitting responses, use `responseBody` NOT `body` (will cause 409 error otherwise)
- Responses appear on App Store after ~24 hours
- Only one response per review allowed

## Files

| File | Description |
|------|-------------|
| `appstore.py` | Main skill - getappid command |
| `fetch_reviews.py` | CS subskill - reviews command |
| `submit_response.py` | CS subskill - response command |
| `setup_config.py` | Interactive configuration setup |
| `config.example.json` | Configuration template |
| `SKILL.md` | Skill definition for opencode |

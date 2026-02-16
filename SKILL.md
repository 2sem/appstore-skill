---
name: appstore
subskill: cs
description: "App Store Connect API skill. Main skill provides getappid command. CS subskill handles reviews and responses."
---

# App Store Skill

## Skill Level Commands

These commands are available at the main `appstore` skill level:

### `getappid {bundle_id}`

Get numeric app ID from bundle ID.

**Usage:**
```
getappid com.credif.relatedstocks
```

**Output:**
```
App Name: Your App Name
Bundle ID: com.example.yourapp
Numeric App ID: 1234567890
```

---

## CS Subskill Commands

The `cs` subskill handles customer support tasks:

### `reviews {app_id} {count?}`

Fetch the latest N reviews from App Store Connect. Default count is 1.

**Note**: If you don't know the app ID, first use the main `appstore` skill with `getappid {bundle_id}`.

**First Run (Initial Setup):**
On first use, run `python setup_config.py` to configure:
1. **Private Key Path** - Path to your .p8 file
2. **Issuer ID** - Your App Store Connect Issuer ID
3. **Key ID** - Your API Key ID

Config is saved to `{skill_path}/config.json`.

**Example:**
```
reviews 1234567890 5
reviews 1234567890
```

### `response {review_id}`

Submit a response to a specific review.

**Usage:**
```
response 00000046-ea46-3002-cf40-2d5b00000000
```

The agent will prompt you for the response text interactively.

---

## Skill Structure

| Level | Commands | Script |
|-------|----------|--------|
| Main skill (`appstore`) | `getappid` | `appstore.py` |
| CS subskill (`appstore cs`) | `reviews`, `response` | `fetch_reviews.py`, `submit_response.py` |

---

## Workflow

### When you don't know the App ID:

If you don't know the numeric app ID, you must first use the main `appstore` skill to get it:

1. **Call main skill**: Use `appstore` skill with `getappid {bundle_id}` command
2. **Get app ID**: The main skill returns the numeric app ID
3. **Use in CS**: Pass the app ID to `reviews` command in cs subskill

Example:
```
# Step 1: Get app ID from bundle ID (main skill)
getappid com.credif.relatedstocks
→ Returns: Numeric App ID: 1234567890

# Step 2: Fetch reviews using the app ID (cs subskill)
reviews 1234567890
```

### Full Workflow:

1. **First Run**: Run `python setup_config.py` to configure credentials
2. **Get App ID**: If unknown, call main `appstore` skill → `getappid {bundle_id}`
3. **Fetch Reviews**: `reviews {app_id}` in cs subskill
4. **Respond**: `response {review_id}` in cs subskill
5. **Report**: If review contains feature request/bug, pass to reporter subskill

### Submitting Review Responses

**IMPORTANT**: When submitting a response to a review, you MUST use `responseBody` NOT `body`.

**Wrong** (will cause 409 error):
```python
"attributes": {
    "body": "Thank you for your feedback!"  # WRONG!
}
```

**Correct**:
```python
"attributes": {
    "responseBody": "Thank you for your feedback!"  # CORRECT!
}
```

### Endpoint for Response Submission

```
POST https://api.appstoreconnect.apple.com/v1/customerReviewResponses
Content-Type: application/json
Authorization: Bearer {token}
```

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 409 Conflict | Using `body` instead of `responseBody` | Change to `responseBody` in payload |
| 401 Unauthorized | Expired or invalid JWT token | Regenerate token before each request |
| 404 Not Found | Invalid app ID or review ID | Verify IDs are correct |
| 403 Forbidden | Missing permissions | Ensure API key has Customer Reviews permission |

---

## Response Templates

### Positive Review Response (Korean)
```
좋은 평가 해주셔서 감사합니다! {app_name}을 사랑해 주셔서 감사합니다.
```

### Feature Request Response (Korean)
```
{name} 관련 의견 주셔서 감사합니다. 앞으로의 업데이트에 반영하도록 하겠습니다.
```

### Bug Report Response (Korean)
```
불편을 끼쳐드려 죄송합니다. 문제를 파악하여 최대한 빠르게 수정하겠습니다.
```

### General Thank You Response
```
피드백 주셔서 감사합니다. 더 나은 앱이 되도록 노력하겠습니다!
```

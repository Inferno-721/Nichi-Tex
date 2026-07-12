# Gmail MCP Setup (Official Google Server)

Goal: connect the **official Google Gmail MCP server** so Claude can create
personalized cold-email **drafts** in your Gmail (shubham05373@gmail.com).

The server is **remote** (hosted by Google) — there's no package to install.
You connect it as a **custom connector in claude.ai**, exactly like your existing
Google Drive connector. Once connected there, its tools appear automatically in
this Claude Code session.

- Server URL: `https://gmailmcp.googleapis.com/mcp/v1`
- Draft tool exposed: `create_draft` (also `list_drafts`, `search_threads`, labels, etc.)

---

## Step 1 — Google Cloud: enable the APIs

You need the `gcloud` CLI installed and initialized, then run:

```powershell
gcloud services enable gmail.googleapis.com --project=PROJECT_ID
gcloud services enable gmailmcp.googleapis.com --project=PROJECT_ID
```

(Replace `PROJECT_ID` with your Google Cloud project id. You can also enable both
APIs from the Console UI under **APIs & Services → Library**.)

## Step 2 — Configure the OAuth consent screen

Google Cloud Console → **Google Auth Platform → Branding**:

- App name: `Gmail MCP Server`
- Audience: **External** (add `shubham05373@gmail.com` as a test user) or Internal
- Add these scopes:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.compose`  ← required to create drafts

## Step 3 — Create the OAuth 2.0 client

Google Auth Platform → **Clients → Create Client**:

- Application type: **Web application**
- Authorized redirect URI (Claude):
  ```
  https://claude.ai/api/mcp/auth_callback
  ```
- Click Create, then **copy the Client ID and Client Secret**.

## Step 4 — Add the connector in claude.ai

In **claude.ai → Settings → Connectors → Add custom connector**:

- Name: `Gmail`
- Remote URL: `https://gmailmcp.googleapis.com/mcp/v1`
- Open **Advanced settings** and paste the OAuth **Client ID** and **Client Secret**
- Save, then click **Connect** and complete the Google sign-in as
  **shubham05373@gmail.com**, granting the requested permissions.

## Step 5 — Make the tools visible here

After it shows **Connected** in claude.ai, reload this Claude Code session (or
toggle the connector) so the Gmail tools sync. You'll know it worked when a tool
named like `create_draft` (namespaced `mcp__claude_ai_Gmail__create_draft`)
becomes available.

---

## After setup

Tell me it's connected. I will then:
1. Use the resume you upload via the frontend (parsed by this project) for your background.
2. Generate a personalized subject + body for each of the 63 contacts in the CSV
   (`DECAGON AND ATOMICWORK EMAILS.csv`), tailored to their name, role, and company.
3. Create each one as a Gmail **draft** via the `create_draft` tool — nothing is sent.

# Lockr Quick Start Guide

This guide will walk you through installing Lockr, creating your first vault, storing secrets, and generating a compliance report.

**Time required:** 10 minutes

---

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Terminal/command line access

---

## Step 1: Install Lockr

```bash
# Install from PyPI (recommended)
pip install lockr

# Or install from source
git clone https://github.com/yourusername/lockr.git
cd lockr
pip install -e .

# Verify installation
lockr --version
```

**Expected output:**
```
lockr, version 0.1.0
```

---

## Step 2: Initialize Your Vault

```bash
# Create a new directory for your secrets
mkdir my-secrets
cd my-secrets

# Initialize a production vault
lockr init --env prod
```

**Expected output:**
```
✓ Vault initialized in .vault/
✓ Environment: prod
✓ Master key generated

⚠️  SAVE THIS MASTER KEY SECURELY:
VAULT_MASTER_KEY=mk_1a2b3c4d5e6f7g8h9i0j...

You need this key to decrypt your vault.
Store it in a password manager or secure location.
```

**Important:** Copy the `VAULT_MASTER_KEY` value - you'll need it for all operations!

---

## Step 3: Set Your Master Key

Export the master key as an environment variable:

```bash
# Replace with your actual key from Step 2
export VAULT_MASTER_KEY=mk_1a2b3c4d5e6f7g8h9i0j...

# Add to your shell profile for persistence
echo 'export VAULT_MASTER_KEY=mk_...' >> ~/.bashrc  # or ~/.zshrc
```

**Tip:** For production, use a secrets manager or environment variable service instead of shell exports.

---

## Step 4: Store Your First Secret

```bash
# Store a database password
lockr set myapp/db_password "SuperSecretPassword123"

# Store an API key
lockr set myapp/stripe_key "sk_test_abc123xyz456"

# Store a secret (will prompt for value)
lockr set myapp/github_token
# Enter value when prompted (hidden input)
```

**Expected output:**
```
✓ Set myapp/db_password
✓ Set myapp/stripe_key
✓ Set myapp/github_token
```

---

## Step 5: Retrieve Secrets

```bash
# Get a specific secret
lockr get myapp/db_password

# List all secrets in a namespace
lockr list myapp/
```

**Expected output:**
```
SuperSecretPassword123

myapp/db_password
myapp/stripe_key
myapp/github_token
```

---

## Step 6: Create Multiple Environments

```bash
# Create and switch to staging environment
lockr checkout staging

# Store staging-specific secrets
lockr set myapp/db_password "StagingPassword456"
lockr set myapp/api_url "https://api-staging.example.com"

# Switch back to production
lockr checkout prod

# Verify production secrets are unchanged
lockr get myapp/db_password
```

**Expected output:**
```
SuperSecretPassword123  (production value, not staging)
```

---

## Step 7: Promote Secrets Between Environments

```bash
# Merge all staging secrets into production
lockr merge staging prod

# This copies all secrets from staging → prod
# You'll be prompted to confirm
```

---

## Step 8: Create Access Tokens

```bash
# Create a token for your application
lockr token create \
  --scope "myapp/*" \
  --ttl 30d \
  --label "production-app"

# List active tokens
lockr token list
```

**Expected output:**
```
✓ Token created: tk_a1b2c3d4e5f6g7h8
  Scope: myapp/*
  Expires: 2024-04-15T10:30:00Z
  Label: production-app

Token ID         Scope        Expires              Label
────────────────────────────────────────────────────────
tk_a1b2c3...     myapp/*      2024-04-15 10:30     production-app
```

---

## Step 9: Check Compliance (SOC-2)

```bash
# Run a SOC-2 compliance check
lockr compliance check --framework soc2

# Generate a detailed report
lockr compliance report \
  --framework soc2 \
  --format json \
  --output soc2-report.json

# Generate a PDF report for auditors
lockr compliance report \
  --framework soc2 \
  --format pdf \
  --output soc2-evidence.pdf
```

**Expected output:**
```
Framework: SOC-2 Trust Services Criteria 2020
Controls Checked: 7

✓ CC6.1 - Logical Access Controls: PASS
✓ CC6.6 - Token Revocation: PASS
✓ CC6.7 - Encryption at Rest: PASS
✓ CC7.2 - Audit Log Integrity: PASS
✓ CC6.8 - Environment Separation: PASS
✓ A.9.2.1 - Admin Access Controls: PASS
⚠ CC6.2 - Multi-Factor Authentication: MANUAL REVIEW

Compliance Score: 86%
Passed: 6 | Failed: 0 | Manual: 1
```

---

## Step 10: View Audit Logs

```bash
# View recent activity
lockr audit tail --n 20

# Verify audit chain integrity
lockr audit verify

# Check for suspicious activity
lockr audit anomalies --since 24h
```

**Expected output:**
```
2024-03-15 10:30:45 | admin | secret_write | myapp/db_password | success
2024-03-15 10:31:12 | admin | secret_read  | myapp/db_password | success
2024-03-15 10:35:00 | admin | token_create | production-app    | success

✓ Audit chain intact (500 entries verified)
✓ No anomalies detected in the last 24 hours
```

---

## Step 11: Inject Secrets into Applications

```bash
# Run a Python script with secrets as environment variables
lockr run --namespace myapp -- python app.py

# Run any command with secrets injected
lockr run --namespace myapp -- npm start

# Secrets are automatically transformed:
# myapp/db_password → MYAPP_DB_PASSWORD
# myapp/api_key → MYAPP_API_KEY
```

**In your application (app.py):**
```python
import os

# Secrets are available as environment variables
db_password = os.environ['MYAPP_DB_PASSWORD']
api_key = os.environ['MYAPP_API_KEY']

print(f"Connected to database with password: {db_password[:5]}...")
```

---

## Step 12: Rotate Secrets

```bash
# Manually rotate a secret
lockr rotate secret myapp/api_key --generate --length 32 --reason "quarterly-rotation"

# View rotation history
lockr rotate history myapp/api_key

# Rollback if needed
lockr rotate rollback myapp/api_key 1
```

---

## Step 13: Prevent Secret Leaks

```bash
# Install pre-commit hook to scan for hardcoded secrets
lockr guard install

# Manually scan your codebase
lockr scan --path ./src --exit-code

# Now try to commit a file with a secret:
echo 'API_KEY="sk-abc123"' > config.py
git add config.py
git commit -m "add config"

# ✗ Commit blocked! Secret detected.
```

---

## Step 14: Start the API Server

```bash
# Start the REST API server
uvicorn server.main:app --reload

# In another terminal, test the API
curl http://localhost:8000/health

# Use your token to access secrets via API
curl -H "Authorization: Bearer tk_..." \
  http://localhost:8000/secrets/myapp/db_password
```

---

## Next Steps

Congratulations! You've completed the Lockr quick start. Here's what to explore next:

### Production Deployment
- [Deployment Guide](DEPLOYMENT.md) - Docker, Kubernetes, systemd
- [API Reference](API.md) - Full REST API documentation
- [Security Best Practices](SECURITY.md) - Hardening your vault

### Advanced Features
- **Secret Rotation Policies** - Automate rotation based on age
- **Custom Compliance Frameworks** - Upload your own framework definitions
- **Natural Language Interface** - `lockr ask "show me production secrets"`
- **Remote Vault Sync** - Git-style push/pull (coming soon)

### Common Tasks
```bash
# Backup your vault
tar -czf vault-backup.tar.gz .vault/

# Delete a secret
lockr delete myapp/old_key --yes

# Revoke a token
lockr token revoke tk_abc123

# Check vault status
lockr status
```

---

## Troubleshooting

### "Vault not initialized"
```bash
# Solution: Run lockr init first
lockr init --env prod
```

### "Master key not set"
```bash
# Solution: Export your master key
export VAULT_MASTER_KEY=mk_...
```

### "Token expired"
```bash
# Solution: Create a new token
lockr token create --scope "*" --ttl 30d
```

### "Permission denied"
```bash
# Solution: Check token scope
lockr token list
# Create token with correct scope
lockr token create --scope "myapp/*"
```

---

## Getting Help

- **Documentation**: [GitHub Wiki](https://github.com/yourusername/lockr/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/lockr/issues)
- **Email**: hello@lockr.dev
- **Community**: [Discord](https://discord.gg/lockr)

---

## What You've Learned

✅ Install and initialize Lockr
✅ Store and retrieve secrets
✅ Manage multiple environments
✅ Create access tokens
✅ Generate compliance reports
✅ Audit secret access
✅ Inject secrets into applications
✅ Rotate secrets safely
✅ Prevent credential leaks
✅ Use the REST API

**You're now ready to use Lockr in production!**

---

**Need more help?** Check out the [full documentation](https://github.com/yourusername/lockr/wiki) or join our [Discord community](https://discord.gg/lockr).

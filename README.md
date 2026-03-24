# 🔐 Lockr

**Git-style secrets manager with post-quantum encryption and automated SOC-2 compliance reports**

Lockr combines the simplicity of Git with enterprise-grade security. Store secrets safely, manage access with tokens, and generate compliance reports with a single command.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

- **Git-Style Workflow** - Familiar commands: `lockr checkout prod`, `lockr merge staging prod`
- **Post-Quantum Encryption** - FrodoKEM-1344-SHAKE + AES-256-GCM envelope encryption
- **Automated Compliance** - Generate SOC-2/ISO 27001 reports with `lockr compliance check`
- **Token-Based RBAC** - Fine-grained access control with namespace scoping
- **Tamper-Evident Audit Log** - Hash-chained audit trail with anomaly detection
- **Secret Rotation** - Automated rotation policies with version history
- **Secret Scanning** - Pre-commit hooks to prevent credential leaks
- **Natural Language Interface** - `lockr ask "show me production secrets"`
- **Zero-Code Injection** - `lockr run --namespace myapp -- python app.py`

---

## 🚀 Quick Start

### Installation

```bash
# From source (currently)
git clone https://github.com/balakumaran1507/Lockr.git
cd Lockr
pip install -e .

# From PyPI (coming soon)
# pip install lockr
```

### Basic Usage

```bash
# Initialize a vault
lockr init --env prod

# Set your master key (from init output)
export VAULT_MASTER_KEY=<your-master-key>

# Store a secret
lockr set myapp/db_password "SuperSecret123"

# Retrieve a secret
lockr get myapp/db_password

# List secrets in a namespace
lockr list myapp/

# Switch environments
lockr checkout staging
lockr set myapp/api_key "staging-key"

# Promote staging secrets to production
lockr merge staging prod

# Generate compliance report
lockr compliance check --framework soc2
```

---

## 📚 Core Concepts

### Environments

Like Git branches, Lockr uses environments to isolate secrets:

```bash
lockr init --env prod      # Create production environment
lockr checkout staging     # Switch to staging
lockr checkout dev         # Switch to development
```

### Namespaces

Organize secrets by application or team:

```bash
lockr set myapp/db_password "secret1"
lockr set myapp/api_key "secret2"
lockr set billing/stripe_key "secret3"
```

### Access Tokens

Create scoped tokens for applications and team members:

```bash
# Create a token with namespace access
lockr token create --scope "myapp/*" --ttl 24h --label "dev-team"

# Revoke a token
lockr token revoke tk_abc123

# List all active tokens
lockr token list
```

---

## 🔒 Security Features

### Post-Quantum Encryption

Lockr uses FrodoKEM-1344-SHAKE for key encapsulation, protecting against quantum computer attacks:

```bash
# Install post-quantum support (optional)
brew install liboqs  # macOS
pip install lockr[pq]
```

Without `liboqs`, Lockr falls back to X25519 (classical Diffie-Hellman).

### Tamper-Evident Audit Log

Every operation is logged in a hash-chained audit log:

```bash
# View recent activity
lockr audit tail --n 50

# Verify chain integrity
lockr audit verify

# Detect anomalies
lockr audit anomalies --since 24h
```

### Secret Scanning

Prevent credential leaks with pre-commit hooks:

```bash
# Install git hook
lockr guard install

# Manually scan files
lockr scan --path . --exit-code

# Bypass when needed
LOCKR_SKIP=1 git commit -m "safe commit"
```

---

## 📊 Compliance Automation

Generate SOC-2 and ISO 27001 compliance reports automatically:

```bash
# Check SOC-2 compliance
lockr compliance check --framework soc2

# Generate detailed report
lockr compliance report --framework soc2 --format json --output soc2_report.json

# Check ISO 27001 compliance
lockr compliance check --framework iso27001

# Upload custom framework
lockr compliance upload ./custom-framework.json
```

### Automated Controls Checked

- ✅ CC6.1 - Logical access controls (token scoping)
- ✅ CC6.6 - Token revocation capability
- ✅ CC6.7 - Encryption at rest (AES-256-GCM)
- ✅ CC7.2 - Audit log integrity (hash chain)
- ✅ CC6.8 - Environment separation
- ✅ A.9.2.1 - Admin access controls

---

## 🔄 Secret Rotation

### Manual Rotation

```bash
# Rotate a secret with auto-generation
lockr rotate secret myapp/api_key --generate --length 32 --reason "quarterly-rotation"

# View rotation history
lockr rotate history myapp/api_key

# Rollback to previous version
lockr rotate rollback myapp/api_key 1 --yes
```

### Rotation Policies

```bash
# Set rotation policy for a namespace
lockr rotate policy myapp/ --max-age 90d

# Check which secrets need rotation
lockr rotate status myapp/
```

---

## 💻 CLI Commands

### Vault Operations

| Command | Description |
|---------|-------------|
| `lockr init --env <env>` | Initialize a new vault |
| `lockr status` | Show vault status and current environment |
| `lockr set <key> [value]` | Store a secret (prompts if value omitted) |
| `lockr get <key>` | Retrieve a secret |
| `lockr delete <key>` | Delete a secret |
| `lockr list [namespace]` | List all secrets in a namespace |
| `lockr checkout <env>` | Switch to a different environment |
| `lockr merge <src> <dst>` | Promote secrets from src to dst environment |

### Access Control

| Command | Description |
|---------|-------------|
| `lockr token create` | Create an access token |
| `lockr token revoke <id>` | Revoke a token |
| `lockr token list` | List all active tokens |

### Audit & Compliance

| Command | Description |
|---------|-------------|
| `lockr audit tail` | View audit log |
| `lockr audit verify` | Verify audit chain integrity |
| `lockr audit anomalies` | Detect suspicious activity |
| `lockr compliance check --framework <name>` | Run compliance check |
| `lockr compliance report` | Generate compliance report |
| `lockr compliance list` | List available frameworks |

### Secret Management

| Command | Description |
|---------|-------------|
| `lockr rotate secret <key>` | Rotate a secret |
| `lockr rotate policy <namespace>` | Set rotation policy |
| `lockr rotate status <namespace>` | Check rotation status |
| `lockr rotate history <key>` | View rotation history |
| `lockr run --namespace <ns> -- <cmd>` | Inject secrets as env vars |

### Security Tools

| Command | Description |
|---------|-------------|
| `lockr scan` | Scan for hardcoded secrets |
| `lockr guard install` | Install pre-commit hook |
| `lockr guard uninstall` | Remove pre-commit hook |
| `lockr ask <query>` | Natural language interface |

---

## 🌐 REST API

Lockr includes a FastAPI server for HTTP access:

```bash
# Start the API server
uvicorn server.main:app --host 0.0.0.0 --port 8000

# Or use Docker
docker run -p 8000:8000 -v $(pwd)/.vault:/app/.vault lockr/lockr
```

### API Examples

```bash
# Health check
curl http://localhost:8000/health

# Create a secret (requires token)
curl -X PUT http://localhost:8000/secrets/myapp/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "secret-value"}'

# Read a secret
curl http://localhost:8000/secrets/myapp/test \
  -H "Authorization: Bearer $TOKEN"

# Run compliance check
curl http://localhost:8000/compliance/check/soc2 \
  -H "Authorization: Bearer $TOKEN"
```

See [API Documentation](docs/API.md) for full reference.

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Using Docker Compose
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

---

## 📖 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Step-by-step tutorial
- [API Reference](docs/API.md) - REST API documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Architecture](docs/ARCHITECTURE.md) - How Lockr works internally

---

## 🏢 Use Cases

### Startups Seeking SOC-2 Certification

```bash
# Initialize vault for compliance
lockr init --env production

# Generate SOC-2 evidence
lockr compliance check --framework soc2
lockr compliance report --framework soc2 --format pdf --output soc2-evidence.pdf

# Hand the PDF to your auditor ✅
```

### DevOps Teams Managing Secrets

```bash
# Different environments
lockr checkout dev
lockr set myapp/db_url "postgres://dev.internal"

lockr checkout staging
lockr set myapp/db_url "postgres://staging.internal"

lockr checkout prod
lockr set myapp/db_url "postgres://prod.internal"

# Inject secrets into applications
lockr run --namespace myapp -- python app.py
```

### Security Teams Preventing Credential Leaks

```bash
# Install pre-commit hook across all repos
lockr guard install

# Scan existing codebases
lockr scan --path ./src --exit-code

# Monitor for suspicious access
lockr audit anomalies --since 7d
```

---

## 🗺️ Roadmap

- [x] Core vault operations
- [x] Post-quantum encryption
- [x] Token-based RBAC
- [x] Tamper-evident audit log
- [x] SOC-2 compliance automation
- [x] Secret rotation
- [x] Secret scanning
- [x] REST API
- [ ] PDF compliance reports
- [ ] Remote vault sync (Git-style push/pull)
- [ ] SSO integration
- [ ] Kubernetes operator
- [ ] Auditor portal
- [ ] Multi-tenancy

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/yourusername/lockr.git
cd lockr
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linter
ruff check .
black .
```

---

## 📄 License

Lockr is open-source software licensed under the [MIT License](LICENSE).

The core secrets management features are free forever. Enterprise features (SSO, multi-tenancy, auditor portal) will be available under a commercial license.

---

## 🙋 Support

- **Documentation**: [GitHub Wiki](https://github.com/balakumaran1507/Lockr/wiki)
- **Issues**: [GitHub Issues](https://github.com/balakumaran1507/Lockr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/balakumaran1507/Lockr/discussions)

---

## ⭐ Show Your Support

If you find Lockr useful, please consider:

- Starring the repository on GitHub
- Sharing it with your team
- Contributing code or documentation
- Reporting bugs or suggesting features

---

## 🔗 Links

- **GitHub**: https://github.com/balakumaran1507/Lockr
- **Issues**: https://github.com/balakumaran1507/Lockr/issues
- **PyPI**: Coming soon
- **Docker Hub**: Coming soon

---

**Built with ❤️ by developers who are tired of paying $50k for SOC-2 compliance.**

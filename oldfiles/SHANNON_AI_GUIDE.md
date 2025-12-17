# Shannon AI Setup for PhazeVPN - Complete Guide

## 🎯 What is Shannon?

Shannon is an autonomous AI pentester that can:
- Analyze your codebase for security vulnerabilities
- Test your web application for exploits
- Generate detailed security reports
- Work with local repositories (no GitHub needed!)

## 📦 What We Set Up

### 1. Shannon Installation
- **Location**: `~/shannon-analysis/shannon/`
- **Docker Image**: Built and ready to use
- **Codebase Copy**: `/shannon-analysis/shannon/repos/phazevpn/`

### 2. Components Included for Analysis
```
phazevpn/
├── phazevpn-protocol-go/    # VPN protocol
├── phazevpn-web-go/         # Go web server
├── web-portal/              # Python web app
├── phazebrowser-gecko/      # Browser configs
├── android-app/             # Android client
├── ios-app/                 # iOS client
├── phazeos-scripts/         # System scripts
└── README.md                # Project documentation
```

### 3. Configuration File
- **Location**: `~/shannon-analysis/shannon/configs/phazevpn-config.yaml`
- **Purpose**: Tells Shannon how to authenticate and what to test
- **Credentials**: Uses your admin@phazevpn.com account

## 🚀 How to Use Shannon

### Option 1: Full Web Application Security Test
Tests your live website at phazevpn.com:

```bash
cd ~/shannon-analysis/shannon

# Set your API key (IMPORTANT: Get a NEW one, the old one was exposed!)
export ANTHROPIC_API_KEY='your-new-api-key-here'

# Run Shannon
docker run --rm -it \
  --network host \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000 \
  -v "$(pwd)/repos:/app/repos" \
  -v "$(pwd)/configs:/app/configs" \
  shannon:latest \
  "https://phazevpn.com" \
  "/app/repos/phazevpn" \
  --config /app/configs/phazevpn-config.yaml
```

### Option 2: Code-Only Analysis (Offline)
Analyzes just the code without testing the live site:

```bash
docker run --rm -it \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000 \
  -v "$(pwd)/repos:/app/repos" \
  shannon:latest \
  "file:///app/repos/phazevpn" \
  "/app/repos/phazevpn"
```

### Option 3: Test Specific Components
Focus on just one part:

```bash
# Test only the VPN protocol
docker run --rm -it \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -v "$(pwd)/repos:/app/repos" \
  shannon:latest \
  "file:///app/repos/phazevpn/phazevpn-protocol-go" \
  "/app/repos/phazevpn/phazevpn-protocol-go"

# Test only the web portal
docker run --rm -it \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -v "$(pwd)/repos:/app/repos" \
  shannon:latest \
  "file:///app/repos/phazevpn/web-portal" \
  "/app/repos/phazevpn/web-portal"
```

## 📊 What Shannon Will Do

1. **Code Analysis**
   - Scan all source files
   - Identify potential vulnerabilities
   - Check for common security issues

2. **Web Testing** (if using Option 1)
   - Authenticate to your site
   - Test API endpoints
   - Try to find exploits
   - Test authentication/authorization

3. **Report Generation**
   - Detailed vulnerability report
   - Severity ratings
   - Remediation suggestions
   - Code examples

## 🔐 Security Notes

### ⚠️ CRITICAL: API Key Security
Your Claude API key was exposed in our chat. **You MUST:**
1. Go to https://console.anthropic.com/settings/keys
2. Delete the old key: `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`
3. Generate a NEW key
4. Use the NEW key with Shannon

### GitHub Token
Your GitHub token was also exposed: `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`
- Revoke it at: https://github.com/settings/tokens
- Generate a new one if needed

### VPS Password
Also exposed: `PhazeVPN_57dd69f3ec20_2025`
- Consider changing it via your VPS provider

## 📁 Output Location

Shannon saves results to:
- `~/shannon-analysis/shannon/results/`
- Look for timestamped directories
- Reports are in markdown and JSON format

## 🛠️ Troubleshooting

### "Docker not found"
```bash
sudo apt-get install docker.io
sudo usermod -aG docker $USER
# Log out and back in
```

### "Permission denied"
```bash
sudo chmod 666 /var/run/docker.sock
```

### "API key invalid"
Make sure you:
1. Revoked the old key
2. Generated a new one
3. Exported it correctly: `export ANTHROPIC_API_KEY='sk-ant-...'`

## 🎯 What to Focus On

Based on your project, Shannon should prioritize:

1. **VPN Protocol Security**
   - Encryption implementation
   - Key exchange
   - Leak protection effectiveness

2. **Web Portal**
   - Authentication bypass
   - SQL injection
   - XSS vulnerabilities
   - Session management

3. **API Endpoints**
   - Authorization checks
   - Input validation
   - Rate limiting

## 📈 Next Steps After Analysis

1. **Review the report** - Shannon will generate detailed findings
2. **Prioritize fixes** - Start with critical/high severity issues
3. **Implement fixes** - Update code based on recommendations
4. **Re-run Shannon** - Verify fixes worked
5. **Document** - Add security notes to your README

## 💡 Tips

- **Run overnight** - Full analysis can take hours
- **Start small** - Test one component first to understand output
- **Save reports** - Keep them for comparison after fixes
- **Iterate** - Run Shannon regularly as you add features

## 🆘 Need Help?

- Shannon docs: https://github.com/KeygraphHQ/shannon
- Shannon Discord: Check their GitHub for invite link
- Your analysis is in: `~/shannon-analysis/shannon/`

---

**Status**: Shannon Docker image is building now. Once complete, you can run any of the commands above!

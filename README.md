# NX-OS VXLAN EVPN Automation Platform

A GitOps-based network automation platform for managing Cisco NX-OS switches with VXLAN EVPN fabric. This solution provides a professional web interface, pre-configuration validation, Git-based versioning, and one-click rollback capabilities.

## 🎯 Features

- ✅ **Pre-Configuration Checks**: Validates port status, MAC addresses, and current configuration before applying changes
- ✅ **GitOps Workflow**: All configurations are version-controlled with Git for full audit trail
- ✅ **One-Click Rollback**: Instantly revert to any previous configuration
- ✅ **Modern Web Interface**: React-based UI with real-time updates
- ✅ **REST API**: FastAPI backend for programmatic access
- ✅ **VXLAN EVPN Support**: Native support for VXLAN/EVPN configurations
- ✅ **Multi-Device Management**: Manage multiple spine and leaf switches
- ✅ **Configuration History**: Complete audit trail of all changes

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Saving and Running the Web Interface Locally](#saving-and-running-the-web-interface-locally)
- [API Reference](#api-reference)
- [Adding New Features](#adding-new-features)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Interface (React)                    │
│              Port Configuration | History | Rollback         │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────┴────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Pre-Check   │  │ Config Gen   │  │  GitOps Mgr  │      │
│  │   Engine     │  │   (Jinja2)   │  │  (GitPython) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ Nornir + Netmiko
┌────────────────────────┴────────────────────────────────────┐
│                    NX-OS Switches                            │
│   Spine-01  │  Spine-02  │  Leaf-01  │  Leaf-02  │ Leaf-03  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Prerequisites

### System Requirements
- Linux/macOS/Windows (WSL2 recommended for Windows)
- Python 3.9 or higher
- Git 2.0+
- Node.js 16+ (for local web interface development)
- SSH access to NX-OS switches
- Network connectivity to management network

### NX-OS Switch Requirements
- Cisco Nexus 9000 series or NX-OSv
- NX-OS 7.0(3)I7(1) or higher
- SSH enabled
- User account with appropriate privileges

## 📥 Installation

### 1. Clone or Create Project Structure

```bash
# Create project directory
mkdir nx-automation-platform
cd nx-automation-platform

# Create directory structure
mkdir -p {backend,frontend,inventory,templates,configs/devices}
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
nornir==3.4.1
nornir-netmiko==1.0.1
nornir-utils==0.2.0
netmiko==4.3.0
GitPython==3.1.40
jinja2==3.1.2
pyyaml==6.0.1
requests==2.31.0
redis==5.0.1
celery==5.3.4
python-dotenv==1.0.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### 3. Create Backend Files

Save the FastAPI backend code (provided in artifact) as `backend/main.py`

### 4. Configure Inventory

```bash
# Create inventory files
mkdir -p inventory

# inventory/hosts.yaml
cat > inventory/hosts.yaml << 'EOF'
---
spine-01:
  hostname: 10.0.1.1
  platform: nxos
  port: 22
  username: admin
  password: !vault |
    $ANSIBLE_VAULT;1.1;AES256
    # Use environment variable in production

spine-02:
  hostname: 10.0.1.2
  platform: nxos
  port: 22
  username: admin
  password: !vault |
    $ANSIBLE_VAULT;1.1;AES256

leaf-01:
  hostname: 10.0.2.1
  platform: nxos
  port: 22
  username: admin
  password: !vault |
    $ANSIBLE_VAULT;1.1;AES256

leaf-02:
  hostname: 10.0.2.2
  platform: nxos
  port: 22
  username: admin
  password: !vault |
    $ANSIBLE_VAULT;1.1;AES256

leaf-03:
  hostname: 10.0.2.3
  platform: nxos
  port: 22
  username: admin
  password: !vault |
    $ANSIBLE_VAULT;1.1;AES256
EOF

# inventory/groups.yaml
cat > inventory/groups.yaml << 'EOF'
---
spine:
  members:
    - spine-01
    - spine-02

leaf:
  members:
    - leaf-01
    - leaf-02
    - leaf-03
EOF
```

### 5. Create Configuration Templates

```bash
mkdir -p templates

# templates/access_port.j2
cat > templates/access_port.j2 << 'EOF'
interface {{ interface }}
{% if description %}
  description {{ description }}
{% endif %}
  switchport
  switchport mode access
  switchport access vlan {{ vlan }}
{% if vni %}
  vxlan
    vni {{ vni }}
{% endif %}
  no shutdown
EOF

# templates/trunk_port.j2
cat > templates/trunk_port.j2 << 'EOF'
interface {{ interface }}
{% if description %}
  description {{ description }}
{% endif %}
  switchport
  switchport mode trunk
  switchport trunk allowed vlan {{ vlan_list }}
  no shutdown
EOF
```

### 6. Initialize Git Repository

```bash
cd configs
git init
git config user.name "Network Automation"
git config user.email "automation@example.com"

# Create initial README
cat > README.md << 'EOF'
# Network Configuration Repository

This repository contains all network device configurations managed by the automation platform.

## Structure
- `devices/`: Device-specific configurations organized by hostname
- `templates/`: Jinja2 templates for configuration generation
EOF

git add README.md
git commit -m "Initial commit"
cd ..
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
cat > backend/.env << 'EOF'
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Git Configuration
CONFIG_REPO_PATH=/opt/network-configs
GIT_USER_NAME=automation
GIT_USER_EMAIL=automation@example.com

# Device Credentials (Use Vault in production!)
NXOS_USERNAME=admin
NXOS_PASSWORD=your_password_here

# Database (Optional - for NetBox integration)
NETBOX_URL=http://localhost:8080
NETBOX_TOKEN=your_token_here

# Redis (for Celery tasks)
REDIS_URL=redis://localhost:6379/0
EOF
```

### Update main.py Configuration Paths

Edit `backend/main.py` and update:
```python
CONFIG_REPO_PATH = os.getenv("CONFIG_REPO_PATH", "./configs")
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "./templates")
```

## 🚀 Usage

### Starting the Backend

```bash
cd backend
source venv/bin/activate

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or in production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Testing the API

```bash
# Check API health
curl http://localhost:8000/

# Run pre-check
curl -X POST "http://localhost:8000/api/v1/port/pre-check?device=spine-01&interface=Ethernet1/1"

# Configure a port
curl -X POST "http://localhost:8000/api/v1/port/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "device": "spine-01",
    "interface": "Ethernet1/1",
    "vlan": 100,
    "description": "Server Port - Production",
    "mode": "access"
  }'

# Get configuration history
curl http://localhost:8000/api/v1/history

# Rollback to specific commit
curl -X POST "http://localhost:8000/api/v1/rollback/a3f2d1b"
```

## 💾 Saving and Running the Web Interface Locally

### Method 1: Save as Standalone HTML File

1. **Copy the React component code** from the artifact
2. **Create a standalone HTML file:**

```bash
mkdir frontend
cd frontend
```

Create `index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NX-OS Automation Platform</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        // PASTE THE REACT COMPONENT CODE HERE
        // (The entire component from the artifact)
        
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<NXOSAutomationPortal />);
    </script>
</body>
</html>
```

3. **Open the file in your browser:**
   - Simply double-click `index.html`
   - Or run a local server: `python3 -m http.server 3000`

### Method 2: Create React App (Recommended for Development)

```bash
# Install Node.js and create React app
npx create-react-app nx-automation-ui
cd nx-automation-ui

# Install dependencies
npm install lucide-react

# Replace src/App.js with the component code
# Copy the artifact code to src/App.js

# Start development server
npm start
```

The interface will open at `http://localhost:3000`

### Method 3: Build Production Version

```bash
# After setting up with Method 2
npm run build

# Serve the production build
npx serve -s build -p 3000
```

### Connecting Frontend to Backend

Update the React component to call your actual API:

```javascript
// Add at the top of the component
const API_BASE_URL = 'http://localhost:8000';

// Update the simulatePreCheck function:
const runPreCheck = async () => {
  setIsChecking(true);
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/port/pre-check?device=${device}&interface=${port}`,
      { method: 'POST' }
    );
    const data = await response.json();
    setCheckResults(data);
  } catch (error) {
    console.error('Error:', error);
  } finally {
    setIsChecking(false);
  }
};

// Similar updates for other functions
```

## 📚 API Reference

### Endpoints

#### `GET /`
Health check and API information

#### `POST /api/v1/port/pre-check`
Run pre-configuration checks on a port

**Parameters:**
- `device` (string): Device hostname
- `interface` (string): Interface name (e.g., Ethernet1/1)

**Response:**
```json
{
  "port_exists": true,
  "admin_status": "up",
  "oper_status": "down",
  "current_config": {...},
  "mac_addresses": [],
  "recommendations": ["..."],
  "is_safe_to_configure": true
}
```

#### `POST /api/v1/port/configure`
Configure a port with validation and Git versioning

**Request Body:**
```json
{
  "device": "spine-01",
  "interface": "Ethernet1/1",
  "vlan": 100,
  "description": "Server Port",
  "mode": "access",
  "vni": 10100,
  "vrf": "prod"
}
```

**Response:**
```json
{
  "success": true,
  "commit_hash": "a3f2d1b",
  "timestamp": "2025-10-16T14:30:00",
  "applied_config": "interface Ethernet1/1...",
  "message": "Successfully configured..."
}
```

#### `GET /api/v1/history`
Get configuration history

**Parameters:**
- `device` (optional): Filter by device
- `limit` (optional, default=50): Number of commits

#### `POST /api/v1/rollback/{commit_hash}`
Rollback to a specific commit

#### `GET /api/v1/devices`
Get list of managed devices

## 🔨 Adding New Features

### 1. Adding VLAN Provisioning

**Backend (main.py):**

```python
class VlanConfigRequest(BaseModel):
    device: str
    vlan_id: int
    name: str
    vni: Optional[int] = None
    vrf: Optional[str] = None

@app.post("/api/v1/vlan/configure")
async def configure_vlan(request: VlanConfigRequest):
    config = f"""
vlan {request.vlan_id}
  name {request.name}
  vn-segment {request.vni if request.vni else request.vlan_id}
"""
    # Apply configuration...
    return {"success": True}
```

**Frontend (Add new tab):**

```javascript
// Add VLAN configuration form
const [activeTab, setActiveTab] = useState('configure');
// Add 'vlan' option

{activeTab === 'vlan' && (
  <VlanConfigurationForm />
)}
```

### 2. Adding BGP EVPN Configuration

Create new template `templates/bgp_evpn.j2`:

```jinja2
router bgp {{ asn }}
  neighbor {{ neighbor_ip }}
    remote-as {{ remote_asn }}
    address-family l2vpn evpn
      send-community extended
      route-reflector-client
```

Add endpoint:

```python
@app.post("/api/v1/bgp/configure")
async def configure_bgp_evpn(request: BgpConfigRequest):
    # Implementation
    pass
```

### 3. Adding NetBox Integration

```python
import requests

class NetBoxClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
    
    def get_device(self, name: str):
        response = requests.get(
            f"{self.url}/api/dcim/devices/?name={name}",
            headers=self.headers
        )
        return response.json()
    
    def update_interface(self, device: str, interface: str, data: dict):
        # Update interface in NetBox
        pass

# Use in endpoints
netbox = NetBoxClient(os.getenv("NETBOX_URL"), os.getenv("NETBOX_TOKEN"))
```

### 4. Adding Automated Testing

Create `tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_pre_check():
    response = client.post(
        "/api/v1/port/pre-check?device=spine-01&interface=Ethernet1/1"
    )
    assert response.status_code == 200
    assert "port_exists" in response.json()

def test_configure_port():
    payload = {
        "device": "spine-01",
        "interface": "Ethernet1/1",
        "vlan": 100,
        "mode": "access"
    }
    response = client.post("/api/v1/port/configure", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] == True
```

Run tests: `pytest tests/`

### 5. Adding Webhook Notifications

```python
from typing import Callable
import httpx

class WebhookManager:
    def __init__(self):
        self.webhooks = []
    
    def register(self, url: str):
        self.webhooks.append(url)
    
    async def notify(self, event: str, data: dict):
        async with httpx.AsyncClient() as client:
            for webhook_url in self.webhooks:
                await client.post(webhook_url, json={
                    "event": event,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })

# Use in configure endpoint
webhook_manager = WebhookManager()
await webhook_manager.notify("port_configured", {...})
```

### 6. Adding Bulk Operations

```python
class BulkConfigRequest(BaseModel):
    operations: List[PortConfigRequest]

@app.post("/api/v1/port/configure/bulk")
async def configure_ports_bulk(request: BulkConfigRequest):
    results = []
    for operation in request.operations:
        result = await configure_port(operation)
        results.append(result)
    return {"results": results}
```

## 🐛 Troubleshooting

### Common Issues

**Issue: Connection timeout to switches**
```bash
# Check connectivity
ping 10.0.1.1

# Verify SSH access
ssh admin@10.0.1.1

# Check firewall rules
sudo iptables -L
```

**Issue: Git commit errors**
```bash
# Verify Git configuration
cd configs
git config --list

# Reset if needed
git config user.name "automation"
git config user.email "automation@example.com"
```

**Issue: API not accessible from frontend**
```bash
# Check CORS settings in main.py
# Verify API is running
curl http://localhost:8000/

# Check browser console for errors
```

**Issue: Authentication failures**
```bash
# Test credentials manually
ssh admin@10.0.1.1

# Update inventory with correct credentials
vi inventory/hosts.yaml
```

## 🚀 Production Deployment

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./configs:/app/configs
      - ./inventory:/app/inventory
    environment:
      - CONFIG_REPO_PATH=/app/configs
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

Deploy:
```bash
docker-compose up -d
```

### Using Systemd

Create `/etc/systemd/system/nx-automation.service`:

```ini
[Unit]
Description=NX-OS Automation API
After=network.target

[Service]
Type=simple
User=automation
WorkingDirectory=/opt/nx-automation/backend
Environment="PATH=/opt/nx-automation/backend/venv/bin"
ExecStart=/opt/nx-automation/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nx-automation
sudo systemctl start nx-automation
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name automation.example.com;

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
    }
}
```

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nornir Documentation](https://nornir.readthedocs.io/)
- [Cisco NX-OS API Documentation](https://developer.cisco.com/docs/nx-os/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - feel free to use this in your environment

## 👥 Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation at `/docs`
- Check logs: `tail -f /var/log/nx-automation.log`

---

**Version:** 1.0.0  
**Last Updated:** October 2025  
**Maintainer:** Network Automation Team

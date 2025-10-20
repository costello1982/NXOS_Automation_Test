# 🚀 Quick Start Guide - 5 Minutes to Running

Get the NX-OS Automation Platform up and running quickly!

## Option 1: View the Web Interface Immediately (No Installation)

### Step 1: Save the HTML File

1. **Copy the standalone HTML** from the artifact titled "Standalone HTML - NX-OS Automation Portal"
2. **Save it as** `nx-automation.html` on your computer
3. **Double-click the file** - it opens in your browser!

That's it! The interface is now running locally in your browser.

### Step 2: View the Live Demo

Simply open the file and you'll see:
- ✅ Port Configuration Interface
- ✅ Pre-Check Results Display
- ✅ Configuration History
- ✅ Rollback Capabilities

**Note:** This is a demo version with simulated data. To connect to real switches, continue to Option 2.

---

## Option 2: Full Backend + Frontend (Connect to Real Switches)

### Prerequisites Check (30 seconds)

```bash
# Check Python version (need 3.9+)
python3 --version

# Check Git
git --version

# Check if you can reach your switches
ping 10.0.1.1  # Replace with your switch IP
```

### Step 1: Quick Setup (2 minutes)

```bash
# Create project
mkdir nx-automation && cd nx-automation

# Download the backend code
# (Copy from the "NX-OS Automation Backend" artifact to main.py)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn nornir nornir-netmiko netmiko GitPython pyyaml
```

### Step 2: Create Minimal Inventory (1 minute)

```bash
mkdir -p inventory

# Create hosts file
cat > inventory/hosts.yaml << 'EOF'
---
spine-01:
  hostname: 10.0.1.1  # Change to your switch IP
  platform: nxos
  username: admin
  password: YourPassword  # Change this!
EOF

# Create groups file
cat > inventory/groups.yaml << 'EOF'
---
spine:
  members:
    - spine-01
EOF
```

### Step 3: Start the Backend (30 seconds)

```bash
# Run the API server
uvicorn main:app --reload
```

**✅ Backend is running!** Open http://localhost:8000/docs to see API documentation.

### Step 4: Connect Frontend to Backend (1 minute)

Open the `nx-automation.html` file and modify the API calls to point to your backend:

```javascript
// Add this at the top of the script section
const API_URL = 'http://localhost:8000';

// Modify simulatePreCheck function to:
const simulatePreCheck = async () => {
  setIsChecking(true);
  try {
    const response = await fetch(
      `${API_URL}/api/v1/port/pre-check?device=${device}&interface=${port}`,
      { method: 'POST' }
    );
    const data = await response.json();
    setCheckResults(data);
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to connect to backend. Is it running?');
  } finally {
    setIsChecking(false);
  }
};
```

### Step 5: Test It! (30 seconds)

```bash
# Test pre-check API
curl -X POST "http://localhost:8000/api/v1/port/pre-check?device=spine-01&interface=Ethernet1/1"

# You should see JSON response with port information!
```

---

## 🎉 You're Done!

Now you have:
- ✅ Backend API running on port 8000
- ✅ Web interface showing your switches
- ✅ Ability to configure ports with pre-checks
- ✅ Git-based version control

## Next Steps

### Test Port Configuration

1. Open the web interface
2. Select a device and interface
3. Click "Run Pre-Configuration Checks"
4. Review the results
5. Apply configuration
6. Check "Configuration History" tab

### View in Browser

**Frontend:** Open `nx-automation.html` in your browser
**API Docs:** http://localhost:8000/docs
**Health Check:** http://localhost:8000/

---

## 🔧 Common Quick Fixes

### "Can't connect to switch"
```bash
# Test SSH manually
ssh admin@10.0.1.1

# Check credentials in inventory/hosts.yaml
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Check what's using port 8000
lsof -i :8000

# Or run on different port
uvicorn main:app --port 8001
```

### "CORS errors in browser"
The backend has CORS enabled by default. If you still see errors:
1. Make sure backend is running
2. Check browser console for the actual error
3. Verify the API_URL in your HTML file

---

## 📱 Mobile/Tablet Access

Access from other devices on your network:

```bash
# Find your computer's IP
ip addr show  # Linux
ipconfig      # Windows

# Start backend on all interfaces
uvicorn main:app --host 0.0.0.0 --port 8000

# Access from other devices
http://YOUR_COMPUTER_IP:8000
```

---

## 🎨 Customizing the Interface

### Change Colors
Edit the HTML file and modify Tailwind classes:
- `bg-blue-600` → `bg-purple-600` (Purple theme)
- `from-slate-900` → `from-gray-900` (Different gradient)

### Add Your Logo
Add before the `<h1>` tag:
```html
<img src="your-logo.png" alt="Logo" className="w-12 h-12" />
```

### Change Device List
In the HTML file, find:
```javascript
const devices = ['spine-01', 'spine-02', 'leaf-01'];
```
Change to your devices!

---

## 📊 Understanding What You Have

### File Structure After Setup

```
nx-automation/
├── main.py                    # Backend API server
├── nx-automation.html         # Web interface
├── venv/                      # Python virtual environment
├── inventory/
│   ├── hosts.yaml            # Your switches
│   └── groups.yaml           # Device groups
└── configs/                   # Git repo for configs
    └── devices/
        └── spine-01/
            └── Ethernet1_1.conf
```

### What Happens When You Configure a Port

1. **Pre-Check**: Queries switch via SSH
2. **Validation**: Checks if safe to configure
3. **Config Generation**: Creates NX-OS commands
4. **Git Commit**: Saves to version control
5. **Apply**: Pushes config to switch
6. **Verify**: Checks if applied successfully

---

## 🆘 Need Help?

### Check Logs
```bash
# Backend logs
# They appear in the terminal where you ran uvicorn

# Check if API is responding
curl http://localhost:8000/
```

### Test Individual Components

```bash
# Test device connectivity
python3 << 'EOF'
from netmiko import ConnectHandler
device = {
    'device_type': 'cisco_nxos',
    'host': '10.0.1.1',
    'username': 'admin',
    'password': 'YourPassword',
}
connection = ConnectHandler(**device)
print(connection.send_command('show version'))
connection.disconnect()
EOF
```

### Enable Debug Mode
```bash
# Run with more verbose logging
uvicorn main:app --reload --log-level debug
```

---

## 🎓 Learning Resources

- **API Documentation**: http://localhost:8000/docs (Interactive!)
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **Nornir Docs**: https://nornir.readthedocs.io/
- **NX-OS Commands**: Cisco NX-OS documentation

---

## ✨ Pro Tips

1. **Use Version Control**: All configs are in Git - you can see history with `git log`
2. **Test in Lab First**: Try on virtual switches before production
3. **Create Backups**: The configs/ directory is your backup
4. **Start Simple**: Begin with read-only operations (pre-checks)
5. **Add Devices Gradually**: Start with one switch, then expand

---

## 🔒 Production Checklist

Before using in production:

- [ ] Change default passwords in inventory
- [ ] Use environment variables for credentials
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up proper authentication (OAuth/LDAP)
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Create backup strategy
- [ ] Document your runbooks
- [ ] Test rollback procedures
- [ ] Train your team

---

## 🎯 What to Try First

### Beginner
1. Run pre-checks on different ports
2. View configuration history
3. Try the rollback feature (simulated)

### Intermediate
1. Configure a real port
2. Add more switches to inventory
3. Customize the interface colors

### Advanced
1. Add VLAN provisioning endpoint
2. Integrate with NetBox
3. Set up automated testing
4. Deploy with Docker

---

**Need the full documentation?** See README.md

**Want to contribute?** Check the "Adding New Features" section in README.md

**Ready to go deeper?** Check out the architecture diagrams and API reference!

---

*Happy Automating! 🚀*

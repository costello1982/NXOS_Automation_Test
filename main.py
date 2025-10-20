# main.py - FastAPI Backend for NX-OS Automation
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from nornir import InitNornir
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result
import git
import json
import os
from pathlib import Path

app = FastAPI(title="NX-OS VXLAN EVPN Automation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CONFIG_REPO_PATH = "/opt/network-configs"
TEMPLATES_DIR = "/opt/network-configs/templates"

# Pydantic Models
class PortConfigRequest(BaseModel):
    device: str
    interface: str
    vlan: Optional[int] = None
    description: Optional[str] = None
    mode: str = "access"  # access or trunk
    vni: Optional[int] = None  # For VXLAN
    vrf: Optional[str] = None

class PreCheckResponse(BaseModel):
    port_exists: bool
    admin_status: str
    oper_status: str
    current_config: Dict[str, Any]
    mac_addresses: List[str]
    recommendations: List[str]
    is_safe_to_configure: bool

class ConfigurationResponse(BaseModel):
    success: bool
    commit_hash: str
    timestamp: str
    applied_config: str
    message: str

# Initialize Nornir
def init_nornir():
    """Initialize Nornir with inventory"""
    nr = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {
                "num_workers": 10,
            },
        },
        inventory={
            "plugin": "SimpleInventory",
            "options": {
                "host_file": "inventory/hosts.yaml",
                "group_file": "inventory/groups.yaml",
            },
        },
    )
    return nr

# Git Integration
class GitOpsManager:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.ensure_repo()
    
    def ensure_repo(self):
        """Ensure Git repository exists"""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
            repo = git.Repo.init(self.repo_path)
            # Initial commit
            with open(f"{self.repo_path}/README.md", "w") as f:
                f.write("# Network Configuration Repository\n")
            repo.index.add(["README.md"])
            repo.index.commit("Initial commit")
    
    def commit_config(self, device: str, interface: str, config: str, user: str = "automation") -> str:
        """Commit configuration to Git"""
        repo = git.Repo(self.repo_path)
        
        # Create device directory if not exists
        device_dir = f"{self.repo_path}/devices/{device}"
        os.makedirs(device_dir, exist_ok=True)
        
        # Save configuration
        config_file = f"{device_dir}/{interface.replace('/', '_')}.conf"
        with open(config_file, "w") as f:
            f.write(config)
        
        # Create metadata
        metadata = {
            "device": device,
            "interface": interface,
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "config": config
        }
        
        metadata_file = f"{device_dir}/{interface.replace('/', '_')}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Git commit
        repo.index.add([config_file, metadata_file])
        commit = repo.index.commit(f"Configure {device} {interface}")
        
        return commit.hexsha[:7]
    
    def get_history(self, device: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get configuration history"""
        repo = git.Repo(self.repo_path)
        commits = []
        
        for commit in list(repo.iter_commits())[:limit]:
            commit_data = {
                "commit_hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat(),
                "author": commit.author.name,
            }
            
            if device:
                if device in commit.message:
                    commits.append(commit_data)
            else:
                commits.append(commit_data)
        
        return commits
    
    def rollback(self, commit_hash: str) -> bool:
        """Rollback to a specific commit"""
        try:
            repo = git.Repo(self.repo_path)
            repo.git.checkout(commit_hash)
            return True
        except Exception as e:
            print(f"Rollback error: {e}")
            return False

# Network Operations
class NXOSOperations:
    def __init__(self):
        self.nr = None
    
    async def pre_check_port(self, device: str, interface: str) -> PreCheckResponse:
        """Run pre-configuration checks on a port"""
        
        # Simulated for demo - in production, use actual NXAPI/Netmiko
        # commands = [
        #     f"show interface {interface}",
        #     f"show interface {interface} switchport",
        #     f"show mac address-table interface {interface}",
        #     f"show running-config interface {interface}"
        # ]
        
        # Mock response for demonstration
        return PreCheckResponse(
            port_exists=True,
            admin_status="up",
            oper_status="down",
            current_config={
                "description": "Uplink to Core",
                "vlan": "10",
                "mode": "access",
                "speed": "auto",
                "duplex": "auto"
            },
            mac_addresses=[],
            recommendations=[
                "Port is administratively up but operationally down",
                "No MAC addresses learned - safe to reconfigure",
                "Consider checking physical connectivity"
            ],
            is_safe_to_configure=True
        )
    
    def generate_config(self, request: PortConfigRequest) -> str:
        """Generate NX-OS configuration from request"""
        config_lines = [
            f"interface {request.interface}",
        ]
        
        if request.description:
            config_lines.append(f"  description {request.description}")
        
        config_lines.append(f"  switchport")
        
        if request.mode == "access":
            config_lines.append(f"  switchport mode access")
            if request.vlan:
                config_lines.append(f"  switchport access vlan {request.vlan}")
        elif request.mode == "trunk":
            config_lines.append(f"  switchport mode trunk")
            if request.vlan:
                config_lines.append(f"  switchport trunk allowed vlan {request.vlan}")
        
        # VXLAN configuration
        if request.vni:
            config_lines.append(f"  vxlan")
            config_lines.append(f"    vni {request.vni}")
        
        if request.vrf:
            config_lines.append(f"  vrf member {request.vrf}")
        
        config_lines.append(f"  no shutdown")
        
        return "\n".join(config_lines)
    
    async def apply_config(self, device: str, config: str) -> bool:
        """Apply configuration to device"""
        # In production, use Nornir with NXAPI or Netmiko
        # nr = init_nornir()
        # result = nr.filter(name=device).run(
        #     task=netmiko_send_config,
        #     config_commands=config.split('\n')
        # )
        
        # Simulate successful application
        await asyncio.sleep(2)  # Simulate network delay
        return True

# Initialize managers
git_manager = GitOpsManager(CONFIG_REPO_PATH)
nxos_ops = NXOSOperations()

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "NX-OS VXLAN EVPN Automation API",
        "version": "1.0.0",
        "endpoints": {
            "pre_check": "/api/v1/port/pre-check",
            "configure": "/api/v1/port/configure",
            "history": "/api/v1/history",
            "rollback": "/api/v1/rollback"
        }
    }

@app.post("/api/v1/port/pre-check", response_model=PreCheckResponse)
async def pre_check_port(device: str, interface: str):
    """Run pre-configuration checks on a port"""
    try:
        result = await nxos_ops.pre_check_port(device, interface)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/port/configure", response_model=ConfigurationResponse)
async def configure_port(request: PortConfigRequest, background_tasks: BackgroundTasks):
    """Configure a port with pre-checks and Git versioning"""
    try:
        # 1. Run pre-checks
        pre_check = await nxos_ops.pre_check_port(request.device, request.interface)
        
        if not pre_check.is_safe_to_configure:
            raise HTTPException(
                status_code=400, 
                detail="Port is not safe to configure. Check pre-check results."
            )
        
        # 2. Generate configuration
        config = nxos_ops.generate_config(request)
        
        # 3. Commit to Git (before applying)
        commit_hash = git_manager.commit_config(
            device=request.device,
            interface=request.interface,
            config=config,
            user="api_user"
        )
        
        # 4. Apply configuration
        success = await nxos_ops.apply_config(request.device, config)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply configuration")
        
        return ConfigurationResponse(
            success=True,
            commit_hash=commit_hash,
            timestamp=datetime.now().isoformat(),
            applied_config=config,
            message=f"Successfully configured {request.interface} on {request.device}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/history")
async def get_history(device: Optional[str] = None, limit: int = 50):
    """Get configuration history from Git"""
    try:
        history = git_manager.get_history(device=device, limit=limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/rollback/{commit_hash}")
async def rollback_config(commit_hash: str):
    """Rollback to a specific commit"""
    try:
        success = git_manager.rollback(commit_hash)
        
        if not success:
            raise HTTPException(status_code=500, detail="Rollback failed")
        
        return {
            "success": True,
            "message": f"Successfully rolled back to commit {commit_hash}",
            "commit_hash": commit_hash
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/devices")
async def get_devices():
    """Get list of managed devices"""
    # In production, get from NetBox or Nornir inventory
    return {
        "devices": [
            {"name": "spine-01", "role": "spine", "site": "dc1"},
            {"name": "spine-02", "role": "spine", "site": "dc1"},
            {"name": "leaf-01", "role": "leaf", "site": "dc1"},
            {"name": "leaf-02", "role": "leaf", "site": "dc1"},
            {"name": "leaf-03", "role": "leaf", "site": "dc1"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

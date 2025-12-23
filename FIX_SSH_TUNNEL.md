# Fix SSH Tunnel Connection Issue

## Problem
SSH tunnel is running on port 11435, but getting "socket hang up" error when accessing `http://localhost:11435/api/tags`.

## Diagnosis

### Step 1: Check SSH Tunnel Process

The tunnel processes (PIDs 72300, 70872) are running, but they might be:
- Pointing to wrong destination
- Not properly forwarding
- Connected to wrong IP address

### Step 2: Test Mac Studio Ollama Directly

**On Mac Studio terminal, test:**
```bash
curl http://localhost:11434/api/tags
```

If this works, Ollama is running correctly on Mac Studio.

### Step 3: Verify SSH Tunnel Destination

The tunnel should forward:
- **From**: Your laptop `localhost:11435`
- **To**: Mac Studio `localhost:11434`

## Solution: Recreate Tunnel Correctly

### Step 1: Kill Existing Tunnels

**On your laptop, run:**
```bash
taskkill /PID 72300 /F
taskkill /PID 70872 /F
```

**Verify they're stopped:**
```bash
netstat -ano | findstr :11435
```
(Should return nothing)

### Step 2: Find Correct Mac Studio IP

**On Mac Studio, run:**
```bash
ifconfig | grep "inet "
```

Look for the IP address (usually 192.168.x.x or 192.178.x.x)

**OR check from your laptop:**
```bash
ping 192.178.90.31
```

### Step 3: Test SSH Connection First

**On your laptop, test SSH:**
```bash
ssh rivemain@192.178.90.31
```

If this works, SSH is configured correctly.

### Step 4: Create Tunnel with Correct IP

**On your laptop, run:**
```bash
ssh -v -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

The `-v` flag shows verbose output to debug issues.

**OR if you need to specify SSH key:**
```bash
ssh -v -f -N -L 11435:localhost:11434 -i ~/.ssh/id_rsa rivemain@192.178.90.31
```

### Step 5: Test Tunnel

**On your laptop:**
```bash
curl -v http://localhost:11435/api/tags
```

The `-v` flag shows detailed connection info.

## Alternative: Test Tunnel Manually

### Step 1: Create Tunnel Without Background

**On your laptop, run (keep terminal open):**
```bash
ssh -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**In another terminal, test:**
```bash
curl http://localhost:11435/api/tags
```

If this works, the issue is with the background process.

### Step 2: Check for SSH Config Issues

**Create/Edit `~/.ssh/config` on your laptop:**
```
Host macstudio
    HostName 192.178.90.31
    User rivemain
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

**Then use:**
```bash
ssh -f -N -L 11435:localhost:11434 macstudio
```

## Common Issues and Fixes

### Issue 1: Wrong IP Address

**Fix:** Verify Mac Studio IP with `ifconfig` on Mac Studio

### Issue 2: Ollama Not Accessible on Mac Studio

**Fix:** On Mac Studio, verify:
```bash
curl http://localhost:11434/api/tags
```

### Issue 3: SSH Key Authentication

**Fix:** Use SSH key instead of password:
```bash
ssh -f -N -L 11435:localhost:11434 -i ~/.ssh/id_rsa rivemain@192.178.90.31
```

### Issue 4: Firewall Blocking

**Fix:** Check Mac Studio firewall allows SSH connections

## Debugging Commands

**Check tunnel status:**
```bash
netstat -ano | findstr :11435
```

**Check SSH process:**
```bash
tasklist | findstr ssh
```

**Test connection with verbose output:**
```bash
curl -v http://localhost:11435/api/tags
```

**Test SSH connection:**
```bash
ssh -v rivemain@192.178.90.31 "curl http://localhost:11434/api/tags"
```

This tests if you can access Mac Studio Ollama via SSH.


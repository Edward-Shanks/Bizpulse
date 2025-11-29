# How to Clean Git History to Remove Committed Secrets

## ⚠️ IMPORTANT WARNINGS

1. **This will rewrite git history** - All commit hashes will change
2. **You MUST coordinate with your team** - Everyone will need to re-clone
3. **Rotate the exposed API key immediately** - Generate a new one from Perplexity
4. **Backup your repository first** - Create a backup branch before proceeding

## Method 1: Using git filter-branch (Built-in, but slower)

### Step 1: Backup your repository
```bash
# Create a backup branch
git branch backup-before-cleanup

# Or create a full backup
cd ..
cp -r Bizpulse Bizpulse-backup
cd Bizpulse
```

### Step 2: Remove the secret from all commits
```bash
# Remove the Perplexity API key from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/app.py" \
  --prune-empty --tag-name-filter cat -- --all

# Then add the file back with the cleaned version
git add backend/app.py
git commit -m "Remove hardcoded API key from app.py"

# Force update all branches
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/app.py" \
  --prune-empty --tag-name-filter cat -- --all
```

### Step 3: Clean up and force push
```bash
# Remove backup refs created by filter-branch
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push to remote (WARNING: This rewrites history)
git push origin --force --all
git push origin --force --tags
```

## Method 2: Using BFG Repo-Cleaner (Recommended - Faster)

### Step 1: Install BFG Repo-Cleaner

**On Windows (using Chocolatey):**
```bash
choco install bfg
```

**On Windows (using Java directly):**
1. Download from: https://rtyley.github.io/bfg-repo-cleaner/
2. Download the JAR file

**On Mac:**
```bash
brew install bfg
```

**On Linux:**
```bash
sudo apt-get install bfg
# Or download JAR from https://rtyley.github.io/bfg-repo-cleaner/
```

### Step 2: Create a file with secrets to remove
```bash
# Create a file listing all secrets to remove
echo "REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5" > secrets.txt
```

### Step 3: Clone a fresh copy (BFG requires this)
```bash
# Go to parent directory
cd ..

# Clone a fresh copy
git clone --mirror https://github.com/Edward-Shanks/Bizpulse.git Bizpulse.git

# Or if using SSH:
# git clone --mirror git@github.com:Edward-Shanks/Bizpulse.git Bizpulse.git
```

### Step 4: Run BFG to remove secrets
```bash
# If using installed BFG:
bfg --replace-text secrets.txt Bizpulse.git

# If using JAR file:
java -jar bfg.jar --replace-text secrets.txt Bizpulse.git
```

### Step 5: Clean up and push
```bash
cd Bizpulse.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force
```

### Step 6: Update your local repository
```bash
# Go back to your working directory
cd ../Bizpulse

# Fetch the cleaned history
git fetch origin

# Reset your local branch
git reset --hard origin/phase2_2.12
```

## Method 3: Using git-filter-repo (Modern alternative)

### Step 1: Install git-filter-repo

**On Windows:**
```bash
pip install git-filter-repo
```

**On Mac:**
```bash
brew install git-filter-repo
```

**On Linux:**
```bash
pip3 install git-filter-repo
```

### Step 2: Remove the secret
```bash
# Remove the specific API key from all commits
git filter-repo --replace-text <(echo "REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5==>REMOVED_SECRET") --force

# Or remove the entire file from history
git filter-repo --path backend/app.py --invert-paths --force
```

### Step 3: Force push
```bash
git push origin --force --all
git push origin --force --tags
```

## Method 4: Quick Fix - Remove from Recent Commits Only

If the secret was only in recent commits, you can use interactive rebase:

```bash
# Find the commit where the secret was added
git log --all --full-history -- backend/app.py

# Interactive rebase from before the secret was added
git rebase -i <commit-hash-before-secret>

# In the editor, mark commits for editing, then:
# - Remove the secret
# - Continue rebase

# Force push
git push origin --force
```

## After Cleaning History

### 1. Rotate the Exposed API Key
**CRITICAL:** The API key was exposed in git history. You MUST:
1. Go to Perplexity AI dashboard
2. Revoke/delete the old API key: `REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5`
3. Generate a new API key
4. Update your `.env` file with the new key

### 2. Notify Your Team
```bash
# Send this message to your team:
# "I've cleaned git history to remove exposed secrets. 
#  Please re-clone the repository or run:
#  git fetch origin
#  git reset --hard origin/phase2_2.12"
```

### 3. Verify the Cleanup
```bash
# Search for the secret in git history (should return nothing)
git log --all --full-history -S "REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5"

# Search in all files
git grep "REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5" $(git rev-list --all)
```

### 4. Update GitHub Settings
1. Go to: https://github.com/Edward-Shanks/Bizpulse/settings/security
2. Check "Secret scanning" is enabled
3. Review any alerts about the exposed secret

## Recommended Approach for Your Situation

Since you're working on a specific branch (`phase2_2.12`), I recommend:

### Option A: Clean just the branch (Safest)
```bash
# 1. Create a new clean branch from main/master
git checkout main  # or master
git pull origin main
git checkout -b phase2_2.12_clean

# 2. Cherry-pick only the commits you need (without secrets)
# Or manually copy your changes

# 3. Push the clean branch
git push origin phase2_2.12_clean

# 4. Delete the old branch
git push origin --delete phase2_2.12
```

### Option B: Use BFG (Most thorough)
```bash
# Follow Method 2 above - it's the fastest and most reliable
```

## Prevention for Future

1. **Use `.gitignore`** - Ensure `.env` is in `.gitignore`
2. **Use pre-commit hooks** - Install `git-secrets` or `truffleHog`
3. **Use GitHub Secret Scanning** - Already enabled, but review alerts
4. **Code review** - Always review commits before merging
5. **Use environment variables** - Never hardcode secrets

## Quick Reference Commands

```bash
# Check if secret still exists in history
git log --all -p -S "REMOVED_SECRETXcgtQ8j0QXURm7eyj3aOLgIHBrNrFwTswl3LiTj5Ni5dFT5"

# Check current .gitignore
cat .gitignore | grep -E "\.env|secrets"

# Verify .env is ignored
git check-ignore -v .env
```

## Need Help?

If you encounter issues:
1. Check the backup branch: `git checkout backup-before-cleanup`
2. Restore from backup: `git checkout -b restore-from-backup backup-before-cleanup`
3. Contact GitHub support if the secret was already pushed to a public repo


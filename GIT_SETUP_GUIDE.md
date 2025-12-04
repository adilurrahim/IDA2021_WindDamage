# Git & GitHub Setup Guide

Complete guide to push your code to GitHub for publication.

---

## Prerequisites

1. **Install Git** (if not already installed)
   - Download from: https://git-scm.com/downloads
   - Windows: Run installer with default options
   - Verify installation:
     ```bash
     git --version
     ```

2. **Create GitHub Account** (if you don't have one)
   - Go to: https://github.com/signup
   - Follow signup process

---

## Step-by-Step Guide

### Step 1: Configure Git (First Time Only)

Open terminal/command prompt and set your identity:

```bash
# Set your name (will appear in commits)
git config --global user.name "Your Name"

# Set your email (use same as GitHub account)
git config --global user.email "your.email@example.com"

# Verify configuration
git config --global --list
```

---

### Step 2: Create GitHub Repository

1. **Go to GitHub**: https://github.com
2. **Click** the "+" icon (top right) → "New repository"
3. **Fill in details**:
   - **Repository name**: `ida-wind-loss-analysis` (or your preferred name)
   - **Description**: "Hurricane Ida Wind Loss Analysis Pipeline for Nature Climate Change"
   - **Visibility**:
     - ✅ **Public** (for open science)
     - Or **Private** (until paper published)
   - **Initialize**:
     - ❌ **DO NOT** check "Add a README file"
     - ❌ **DO NOT** add .gitignore or license yet (we have them)
4. **Click** "Create repository"

**Save the repository URL!** It looks like:
```
https://github.com/YourUsername/ida-wind-loss-analysis.git
```

---

### Step 3: Initialize Git in Your Project

Open terminal and navigate to your project folder:

```bash
# Navigate to the github_publication folder
cd "c:\Computer backup\projects\LSU_NSF_IDA_WindAnalysis\github_publication"

# Initialize git repository
git init

# Verify git initialized (you should see "Initialized empty Git repository")
```

---

### Step 4: Add Files to Git

```bash
# Check status (see which files will be added)
git status

# Add all files
git add .

# Verify files are staged (should show in green)
git status
```

**What gets added:**
- ✅ main_pipeline.py
- ✅ config.py
- ✅ modules/
- ✅ README.md
- ✅ All documentation
- ❌ Data files (excluded by .gitignore)
- ❌ Output files (excluded by .gitignore)

---

### Step 5: Create First Commit

```bash
# Create commit with descriptive message
git commit -m "Initial commit: Hurricane Ida wind loss analysis pipeline"

# Verify commit created
git log --oneline
```

---

### Step 6: Rename Main Branch (if needed)

GitHub uses "main" as default, Git might use "master":

```bash
# Check current branch name
git branch

# If it says "master", rename to "main"
git branch -M main
```

---

### Step 7: Connect to GitHub Repository

```bash
# Add remote repository (replace with YOUR repository URL)
git remote add origin https://github.com/YourUsername/ida-wind-loss-analysis.git

# Verify remote added
git remote -v
```

**You should see:**
```
origin  https://github.com/YourUsername/ida-wind-loss-analysis.git (fetch)
origin  https://github.com/YourUsername/ida-wind-loss-analysis.git (push)
```

---

### Step 8: Push to GitHub

#### Option A: Using HTTPS (Easier, Recommended)

```bash
# Push code to GitHub
git push -u origin main
```

**First time:** GitHub will prompt for credentials:
1. **Username**: Your GitHub username
2. **Password**: **NOT your GitHub password!** You need a Personal Access Token

**Create Personal Access Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. **Note**: "Git access for Ida analysis"
4. **Expiration**: Choose duration (90 days, 1 year, or no expiration)
5. **Select scopes**:
   - ✅ `repo` (full control of private repositories)
6. Click "Generate token"
7. **COPY THE TOKEN** (you won't see it again!)
8. Use this token as password when git asks

#### Option B: Using SSH (More Secure, Requires Setup)

See "SSH Setup" section below.

---

### Step 9: Verify Upload

1. Go to your GitHub repository URL
2. You should see all your files!
3. Click on README.md to verify it displays correctly

---

## Common Commands

### After Making Changes

```bash
# See what changed
git status

# Add changed files
git add .

# Or add specific file
git add main_pipeline.py

# Commit changes
git commit -m "Description of what you changed"

# Push to GitHub
git push
```

### View History

```bash
# See commit history
git log

# See compact history
git log --oneline

# See what changed in last commit
git show
```

### Undo Changes

```bash
# Discard changes to a file (before commit)
git checkout -- filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - BE CAREFUL!
git reset --hard HEAD~1
```

---

## SSH Setup (Optional, More Secure)

### Generate SSH Key

```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Press Enter for default location
# Enter passphrase (or press Enter for none)

# Start SSH agent
eval "$(ssh-agent -s)"

# Add SSH key to agent
ssh-add ~/.ssh/id_ed25519

# Copy SSH key to clipboard (Windows)
clip < ~/.ssh/id_ed25519.pub

# Or view it (Linux/Mac)
cat ~/.ssh/id_ed25519.pub
```

### Add SSH Key to GitHub

1. Go to: https://github.com/settings/keys
2. Click "New SSH key"
3. **Title**: "My Computer" (or descriptive name)
4. **Key**: Paste the SSH key you copied
5. Click "Add SSH key"

### Use SSH Remote

```bash
# Remove HTTPS remote
git remote remove origin

# Add SSH remote (replace with YOUR username)
git remote add origin git@github.com:YourUsername/ida-wind-loss-analysis.git

# Push using SSH
git push -u origin main
```

---

## Troubleshooting

### Problem: "fatal: not a git repository"

**Solution:**
```bash
# Make sure you're in the right folder
cd "c:\Computer backup\projects\LSU_NSF_IDA_WindAnalysis\github_publication"

# Initialize git
git init
```

---

### Problem: Authentication Failed (HTTPS)

**Solution:**
- You need a Personal Access Token, not your GitHub password
- Generate token: https://github.com/settings/tokens
- Use token as password when prompted

---

### Problem: "rejected" or "non-fast-forward"

**Solution:**
```bash
# Pull changes from GitHub first
git pull origin main --allow-unrelated-histories

# Then push again
git push origin main
```

---

### Problem: Wrong remote URL

**Solution:**
```bash
# Check current remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/YourUsername/correct-repo.git

# Verify
git remote -v
```

---

### Problem: Want to ignore certain files

**Solution:**
- Add patterns to `.gitignore` file
- Example:
  ```
  # Ignore data files
  *.nc
  *.gpkg
  data/

  # Ignore outputs
  output/
  logs/
  ```

---

## Quick Reference

```bash
# Setup (one time)
git init
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git remote add origin https://github.com/YourUsername/repo.git

# Workflow (repeat)
git status                          # Check what changed
git add .                           # Stage all changes
git commit -m "Description"         # Commit changes
git push                            # Push to GitHub

# Viewing
git log                             # View history
git status                          # View current state
git diff                            # View changes

# Branching
git branch                          # List branches
git branch feature-name             # Create branch
git checkout feature-name           # Switch to branch
git checkout -b feature-name        # Create and switch
```

---

## Best Practices

### Commit Messages

Good commit messages:
```bash
git commit -m "Add checkpointing to building characterization"
git commit -m "Fix bug in spatial join distance calculation"
git commit -m "Update README with data sources"
```

Bad commit messages:
```bash
git commit -m "update"
git commit -m "fix"
git commit -m "changes"
```

### Commit Often

- Commit after each logical change
- Don't wait until everything is done
- Small, frequent commits are better than large, infrequent ones

### Use Branches

For major changes:
```bash
# Create feature branch
git checkout -b add-new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Switch back to main
git checkout main

# Merge feature
git merge add-new-feature
```

---

## Complete Example Workflow

```bash
# 1. Navigate to folder
cd "c:\Computer backup\projects\LSU_NSF_IDA_WindAnalysis\github_publication"

# 2. Initialize git
git init

# 3. Configure (first time only)
git config --global user.name "John Doe"
git config --global user.email "john.doe@university.edu"

# 4. Add files
git add .

# 5. Commit
git commit -m "Initial commit: Hurricane Ida wind loss analysis pipeline"

# 6. Rename branch to main
git branch -M main

# 7. Add remote (replace with YOUR URL!)
git remote add origin https://github.com/YourUsername/ida-wind-loss-analysis.git

# 8. Push to GitHub
git push -u origin main

# Enter username and Personal Access Token when prompted
```

---

## After Upload: Update Repository Settings

On GitHub repository page:

1. **Add Description**:
   - Click "About" (gear icon)
   - Add: "Hurricane Ida Wind Loss Analysis Pipeline for Nature Climate Change"
   - Add topics: `climate-change`, `hurricane`, `wind-damage`, `hazus`, `python`

2. **Add LICENSE**:
   - Click "Add file" → "Create new file"
   - Filename: `LICENSE`
   - Choose license template (e.g., MIT)

3. **Enable Issues** (for feedback):
   - Settings → Features → Enable Issues

4. **Add Social Preview**:
   - Settings → Social preview → Upload image (optional)

---

## Next Steps After Pushing

1. ✅ Repository is live on GitHub
2. 📝 Copy repository URL for your paper
3. 🔗 Add URL to manuscript
4. 🎯 Consider:
   - Adding DOI via Zenodo
   - Adding CITATION.cff file
   - Creating release for paper submission

---

## Need Help?

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **Git Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf

---

**You're ready to publish your code! 🚀**

After pushing to GitHub, your code will be accessible at:
```
https://github.com/YourUsername/ida-wind-loss-analysis
```

Include this URL in your Nature Climate Change manuscript!

# How to Remove .env.local from Git History

GitHub detected your API key in `.env.local` and blocked the push. Follow these steps to fix it:

## Quick Fix (if .env.local is only in the last commit):

```powershell
# 1. Remove .env.local from git tracking (keeps the file locally)
git rm --cached .env.local

# 2. Commit the removal
git commit -m "Remove .env.local from git (contains API key)"

# 3. Push again
git push
```

## If .env.local is in multiple commits (rewrite history):

### Option 1: Using git filter-branch (built-in)

```powershell
# Remove .env.local from entire git history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env.local" --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: This rewrites history - coordinate with team!)
git push --force --all
```

### Option 2: Using BFG Repo-Cleaner (faster, recommended)

1. Download BFG: https://rtyley.github.io/bfg-repo-cleaner/
2. Run:
```powershell
java -jar bfg.jar --delete-files .env.local
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Option 3: If it's only in recent commits

```powershell
# Reset to before .env.local was added (replace N with number of commits)
git reset --soft HEAD~N
git rm --cached .env.local
git commit -m "Your commit message"
git push --force
```

## Verify .env.local is ignored:

Make sure `.gitignore` contains:
```
.env.local
.env
```

## After fixing:

1. ✅ `.env.local` is in `.gitignore` (already done)
2. ✅ `.env.local` is removed from git history
3. ✅ Your local `.env.local` file still exists (for your use)
4. ✅ Push will succeed

## Important Notes:

- **Never commit API keys or secrets to git**
- `.env.local` should always be in `.gitignore`
- If you've already pushed the secret, consider rotating your API key
- The `.env.local.example` file is safe to commit (it doesn't contain real keys)


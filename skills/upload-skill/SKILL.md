---
name: upload-skill
description: Upload a skill to an existing, already connected Claude Code marketplace. Use this when the user wants to publish, add, or upload a skill to their marketplace repository.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Upload Skill to Marketplace

Upload a skill folder to an existing Claude Code plugin marketplace.

## Prerequisites

- Skill folder with `SKILL.md` file
- Connected marketplace repository (cloned locally)
- Write access to the marketplace repo

## Workflow

### Step 1: Validate the Skill

Ensure the skill has a valid `SKILL.md` with required YAML frontmatter:

```yaml
---
name: skill-name          # Required: lowercase, hyphens only
description: Description  # Required: max 1024 chars
allowed-tools: Bash, Read # Optional: restrict tools
---
```

### Step 2: Copy Skill to Marketplace

```bash
# Copy skill folder (exclude cache files)
rsync -av --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
  /path/to/skill-folder \
  /path/to/marketplace/skills/
```

### Step 3: Update marketplace.json

Edit `.claude-plugin/marketplace.json` to add the skill path:

```json
{
  "plugins": [
    {
      "name": "plugin-name",
      "skills": [
        "./skills/existing-skill",
        "./skills/new-skill"  // Add this line
      ]
    }
  ]
}
```

### Step 4: Commit and Push

```bash
cd /path/to/marketplace
git add .
git commit -m "Add [skill-name] skill

- Description of what the skill does

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
git push origin main
```

### Step 5: Reinstall Plugin

Users need to reinstall to get the new skill:

```
/plugin install plugin-name@marketplace-name
```

## Example

Upload `my-analysis` skill to `cssi-claude-skills` marketplace:

```bash
# 1. Copy skill
rsync -av --exclude='__pycache__' \
  ~/.claude/skills/my-analysis \
  ~/Desktop/cssi-claude-skills/skills/

# 2. Update marketplace.json - add "./skills/my-analysis" to skills array

# 3. Commit and push
cd ~/Desktop/cssi-claude-skills
git add .
git commit -m "Add my-analysis skill"
git push origin main
```

## Skill File Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Lowercase, letters/numbers/hyphens (max 64 chars) |
| `description` | Yes | When Claude should use this skill (max 1024 chars) |
| `allowed-tools` | No | Restrict which tools the skill can use |
| `user-invocable` | No | Set `true` to show in slash command menu |
| `version` | No | Semantic version string |

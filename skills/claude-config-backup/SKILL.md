---
name: claude-config-backup
description: Backup and migrate Claude Code configurations including settings, plugins, skills, and custom commands. Use this skill when the user wants to backup their Claude Code config, migrate settings to another machine, export their configuration, or sync their Claude Code setup. Handles identifying migratable files, cleaning machine-specific paths, and optionally pushing to a git repository.
---

# Claude Code Configuration Backup Skill

You are helping the user backup their Claude Code configuration for migration to another machine or for version control.

## Configuration Locations

Claude Code stores configuration in these locations:

| Path | Contents | Migratable? |
|------|----------|-------------|
| `~/.claude/settings.json` | Global permissions, enabled plugins | YES |
| `~/.claude/skills/` | Custom skills | YES |
| `~/.claude/commands/` | Custom slash commands | YES |
| `~/.claude/plugins/installed_plugins.json` | List of installed plugins | YES (reference only) |
| `~/.claude/plugins/known_marketplaces.json` | Registered marketplaces | YES (reference only) |
| `~/.claude.json` | User preferences, OAuth tokens, project settings | NO (contains secrets) |
| `~/.claude/settings.local.json` | Local permissions with machine-specific paths | NO |
| `~/.claude/plugins/cache/` | Downloaded plugin binaries | NO (reinstall needed) |
| `~/.claude/plugins/marketplaces/` | Cloned marketplace repos | NO (reinstall needed) |
| `~/.claude/history.jsonl` | Conversation history | NO |
| `~/.claude/projects/` | Project-specific settings | NO |
| `~/.claude/debug/`, `~/.claude/todos/`, etc. | Temporary/session data | NO |

## Backup Workflow

### Step 1: Create Backup Directory

```bash
mkdir -p <backup_dir>
```

### Step 2: Copy Migratable Files

```bash
# Core settings
cp ~/.claude/settings.json <backup_dir>/

# Custom skills (exclude this skill if backing up to same repo)
cp -r ~/.claude/skills <backup_dir>/

# Custom commands
cp -r ~/.claude/commands <backup_dir>/

# Plugin references (not the actual plugins)
mkdir -p <backup_dir>/plugins
cp ~/.claude/plugins/installed_plugins.json <backup_dir>/plugins/
cp ~/.claude/plugins/known_marketplaces.json <backup_dir>/plugins/
```

### Step 3: Clean Machine-Specific Paths

The following files contain absolute paths that need cleaning:

1. **plugins/installed_plugins.json** - Contains `installPath` with absolute paths
   - Replace absolute paths like `/Users/username/.claude/...` with `~/.claude/...`
   - Add a `_note` field explaining reinstallation commands

2. **plugins/known_marketplaces.json** - Contains `installLocation` with absolute paths
   - Replace absolute paths with `~/.claude/...`
   - Add a `_note` field with marketplace add commands

### Step 4: Remove Embedded Git Repos

If `~/.claude/plugins/marketplaces/` was copied, remove it:
```bash
rm -rf <backup_dir>/plugins/marketplaces
```

These are cloned git repos that cause submodule issues and can be reinstalled.

### Step 5: Generate README

Create a README.md with:
- List of included configurations
- Migration instructions for new machine
- Commands to reinstall plugins and marketplaces
- List of installed plugins with install commands
- List of registered marketplaces with add commands

### Step 6: Git Operations (Optional)

If user wants to push to a repository:

```bash
cd <backup_dir>
git init  # if not already a repo
git add -A
git commit -m "Backup Claude Code configuration"
git remote add origin <repo_url>  # if not already set
git push -u origin main
```

## Restoration Instructions (Include in README)

```bash
# Clone backup
git clone <repo_url>
cd <repo_name>

# Copy configurations
mkdir -p ~/.claude
cp settings.json ~/.claude/
cp -r skills ~/.claude/
cp -r commands ~/.claude/

# Reinstall marketplaces (in Claude Code)
/plugin marketplace add anthropics/claude-plugins-official
/plugin marketplace add anthropics/skills

# Reinstall plugins (in Claude Code)
/plugin install <plugin-name>@<marketplace>
```

## Important Notes

1. **Exclude the backup skill itself** if backing up to the same repo where this skill lives
2. **Never include** `~/.claude.json` as it contains OAuth tokens
3. **Plugin reinstallation required** - JSON files are references only
4. **Test restoration** on a fresh machine to verify completeness
5. **skills/ may contain API keys or secrets** in helper scripts - review before pushing to public repos

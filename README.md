# CSSI Claude Skills

A curated collection of Claude Code skills developed by Northwestern University's [Center for Science of Science & Innovation (CSSI)](https://cssi.kellogg.northwestern.edu/).

## Getting Started

### Install as a Claude Code Plugin

Connect your Claude Code instance to this skills marketplace by running:

```bash
claude skill add-marketplace https://github.com/Northwestern-CSSI/cssi-claude-skills
```

This registers the repository as a skill source, making all available skills accessible from your Claude Code environment.

### Enable Auto-Update

To ensure you always have the latest skill versions, enable automatic updates:

```bash
claude skill enable-auto-update cssi-skills
```

With auto-update enabled, Claude Code will periodically sync with this repository and pull any new or updated skills automatically.

### Browse Available Skills

After installation, view all available skills with:

```bash
claude skill list
```

Or invoke any skill directly by name during a Claude Code session using the `/<skill-name>` syntax.

## Contributing Skills

Have a useful skill to share? You can upload your own skills to this marketplace.

### Using the Upload Skill

The easiest way to contribute is through Claude Code itself:

```
/upload-skill
```

This interactive command will guide you through packaging and submitting your skill to the repository.

### Manual Contribution

Alternatively, you can contribute manually:

1. Fork this repository
2. Create your skill in the `skills/` directory following the standard structure:
   ```
   skills/your-skill-name/
   ├── SKILL.md        # Main skill instructions (required)
   ├── CLAUDE.md       # Claude-specific context (optional)
   ├── helper.py       # Helper scripts (optional)
   └── tests/          # Test files (optional)
   ```
3. Use the template in `template/` as a starting point
4. Submit a pull request

See `spec/` for detailed skill specification standards.

## Skill Structure

Each skill follows a consistent format:

- **`SKILL.md`** - The main instruction file with YAML frontmatter defining metadata and the skill's behavior
- **`CLAUDE.md`** - Optional file providing additional context for Claude
- **Helper files** - Optional Python scripts or other resources the skill may reference

## Requirements

Individual skills may have their own dependencies (Python packages, API credentials, etc.). Refer to each skill's documentation for specific requirements.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## About CSSI

The [Center for Science of Science & Innovation](https://cssi.kellogg.northwestern.edu/) at Northwestern University studies the structure and dynamics of science, including team collaboration, research impact, funding allocation, and knowledge diffusion.

# Splitux Handlers Registry

Community-contributed game handlers for [Splitux](https://github.com/splitux-gg/splitux) - local splitscreen and remote-play multiplayer on Linux.

## What are Handlers?

Handlers are configuration files that tell Splitux how to run a specific game with local splitscreen multiplayer. Each handler contains game-specific settings like executable paths, multiplayer backend configuration, and launch parameters.

## Structure

```
handlers/
├── game-id/
│   ├── handler.yaml    # Handler configuration (required)
│   ├── icon.jpg        # Game icon from Steam cache (required)
│   ├── header.jpg      # Banner image for detail view (required)
│   └── background.jpg  # Background image (optional)
```

## Contributing a Handler

1. Fork this repository
2. Create a new directory under `handlers/` with your game's ID (lowercase, hyphens for spaces)
3. Add the required files:
   - `handler.yaml` - Your handler configuration
   - `icon.jpg` - Game icon (can be copied from Steam's librarycache)
   - `header.jpg` - Banner image (library_header.jpg from Steam cache)
4. Update `index.json` with your handler's metadata
5. Submit a pull request

### handler.yaml Template

Handlers use **nested backend blocks** (the canonical form). Include three
required fields, a way to find the game, and one backend block:

```yaml
name: Game Name
exec: game.exe
spec_ver: 3
steam_appid: 123456
author: YourName
version: "1.0"
info: |
  Brief description of the handler.
  Any special instructions or notes.

# One backend block, auto-detected by being present:
goldberg:
  settings:
    force_lobby_type.txt: "2"
    invite_all.txt: ""
```

Available backends: `goldberg` (Steam/gbe_fork), `eos` (Epic Online Services LAN),
`photon`, `facepunch`, `standalone`. Multiple can coexist (e.g. `eos` + `goldberg`).
See the full field and emulator-tuning reference:
[**HANDLER_OPTIONS.md**](https://github.com/splitux-gg/splitux/blob/main/docs/HANDLER_OPTIONS.md)
(and `assets/handler_template.yaml` in the splitux repo).

> Older handlers using dot-notation (`goldberg.settings.x.txt`) or the legacy
> `backend:` field still load, but new handlers should use nested blocks.

### index.json Entry

Add your handler to the `handlers` array. The `backend` field is a short label
(e.g. `goldberg`, `eos+goldberg`, `photon`):

```json
{
  "id": "game-id",
  "name": "Game Name",
  "author": "YourName",
  "steam_appid": 123456,
  "backend": "goldberg",
  "description": "Brief description for the browse list",
  "updated": "2026-06-13"
}
```

## Guidelines

- Test your handler before submitting
- Include clear instructions in the `info` field if special setup is required
- Use descriptive IDs (e.g., `portal-2`, `stardew-valley`)
- Provide high-quality images when possible

## License

Handler configurations in this repository are provided as-is for use with Splitux.

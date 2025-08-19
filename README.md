# PlexAniSync Mapping Viewer

A webpage built with Svelte 5 to visualize PlexAniSync YAML mapping files. This displays anime and movie mappings with their corresponding AniList IDs, seasons, and episode ranges.

## Setup

1. **Install dependencies**:
   ```bash
   pnpm i
   ```

2. **Start development server**:
   ```bash
   pnpm dev
   ```

3. **Build for production**:
   ```bash
   pnpm build
   ```

## File Structure

```
├── src/
│   ├── App.svelte          # Main application component
│   └── main.js             # Application entry point
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite configuration
└── svelte.config.js        # Svelte configuration
```

## Supported YAML Format

The application expects YAML files with the following structure:

```yaml
entries:
  - title: "Anime Title"
    guid: plex://show/id
    synonyms: ["Alternative Title"]
    seasons:
      - season: 1
        anilist-id: 12345
      - season: 1
        anilist-id: 67890
        start: 13
```

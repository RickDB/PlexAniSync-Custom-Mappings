# PlexAniSync Mapping Viewer - Svelte 5

A modern web application built with Svelte 5 to visualize PlexAniSync YAML mapping files. This tool displays anime series and movie mappings with their corresponding AniList IDs, seasons, and episode ranges.

## Features

- **File Upload**: Drag and drop or select YAML files to view mappings
- **Visual Season Display**: Interactive progress bars showing episode ranges
- **AniList Integration**: Direct links to AniList entries
- **Responsive Design**: Works on desktop and mobile devices
- **Multiple File Support**: Handles series-tmdb.en.yaml, series-tvdb.en.yaml, and movies-tmdb.en.yaml

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

## Usage

1. Open the application in your browser
2. Click "Choose File" or drag and drop a YAML mapping file
3. Browse the visualized mappings with:
   - Series/movie titles and synonyms
   - Season breakdowns with episode ranges
   - Clickable AniList links
   - Visual progress bars for multi-part seasons

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

## Technologies

- **Svelte 5**: Modern reactive framework with runes
- **Vite**: Fast build tool and dev server
- **js-yaml**: YAML parsing library
- **CSS Grid**: Responsive layout system

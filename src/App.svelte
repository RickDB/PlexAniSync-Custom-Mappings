<script>
  import { load } from 'js-yaml'
  
  let data = $state(null)
  let fileInput

  function handleFileUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const yamlText = e.target.result
        const parsed = load(yamlText)
        
        // Parse external links from comments
        if (parsed.entries) {
          parsed.entries = parsed.entries.map((entry, index) => {
            const entryLinks = parseExternalLinks(yamlText, entry.title, index)
            return { ...entry, externalLinks: entryLinks }
          })
        }
        
        data = parsed
      } catch (err) {
        alert('Error parsing YAML: ' + err.message)
      }
    }
    reader.readAsText(file)
  }

  // Parse external links from YAML comments
  function parseExternalLinks(yamlText, title, entryIndex) {
    const links = { imdb: null, tmdb: null, tvdb: null, plex: null }
    
    // Split YAML into lines and find the entry
    const lines = yamlText.split('\n')
    let entryStartLine = -1
    let currentEntryIndex = -1
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (line.startsWith('- title:')) {
        currentEntryIndex++
        if (currentEntryIndex === entryIndex) {
          entryStartLine = i
          break
        }
      }
    }
    
    if (entryStartLine === -1) return links
    
    // Look for comment lines after the entry title
    for (let i = entryStartLine + 1; i < lines.length; i++) {
      const line = lines[i].trim()
      
      // Stop if we hit the next entry or seasons
      if (line.startsWith('- title:') || line.startsWith('seasons:')) break
      
      // Parse comment links
      if (line.startsWith('# imdb:')) {
        const match = line.match(/# imdb:\s*(.+)/)
        if (match) links.imdb = match[1].trim()
      } else if (line.startsWith('# tmdb:')) {
        const match = line.match(/# tmdb:\s*(.+)/)
        if (match) links.tmdb = match[1].trim()
      } else if (line.startsWith('# tvdb:')) {
        const match = line.match(/# tvdb:\s*(.+)/)
        if (match) links.tvdb = match[1].trim()
      }
    }
    
    return links
  }

  // Group seasons by season number to handle split AniList IDs with "start" markers
  function groupSeasons(seasons) {
    const grouped = {}
    seasons.forEach((s) => {
      if (!grouped[s.season]) grouped[s.season] = []
      grouped[s.season].push(s)
    })
    return grouped
  }

  // Build episode ranges based on start markers
  function buildRanges(entries) {
    const sorted = [...entries].sort((a, b) => (a.start || 1) - (b.start || 1))
    const ranges = []

    sorted.forEach((s, idx) => {
      const start = s.start || 1
      const end = idx < sorted.length - 1 ? (sorted[idx + 1].start || '') - 1 : ''
      ranges.push({ ...s, start, end, range: end ? `${start}-${end}` : `${start}-` })
    })

    return ranges
  }

  // Merge duplicate AniList IDs in the same season (like Gintama S1-4)
  function mergeSameAniList(ranges) {
    const merged = []
    ranges.forEach((r) => {
      const last = merged[merged.length - 1]
      if (last && last['anilist-id'] === r['anilist-id']) {
        last.end = r.end
        last.range = last.end ? `${last.start}-${last.end}` : `${last.start}-`
      } else {
        merged.push({ ...r })
      }
    })
    return merged
  }
</script>

<div class="container">
  <h1>PlexAniSync Mapping Viewer</h1>
  <input 
    bind:this={fileInput}
    type="file" 
    accept=".yaml,.yml" 
    on:change={handleFileUpload}
    class="file-input"
  />

  {#if data}
    <div class="content">
      <!-- Remote URLs -->
      {#if data['remote-urls']?.length > 0}
        <div class="card">
          <h2>Remote URLs</h2>
          <ul class="url-list">
            {#each data['remote-urls'] as url}
              <li>
                <a href={url} target="_blank" rel="noreferrer" class="url-link">
                  {url}
                </a>
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      <!-- Entries -->
      {#each data.entries || [] as entry, idx}
        {@const groupedSeasons = groupSeasons(entry.seasons)}
        
        <div class="card entry-card">
          <h2 class="entry-title">{entry.title}</h2>
          
          {#if entry.synonyms?.length > 0}
            <p class="synonyms">
              Synonyms: {entry.synonyms.join(', ')}
            </p>
          {/if}
          
          {#if !entry.guid.startsWith('plex://')}
            <p class="guid">
              <span class="guid-text">{entry.guid}</span>
            </p>
          {/if}

          <!-- External Links -->
          {#if entry.externalLinks && (entry.externalLinks.imdb || entry.externalLinks.tmdb || entry.externalLinks.tvdb)}
            <div class="external-links">
              {#if entry.externalLinks.imdb}
                <a href={entry.externalLinks.imdb} target="_blank" rel="noreferrer" class="external-link" title="View on IMDB">
                  <img src=".github/assets/imdb.png" alt="IMDB" class="link-icon" />
                </a>
              {/if}
              {#if entry.externalLinks.tmdb}
                <a href={entry.externalLinks.tmdb} target="_blank" rel="noreferrer" class="external-link" title="View on TMDB">
                  <img src=".github/assets/tmdb.png" alt="TMDB" class="link-icon" />
                </a>
              {/if}
              {#if entry.externalLinks.tvdb}
                <a href={entry.externalLinks.tvdb} target="_blank" rel="noreferrer" class="external-link" title="View on TVDB">
                  <img src=".github/assets/tvdb.png" alt="TVDB" class="link-icon" />
                </a>
              {/if}
              {#if entry.guid.startsWith('plex://')}
                <a href={entry.guid} target="_blank" rel="noreferrer" class="external-link" title="View on Plex">
                  <img src=".github/assets/plex.png" alt="Plex" class="link-icon" />
                </a>
              {/if}
            </div>
          {/if}

          <div class="seasons-section">
            <h3>Seasons</h3>
            <div class="seasons-grid">
              {#each Object.entries(groupedSeasons) as [seasonNum, seasonEntries]}
                {@const withRanges = buildRanges(seasonEntries)}
                {@const mergedRanges = mergeSameAniList(withRanges)}
                {@const totalSegments = mergedRanges.length}
                
                <div class="season-item">
                  <div class="season-number">
                    {seasonNum}
                  </div>

                  <!-- Visual merged bar with segments -->
                  <div class="progress-bar">
                    {#each mergedRanges as segment, j}
                      <a
                        href="https://anilist.co/anime/{segment['anilist-id']}/"
                        target="_blank"
                        rel="noreferrer"
                        style="width: {100 / totalSegments}%"
                        class="segment segment-{j % 2}"
                        title="Ep {segment.range} ({segment['anilist-id']})"
                      ></a>
                    {/each}
                  </div>

                  <!-- Labels -->
                  <div class="labels">
                    {#each mergedRanges as segment, j}
                      <div class="label-item">
                        <a
                          href="https://anilist.co/anime/{segment['anilist-id']}/"
                          target="_blank"
                          rel="noreferrer"
                          class="anilist-link anilist-link-{j % 2}"
                          title="Anilist ID {segment['anilist-id']}"
                        >
                          {segment['anilist-id']}
                        </a>
                        <span class="episode-range">(Ep {segment.range})</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .container {
    padding: 1.5rem;
    max-width: 1200px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  h1 {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 1.5rem;
    color: #1f2937;
  }

  .file-input {
    margin-bottom: 1.5rem;
    padding: 0.5rem;
    border: 2px dashed #d1d5db;
    border-radius: 0.5rem;
    background: #f9fafb;
    cursor: pointer;
  }

  .file-input:hover {
    border-color: #6366f1;
    background: #f0f9ff;
  }

  .content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .card {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    border: 1px solid #e5e7eb;
  }

  .entry-card {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  }

  .entry-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #1f2937;
  }

  .synonyms {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
  }

  .guid {
    font-size: 0.875rem;
    color: #374151;
    margin-bottom: 1rem;
  }

  .guid-text {
    font-family: 'Courier New', monospace;
    background: #f3f4f6;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
  }

  .url-list {
    list-style: disc;
    padding-left: 1.25rem;
  }

  .url-link {
    color: #2563eb;
    text-decoration: underline;
  }

  .url-link:hover {
    color: #1d4ed8;
  }

  .seasons-section h3 {
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: #374151;
  }

  .seasons-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr));
    gap: 1.5rem;
    max-width: 800px;
    margin: 0 auto;
  }

  .season-item {
    text-align: center;
    position: relative;
    width: 12rem;
    margin: 0 auto;
  }

  .season-number {
    width: 2.5rem;
    height: 2.5rem;
    margin: 0 auto;
    border-radius: 50%;
    background: #22468114;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-bottom: 0.75rem;
  }

  .progress-bar {
    height: 1rem;
    width: 100%;
    background: #e5e7eb;
    border-radius: 0.25rem;
    overflow: hidden;
    display: flex;
    margin-bottom: 0.5rem;
  }

  .segment {
    height: 100%;
    transition: opacity 0.2s;
    text-decoration: none;
  }

  .segment:hover {
    opacity: 0.8;
  }

  .segment-0 {
    background: #3b82f6;
  }

  .segment-1 {
    background: #10b981;
  }

  .labels {
    font-size: 0.875rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .label-item {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .anilist-link {
    text-decoration: none;
    font-weight: 500;
  }

  .anilist-link-0 {
    color: #2563eb;
  }

  .anilist-link-1 {
    color: #059669;
  }

  .anilist-link:hover {
    opacity: 0.8;
  }

  .episode-range {
    color: #6b7280;
    margin-left: 0.25rem;
  }

  .external-links {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1rem;
    align-items: center;
  }

  .external-link {
    transition: opacity 0.2s, transform 0.2s;
    display: inline-block;
  }

  .external-link:hover {
    opacity: 0.8;
    transform: scale(1.05);
  }

  .link-icon {
    width: 32px;
    height: 32px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  @media (max-width: 640px) {
    .seasons-grid {
      grid-template-columns: 1fr;
    }
    
    .container {
      padding: 1rem;
    }

    .external-links {
      gap: 0.5rem;
    }

    .link-icon {
      width: 28px;
      height: 28px;
    }
  }
</style>

<script>
  import { load } from 'js-yaml'
  
  let data = $state(null)
  let fileInput
  let activeTab = $state('series-tmdb')
  let allData = $state({
    'series-tmdb': null,
    'series-tvdb': null,
    'movies-tmdb': null
  })
  let loading = $state(false)
  let isCustomFile = $state(false)
  let searchQuery = $state('')

  // Load all YAML files on component mount
  async function loadAllFiles() {
    loading = true
    const files = [
      { key: 'series-tmdb', path: './series-tmdb.en.yaml' },
      { key: 'series-tvdb', path: './series-tvdb.en.yaml' },
      { key: 'movies-tmdb', path: './movies-tmdb.en.yaml' }
    ]

    for (const file of files) {
      try {
        const response = await fetch(file.path)
        const yamlText = await response.text()
        const parsed = load(yamlText)
        
        // Parse external links from comments
        if (parsed.entries) {
          parsed.entries = parsed.entries.map((entry, index) => {
            const entryLinks = parseExternalLinks(yamlText, entry.title, index)
            return { ...entry, externalLinks: entryLinks }
          })
        }
        
        allData[file.key] = parsed
      } catch (err) {
        console.error(`Error loading ${file.path}:`, err)
      }
    }
    
    // Set initial data to active tab
    data = allData[activeTab]
    loading = false
  }

  // Switch between tabs
  function switchTab(tabKey) {
    activeTab = tabKey
    data = allData[tabKey]
    isCustomFile = false
    // Clear file input to allow re-uploading the same file
    if (fileInput) {
      fileInput.value = ''
    }
  }

  // Load files when component mounts
  $effect(() => {
    loadAllFiles()
  })

  function handleFileUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    // Validate file type
    const validExtensions = ['.yaml', '.yml']
    const fileName = file.name.toLowerCase()
    const isValidFile = validExtensions.some(ext => fileName.endsWith(ext))
    
    if (!isValidFile) {
      alert('Please upload only YAML files (.yaml or .yml)')
      event.target.value = '' // Clear the input
      return
    }

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
        
        // Set custom file data and unselect tabs
        data = parsed
        activeTab = null
        isCustomFile = true
      } catch (err) {
        alert('Error parsing YAML: ' + err.message)
        event.target.value = '' // Clear the input on error
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

  // Filter entries based on search query
  function filterEntries(entries) {
    if (!searchQuery.trim()) return entries
    
    const query = searchQuery.toLowerCase().trim()
    return entries.filter(entry => {
      // Search in title
      if (entry.title.toLowerCase().includes(query)) return true
      
      // Search in synonyms
      if (entry.synonyms?.some(synonym => synonym.toLowerCase().includes(query))) return true
      
      // Search in AniList IDs
      if (entry.seasons?.some(season => season['anilist-id'].toString().includes(query))) return true
      
      // Search in GUID
      if (entry.guid?.toLowerCase().includes(query)) return true
      
      return false
    })
  }

  // Extract YAML for a specific entry
  function extractEntryYaml(entry, entryIndex) {
    if (isCustomFile) {
      // For custom files, we need to reconstruct from the parsed data
      return reconstructYamlEntry(entry)
    } else {
      // For built-in files, extract from the original YAML text
      return extractFromOriginalYaml(entry, entryIndex)
    }
  }

  // Reconstruct YAML from parsed entry data
  function reconstructYamlEntry(entry) {
    let yaml = `  - title: "${entry.title}"\n`
    if (entry.guid) {
      yaml += `    guid: ${entry.guid}\n`
    }
    if (entry.synonyms && entry.synonyms.length > 0) {
      yaml += `    synonyms: [${entry.synonyms.map(s => `"${s}"`).join(', ')}]\n`
    }
    if (entry.seasons && entry.seasons.length > 0) {
      yaml += `    seasons:\n`
      entry.seasons.forEach(season => {
        yaml += `      - season: ${season.season}\n`
        yaml += `        anilist-id: ${season['anilist-id']}\n`
        if (season.start && season.start !== 1) {
          yaml += `        start: ${season.start}\n`
        }
      })
    }
    return yaml
  }

  // Extract from original YAML text (for built-in files)
  async function extractFromOriginalYaml(entry, entryIndex) {
    try {
      const fileName = activeTab === 'series-tmdb' ? './series-tmdb.en.yaml' : 
                      activeTab === 'series-tvdb' ? './series-tvdb.en.yaml' : 
                      './movies-tmdb.en.yaml'
      
      const response = await fetch(fileName)
      const yamlText = await response.text()
      const lines = yamlText.split('\n')
      
      let entryStartLine = -1
      let currentEntryIndex = -1
      
      // Find the entry
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
      
      if (entryStartLine === -1) return reconstructYamlEntry(entry)
      
      // Extract the entry until the next entry or end of file
      let entryLines = []
      for (let i = entryStartLine; i < lines.length; i++) {
        const line = lines[i]
        if (i > entryStartLine && line.trim().startsWith('- title:')) {
          break
        }
        entryLines.push(line)
      }
      
      return entryLines.join('\n')
    } catch (err) {
      console.error('Error extracting YAML:', err)
      return reconstructYamlEntry(entry)
    }
  }

  // Copy entry YAML to clipboard
  async function copyEntryYaml(entry, entryIndex, event) {
    try {
      const yamlText = await extractFromOriginalYaml(entry, entryIndex)
      await navigator.clipboard.writeText(yamlText)
      
      // Show temporary feedback
      const button = event.target.closest('.copy-button')
      const originalText = button.textContent
      button.textContent = 'Copied!'
      button.classList.add('copied')
      
      setTimeout(() => {
        button.textContent = originalText
        button.classList.remove('copied')
      }, 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
      alert('Failed to copy to clipboard')
    }
  }
</script>

<div class="container">
  <div class="header">
    <img src=".github/assets/logo.png" alt="PlexAniSync Logo" class="logo" />
    <h1>PlexAniSync Mapping Viewer</h1>
  </div>
  
  <!-- Tab Navigation -->
  <div class="tabs">
    <button 
      class="tab {activeTab === 'series-tmdb' && !isCustomFile ? 'active' : ''}"
      onclick={() => switchTab('series-tmdb')}
    >
      Series (TMDB)
    </button>
    <button 
      class="tab {activeTab === 'series-tvdb' && !isCustomFile ? 'active' : ''}"
      onclick={() => switchTab('series-tvdb')}
    >
      Series (TVDB)
    </button>
    <button 
      class="tab {activeTab === 'movies-tmdb' && !isCustomFile ? 'active' : ''}"
      onclick={() => switchTab('movies-tmdb')}
    >
      Movies (TMDB)
    </button>
    {#if isCustomFile}
      <div class="custom-file-indicator">
        Custom File Loaded
      </div>
    {/if}
  </div>

  <!-- Search/Filter -->
  <div class="search-section">
    <input 
      type="text" 
      placeholder="Search by title, synonyms, AniList ID, or GUID..."
      bind:value={searchQuery}
      class="search-input"
    />
    <div class="search-icon">🔍</div>
  </div>

  <!-- File Upload (Optional) -->
  <details class="file-upload-section">
    <summary>Upload Custom YAML File</summary>
    <input 
      bind:this={fileInput}
      type="file" 
      accept=".yaml,.yml" 
      onchange={handleFileUpload}
      class="file-input"
    />
  </details>

  {#if loading}
    <div class="loading">
      <p>Loading YAML files...</p>
    </div>
  {:else if data}
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
      {#if filterEntries(data.entries || []).length === 0 && searchQuery.trim()}
        <div class="no-results">
          <p>No entries found matching "{searchQuery}"</p>
          <p class="no-results-hint">Try searching by title, synonyms, AniList ID, or GUID</p>
        </div>
      {/if}

      {#each filterEntries(data.entries || []) as entry, idx}
        {@const groupedSeasons = groupSeasons(entry.seasons)}
        
        <div class="card entry-card">
          <button 
            class="copy-button"
            onclick={(e) => copyEntryYaml(entry, idx, e)}
            title="Copy YAML entry to clipboard"
          >
            📋 Copy
          </button>
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

  .header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .logo {
    width: 48px;
    height: 48px;
    object-fit: contain;
  }

  h1 {
    font-size: 2rem;
    font-weight: bold;
    margin: 0;
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
    position: relative;
  }

  .copy-button {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    cursor: pointer;
    transition: all 0.2s;
    z-index: 10;
  }

  .copy-button:hover {
    background: #e5e7eb;
    border-color: #9ca3af;
    transform: translateY(-1px);
  }

  .copy-button.copied {
    background: #d1fae5;
    border-color: #10b981;
    color: #065f46;
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

  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    padding-bottom: 0.25rem;
    border-bottom: 2px solid #e5e7eb;
  }

  .tab {
    padding: 0.75rem 1.5rem;
    border: none;
    background: none;
    cursor: pointer;
    font-weight: 500;
    color: #6b7280;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }

  .tab:hover {
    color: #374151;
    background: #f9fafb;
  }

  .tab.active {
    color: #6366f1;
    border-bottom-color: #6366f1;
    background: #f0f9ff;
  }

  .file-upload-section {
    margin-bottom: 1.5rem;
    padding: 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    background: #f9fafb;
  }

  .file-upload-section summary {
    cursor: pointer;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .file-upload-section[open] summary {
    margin-bottom: 1rem;
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #6b7280;
  }

  .custom-file-indicator {
    padding: 0.5rem 1.25rem;
    background: #fef3c7;
    color: #92400e;
    border-radius: 0.375rem;
    font-weight: 500;
    font-size: 0.875rem;
    border: 1px solid #fbbf24;
  }

  .search-section {
    position: relative;
    margin-bottom: 1.5rem;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
  }

  .search-input {
    width: -webkit-fill-available;
    padding: 0.75rem 3rem 0.75rem 1rem;
    border: 2px solid #d1d5db;
    border-radius: 0.5rem;
    font-size: 1rem;
    background: white;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }

  .search-input::placeholder {
    color: #9ca3af;
  }

  .search-icon {
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: #6b7280;
    font-size: 1.25rem;
    pointer-events: none;
  }

  .no-results {
    text-align: center;
    padding: 3rem 2rem;
    color: #6b7280;
  }

  .no-results p {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
  }

  .no-results-hint {
    font-size: 0.875rem;
    color: #9ca3af;
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

    .tabs {
      flex-wrap: wrap;
      gap: 0.25rem;
    }

    .tab {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
    }

    .copy-button {
      padding: 0.375rem 0.5rem;
      font-size: 0.75rem;
      top: 0.75rem;
      right: 0.75rem;
    }
  }
</style>

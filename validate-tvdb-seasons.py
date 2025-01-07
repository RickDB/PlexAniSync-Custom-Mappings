import os, sys, subprocess
import tvdb_v4_official, yaml
from dotenv import load_dotenv
from pathlib import Path

def getTvdbId(showName):
    # Get TVDB ID of show
    showId = None
    searchResults = tvdb.search(showName)
    for result in searchResults:
        if ((showName == result['name']) or
            ('aliases' in result and showName in result['aliases']) or
            ('translations' in result and 'eng' in result['translations'] and showName == result['translations']['eng'])
            ) and result['primary_type'] == "series":
            # print(result)
            showId = result['tvdb_id']
            break
    return showId

# Validate user-mapped season entries against TVDB seasons
def validateShowSeasons(showName, seasonsToFind):
    errors = 0

    showId = getTvdbId(showName)
    print("Validating: " + showName + " [" + str(showId) + "] - Seasons " + str(seasonsToFind))

    if (showId is None):
        print("No TVDB series result: " + showName)
        return errors
    # TODO: does not work for primary_type: movie, maybe separate method for those? Test with 5cm per second
    series = tvdb.get_series_extended(showId)
    tvdbSeasons = [season['number'] for season in series['seasons'] if season['type']['type'] == 'official']

    # print("Found show: " + showName + " (" + showId + "), with seasons: " + str(tvdbSeasons))
    # print("Validating user-mapped seasons: " + str(seasonsToFind))
    invalidSeasons = []
    for s in seasonsToFind:
        if s not in tvdbSeasons:
            errors += 1
            invalidSeasons.append(s)

    if errors > 0:
        print("Did not find season(s): " + str(invalidSeasons) + " in show: " + showName)
    return errors

# Parse temp.yaml and validate shows/seasons against TVDB
def validateMappings(file="temp.yaml"):
    errors = 0
    with open(file) as f:
        mappings = yaml.safe_load(f)
        for show in sorted(mappings['entries'], key=lambda entry: (entry['title'], entry['seasons'])):
            showName = show['title']
            seasons = set([s['season'] for s in show['seasons'] if 'season' in s])
            errors += validateShowSeasons(showName, seasons)
    return errors

# Get diff compared to main branch
def get_diff(file_path, commit_old='origin/main', commit_new='HEAD'):
    diff_output = subprocess.run(
        ['git', 'diff', '-U20', commit_old, commit_new, '--', file_path],
        capture_output=True, text=True
    )
    return diff_output.stdout

# Parse diff for changed mapping entries
def extract_changed_groups(diff_output):
    changes = []
    change_group = []
    updatedEntry = False
    for line in diff_output.splitlines():
        if line.startswith('-'): continue
        if line.startswith('+'): updatedEntry = True
        if "title:" in line:
            addIfUpdated(change_group, changes, updatedEntry)
            updatedEntry = False
            change_group = []
        change_group.append(f"{line[1:]}")
    if not changes:
        print("No season mapping changes detected in the latest commit")
        sys.exit()
    return changes

def addIfUpdated(group, collection, isUpdate):
    if group and isUpdate and "title:" in str(group) and "season:" in str(group): collection.append(group)

# Create temp yaml with changed entries
def createTempYaml(change_groups):
    lines = []
    lines.append("entries:\n")
    for group in change_groups:
        if "title:" not in str(group):
            # TODO: search full mappings to find the context
            continue
        for line in group:
            lines.append(line+"\n")
    with open('temp.yaml', 'w') as file:
        file.write(''.join(lines))

# Parse `git diff` for new mapped entries and write into temp yaml file
def extractNewMappings():
    diff_output = get_diff("series-tvdb.en.yaml")
    change_groups = extract_changed_groups(diff_output)
    createTempYaml(change_groups)

def cleanup():
    os.remove("temp.yaml")


# TODO: cross reference anilist-id show name
extractNewMappings()
# Load API Key and initialize tvdb
load_dotenv()
apikey = os.getenv("TVDB_API_KEY")
tvdb = tvdb_v4_official.TVDB(apikey)

errors = validateMappings()
if errors != 0:
    sys.exit("Found "+ str(errors) + " error(s) in the season mappings")
# cleanup()
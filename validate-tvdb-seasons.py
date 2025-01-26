import os, sys, subprocess
import tvdb_v4_official, yaml
from dotenv import load_dotenv
from deepdiff import DeepDiff, Delta


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
            series = tvdb.get_series_extended(showId)
            # only mark as found if it's an Anime show
            if any(genre['name'] == 'Anime' for genre in series['genres']):
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

    episodes = tvdb.get_series_episodes(showId)
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
    with open(file, mode='r') as f:
        mappings = yaml.safe_load(f)
        for show in sorted(mappings['entries'], key=lambda entry: (entry['title'], entry['seasons'])):
            showName = show['title']
            seasons = set([s['season'] for s in show['seasons'] if 'season' in s])
            errors += validateShowSeasons(showName, seasons)
    return errors


# Finds new and changed entries and writes them into a temp yaml file
def extractNewMappings():
    old_mappings = dict()
    new_mappings = dict()

    # get old version of TVDB file
    # TODO read old_mappings YAML from stdout so the file is not needed anymore
    with open('tvdb-old.yaml', mode='w') as f:
        subprocess.run(
            ['git', 'show', 'origin/main:series-tvdb.en.yaml'],
            text=True,
            check=True,
            stdout=f
        )

    with open('tvdb-old.yaml', mode='r') as f:
        old_mappings = yaml.safe_load(f)

    with open('series-tvdb.en.yaml', mode='r') as f:
        new_mappings = yaml.safe_load(f)

    # create new mapping file with just the changed entries
    diff = DeepDiff(old_mappings['entries'], new_mappings['entries'], ignore_order=True)
    change_groups = { "entries": [] }
    # diff.affected_root_keys contains the indices of the changed entries
    for key in diff.affected_root_keys:
        change_groups['entries'].append(new_mappings['entries'][key])

    # write the changed entries to temp.yaml
    with open('temp.yaml', mode='w') as file:
        yaml.dump(change_groups, file, encoding='utf-8', allow_unicode=True)


def cleanup():
    os.remove("tvdb-old.yaml")
    os.remove("temp.yaml")


# TODO: cross reference anilist-id show name
extractNewMappings()
# Load API Key and initialize tvdb
load_dotenv()
apikey = os.getenv("TVDB_API_KEY")
tvdb = tvdb_v4_official.TVDB(apikey)

errors = validateMappings()
if errors != 0:
    sys.exit("Found " + str(errors) + " error(s) in the season mappings")
# cleanup()
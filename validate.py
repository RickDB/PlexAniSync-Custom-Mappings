import glob
import json
import logging
import sys
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from ruamel.yaml import YAML
import requests

logger = logging.getLogger("PlexAniSync")
yaml = YAML(typ='safe')
SUCCESS = True
schema_url = "https://raw.githubusercontent.com/RickDB/PlexAniSync/master/custom_mappings_schema.json"
local_schema_path = './custom_mappings_schema.json'

# Try to load the schema from the local file
try:
    with open(local_schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
except FileNotFoundError:
    # If the local file doesn't exist, fetch it from the remote URL
    try:
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()
        
        # Save the fetched schema locally
        with open(local_schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=4)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch schema from {schema_url}: {e}")
        sys.exit(1)

for file in glob.glob("*.yaml"):
    # Create a Data object
    with open(file, 'r', encoding='utf-8') as f:
        file_mappings = yaml.load(f)
    try:
        # Validate data against the schema.
        validate(file_mappings, schema)
    except ValidationError as e:
        logger.error(f"Custom Mappings validation failed for {file}!")
        logger.error(f"{e.message} at entry {e.instance}")
        SUCCESS = False

if not SUCCESS:
    sys.exit(1)

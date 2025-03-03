import glob
import json
import logging
import sys
from typing import List
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from ruamel.yaml import YAML
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("PlexAniSync")

yaml = YAML(typ="safe")
SUCCESS = True
schema_url = "https://raw.githubusercontent.com/RickDB/PlexAniSync/master/custom_mappings_schema.json"
local_schema_path = "./custom_mappings_schema.json"

# Try to load the schema from the local file
try:
    with open(local_schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
except FileNotFoundError:
    # If the local file doesn't exist, fetch it from the remote URL
    try:
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()
        logger.info(f"Successfully fetched schema from {schema_url}")

        # Save the fetched schema locally
        with open(local_schema_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=4)
        logger.info(f"Successfully saved schema to {local_schema_path}")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch schema from {schema_url}: {e}")
        sys.exit(1)

for file in glob.glob("*.yaml"):
    # Create a Data object
    with open(file, "r", encoding="utf-8") as f:
        file_mappings = yaml.load(f)
    try:
        # Validate data against the schema.
        validate(file_mappings, schema)
        titles: List[str] = []
        
        # Read file content as lines
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, entry in enumerate(file_mappings["entries"]):
            title: str = entry["title"]
            # Check if title uses double quotes
            title_line = f'  - title: "{title}"'
            
            # Find the line number for this entry
            line_number = None
            for idx, line in enumerate(lines):
                if title_line in line:
                    line_number = idx
                    break
                    
            if line_number is None:
                raise ValidationError(f"Could not find title line for '{title}'", instance=entry)
                
            # Check for double quotes
            if f'"{title}"' not in lines[line_number]:
                raise ValidationError(f"Title '{title}' must be wrapped in double quotes", instance=entry)
            
            # Check for newline between entries (except before first entry)
            if i > 0 and line_number > 0:
                prev_line = lines[line_number - 1].strip()
                if prev_line != "":
                    raise ValidationError(f"Missing blank line before entry '{title}'", instance=entry)
            
            if title.lower() in titles:
                raise ValidationError(f"{title} is already mapped", instance=entry)

            titles.append(title.lower())
        logger.info(f"Custom Mappings validation successful for {file}")
    except ValidationError as e:
        logger.error(f"Custom Mappings validation failed for {file}!")
        logger.error(f"{e.message} at entry {e.instance}")
        SUCCESS = False

if not SUCCESS:
    sys.exit(1)

import glob
import json
import logging
import sys
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from ruamel.yaml import YAML

logger = logging.getLogger("PlexAniSync")
yaml = YAML(typ='safe')
SUCCESS = True

with open('./custom_mappings_schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

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

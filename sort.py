import glob
import logging

from ruamel.yaml import YAML

logger = logging.getLogger("PlexAniSync")

yaml = YAML()
yaml.default_flow_style = False
yaml.sort_base_mapping_type_on_output = False
yaml.preserve_quotes = True
yaml.indent(sequence=4, offset=2)
yaml.width = 1024

for file in glob.glob("*.yaml"):
    with open(file, 'r+b') as f:
        file_mappings = yaml.load(f)
        file_mappings["entries"].sort(key=lambda entry: entry["title"].lower())
        # Jump to beginning of file and overwrite with sorted entries
        f.seek(0)
        yaml.dump(file_mappings, f)
        f.truncate()

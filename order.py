import glob
import logging

from ruamel.yaml import YAML

logger = logging.getLogger("PlexAniSync")
yaml = YAML(typ='safe')
SUCCESS = True

for file in glob.glob("*.yaml"):
    with open(file, 'r', encoding='utf-8') as f:
        file_mappings = yaml.load(f)
        sortedList = sorted(file_mappings.get("entries"), key=lambda entry: entry["title"])
        yaml.default_flow_style = False
        yaml.sort_base_mapping_type_on_output = False
        yaml.dump({"entries": sortedList}, open(file, "w"))

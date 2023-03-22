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
    with open(file, 'r', encoding='utf-8') as f:
        file_mappings = yaml.load(f)
        file_mappings["entries"] = sorted(file_mappings["entries"], key=lambda entry: entry["title"].lower())
        ff = open(file, "w", encoding='utf-8')
        yaml.dump(file_mappings, ff)
        ff.close()
        f.close()

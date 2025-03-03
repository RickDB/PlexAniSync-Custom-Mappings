import glob
import logging

from ruamel.yaml import YAML

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("PlexAniSync")

yaml = YAML()
yaml.default_flow_style = False
yaml.sort_base_mapping_type_on_output = False
yaml.preserve_quotes = True
yaml.indent(sequence=4, offset=2)
yaml.width = 1024

for file in glob.glob("*.yaml"):
    with open(file, "r+b") as f:
        file_mappings = yaml.load(f)
        original_order = [(i, entry["title"]) for i, entry in enumerate(file_mappings["entries"])]
        file_mappings["entries"].sort(key=lambda entry: entry["title"].lower())
        new_order = [(i, entry["title"]) for i, entry in enumerate(file_mappings["entries"])]
        
        # Log changes in position
        moved_items = []
        for new_pos, (title, _) in enumerate(sorted((title.lower(), title) for _, title in original_order)):
            old_pos = next(i for i, (_, t) in enumerate(original_order) if t.lower() == title)
            if old_pos != new_pos:
                moved_items.append(f"'{title}' moved from position {old_pos} to {new_pos}")
        
        if moved_items:
            logger.info(f"Sorting {file}:")
            for move in moved_items:
                logger.info(move)
        else:
            logger.info(f"{file} was already properly sorted")
            
        # Jump to beginning of file and overwrite with sorted entries
        f.seek(0)
        yaml.dump(file_mappings, f)
        f.truncate()

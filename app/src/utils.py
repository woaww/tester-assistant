import yaml
# from text_constants import *


def load_prompts(file_path="prompts.yaml"):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

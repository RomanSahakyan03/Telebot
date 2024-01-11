import json
import os

# Get the absolute path of the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute texts path
texts_path = os.path.join(current_dir, 'typetalk_texts.json')

# Load the JSON data from a file
with open(texts_path, 'r', encoding="UTF-8") as f:
        texts = json.load(f)

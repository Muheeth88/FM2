import json
import os

with open(r"D:\Workspace\FM2\feature-extraction-response.json", "r") as f:
    features = json.load(f)

all_paths = set()
for feat in features:
    for category in ["test_files", "dependent_files", "config_files", "shared_modules"]:
        for file_ref in feat.get(category, []):
            all_paths.add(file_ref["path"])

print(f"Total unique file paths: {len(all_paths)}")

missing = []
existing = []
for p in sorted(all_paths):
    # Normalize path for Windows
    norm = p.replace("/", os.sep)
    if os.path.isfile(norm):
        existing.append(p)
    else:
        missing.append(p)

print(f"Existing files: {len(existing)}")
print(f"Missing files: {len(missing)}")
print()

if missing:
    print("=== MISSING FILES ===")
    for p in missing:
        # Show just the relative part after source/
        short = p.split("/source/")[-1] if "/source/" in p else p
        print(f"  {short}")

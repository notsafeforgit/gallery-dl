import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

# Replace check_strict_fn with one that only checks exercised paths
check_strict_fn = """
def check_strict():
    \"\"\"Validate that the configuration contains no unmatched/unaccessed keys in the branches visited.\"\"\"
    if not _config_strict:
        return 0

    errors = 0

    def _check(conf_dict, accessed_dict, current_path=""):
        nonlocal errors
        if accessed_dict is None or None in accessed_dict:
            # The entire dictionary was accessed directly
            return

        for k, v in conf_dict.items():
            full_path = current_path + str(k)

            if k not in accessed_dict:
                # We never accessed this key at all!
                # If the parent dict was exercised (some keys were accessed),
                # this is an unmatched key!
                log.error("Unknown configuration key '%s' at '%s'", k, full_path)
                errors += 1
            elif isinstance(v, dict) and isinstance(accessed_dict[k], dict):
                # We accessed this sub-dict path, so recurse
                _check(v, accessed_dict[k], full_path + ".")

    # We only want to flag errors inside sections that were actually touched.
    # We can do this by recursing from the root but treating the root specifically.
    # Wait, if `_accessed` is empty, nothing runs.
    # What if a top-level extractor like "youtube" is never accessed?
    # `k="youtube"` is in `_config["extractor"]`.
    # `accessed_dict` for `"extractor"` might contain `"reddit"`.
    # If `_check` iterates over `_config["extractor"]`, it sees `"youtube"` not in `accessed_dict`.
    # It will log `"youtube"` as an error! That's bad because the user might just not have run youtube!
    pass
"""

# Let's write the actual fix
# For top-level "extractor", "downloader", "output", "postprocessor", "cache"
# we should ONLY recurse into keys that ARE in accessed_dict!
# Wait! The user's config looks like:
# {
#   "extractor": {
#     "reddit": {"archive": true, "archve": true},
#     "youtube": {"quality": "1080p"}
#   }
# }
# If `youtube` isn't run, `extractor.youtube` is never accessed.
# If we flag `youtube` because it's in `_config["extractor"]` but not in `_accessed["extractor"]`, we flag valid keys!
# The user said: "It should be ok to only validate keys for excractor paths actually being exercised"
# This means we only recurse if `k in accessed_dict`.
# But wait! If we ONLY recurse if `k in accessed_dict`, how do we ever find a typo?
# A typo like `archve` is inside `reddit`.
# `reddit` IS in `accessed_dict`! So we recurse into `reddit`.
# `reddit` has `archive` and `archve`.
# `accessed_dict["reddit"]` has `archive`.
# So inside `reddit`, `archve` is NOT in `accessed_dict["reddit"]`!
# Should we flag `archve`? Yes!
# So the rule is:
# For nodes that represent EXTRACTORS, we ONLY recurse if they are in accessed_dict. We DON'T flag them if they are missing from accessed_dict.
# For nodes that represent SETTINGS inside an extractor, we FLAG them if they are missing from accessed_dict!

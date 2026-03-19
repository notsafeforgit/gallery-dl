# It failed to catch because depth was calculated incorrectly!
# "extractor." -> count is 1. depth = 1.
# `reddit` is depth=1. `archive` is depth=2.
# So `current_path="extractor.reddit."`. `count('.')` is 2.
# Yes, depth=2.
# Wait! In `_check(_config, _accessed, current_path="")`, `current_path` is empty.
# `extractor` has `depth=0`. Not in `accessed_dict`? It is!
# `reddit` has `depth=1`. `current_path="extractor."`. It is in `accessed_dict`!
# `archive` has `depth=2`. `current_path="extractor.reddit."`. It is in `accessed_dict`!
# `archve` has `depth=2`. Not in `accessed_dict`!
# It should flag it!
# But `track39.py` printed "Failed"! Why?

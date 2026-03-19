import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

# I also need to track `config.get(("path",))` where `key` is missing or None to mark the path as accessed!
# Wait, `get` takes `path` and `key`. If someone does `config.get(("extractor", "twitter"), "archve")`, it marks `("extractor", "twitter", "archve")`.
# BUT what if they do `config.get(("extractor",), "twitter")` which returns a dictionary?
# Then `get` is called with path `("extractor",)` and key `"twitter"`.
# My _record_access does:
# d = _accessed
# for p in ("extractor",):
#     d = d.setdefault(p, {})
# d["twitter"] = None
#
# But then the code iterates over `twitter_conf.items()`.
# If `_accessed["extractor"]["twitter"] = None`, then `_check` sees that `isinstance(accessed_dict["twitter"], dict)` is FALSE.
# And when `_check` recurses, it won't recurse because it's not a dict in `_accessed`!
# Ah! In my `_record_access`, if `key is not None`, I do `d[key] = None`.
# But `twitter_conf` is a dict! So we SHOULD mark `d["twitter"] = {None: None}` to indicate the whole sub-dict was accessed!

# Let's fix `_record_access` and `check_strict`.

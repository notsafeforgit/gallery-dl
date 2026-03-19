import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

# `check_strict` now perfectly recurses into accessed dictionaries.
# BUT wait! If someone sets `config.set(("extractor", "reddit", "sub"), "archve", True)`
# depth checks:
# extractor (0, no) -> in accessed? Yes.
# reddit (1, no) -> in accessed? Yes.
# sub (2, YES!) -> in accessed? No!
# What if `sub` was never accessed? It gets flagged! That is exactly what we want.
# BUT what if they are adding a global option like `config.set((), "archve", True)`?
# current_path="" (count=0).
# In `_check`, depth=0. It skips if not accessed. Wait, top level keys shouldn't be skipped!
# What if someone has `{"archve": true, "extractor": {}}`?
# "archve" is at depth=0. It will NOT be flagged because `depth >= 2`!

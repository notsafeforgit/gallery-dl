import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

content = content.replace('if not getattr(util, "CONFIG_STRICT", False):', 'if not _config_strict:')
with open("gallery_dl/config.py", "w") as f:
    f.write(content)

import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

new_check = """
def check_strict():
    \"\"\"Validate that the configuration contains no unmatched/unaccessed keys in the branches visited.\"\"\"
    if not getattr(util, "CONFIG_STRICT", False):
        return 0

    errors = 0
    import logging
    log = logging.getLogger("config")

    def _check(conf_dict, accessed_dict, current_path=""):
        nonlocal errors
        if accessed_dict is None or None in accessed_dict:
            return

        for k, v in conf_dict.items():
            full_path = current_path + str(k)

            # The top levels ("extractor", "downloader", etc) and their immediate children (e.g. "reddit", "youtube")
            # represent modules that might just not have been exercised during this specific run.
            # We don't want to flag an entire un-exercised module as an error.
            # However, if a module WAS exercised (i.e. it is in accessed_dict), we MUST recurse into it
            # to check if any of its specific settings were typos.
            depth = current_path.count('.')

            if k not in accessed_dict:
                # If it's a top-level category or a module name (depth 0 or 1),
                # missing from accessed_dict just means it wasn't run. Do not flag.
                if depth >= 2:
                    # Once we are deeper than "extractor.module.", any unaccessed key is a typo!
                    log.error("Unknown configuration key '%s' at '%s'", k, full_path)
                    errors += 1
            else:
                if isinstance(v, dict) and isinstance(accessed_dict[k], dict):
                    _check(v, accessed_dict[k], full_path + ".")

    _check(_config, _accessed)
    if errors > 0:
        raise SystemExit(2)
    return 0
"""

content = re.sub(r'\ndef check_strict\(\):.*', '\n' + new_check, content, flags=re.DOTALL)

with open("gallery_dl/config.py", "w") as f:
    f.write(content)

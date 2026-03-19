import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

new_check = """
def check_strict():
    \"\"\"Validate that the configuration contains no unmatched/unaccessed keys in the branches visited.\"\"\"
    if not _config_strict:
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

            if k not in accessed_dict:
                # If it's a top-level category ("extractor", "downloader", "output", "postprocessor", "cache", "subconfigs")
                # and it's missing from accessed_dict, it just means it wasn't run.
                # If it's a module name (e.g. "reddit", "youtube") under "extractor",
                # and it's missing from accessed_dict, it also means it wasn't run.
                # Anything else that is missing from accessed_dict is a typo!
                is_unexercised_module = False
                if current_path == "" and k in ("extractor", "downloader", "output", "postprocessor", "cache", "subconfigs"):
                    is_unexercised_module = True
                elif current_path == "extractor.":
                    is_unexercised_module = True
                elif current_path == "downloader.":
                    is_unexercised_module = True

                if not is_unexercised_module:
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

import re

with open("gallery_dl/config.py", "r") as f:
    content = f.read()

# 1. Add _accessed structure at top
content = content.replace('_default_configs = ()\n', '_default_configs = ()\n_accessed = {}\n')

# 2. Helper to record access
record_helper = """
def _record_access(path, key=None):
    if not _config_strict:
        return
    d = _accessed
    for p in path:
        d = d.setdefault(p, {})
    if key is not None:
        d[key] = None
    elif not d:
        # mark entire dict as accessed
        d[None] = None

"""

content = content.replace('# public interface', '# public interface\n\n_config_strict = False\n' + record_helper)

# 3. Patch get()
content = content.replace(
    '    try:\n        for p in path:\n            conf = conf[p]\n        return conf[key]',
    '    _record_access(path, key)\n    try:\n        for p in path:\n            conf = conf[p]\n        return conf[key]'
)

# 4. Patch interpolate()
content = content.replace(
    'def interpolate(path, key, default=None, conf=_config):\n    """Interpolate the value of \'key\'"""\n    if key in conf:\n        return conf[key]',
    'def interpolate(path, key, default=None, conf=_config):\n    """Interpolate the value of \'key\'"""\n    _record_access((), key)\n    if key in conf:\n        return conf[key]'
)
content = content.replace(
    '        for p in path:\n            conf = conf[p]\n            if key in conf:\n                default = conf[key]',
    '        current_path = []\n        for p in path:\n            current_path.append(p)\n            _record_access(current_path, key)\n            conf = conf[p]\n            if key in conf:\n                default = conf[key]'
)

# 5. Patch interpolate_common()
content = content.replace(
    'def interpolate_common(common, paths, key, default=None, conf=_config):\n    """Interpolate the value of \'key\'\n    using multiple \'paths\' along a \'common\' ancestor\n    """\n    if key in conf:\n        return conf[key]',
    'def interpolate_common(common, paths, key, default=None, conf=_config):\n    """Interpolate the value of \'key\'\n    using multiple \'paths\' along a \'common\' ancestor\n    """\n    _record_access((), key)\n    if key in conf:\n        return conf[key]'
)
content = content.replace(
    '    try:\n        for p in common:\n            conf = conf[p]\n            if key in conf:\n                default = conf[key]',
    '    try:\n        current_path = []\n        for p in common:\n            current_path.append(p)\n            _record_access(current_path, key)\n            conf = conf[p]\n            if key in conf:\n                default = conf[key]'
)
content = content.replace(
    '        try:\n            for p in path:\n                c = c[p]\n                if key in c:\n                    value = c[key]',
    '        try:\n            current_path = list(common)\n            for p in path:\n                current_path.append(p)\n                _record_access(current_path, key)\n                c = c[p]\n                if key in c:\n                    value = c[key]'
)

# 6. Patch accumulate()
content = content.replace(
    'def accumulate(path, key, conf=_config):\n    """Accumulate the values of \'key\' along \'path\'"""\n    result = []\n    try:\n        if key in conf:',
    'def accumulate(path, key, conf=_config):\n    """Accumulate the values of \'key\' along \'path\'"""\n    _record_access((), key)\n    result = []\n    try:\n        if key in conf:'
)
content = content.replace(
    '        for p in path:\n            conf = conf[p]\n            if key in conf:',
    '        current_path = []\n        for p in path:\n            current_path.append(p)\n            _record_access(current_path, key)\n            conf = conf[p]\n            if key in conf:'
)

# 7. Add check_strict() function at the end
check_strict_fn = """
def check_strict():
    \"\"\"Validate that the configuration contains no unaccessed keys.\"\"\"
    if not _config_strict:
        return 0

    errors = 0

    def _check(conf_dict, accessed_dict, current_path=""):
        nonlocal errors
        if None in accessed_dict:
            # The entire dictionary was accessed (e.g. iterate over all subkeys)
            return

        for k, v in conf_dict.items():
            full_path = current_path + str(k)

            # Sub-dictionaries
            if isinstance(v, dict):
                if k in accessed_dict and isinstance(accessed_dict[k], dict):
                    # We accessed this sub-dict path, so recurse
                    _check(v, accessed_dict[k], full_path + ".")
                else:
                    # We never accessed this dictionary path AT ALL.
                    # This means it's fully unmatched/unused.
                    log.error("Unknown configuration key '%s' at '%s'", k, full_path)
                    errors += 1
            else:
                # Regular keys
                if k not in accessed_dict:
                    # The key was never accessed individually, nor was the parent dict fully accessed
                    log.error("Unknown configuration key '%s' at '%s'", k, full_path)
                    errors += 1

    _check(_config, _accessed)
    if errors > 0:
        raise SystemExit(2)
    return 0
"""
content += check_strict_fn

with open("gallery_dl/config.py", "w") as f:
    f.write(content)

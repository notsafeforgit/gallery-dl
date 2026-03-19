# -*- coding: utf-8 -*-

# Copyright 2015-2026 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Global configuration module"""

import sys
import os.path
import logging
from . import util

log = logging.getLogger("config")


# --------------------------------------------------------------------
# internals

_config = {}
_files = []
_type = "json"
_load = util.json_loads
_default_configs = ()
_accessed = {}
_config_strict = False
_accessed = {}


# --------------------------------------------------------------------
# public interface

def _record_access(path, key=None):
    if not _config_strict:
        return
    d = _accessed

    # Traverse config dictionary to see if the value we are accessing is a dictionary
    try:
        conf = _config
        for p in path:
            conf = conf[p]
        if key is not None:
            conf = conf[key]

        is_dict = isinstance(conf, dict)
    except KeyError:
        is_dict = False

    for p in path:
        d = d.setdefault(p, {})

    if key is not None:
        if is_dict:
            # The value is a dictionary. Mark its subtree as fully accessed via a special key `None`
            sub = d.setdefault(key, {})
            sub[None] = None
        else:
            d[key] = None
    else:
        if is_dict:
            d[None] = None

_config_strict = False

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




def default(type=None):
    global _type
    global _load
    global _default_configs

    if not type or (type := type.lower()) == "json":
        _type = type = "json"
        _load = util.json_loads
    elif type == "yaml":
        _type = "yaml"
        from yaml import safe_load as _load
    elif type == "toml":
        _type = "toml"
        try:
            from tomllib import loads as _load
        except ImportError:
            from toml import loads as _load
    else:
        raise ValueError(f"Unsupported config file type '{type}'")

    if util.WINDOWS:
        _default_configs = [
            r"%APPDATA%\gallery-dl\config." + type,
            r"%USERPROFILE%\gallery-dl\config." + type,
            r"%USERPROFILE%\gallery-dl.conf",
        ]
    else:
        _default_configs = [
            "/etc/gallery-dl.conf",
            "${XDG_CONFIG_HOME}/gallery-dl/config." + type
            if os.environ.get("XDG_CONFIG_HOME") else
            "${HOME}/.config/gallery-dl/config." + type,
            "${HOME}/.gallery-dl.conf",
        ]

    if util.EXECUTABLE:
        # look for config file in PyInstaller executable directory (#682)
        _default_configs.append(os.path.join(
            os.path.dirname(sys.executable),
            "gallery-dl.conf",
        ))


default(os.environ.get("GDL_CONFIG_TYPE"))


def initialize():
    paths = list(map(util.expand_path, _default_configs))

    for path in paths:
        if os.access(path, os.R_OK | os.W_OK):
            log.error("There is already a configuration file at '%s'", path)
            return 1

    for path in paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "x", encoding="utf-8") as fp:
                fp.write("""\
{
    "extractor": {

    },
    "downloader": {

    },
    "output": {

    },
    "postprocessor": {

    }
}
""")
            break
        except OSError as exc:
            log.debug("%s: %s", exc.__class__.__name__, exc)
    else:
        log.error("Unable to create a new configuration file "
                  "at any of the default paths")
        return 1

    log.info("Created a basic configuration file at '%s'", path)
    return 0


def open_extern():
    for path in _default_configs:
        path = util.expand_path(path)
        if os.access(path, os.R_OK | os.W_OK):
            break
    else:
        log.warning("Unable to find any writable configuration file")
        return 1

    if util.WINDOWS:
        openers = ("explorer", "notepad")
    else:
        openers = ("xdg-open", "open")
        if editor := os.environ.get("EDITOR"):
            openers = (editor,) + openers

    import shutil
    for opener in openers:
        if opener := shutil.which(opener):
            break
    else:
        log.warning("Unable to find a program to open '%s' with", path)
        return 1

    log.info("Running '%s %s'", opener, path)
    retcode = util.Popen((opener, path)).wait()

    if not retcode:
        try:
            with open(path, encoding="utf-8") as fp:
                _load(fp.read())
        except Exception as exc:
            log.warning("%s when parsing '%s': %s",
                        exc.__class__.__name__, path, exc)
            return 2

    return retcode


def status():
    from .output import stdout_write

    paths = []
    for path in _default_configs:
        path = util.expand_path(path)

        try:
            with open(path, encoding="utf-8") as fp:
                _load(fp.read())
        except FileNotFoundError:
            status = ""
        except OSError as exc:
            log.debug("%s: %s", exc.__class__.__name__, exc)
            status = "Inaccessible"
        except ValueError as exc:
            log.debug("%s: %s", exc.__class__.__name__, exc)
            status = "Invalid " + _type.upper()
        except Exception as exc:
            log.debug("%s: %s", exc.__class__.__name__, exc)
            status = "Unknown"
        else:
            status = "OK"

        paths.append((path, status))

    fmt = f"{{:<{max(len(p[0]) for p in paths)}}} : {{}}\n".format
    for path, status in paths:
        stdout_write(fmt(path, status))


def remap_categories():
    opts = _config.get("extractor")
    if not opts:
        return

    cmap = opts.get("config-map")
    if cmap is None:
        cmap = (
            ("coomerparty" , "coomer"),
            ("kemonoparty" , "kemono"),
            ("giantessbooru", "sizebooru"),
            ("koharu"      , "schalenetwork"),
            ("naver"       , "naver-blog"),
            ("chzzk"       , "naver-chzzk"),
            ("naverwebtoon", "naver-webtoon"),
            ("pixiv"       , "pixiv-novel"),
            ("saint"       , "turbo"),
        )
    elif not cmap:
        return
    elif isinstance(cmap, dict):
        cmap = cmap.items()

    for old, new in cmap:
        if old in opts and new not in opts:
            opts[new] = opts[old]


def load(files=None, strict=False, loads=None, conf=_config):
    """Load configuration files"""
    if loads is None:
        loads = _load

    for pathfmt in files or _default_configs:
        path = util.expand_path(pathfmt)
        try:
            with open(path, encoding="utf-8") as fp:
                config = loads(fp.read())
        except OSError as exc:
            if strict:
                log.error(exc)
                raise SystemExit(1)
        except Exception as exc:
            log.error("%s when loading '%s': %s",
                      exc.__class__.__name__, path, exc)
            if strict:
                raise SystemExit(2)
        else:
            if not conf:
                conf.update(config)
            else:
                util.combine_dict(conf, config)
            _files.append(pathfmt)

            if "subconfigs" in config:
                if subconfigs := config["subconfigs"]:
                    if isinstance(subconfigs, str):
                        subconfigs = (subconfigs,)
                    load(subconfigs, strict, loads, conf)


def clear():
    """Reset configuration to an empty state"""
    _config.clear()


def get(path, key, default=None, conf=_config):
    """Get the value of property 'key' or a default value"""
    _record_access(path, key)
    try:
        for p in path:
            conf = conf[p]
        return conf[key]
    except Exception:
        return default


def interpolate(path, key, default=None, conf=_config):
    """Interpolate the value of 'key'"""
    _record_access((), key)
    if key in conf:
        return conf[key]
    try:
        current_path = []
        for p in path:
            current_path.append(p)
            _record_access(current_path, key)
            conf = conf[p]
            if key in conf:
                default = conf[key]
    except Exception:
        pass
    return default


def interpolate_common(common, paths, key, default=None, conf=_config):
    """Interpolate the value of 'key'
    using multiple 'paths' along a 'common' ancestor
    """
    _record_access((), key)
    if key in conf:
        return conf[key]

    # follow the common path
    try:
        current_path = []
        for p in common:
            current_path.append(p)
            _record_access(current_path, key)
            conf = conf[p]
            if key in conf:
                default = conf[key]
    except Exception:
        return default

    # try all paths until a value is found
    value = util.SENTINEL
    for path in paths:
        c = conf
        try:
            current_path = list(common)
            for p in path:
                current_path.append(p)
                _record_access(current_path, key)
                c = c[p]
                if key in c:
                    value = c[key]
        except Exception:
            pass
        if value is not util.SENTINEL:
            return value
    return default


def accumulate(path, key, conf=_config):
    """Accumulate the values of 'key' along 'path'"""
    _record_access((), key)
    result = []
    try:
        if key in conf:
            if value := conf[key]:
                if isinstance(value, list):
                    result.extend(value)
                else:
                    result.append(value)
        current_path = []
        for p in path:
            current_path.append(p)
            _record_access(current_path, key)
            conf = conf[p]
            if key in conf:
                if value := conf[key]:
                    if isinstance(value, list):
                        result[:0] = value
                    else:
                        result.insert(0, value)
    except Exception:
        pass
    return result


def set(path, key, value, conf=_config):
    """Set the value of property 'key' for this session"""
    for p in path:
        try:
            conf = conf[p]
        except KeyError:
            conf[p] = conf = {}
    conf[key] = value


def setdefault(path, key, value, conf=_config):
    """Set the value of property 'key' if it doesn't exist"""
    for p in path:
        try:
            conf = conf[p]
        except KeyError:
            conf[p] = conf = {}
    return conf.setdefault(key, value)


def unset(path, key, conf=_config):
    """Unset the value of property 'key'"""
    try:
        for p in path:
            conf = conf[p]
        del conf[key]
    except Exception:
        pass


class apply():
    """Context Manager: apply a collection of key-value pairs"""

    def __init__(self, kvlist):
        self.original = []
        self.kvlist = kvlist

    def __enter__(self):
        for path, key, value in self.kvlist:
            self.original.append((path, key, get(path, key, util.SENTINEL)))
            set(path, key, value)

    def __exit__(self, exc_type, exc_value, traceback):
        self.original.reverse()
        for path, key, value in self.original:
            if value is util.SENTINEL:
                unset(path, key)
            else:
                set(path, key, value)







def check():
    """Perform strict configuration validation by ensuring all keys are valid."""
    try:
        from .config_schema import VALID_KEYS
    except ImportError:
        log.warning("config_schema.py not found; strict configuration validation is disabled.")
        return

    def _validate(conf_dict, current_path=""):
        success = True
        for k, v in conf_dict.items():
            full_path = current_path + str(k)

            if isinstance(k, str):
                # Whitelist structural or highly dynamic paths
                if ">" in k:
                    pass
                elif full_path.startswith("postprocessor.") and len(current_path) == 14:
                    pass
                elif ".directory." in full_path or full_path.endswith(".directory"):
                    pass
                elif ".postprocessors." in full_path:
                    pass
                elif ".cookies." in full_path:
                    pass
                elif ".path-restrict." in full_path:
                    pass
                elif full_path.startswith("extractor.keywords."):
                    pass
                # Many extractors group configurations under dynamic sub-keys (e.g. mastodon domains, tags, instances)
                # If the key is not in VALID_KEYS, check if it's an instance dictionary
                elif k not in VALID_KEYS:
                    if isinstance(v, dict) and ("root" in v or "api_root" in v or "access-token" in v):
                        pass
                    else:
                        log.error("Unknown configuration key '%s' at '%s'", k, full_path)
                        success = False

            if isinstance(v, dict):
                if not _validate(v, full_path + "."):
                    success = False

        return success

    if not _validate(_config):
        raise SystemExit(2)



def check_strict():
    """Validate that the configuration contains no unmatched/unaccessed keys in the branches visited."""
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

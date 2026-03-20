#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import ast
import unittest

class TestConfigSchema(unittest.TestCase):
    def test_config_schema_completeness(self):
        """
        Ensures that all configuration keys accessed or defined in the codebase
        are present in `gallery_dl.config_schema.VALID_KEYS`.
        """
        from gallery_dl import config_schema

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gallery_dl_dir = os.path.join(base_dir, "gallery_dl")

        extracted_keys = set()

        def extract_strings_from_node(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                extracted_keys.add(node.value)
            elif isinstance(node, ast.Tuple) or isinstance(node, ast.List):
                for elt in node.elts:
                    extract_strings_from_node(elt)

        def is_config_target(node):
            if isinstance(node, ast.Name):
                return node.id in ("config", "_config", "conf", "options", "kwargs")
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id in ("self", "cls"):
                    return node.attr in ("config", "options")
            return False

        for root, _, files in os.walk(gallery_dl_dir):
            for file in files:
                if not file.endswith(".py") or file == "config_schema.py":
                    continue
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        src = fp.read()
                    tree = ast.parse(src)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id in ("category", "subcategory", "basecategory"):
                                    extract_strings_from_node(node.value)

                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if is_config_target(target):
                                    if isinstance(node.value, ast.Dict):
                                        for key in node.keys:
                                            if key is not None:
                                                extract_strings_from_node(key)

                        if isinstance(node, ast.Call):
                            if is_config_target(node.func):
                                if len(node.args) >= 1:
                                    extract_strings_from_node(node.args[0])

                            elif isinstance(node.func, ast.Attribute) and is_config_target(node.func.value):
                                if node.func.attr in ("get", "interpolate", "accumulate", "set", "setdefault", "unset", "pop", "getboolean"):
                                    if len(node.args) >= 1:
                                        extract_strings_from_node(node.args[0])

                                    if len(node.args) >= 2 and node.func.attr in ("get", "interpolate", "accumulate", "set", "setdefault", "unset"):
                                        target_name = node.func.value.id if isinstance(node.func.value, ast.Name) else node.func.value.attr
                                        if target_name in ("config", "_config", "conf"):
                                            extract_strings_from_node(node.args[1])

                                elif node.func.attr == "interpolate_common":
                                    if len(node.args) >= 3:
                                        extract_strings_from_node(node.args[0])
                                        extract_strings_from_node(node.args[1])
                                        extract_strings_from_node(node.args[2])

                        if isinstance(node, ast.Subscript):
                            if is_config_target(node.value):
                                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                                    extracted_keys.add(node.slice.value)

                except Exception:
                    pass

        filtered_keys = set(["#"])
        for k in extracted_keys:
            if not isinstance(k, str): continue

            if len(k) < 2 and k not in ('\\\\', '/', '|', ':', '*', '?', '"', '<', '>'): continue
            if " " in k: continue
            if "\\n" in k: continue
            if "\\x00" in k or "\\x1f" in k or "\\x7f" in k: continue
            if "://" in k: continue
            if "{" in k or "}" in k: continue
            if "[" in k or "]" in k: continue
            if "(" in k or ")" in k: continue
            if "%" in k: continue
            if k.startswith("/") and len(k) > 1: continue
            filtered_keys.add(k)

        missing_keys = filtered_keys - config_schema.VALID_KEYS

        self.assertFalse(
            missing_keys,
            f"The following configuration keys were accessed or defined in the codebase but are missing from `gallery_dl/config_schema.py`:\\n{missing_keys}\\n\\n"
            f"Please add these keys to `VALID_KEYS` in `gallery_dl/config_schema.py` so they are permitted when running `--config-strict`."
        )

if __name__ == "__main__":
    unittest.main()

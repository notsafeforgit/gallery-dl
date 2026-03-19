import re

with open("gallery_dl/__init__.py", "r") as f:
    content = f.read()

content = content.replace(
"""        if args.config_strict:
            config.check()

        output.configure_standard_streams()""",
"""        if args.config_strict:
            config._config_strict = True
            import atexit
            atexit.register(config.check_strict)

        output.configure_standard_streams()"""
)

with open("gallery_dl/__init__.py", "w") as f:
    f.write(content)

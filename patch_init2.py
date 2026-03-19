import re

with open("gallery_dl/__init__.py", "r") as f:
    content = f.read()

# Replace the previous check() at loading with check_strict() at the end
content = content.replace(
"""        if args.config_strict:
            config.check()

        output.configure_standard_streams()""",
"""        if args.config_strict:
            config._config_strict = True

        output.configure_standard_streams()"""
)

# And add the atexit check at the very end of main()
content = content.replace(
"""                input_manager.next()
            return retval
        return 0

    except KeyboardInterrupt:""",
"""                input_manager.next()

            if args.config_strict:
                config.check_strict()

            return retval
        return 0

    except KeyboardInterrupt:"""
)

# There is a problem: main() has early returns like `if args.cache_status: return 0`.
# In python, `atexit` is safer. Let's add it via atexit!

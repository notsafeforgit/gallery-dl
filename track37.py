from gallery_dl import config

config._config_strict = True

# Simulate a full sub-dict access
config.set(("extractor", "reddit"), "options_dict", {"archive": True, "archve": True})

# Someone calls get on the dict itself
val = config.get(("extractor", "reddit"), "options_dict")

try:
    config.check_strict()
    print("Dict unpacked safely, no typo because whole dict was requested.")
except SystemExit:
    print("Wait, if a dict is requested, its contents shouldn't trigger typos since the dict itself was used!")

from gallery_dl import config

config._config_strict = True

config.set((), "archve", True)
config.set(("extractor", "reddit"), "archive", True)
config.set(("extractor", "youtube"), "quality", "1080p")

config.get(("extractor", "reddit"), "archive")

try:
    config.check_strict()
    print("Failed")
except SystemExit:
    print("Caught")

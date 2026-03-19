from gallery_dl import config

config._config_strict = True

config.set(("extractor", "reddit"), "archive", True)
config.set(("extractor", "reddit"), "archve", True)

config.get(("extractor", "reddit"), "archive")

try:
    config.check_strict()
    print("Failed to catch typo")
except SystemExit:
    print("Caught typo")

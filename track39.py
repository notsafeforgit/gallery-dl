from gallery_dl import config, util
import logging
logging.basicConfig()

util.CONFIG_STRICT = True

# Simulate a full sub-dict access
config.set(("extractor", "reddit"), "archive", True)
config.set(("extractor", "reddit"), "archve", True)
config.set(("extractor", "youtube"), "quality", "1080p")

# Only reddit runs!
config.get(("extractor", "reddit"), "archive")

try:
    config.check_strict()
    print("Failed")
except SystemExit:
    print("Caught")

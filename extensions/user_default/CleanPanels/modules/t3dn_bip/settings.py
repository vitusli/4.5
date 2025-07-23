import os

# Print warnings about which features are supported.
# WARNINGS = False
WARNINGS = True

# Use magic bytes to check file type, instead of extension.
USE_MAGIC = False

# Max number of threads used for loading image contents.
MAX_THREADS = os.cpu_count() - 2

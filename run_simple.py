#!/usr/bin/env python3
"""
Simplified runner that patches SSL globally before everything
"""
import ssl
import os

# MUST be first - patch SSL before any imports
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Suppress all SSL warnings
import warnings
warnings.filterwarnings('ignore')

# Monkey-patch httpcore to use unverified SSL
try:
    import httpcore._backends.sync as httpcore_sync
    original_start_tls = httpcore_sync.SyncStream.start_tls

    def patched_start_tls(self, *args, **kwargs):
        kwargs['ssl_context'] = ssl._create_unverified_context()
        return original_start_tls(self, *args, **kwargs)

    httpcore_sync.SyncStream.start_tls = patched_start_tls
except Exception as e:
    print(f"Warning: Could not patch httpcore: {e}")

# Now run main
if __name__ == "__main__":
    # Import and run after SSL is patched
    from main import main
    main()

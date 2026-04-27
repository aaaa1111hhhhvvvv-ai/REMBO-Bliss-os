# REMBO Health Check APK
# Status: Build separately using Android Studio / AAPT2
# The health check functionality is handled by rembo-sentinel.sh
# which provides equivalent monitoring without requiring an APK.
#
# The Sentinel daemon (overlay/bin/rembo-sentinel.sh) monitors:
# - GPU driver status (NVK initialization)
# - GSP firmware loading
# - Sovereign property injection
# - OverlayFS mount integrity
# - Performance metrics (Hz, polling rates)

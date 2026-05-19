"""Slim init for the review-pipeline export.

The full ``utils`` package in the source repo re-exports task/subprocess
helpers and pulls in PyYAML at module load. The exported pipeline only needs
``runtime_paths``, so import that explicitly:

    from utils.runtime_paths import claude_home, review_monitor_dir
"""

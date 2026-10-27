# DEPRECATED: This module is no longer used.
# fetch_news.py now builds queries inline with dynamic suffixes.
def get_query_variations(industry: str) -> list[str]:
    """Returns a single targeted query for the given industry."""
    # The user requested to remove the 5+ query variations feature.
    # Returns a list of one query to remain compatible with fetch_news.py loop
    return [f"{industry} industry news"]

class PipelineError(Exception):
    """The pipeline cannot continue (for example unreadable state). The message is safe to show."""

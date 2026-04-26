import hou


def handle_error(message: str) -> None:
    """
    Display an error message in Houdini.

    Args:
        message: Error message.
    """
    if hou.isUIAvailable():
        hou.ui.displayMessage(
            text=message,
            buttons=('OK',),
            title="Error",
            severity=hou.severityType.Error
        )
    else:
        hou.puts(f"ERROR: {message}")
    raise ValueError(message)

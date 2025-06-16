# Configuration errors

class ConfigurationError(Exception):
    """Configuration base error."""

class ConfigNotFoundError(ConfigurationError):
    """Configuration file not found."""

    def __init__(self, *args) -> None:
        super().__init__(*args)

class ConfigLookupError(ConfigurationError):
    """Config key not found."""

    def __init__(self, *args) -> None:
        super().__init__(*args)

# BoardManager errors

class ModuleNotFoundError(KeyError):
    """Module name not found."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


# Camera errors

class CameraError(Exception):
    """Camera base error."""


class CameraNotReadyError(CameraError):
    """Camera not initialized."""

    def __init__(self, *args) -> None:
        super().__init__(*args)


class CannotTakePictureError(CameraError):
    """Camera can't take picture."""

    def __init__(self, *args) -> None:
        super().__init__(*args)

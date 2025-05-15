class GameException(Exception):
    """Base exception for all game-related errors."""
    pass

class PlayerNotFoundException(GameException):
    """Exception raised when a player is not found."""
    pass

class PokemonNotFoundException(GameException):
    """Exception raised when a specific pokemon instance is not found."""
    pass

class RaceNotFoundException(GameException):
    """Exception raised when a pokemon race (species) is not found."""
    pass

class ItemNotFoundException(GameException):
    """Exception raised when an item is not found."""
    pass

class InsufficientItemException(GameException):
    """Exception raised when a player does not have enough of an item."""
    pass

class CommandParseException(GameException):
    """Exception raised when a command cannot be parsed correctly."""
    pass

class InvalidArgumentException(GameException):
    """Exception raised when a command argument is invalid."""
    pass

class MapNotFoundException(GameException):
    """Exception raised when a map is not found."""
    pass

# Add other specific exceptions as needed

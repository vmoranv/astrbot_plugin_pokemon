from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid # Using uuid for unique battle IDs
import datetime

# Assuming Pokemon model is defined in backend.models.pokemon
# from .pokemon import Pokemon

@dataclass
class Battle:
    """
    Represents an active battle session.

    This model holds the state of a battle, including the participants,
    current turn, log of events, and battle-specific conditions like weather or terrain.
    """
    battle_id: str = field(default_factory=lambda: str(uuid.uuid4())) # Unique ID for the battle session
    player_id: str # ID of the player involved
    wild_pokemon_instance_id: str # Instance ID of the wild pokemon
    player_pokemon_instance_id: str # Instance ID of the player's active pokemon
    current_turn: int = 1
    log: List[str] = field(default_factory=list) # List of strings representing battle events
    start_time: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    end_time: Optional[datetime.datetime] = None # Set when battle ends
    outcome: Optional[str] = None # 'win', 'loss', 'ran', 'caught', 'draw'
    run_attempts: int = 0 # Number of times the player has attempted to run
    # Add battle-specific conditions
    weather: Optional[str] = None # e.g., 'sun', 'rain', 'hail', 'sandstorm'
    terrain: Optional[str] = None # e.g., 'electric', 'grassy', 'misty', 'psychic' # Add terrain field

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Battle object to a dictionary for storage/serialization."""
        return {
            "battle_id": self.battle_id,
            "player_id": self.player_id,
            "wild_pokemon_instance_id": self.wild_pokemon_instance_id,
            "player_pokemon_instance_id": self.player_pokemon_instance_id,
            "current_turn": self.current_turn,
            "log": self.log, # Assuming log is list of strings, directly serializable
            "start_time": self.start_time.isoformat(), # Convert datetime to string
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "outcome": self.outcome,
            "run_attempts": self.run_attempts,
            "weather": self.weather, # Include weather
            "terrain": self.terrain, # Include terrain
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Battle":
        """Creates a Battle object from a dictionary."""
        return Battle(
            battle_id=data["battle_id"],
            player_id=data["player_id"],
            wild_pokemon_instance_id=data["wild_pokemon_instance_id"],
            player_pokemon_instance_id=data["player_pokemon_instance_id"],
            current_turn=data.get("current_turn", 1),
            log=data.get("log", []),
            start_time=datetime.datetime.fromisoformat(data["start_time"]),
            end_time=datetime.datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            outcome=data.get("outcome"),
            run_attempts=data.get("run_attempts", 0),
            weather=data.get("weather"), # Load weather
            terrain=data.get("terrain"), # Load terrain
        )

    def is_finished(self) -> bool:
        """Checks if the battle has finished."""
        return self.outcome is not None

    def add_log_message(self, message: str):
        """Adds a message to the battle log."""
        self.log.append(message)

    # S2 refinement: Add battle state details like active pokemon, pending actions, etc.
    # This could be a more complex structure depending on battle complexity.
    # For simplicity initially, we might just track the participants.

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Battle object to a dictionary for database storage."""
        return {
            "battle_id": self.battle_id,
            "player_id": self.player_id,
            "wild_pokemon_instance_id": self.wild_pokemon_instance_id,
            "player_active_pokemon_instance_id": self.player_pokemon_instance_id,
            "current_turn": self.current_turn,
            "is_active": self.end_time is None,
            "outcome": self.outcome,
            # Save other attributes here
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Battle":
        """Creates a Battle object from a dictionary retrieved from the database."""
        return Battle(
            battle_id=data["battle_id"],
            player_id=data["player_id"],
            wild_pokemon_instance_id=data["wild_pokemon_instance_id"],
            player_pokemon_instance_id=data["player_pokemon_instance_id"],
            current_turn=data["current_turn"],
            log=data.get("log", []),
            start_time=datetime.datetime.fromisoformat(data["start_time"]),
            end_time=datetime.datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            outcome=data["outcome"],
            run_attempts=data.get("run_attempts", 0),
            weather=data.get("weather"),
            terrain=data.get("terrain"),
        )

    def get_all_pokemon(self) -> List[Pokemon]:
        """
        获取战斗中的所有宝可梦（双方的活跃宝可梦）。
        
        Returns:
            包含所有宝可梦的列表
        """
        pokemons = []
        
        if self.active_player_pokemon:
            pokemons.append(self.active_player_pokemon)
        
        if self.active_opponent_pokemon:
            pokemons.append(self.active_opponent_pokemon)
        
        return pokemons 
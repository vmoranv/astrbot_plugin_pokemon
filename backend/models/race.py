from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Assuming Attribute and Skill models are defined
from .attribute import Attribute # Import Attribute model
from .skill import Skill # Import Skill model

@dataclass
class LearnableSkill:
    """Represents a skill a Pokemon race can learn at a specific level."""
    skill_id: int
    level: int

@dataclass
class Race:
    """Represents a Pokemon race (e.g., Bulbasaur, Charmander)."""
    race_id: int # Unique ID for the race
    name: str # Name of the race (e.g., "Bulbasaur")
    types: List[Attribute] # List of Attribute objects representing the pokemon's types
    base_stats: Dict[str, int] # Base stats (hp, attack, defense, etc.)
    abilities: List[str] # List of ability names (simplified)
    # Add other race-specific attributes here (e.g., gender ratio, egg group, habitat)
    growth_rate: str # Experience growth rate ("fast", "medium_fast", etc.)
    base_exp_yield: int # Base experience points gained when this pokemon is defeated
    item_drop_chance: Optional[float] = None # Chance (0.0 to 1.0) of dropping an item when defeated
    item_drop_id: Optional[int] = None # The ID of the item that might be dropped

    # Skills learned by level up
    learnable_skills: List[LearnableSkill] = field(default_factory=list)

    # Add other ways to learn skills (e.g., TM/HM, egg moves, tutor moves) - TODO (S3 refinement)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Race object to a dictionary for storage/serialization."""
        return {
            "race_id": self.race_id,
            "name": self.name,
            "types": [t.to_dict() for t in self.types],
            "base_stats": self.base_stats,
            "abilities": self.abilities,
            "growth_rate": self.growth_rate,
            "base_exp_yield": self.base_exp_yield,
            "item_drop_chance": self.item_drop_chance, # Include item_drop_chance
            "item_drop_id": self.item_drop_id, # Include item_drop_id
            "learnable_skills": [ls.__dict__ for ls in self.learnable_skills], # Convert LearnableSkill to dict
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Race":
        """Creates a Race object from a dictionary."""
        return Race(
            race_id=data["race_id"],
            name=data["name"],
            types=[Attribute.from_dict(t_data) for t_data in data.get("types", [])],
            base_stats=data.get("base_stats", {}),
            abilities=data.get("abilities", []),
            growth_rate=data.get("growth_rate", "medium_fast"), # Default growth rate
            base_exp_yield=data.get("base_exp_yield", 0), # Default base exp yield
            item_drop_chance=data.get("item_drop_chance"), # Load item_drop_chance
            item_drop_id=data.get("item_drop_id"), # Load item_drop_id
            learnable_skills=[LearnableSkill(**ls_data) for ls_data in data.get("learnable_skills", [])],
        ) 
from typing import List, Dict, Any

class Race:
    """Represents a pokemon species (Pokedex data)."""
    def __init__(self,
                 race_id: int,
                 name: str,
                 type1_id: int,
                 type2_id: int = None,
                 base_stats: Dict[str, int] = None, # {stat_name: value}
                 abilities: List[int] = None, # List of ability IDs
                 learnable_skills: List[int] = None, # List of skill IDs
                 evolution_chain_id: int = None, # ID linking to evolution data
                 description: str = ""
                ):
        self.race_id = race_id
        self.name = name
        self.type1_id = type1_id
        self.type2_id = type2_id
        self.base_stats = base_stats if base_stats is not None else {}
        self.abilities = abilities if abilities is not None else []
        self.learnable_skills = learnable_skills if learnable_skills is not None else []
        self.evolution_chain_id = evolution_chain_id
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Race object to a dictionary."""
        return {
            "race_id": self.race_id,
            "name": self.name,
            "type1_id": self.type1_id,
            "type2_id": self.type2_id,
            "base_stats": self.base_stats,
            "abilities": self.abilities,
            "learnable_skills": self.learnable_skills,
            "evolution_chain_id": self.evolution_chain_id,
            "description": self.description,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Race":
        """Creates a Race object from a dictionary."""
        return Race(
            race_id=data["race_id"],
            name=data["name"],
            type1_id=data["type1_id"],
            type2_id=data.get("type2_id"),
            base_stats=data.get("base_stats", {}),
            abilities=data.get("abilities", []),
            learnable_skills=data.get("learnable_skills", []),
            evolution_chain_id=data.get("evolution_chain_id"),
            description=data.get("description", "")
        )

    # Add methods if needed, e.g., get_effective_type

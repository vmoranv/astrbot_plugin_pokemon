from typing import List, Dict, Any
# Assuming Skill, StatusEffect, Race models will be defined
# from .skill import Skill
# from .status_effect import StatusEffect
# from .race import Race
# from ..core.battle import formulas # Example dependency for calculations

class Pokemon:
    """Represents a specific pokemon instance owned by a player."""
    def __init__(self,
                 pokemon_id: int, # Unique instance ID
                 race_id: int,    # ID of the pokemon species
                 owner_id: str,   # Player ID
                 nickname: str,
                 level: int,
                 current_hp: int,
                 experience: int,
                 # Base stats (from Race) + IVs + EVs + Nature -> Calculated Stats
                 # For simplicity in MVP, store calculated stats directly or calculate on the fly
                 max_hp: int,
                 attack: int,
                 defense: int,
                 special_attack: int,
                 special_defense: int,
                 speed: int,
                 skills: List[int], # List of skill IDs
                 status_effects: List[int] = None, # List of status effect IDs
                 nature_id: int = None,
                 ability_id: int = None,
                 individual_values: Dict[str, int] = None, # {stat_name: value}
                 effort_values: Dict[str, int] = None,     # {stat_name: value}
                ):
        self.pokemon_id = pokemon_id
        self.race_id = race_id
        self.owner_id = owner_id
        self.nickname = nickname
        self.level = level
        self.current_hp = current_hp
        self.experience = experience
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense
        self.special_attack = special_attack
        self.special_defense = special_defense
        self.speed = speed
        self.skills = skills
        self.status_effects = status_effects if status_effects is not None else []
        self.nature_id = nature_id
        self.ability_id = ability_id
        self.individual_values = individual_values if individual_values is not None else {}
        self.effort_values = effort_values if effort_values is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Pokemon object to a dictionary."""
        return {
            "pokemon_id": self.pokemon_id,
            "race_id": self.race_id,
            "owner_id": self.owner_id,
            "nickname": self.nickname,
            "level": self.level,
            "current_hp": self.current_hp,
            "experience": self.experience,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "special_attack": self.special_attack,
            "special_defense": self.special_defense,
            "speed": self.speed,
            "skills": self.skills,
            "status_effects": self.status_effects,
            "nature_id": self.nature_id,
            "ability_id": self.ability_id,
            "individual_values": self.individual_values,
            "effort_values": self.effort_values,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Pokemon":
        """Creates a Pokemon object from a dictionary."""
        return Pokemon(
            pokemon_id=data["pokemon_id"],
            race_id=data["race_id"],
            owner_id=data["owner_id"],
            nickname=data["nickname"],
            level=data["level"],
            current_hp=data["current_hp"],
            experience=data["experience"],
            max_hp=data["max_hp"],
            attack=data["attack"],
            defense=data["defense"],
            special_attack=data["special_attack"],
            special_defense=data["special_defense"],
            speed=data["speed"],
            skills=data["skills"],
            status_effects=data.get("status_effects", []),
            nature_id=data.get("nature_id"),
            ability_id=data.get("ability_id"),
            individual_values=data.get("individual_values", {}),
            effort_values=data.get("effort_values", {}),
        )

    # Add methods for taking damage, healing, gaining experience, leveling up, etc.
    # def take_damage(self, damage: int):
    #     self.current_hp -= damage
    #     if self.current_hp < 0:
    #         self.current_hp = 0

    # def heal(self, amount: int):
    #     self.current_hp += amount
    #     if self.current_hp > self.max_hp:
    #         self.current_hp = self.max_hp

    # async def gain_experience(self, exp: int):
    #     self.experience += exp
    #     # Check for level up and update stats (potentially calling core.pet.pet_grow)
    #     pass

    # def add_status_effect(self, effect_id: int):
    #     if effect_id not in self.status_effects:
    #         self.status_effects.append(effect_id)

    # def remove_status_effect(self, effect_id: int):
    #     if effect_id in self.status_effects:
    #         self.status_effects.remove(effect_id)

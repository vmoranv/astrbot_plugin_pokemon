import random
from typing import Optional, List
from backend.models.pokemon import Pokemon
from backend.models.race import Race # Need Race data for base stats, type, abilities, moves
from backend.models.skill import Skill # Need Skill data for initial moves
# from backend.services.metadata_service import MetadataService # Core should not depend on Services
from backend.core.battle.formulas import calculate_stats # Assuming this function exists

class PokemonFactory:
    """Factory for creating Pokemon instances."""

    async def create_pokemon_instance(
        self,
        race_data: Race,
        level: int,
        owner_id: Optional[str] = None,
        is_wild: bool = True
    ) -> Pokemon:
        """
        Creates a new Pokemon instance.
        Requires Race data, desired level, optional owner ID, and wild status.
        """
        # This factory function uses pure logic to initialize a Pokemon object.
        # It needs Race data to determine base stats, types, abilities, and initial moves.
        # It should NOT fetch Race data itself; that should be done by the Service layer.

        # 1. Generate IVs (Individual Values) - random numbers for each stat (0-31)
        ivs = {
            "hp": random.randint(0, 31),
            "attack": random.randint(0, 31),
            "defense": random.randint(0, 31),
            "special_attack": random.randint(0, 31),
            "special_defense": random.randint(0, 31),
            "speed": random.randint(0, 31),
        }

        # 2. Initialize EVs (Effort Values) - start at 0
        evs = {
            "hp": 0,
            "attack": 0,
            "defense": 0,
            "special_attack": 0,
            "special_defense": 0,
            "speed": 0,
        }

        # 3. Determine Nature (affects two stats, one +10%, one -10%) - random for wild pokemon
        # Need a list of natures and their effects. This could be metadata.
        # For simplicity, let's skip Nature for MVP or pick a neutral one.
        # Assuming Nature is represented by an ID or string.
        nature = "hardy" # Placeholder: neutral nature

        # 4. Determine Ability - pick one from the race's abilities (random for wild)
        # Assuming Race data has a list of possible ability IDs.
        # ability_id = random.choice(race_data.abilities) if race_data.abilities else None
        ability_id = race_data.abilities[0] if race_data.abilities else None # Pick first ability for simplicity

        # 5. Determine initial moveset
        # Wild pokemon usually have moves based on their level.
        # Need to get the list of moves the race learns by level (from Race data).
        # Select the latest 4 moves learned up to the current level.
        # Assuming Race data has a list of learnable moves with levels:
        # race_data.learnable_moves = [{"skill_id": 1, "level": 1}, {"skill_id": 5, "level": 7}, ...]
        # Need access to Skill data to create Skill objects for the moveset.
        # This requires Skill data to be passed in or fetched by the Service layer.
        # Let's assume the Service layer provides the list of possible skills for this race.

        # For MVP, let's just give it a placeholder move or no moves initially.
        # A proper implementation needs the list of skills the race can learn.
        # Let's assume the Service layer passes a list of relevant Skill objects.
        # Example: skills_for_race = await metadata_service.get_skills_for_race(race_data.race_id)
        # Then filter skills_for_race by level <= pokemon.level and pick up to 4.

        # Placeholder for moves:
        initial_skills: List[Skill] = []
        # In a real implementation:
        # learned_moves_at_level = [skill for skill in skills_for_race if skill.learn_level <= level]
        # initial_skills = sorted(learned_moves_at_level, key=lambda s: s.learn_level, reverse=True)[:4] # Get latest 4

        # 6. Calculate initial stats
        # Assuming calculate_stats function exists in core.battle.formulas
        # It needs the Pokemon object (partially created), Race data, and Nature.
        # We need to create the Pokemon object first, then calculate stats.

        pokemon = Pokemon(
            pokemon_id=None, # ID will be assigned when saved to DB (Service layer)
            owner_id=owner_id,
            race_id=race_data.race_id,
            name=race_data.name, # Use race name as default name
            nickname=race_data.name, # Use race name as default nickname
            level=level,
            experience=0, # Start with 0 EXP at the beginning of a level
            ivs=ivs,
            evs=evs,
            nature=nature,
            ability_id=ability_id,
            skills=initial_skills, # Add the determined initial skills
            current_hp=0, # Will be set to max_hp after stats calculation
            status_effect=None,
            is_wild=is_wild,
            location_id=None, # Location is set when encountered/placed
            held_item_id=None,
            friendship=0, # Start with base friendship
            met_location=None,
            met_level=level,
            can_evolve_to=None,
            stats={}, # Stats will be calculated next
            max_hp=0 # Max HP will be calculated next
        )

        # Calculate initial stats and set current HP to max HP
        pokemon.stats = calculate_stats(pokemon, race_data)
        pokemon.max_hp = pokemon.stats.get("hp", 1) # Get calculated HP stat, default to 1
        pokemon.current_hp = pokemon.max_hp # Start with full HP

        logger.info(f"Created new Pokemon instance: {pokemon.nickname} (Race ID: {pokemon.race_id}, Level: {pokemon.level})")

        return pokemon

# Example usage (in Service layer):
# from backend.core.pokemon_factory import PokemonFactory
# from backend.services.metadata_service import MetadataService
#
# metadata_service = MetadataService()
# pokemon_factory = PokemonFactory()
#
# race_data = await metadata_service.get_race(race_id)
# # skills_for_race = await metadata_service.get_skills_for_race(race_id) # Need this method
# # wild_pokemon = await pokemon_factory.create_pokemon_instance(race_data, level=5, is_wild=True, skills_for_race=skills_for_race)
# # Or, pass all skills data and filter inside factory:
# # all_skills = await metadata_service.get_all_skills()
# # wild_pokemon = await pokemon_factory.create_pokemon_instance(race_data, level=5, is_wild=True, all_skills=all_skills) 
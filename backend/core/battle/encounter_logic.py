# backend/core/battle/encounter_logic.py

import random
from typing import Optional, Tuple, List, Dict, Any
from backend.data_access.repositories.metadata_repository import MetadataRepository
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class EncounterLogic:
    """Core logic for determining wild pokemon encounters."""

    def __init__(self):
        self.metadata_repo = MetadataRepository()

    async def check_encounter(self, location_id: str) -> bool:
        """
        Determines if a wild pokemon encounter occurs at the given location.
        Probability is based on the location's base encounter chance.
        """
        location_data = await self.metadata_repo.get_location_data(location_id)
        if not location_data:
            logger.error(f"Location data not found for location_id: {location_id}")
            return False # Cannot have encounter if location data is missing

        base_chance = location_data.get('base_encounter_chance', 0.0) # Default to 0 if not specified
        # TODO: Implement additional factors influencing encounter chance (e.g., player items, time of day) (S2 refinement)
        encounter_chance = base_chance

        # Perform the random check
        return random.random() < encounter_chance

    async def get_wild_pokemon_details(self, location_id: str) -> Optional[Tuple[int, int]]:
        """
        If an encounter occurs, selects a random wild pokemon race and level
        based on the location's encounter data and weights.
        Returns a tuple of (pokemon_race_id, level) or None if no encounter data.
        """
        encounter_data = await self.metadata_repo.get_location_encounters(location_id)
        if not encounter_data:
            logger.warning(f"No encounter data found for location_id: {location_id}")
            return None # No pokemon to encounter

        # Calculate total weight
        total_weight = sum(item['weight'] for item in encounter_data)
        if total_weight <= 0:
            logger.warning(f"Total weight for encounters at location {location_id} is zero or negative.")
            return None # Cannot select if total weight is zero

        # Select a pokemon based on weights
        # Use random.choices for weighted selection (requires Python 3.6+)
        # If using older Python, implement manual weighted selection
        selected_encounter = random.choices(encounter_data, weights=[item['weight'] for item in encounter_data], k=1)[0]

        race_id = selected_encounter['pokemon_race_id']
        min_level = selected_encounter['min_level']
        max_level = selected_encounter['max_level']

        # Select a random level within the range
        # Ensure min_level <= max_level
        if min_level > max_level:
             logger.error(f"Invalid level range for race {race_id} at location {location_id}: min_level {min_level} > max_level {max_level}")
             # Fallback or raise error? Let's return None for now.
             return None

        level = random.randint(min_level, max_level)

        logger.debug(f"Selected wild pokemon race {race_id} at level {level} for location {location_id}")
        return (race_id, level)

# Instantiate the logic class (or use a singleton pattern if preferred)
encounter_logic = EncounterLogic()

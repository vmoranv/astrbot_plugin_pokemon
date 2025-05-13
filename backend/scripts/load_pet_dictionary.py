import os
import csv
from backend.config.settings import settings
from backend.utils.logger import get_logger
# from backend.data_access.repositories.pokemon_repository import PokemonRepository # 导入正确的宝可梦仓库 - Remove this import
# Import the repository for pet dictionary data
from backend.data_access.repositories.pet_dictionary_repository import PetDictionaryRepository # Assuming you have this repository

logger = get_logger(__name__)

async def load_pet_dictionary_data() -> None:
    """
    Loads pet dictionary data from a CSV file into the database.
    """
    logger.info("Loading pet dictionary data...")
    file_path = os.path.join(settings.DATA_DIR, 'pet_dictionary.csv')
    data_to_insert = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Assuming your CSV columns match the pet_dictionary table columns
                # Adjust column names as per your actual CSV file
                # Handle potential missing values and type conversions
                try:
                    # Create a dictionary representing a row in the pet_dictionary table
                    # Ensure keys match the table column names
                    data_item = {
                        'race_id': int(row['race_id']),
                        'name': row['name'],
                        'evo_level': int(row['evo_level']),
                        'evolution_stage': int(row['evolution_stage']),
                        'base_hp': int(row['base_hp']),
                        'base_attack': int(row['base_attack']),
                        'base_defence': int(row['base_defence']),
                        'base_special_attack': int(row['base_special_attack']),
                        'base_special_defence': int(row['base_special_defence']),
                        'base_speed': int(row['base_speed']),
                        'catch_rate': int(row['catch_rate']),
                        'growth_rate': row['growth_rate'],
                        'attribute_id1': int(row['attribute_id1']) if row.get('attribute_id1') else None,
                        'attribute_id2': int(row.get('attribute_id2')) if row.get('attribute_id2') else None,
                        'height': float(row['height']) if row.get('height') else None,
                        'weight': float(row['weight']) if row.get('weight') else None,
                        'description': row.get('description', '')
                    }
                    data_to_insert.append(data_item)
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to data error: {row}. Error: {e}")
                    continue # Skip this row and continue with the next
                except Exception as e:
                    logger.error(f"An unexpected error occurred processing row {row}: {e}")
                    continue

        if data_to_insert:
            # Use the correct repository for inserting pet dictionary data
            # Assuming PetDictionaryRepository has an insert_many method that accepts a list of dictionaries
            await PetDictionaryRepository.insert_many(data_to_insert) # Use the correct repository method
            logger.info(f"Successfully loaded {len(data_to_insert)} pet dictionary entries.")
        else:
            logger.warning("No valid pet dictionary entries found in the CSV file.")

    except FileNotFoundError:
        logger.error(f"Pet dictionary CSV file not found at {file_path}")
        # Depending on your error handling strategy, you might want to raise the exception
        # raise
    except Exception as e:
        logger.error(f"Error loading pet dictionary data: {e}")
        # raise # Re-raise the exception after logging if necessary

# Example of how this function might be called (e.g., from initialize_database.py)
# async def main():
#     await load_pet_dictionary_data()

# if __name__ == "__main__":
#     asyncio.run(main())

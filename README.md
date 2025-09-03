# DAO Bot Database Implementation

## Overview

This implementation adds a SQLite database to your Discord bot to ensure data persistence across updates and hosting transfers. The database stores all user data, including economy information, jobs, inventory, sects, and tournaments.

## Files

- `database.py` - Core database implementation using SQLite
- `db_integration.py` - Integration layer that maintains backward compatibility with JSON files
- `migrate.py` - Migration tool to transfer data from JSON files to the database
- `main_db.py` - Updated version of main.py that uses the database

## How to Migrate

1. **Backup your data**: The migration script will automatically create backups, but it's always good to make your own copy of your JSON files.

2. **Run the migration script**:
   ```
   python migrate.py run
   ```
   This will transfer all your data from JSON files to the SQLite database.

3. **Update your bot**:
   - Rename `main_db.py` to `main.py` (after backing up your original)
   - OR
   - Start using `main_db.py` directly: `python main_db.py`

## Benefits

- **Data Persistence**: All data is stored in a single SQLite file (`dao_bot.db`), making it easy to back up and transfer.
- **Reliability**: SQLite provides ACID compliance, ensuring your data remains consistent even during crashes or power failures.
- **Performance**: Database operations are more efficient than reading/writing JSON files, especially as your data grows.
- **Backward Compatibility**: The integration layer maintains compatibility with your existing code.

## How It Works

1. **Database Layer** (`database.py`):
   - Provides a direct interface to the SQLite database
   - Handles table creation, data retrieval, and updates
   - Includes migration utilities

2. **Integration Layer** (`db_integration.py`):
   - Maintains the same function signatures as your original code
   - Transparently redirects data operations to the database
   - Preserves backward compatibility with JSON files for non-critical data

3. **Migration Tool** (`migrate.py`):
   - Creates backups of all JSON files
   - Transfers data to the database
   - Provides clear feedback on the migration process

## Tables

The database includes the following tables:

- `users` - Basic user information (cash, bank, job, etc.)
- `user_meta` - Additional user metadata
- `inventory` - User inventory items
- `jobs` - Job definitions
- `user_jobs` - User job progress
- `sects` - Sect information
- `sect_members` - Sect membership
- `store_items` - Store items
- `tournaments` - Tournament information
- `tournament_participants` - Tournament participants

## Transferring to a New Host

To transfer your bot to a new host:

1. Copy the entire bot directory, including the `dao_bot.db` file
2. Install the required dependencies on the new host
3. Run the bot as usual

## Updating the Bot

When updating your bot:

1. Back up the `dao_bot.db` file
2. Update your bot code
3. Restore the `dao_bot.db` file if needed

## Troubleshooting

- If the database becomes corrupted, you can restore from a backup or re-run the migration
- Check the `migration.log` file for details on any migration issues
- The database file is located in the same directory as your bot code
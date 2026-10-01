# SynBioCrow 2.4.13.2 — RetroBioCat2 data-readiness repair

The 2.4.13.1 run verified DORAnet and the native RetroBioCat2 MCTS API, but
all four RBC2 executions failed with SQLite `no such table: building_blocks`.

The pinned RBC2 source includes its own source-molecule database downloader:
`rbc2.configs.download_data_files.download_source_mols.download_source_mols_db`.
2.4.13.2 uses that upstream mechanism rather than constructing a substitute
database.

Before generation, SynBioCrow now verifies:

- `source_mols.db` exists and is nonempty;
- SQLite opens successfully;
- the `building_blocks` table exists;
- `building_blocks` contains at least one row;
- database byte size and SHA-256 are recorded;
- available table names and relevant row counts are persisted.

An invalid or partial existing database is deleted and re-downloaded through
the pinned RBC2 downloader. Failure of the schema/row-count gate stops the run.

The frozen central-metabolite sink panel and development/validation firewall
from 2.4.13.1 remain unchanged.

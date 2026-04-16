# x4explorer

A standalone web application for browsing X4: Foundations game data and analyzing mod conflicts. Takes an [x4cat](https://github.com/meethune/x4cat) SQLite database as input and serves it as a read-only web interface.

## What it does

The [x4cat CLI](https://github.com/meethune/x4cat) handles one-hop lookups well (`inspect`, `search`). x4explorer provides **linked navigation** and **visual analysis** that a terminal can't:

- **Unified browsable database** — click a ship → see macro properties → click a weapon reference → see weapon stats → click its ware entry → see price and owners
- **Filterable tables** — all ships by hull, all weapons by damage, all wares by price
- **Scriptproperties reference** — 170 datatypes, 87 keywords, 1,931 MD/AI script properties with interlinked navigation and inheritance browsing
- **Visual mod conflict analysis** — compare two or more mods, color-coded by severity (SAFE/CONFLICT/INFO)
- **No game files needed** — build the index once with `x4cat index`, serve from anywhere

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | SQLite ([x4cat](https://github.com/meethune/x4cat) index) |
| Frontend | [htmx](https://htmx.org/) + [Jinja2](https://jinja.palletsprojects.com/) |
| Styling | [Pico CSS](https://picocss.com/) |

No JavaScript build tooling. Server-rendered with htmx for partial page updates.

## Pages

| Route | Content |
|-------|---------|
| `/` | Dashboard — game version, index stats, quick search |
| `/wares` | Filterable ware table (group, transport, price range) |
| `/wares/{id}` | Ware detail with linked macro, owners, production chain |
| `/macros` | Filterable macro table (class, name pattern) |
| `/macros/{id}` | Macro detail with all properties, linked component and ware |
| `/components` | Component table and detail views |
| `/scripts/datatypes` | Scriptproperties datatype browser with inheritance |
| `/scripts/keywords` | Keyword reference |
| `/search` | Unified search across all asset types + script properties |
| `/conflicts` | Mod conflict analysis |

## Prerequisites

Build a game index with x4cat:

```bash
uv tool install git+https://github.com/meethune/x4cat.git
x4cat index "/path/to/X4 Foundations"
```

## Usage

```bash
# Install
uv sync

# Serve
x4explorer serve --db ~/.cache/x4cat/<hash>.db

# Or auto-detect the most recent index
x4explorer serve
```

## Relationship to x4cat

x4explorer is a **read-only consumer** of the x4cat SQLite index. It does not modify game files or catalogs — that's [x4cat's](https://github.com/meethune/x4cat) job. The workflow is:

```
x4cat index "/path/to/X4 Foundations"  →  SQLite DB  →  x4explorer serve
```

## Not in scope

- Writing/modifying game files
- Replacing x4cat CLI commands
- User accounts or authentication
- Public web hosting (designed for local use)

## License

MIT

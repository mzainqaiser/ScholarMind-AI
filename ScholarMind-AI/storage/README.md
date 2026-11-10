# storage/

Runtime data lives here in `storage/data/` (created on first start, **git-ignored and never packaged**):

- `scholarmind.db` — SQLite: document metadata, conversations, messages
- `chroma/` — persistent ChromaDB vector store
- `uploads/` — the original uploaded files (stored under server-generated names)

Delete `storage/data/` to reset the application completely. Change the location with `SCHOLARMIND_DATA_DIR`.

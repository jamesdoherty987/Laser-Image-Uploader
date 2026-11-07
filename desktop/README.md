# Desktop CorelDRAW connector

**Stages 5–6 — not implemented yet.**

Planned layout:

```
desktop/
  coreldraw_connector/
    main.py          # background loop / tray
    api_client.py    # HTTPS + pairing token
    coreldraw.py     # COM automation + file-open fallback
    downloader.py
    config.py
```

Goals:

- Run in the logged-in Windows user session (not a service)
- Auto-start with Windows
- Poll (or long-poll) for `ready` jobs
- Download prepared PNG
- Import into CorelDRAW via COM when available; otherwise open the file
- Report `imported` / `failed` back to the API
- Package with PyInstaller + simple installer

Do not claim CorelDRAW automation works until tested against the installed version on the teacher laptop.

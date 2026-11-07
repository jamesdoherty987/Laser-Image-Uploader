# Desktop CorelDRAW connector

Polls the Galvin Crafts API for laser-ready jobs, downloads prepared PNGs, and opens them in CorelDRAW (Windows COM) or the default image viewer.

## Quick start (Windows PC next to the laser)

1. Sign in to **Admin** on the website.
2. Download the desktop connector zip and copy the **pairing token**.
3. Unzip on the Windows PC.
4. Double-click `run_connector.bat`, or:

```bat
cd coreldraw_connector
python main.py --setup
```

5. Paste the API URL (e.g. `https://your-server`) and pairing token when prompted.
6. Leave the connector running while customers upload. Ready jobs download automatically.

## Files

```
desktop/
  run_connector.bat
  coreldraw_connector/
    main.py
    api_client.py
    config.py
    downloader.py
    coreldraw.py
```

Config is stored at `%USERPROFILE%\.galvin-crafts\connector.json`.
Downloaded laser files go to `%USERPROFILE%\GalvinCrafts\laser-ready\` by default.

## Notes

- CorelDRAW COM import is attempted first on Windows; if COM is unavailable the file opens with the OS default.
- Pairing token is created automatically by the backend and shown in Admin.
- Admin can also download prepared files directly from the job inbox without this app.

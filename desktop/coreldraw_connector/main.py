#!/usr/bin/env python3
"""Galvin Crafts desktop connector — poll ready jobs and open laser files."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from api_client import DesktopApi, DesktopApiError
from config import load_config, save_config
from coreldraw import open_in_coreldraw
from downloader import absolute_media_url, download_file


def setup_interactive() -> dict:
    cfg = load_config()
    print("Galvin Crafts — desktop connector setup")
    api_base = input(f"API base URL [{cfg.get('api_base', '')}]: ").strip() or cfg.get("api_base", "")
    token = input(f"Pairing token [{'(set)' if cfg.get('pairing_token') else '(empty)'}]: ").strip()
    if not token:
        token = cfg.get("pairing_token", "")
    download_dir = (
        input(f"Download folder [{cfg.get('download_dir', '')}]: ").strip()
        or cfg.get("download_dir", "")
    )
    cfg.update(
        {
            "api_base": api_base.rstrip("/"),
            "pairing_token": token,
            "download_dir": download_dir,
            "poll_seconds": int(cfg.get("poll_seconds") or 8),
        }
    )
    save_config(cfg)
    print(f"Saved config to {Path.home() / '.galvin-crafts' / 'connector.json'}")
    return cfg


def process_once(api: DesktopApi, download_dir: Path) -> int:
    jobs = api.list_ready()
    handled = 0
    for job in jobs:
        job_id = job["id"]
        prepared = job.get("prepared_url")
        if not prepared:
            continue
        print(f"Claiming {job_id} — {job.get('original_filename')}")
        claimed = api.claim(job_id)
        url = absolute_media_url(api.api_base, claimed.get("prepared_url") or prepared)
        filename = f"{job_id[:8]}-{(job.get('original_filename') or 'laser').rsplit('.', 1)[0]}-laser.png"
        dest = download_dir / filename
        try:
            download_file(url, dest)
            mode = open_in_coreldraw(dest)
            api.mark_imported(job_id)
            print(f"  Imported via {mode}: {dest}")
            handled += 1
        except Exception as exc:  # noqa: BLE001
            api.mark_failed(job_id, str(exc))
            print(f"  Failed: {exc}")
    return handled


def run_loop(cfg: dict) -> None:
    token = (cfg.get("pairing_token") or "").strip()
    if not token:
        print("No pairing token set. Run with --setup first (copy token from Admin).")
        sys.exit(1)
    api = DesktopApi(cfg["api_base"], token)
    download_dir = Path(cfg.get("download_dir") or Path.home() / "GalvinCrafts" / "laser-ready")
    poll = max(3, int(cfg.get("poll_seconds") or 8))
    print(f"Polling {api.api_base} every {poll}s…")
    print(f"Saving files to {download_dir}")
    while True:
        try:
            n = process_once(api, download_dir)
            if n:
                print(f"Handled {n} job(s).")
        except DesktopApiError as exc:
            print(f"API error: {exc}")
        except KeyboardInterrupt:
            print("\nStopped.")
            return
        time.sleep(poll)


def main() -> None:
    parser = argparse.ArgumentParser(description="Galvin Crafts CorelDRAW connector")
    parser.add_argument("--setup", action="store_true", help="Configure API URL and pairing token")
    parser.add_argument("--once", action="store_true", help="Poll once then exit")
    args = parser.parse_args()

    if args.setup:
        cfg = setup_interactive()
        if not args.once:
            run_loop(cfg)
            return
    else:
        cfg = load_config()

    if args.once:
        api = DesktopApi(cfg["api_base"], cfg.get("pairing_token") or "")
        process_once(api, Path(cfg.get("download_dir") or "."))
        return

    run_loop(cfg)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Backfill PostIntelligence.evidence_inventory from already saved analysis data.

This script does not collect Instagram posts and does not call Apify. It only
reads existing Post/PostIntelligence rows and asks the evidence extractor to
structure the data lock inventory from saved transcript/caption/analysis fields.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

load_dotenv()

from src.analyzer.post_intelligence import _extract_evidence_inventory
from src.database import get_session
from src.models import Post, PostIntelligence, Profile


def _has_inventory(inventory: Any) -> bool:
    if not isinstance(inventory, dict) or not inventory:
        return False
    required = inventory.get("required") or {}
    optional = inventory.get("optional") or {}
    if any(required.get(key) for key in ("numbers", "mechanisms", "causal_steps", "definitions")):
        return True
    if any(optional.get(key) for key in ("claims", "sources", "context")):
        return True
    return False


def _analysis_payload(intelligence: PostIntelligence) -> dict[str, Any]:
    return {
        "core_argument": intelligence.core_argument or "",
        "technical_claims": intelligence.technical_claims or [],
        "data_points": intelligence.data_points or [],
        "sources_referenced": intelligence.sources_referenced or [],
    }


def backfill_evidence_inventory(
    handle: str | None = None,
    post_type: str = "carousel",
    limit: int | None = None,
    force: bool = False,
    dry_run: bool = False,
    use_gpt: bool = True,
) -> dict[str, int]:
    session = get_session()
    try:
        query = (
            session.query(PostIntelligence)
            .join(PostIntelligence.post)
            .join(Post.profile)
            .options(
                joinedload(PostIntelligence.post).joinedload(Post.profile),
            )
            .order_by(Post.published_at.desc())
        )
        if post_type:
            query = query.filter(Post.post_type == post_type)
        if handle:
            query = query.filter(Profile.handle == handle)

        rows = query.all()
        if not force:
            rows = [row for row in rows if not _has_inventory(row.evidence_inventory)]
        if limit is not None:
            rows = rows[:limit]

        updated = 0
        skipped = 0
        failed = 0

        print(f"Found {len(rows)} intelligence rows to backfill.")
        for index, intelligence in enumerate(rows, start=1):
            post = intelligence.post
            label = f"{index}/{len(rows)} post_id={post.id} @{post.profile.handle}"
            try:
                inventory = _extract_evidence_inventory(
                    intelligence.visual_transcript or "",
                    _analysis_payload(intelligence),
                    post.caption or "",
                    use_gpt=use_gpt,
                )
                if not _has_inventory(inventory):
                    skipped += 1
                    print(f"SKIP {label}: extractor returned no usable inventory")
                    continue

                if not dry_run:
                    intelligence.evidence_inventory = inventory
                    intelligence.analyzed_at = datetime.now(timezone.utc)
                    session.add(intelligence)
                    session.commit()

                updated += 1
                required = inventory.get("required") or {}
                print(
                    "OK "
                    f"{label}: numbers={len(required.get('numbers') or [])}, "
                    f"mechanisms={len(required.get('mechanisms') or [])}, "
                    f"steps={len(required.get('causal_steps') or [])}, "
                    f"definitions={len(required.get('definitions') or [])}"
                )
            except Exception as exc:
                session.rollback()
                failed += 1
                print(f"FAIL {label}: {exc}")

        return {"updated": updated, "skipped": skipped, "failed": failed}
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill evidence inventory without Apify.")
    parser.add_argument("--handle", help="Only process one Instagram handle.")
    parser.add_argument("--post-type", default="carousel", help="Post type filter. Default: carousel.")
    parser.add_argument("--limit", type=int, help="Maximum number of rows to process.")
    parser.add_argument("--force", action="store_true", help="Rebuild even when evidence_inventory already exists.")
    parser.add_argument("--dry-run", action="store_true", help="Run extractor but do not write to the database.")
    parser.add_argument("--no-gpt", action="store_true", help="Use deterministic extraction only; no OpenAI calls.")
    args = parser.parse_args()

    result = backfill_evidence_inventory(
        handle=args.handle,
        post_type=args.post_type,
        limit=args.limit,
        force=args.force,
        dry_run=args.dry_run,
        use_gpt=not args.no_gpt,
    )
    print(f"Done: {result}")


if __name__ == "__main__":
    main()

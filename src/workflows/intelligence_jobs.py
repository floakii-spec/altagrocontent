import copy
import logging
import os
from datetime import datetime, timezone
from threading import Lock, Thread
from typing import Callable, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from src.analyzer.image_analyzer import analyze_post
from src.analyzer.post_intelligence import analyze_post_intelligence
from src.collector.collector import collect_profile
from src.database import get_session
from src.models import Post, PostIntelligence, Profile

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict], None]

_jobs: dict[str, dict] = {}
_jobs_lock = Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _copy_job(job: dict) -> dict:
    return copy.deepcopy(job)


def _set_job(job_id: str, **updates) -> dict:
    with _jobs_lock:
        job = _jobs[job_id]
        job.update(updates)
        job["updated_at"] = _utcnow()
        return _copy_job(job)


def _append_error(job_id: str, message: str) -> dict:
    with _jobs_lock:
        job = _jobs[job_id]
        errors = list(job.get("errors", []))
        errors.append(message)
        job["errors"] = errors[-20:]
        job["updated_at"] = _utcnow()
        return _copy_job(job)


def get_analysis_job(job_id: str) -> Optional[dict]:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return _copy_job(job) if job else None


def _emit(on_progress: Optional[ProgressCallback], payload: dict) -> None:
    if on_progress:
        on_progress(payload)


def sync_profiles_workflow(
    db: Session,
    handle: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> dict:
    profiles_query = db.query(Profile).filter_by(active=True)
    if handle:
        profiles_query = profiles_query.filter(Profile.handle == handle)
    profiles = profiles_query.order_by(Profile.handle).all()

    apify_token = os.environ.get("APIFY_API_TOKEN")
    if not apify_token:
        raise ValueError("APIFY_API_TOKEN not configured")

    errors: list[dict] = []
    total_new = 0
    total_posts = 0
    completed_posts = 0
    successful_posts = 0
    failed_posts = 0

    _emit(on_progress, {
        "phase": "sync_profiles",
        "message": "Preparando coleta de perfis",
        "phase_total": len(profiles),
        "phase_completed": 0,
        "total_profiles": len(profiles),
        "completed_profiles": 0,
        "total_posts": 0,
        "completed_posts": 0,
        "successful_posts": 0,
        "failed_posts": 0,
        "current_handle": None,
        "current_post_id": None,
    })

    for profile_index, profile in enumerate(profiles, start=1):
        _emit(on_progress, {
            "phase": "sync_profiles",
            "message": f"Coletando @{profile.handle}",
            "phase_total": len(profiles),
            "phase_completed": profile_index - 1,
            "total_profiles": len(profiles),
            "completed_profiles": profile_index - 1,
            "current_handle": profile.handle,
            "current_post_id": None,
        })

        try:
            collect_profile(profile, db, apify_token)
        except Exception as exc:
            db.rollback()
            error = {"handle": profile.handle, "error": str(exc)}
            errors.append(error)
            failed_posts += 1
            _emit(on_progress, {
                "message": f"Falha ao coletar @{profile.handle}",
                "failed_posts": failed_posts,
                "current_handle": profile.handle,
            })
            continue

        new_posts = (
            db.query(Post)
            .filter_by(profile_id=profile.id)
            .filter(Post.analysis == None)
            .order_by(Post.published_at.desc())
            .all()
        )
        pending_intelligence = (
            db.query(Post)
            .filter_by(profile_id=profile.id)
            .join(Post.analysis)
            .filter(Post.intelligence == None)
            .order_by(Post.published_at.desc())
            .all()
        )

        total_posts += len(new_posts) + len(pending_intelligence)
        _emit(on_progress, {
            "phase": "sync_post_analyses",
            "message": f"Processando posts de @{profile.handle}",
            "phase_total": total_posts,
            "phase_completed": completed_posts,
            "total_posts": total_posts,
            "completed_posts": completed_posts,
            "current_handle": profile.handle,
        })

        for post in new_posts:
            _emit(on_progress, {
                "phase": "sync_post_analyses",
                "message": f"Analisando post {completed_posts + 1}/{total_posts} de @{profile.handle}",
                "phase_total": total_posts,
                "phase_completed": completed_posts,
                "current_handle": profile.handle,
                "current_post_id": post.id,
            })
            try:
                analyze_post(post, db)
                total_new += 1
            except Exception as exc:
                db.rollback()
                errors.append({"handle": profile.handle, "post_id": post.id, "error": str(exc)})
                failed_posts += 1
                completed_posts += 1
                _emit(on_progress, {
                    "completed_posts": completed_posts,
                    "phase_completed": completed_posts,
                    "failed_posts": failed_posts,
                    "message": f"Falha na análise visual do post {post.id}",
                })
                continue

            try:
                analyze_post_intelligence(post, db)
                successful_posts += 1
            except Exception as exc:
                db.rollback()
                errors.append({"handle": profile.handle, "post_id": post.id, "error": f"intelligence: {exc}"})
                failed_posts += 1
            finally:
                completed_posts += 1
                _emit(on_progress, {
                    "completed_posts": completed_posts,
                    "phase_completed": completed_posts,
                    "successful_posts": successful_posts,
                    "failed_posts": failed_posts,
                })

        for post in pending_intelligence:
            _emit(on_progress, {
                "phase": "sync_post_analyses",
                "message": f"Gerando deep dive do post {completed_posts + 1}/{total_posts} de @{profile.handle}",
                "phase_total": total_posts,
                "phase_completed": completed_posts,
                "current_handle": profile.handle,
                "current_post_id": post.id,
            })
            try:
                analyze_post_intelligence(post, db)
                successful_posts += 1
            except Exception as exc:
                db.rollback()
                errors.append({"handle": profile.handle, "post_id": post.id, "error": f"intelligence: {exc}"})
                failed_posts += 1
            finally:
                completed_posts += 1
                _emit(on_progress, {
                    "completed_posts": completed_posts,
                    "phase_completed": completed_posts,
                    "successful_posts": successful_posts,
                    "failed_posts": failed_posts,
                })

        _emit(on_progress, {
            "phase": "sync_profiles",
            "message": f"Perfil @{profile.handle} sincronizado",
            "phase_total": len(profiles),
            "phase_completed": profile_index,
            "total_profiles": len(profiles),
            "completed_profiles": profile_index,
            "current_handle": profile.handle,
            "current_post_id": None,
        })

    return {
        "synced": len(profiles),
        "new_posts_analyzed": total_new,
        "errors": errors,
        "total_posts": total_posts,
        "completed_posts": completed_posts,
        "successful_posts": successful_posts,
        "failed_posts": failed_posts,
    }


def intelligence_analysis_workflow(
    db: Session,
    handle: Optional[str] = None,
    force: bool = False,
    limit: int = 50,
    on_progress: Optional[ProgressCallback] = None,
) -> dict:
    q = db.query(Post).join(Post.profile)
    if handle:
        q = q.filter(Profile.handle == handle)
    if not force:
        analyzed_ids = [r[0] for r in db.query(PostIntelligence.post_id).all()]
        if analyzed_ids:
            q = q.filter(Post.id.notin_(analyzed_ids))
    posts = q.order_by(Post.published_at.desc()).limit(limit).all()

    processed = 0
    failed = 0
    errors: list[str] = []

    _emit(on_progress, {
        "phase": "intelligence",
        "message": f"Preparando análise de inteligência de {len(posts)} posts",
        "phase_total": len(posts),
        "phase_completed": 0,
        "total_posts": len(posts),
        "completed_posts": 0,
        "successful_posts": 0,
        "failed_posts": 0,
    })

    for index, post in enumerate(posts, start=1):
        _emit(on_progress, {
            "phase": "intelligence",
            "message": f"Analisando post {index}/{len(posts)} de @{post.profile.handle}",
            "phase_total": len(posts),
            "phase_completed": index - 1,
            "current_handle": post.profile.handle,
            "current_post_id": post.id,
        })
        try:
            analyze_post_intelligence(post, db, force=force)
            processed += 1
        except Exception as exc:
            logger.error("Failed to analyze post %s: %s", post.id, exc)
            failed += 1
            errors.append(f"post {post.id}: {exc}")
        finally:
            _emit(on_progress, {
                "completed_posts": index,
                "phase_completed": index,
                "successful_posts": processed,
                "failed_posts": failed,
            })

    return {
        "processed": processed,
        "errors": errors,
        "total_posts": len(posts),
        "completed_posts": len(posts),
        "successful_posts": processed,
        "failed_posts": failed,
    }


def _new_job_state(
    job_id: str,
    handle: Optional[str],
    force: bool,
    sync_before: bool,
    limit: int,
) -> dict:
    now = _utcnow()
    return {
        "job_id": job_id,
        "status": "queued",
        "phase": "queued",
        "handle": handle,
        "force": force,
        "sync_before": sync_before,
        "limit": limit,
        "message": "Fila criada",
        "phase_total": 0,
        "phase_completed": 0,
        "total_profiles": 0,
        "completed_profiles": 0,
        "total_posts": 0,
        "completed_posts": 0,
        "successful_posts": 0,
        "failed_posts": 0,
        "current_handle": None,
        "current_post_id": None,
        "errors": [],
        "started_at": None,
        "updated_at": now,
        "finished_at": None,
    }


def _progress_updater(job_id: str) -> ProgressCallback:
    def _update(payload: dict) -> None:
        _set_job(job_id, **payload)
    return _update


def _run_analysis_job(
    job_id: str,
    handle: Optional[str],
    force: bool,
    sync_before: bool,
    limit: int,
) -> None:
    session = get_session()
    try:
        _set_job(
            job_id,
            status="running",
            phase="starting",
            message="Iniciando job",
            started_at=_utcnow(),
        )
        updater = _progress_updater(job_id)

        if sync_before:
            sync_result = sync_profiles_workflow(session, handle=handle, on_progress=updater)
            for error in sync_result["errors"]:
                _append_error(job_id, str(error))

        analysis_result = intelligence_analysis_workflow(
            session,
            handle=handle,
            force=force,
            limit=limit,
            on_progress=updater,
        )
        for error in analysis_result["errors"]:
            _append_error(job_id, error)

        _set_job(
            job_id,
            status="completed",
            phase="completed",
            message=f"Job concluído: {analysis_result['processed']} posts processados",
            phase_total=analysis_result["total_posts"],
            phase_completed=analysis_result["completed_posts"],
            total_posts=analysis_result["total_posts"],
            completed_posts=analysis_result["completed_posts"],
            successful_posts=analysis_result["successful_posts"],
            failed_posts=analysis_result["failed_posts"],
            current_post_id=None,
            finished_at=_utcnow(),
        )
    except Exception as exc:
        logger.exception("Live intelligence job %s failed: %s", job_id, exc)
        _append_error(job_id, str(exc))
        _set_job(
            job_id,
            status="failed",
            phase="failed",
            message=f"Job falhou: {exc}",
            finished_at=_utcnow(),
        )
    finally:
        session.close()


def create_analysis_job(
    handle: Optional[str] = None,
    force: bool = False,
    sync_before: bool = False,
    limit: int = 50,
) -> dict:
    job_id = uuid4().hex
    state = _new_job_state(job_id, handle=handle, force=force, sync_before=sync_before, limit=limit)
    with _jobs_lock:
        _jobs[job_id] = state

    thread = Thread(
        target=_run_analysis_job,
        args=(job_id, handle, force, sync_before, limit),
        daemon=True,
    )
    thread.start()
    return get_analysis_job(job_id) or state

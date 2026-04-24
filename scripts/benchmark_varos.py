#!/opt/homebrew/opt/python@3.11/bin/python3.11
import argparse
import json
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import joinedload

from src.database import get_session
from src.generator.content_generator import (
    _build_evidence_pack,
    _build_validated_data_catalog,
    _combine_issues,
    _evaluate_generation,
    _passes_quality_gate,
    _select_top_arguments,
    generate_post,
)
from src.carousel_quality import format_quality_feedback, estimate_target_slide_count
from src.models import GeneratedPost, Post, Profile, ProfileVoice

_PLANNING_STORAGE_ISSUE = "planejamento_narrativo ausente — o modelo pulou a etapa de pensamento narrativo"


def _query_candidate_post_ids(session, handle: str | None, limit: int) -> list[int]:
    query = (
        session.query(Post.id)
        .join(Post.profile)
        .join(Post.analysis)
        .join(Post.intelligence)
        .filter(Profile.type == "competitor", Post.post_type == "carousel")
        .order_by(Post.published_at.desc())
    )
    if handle:
        query = query.filter(Profile.handle == handle)
    return [post_id for (post_id,) in query.limit(limit).all()]


def _evaluate_generated_output(session, source_post: Post, generated: GeneratedPost) -> dict[str, object]:
    top_args = _select_top_arguments(session, source_post)
    validated_data_catalog = _build_validated_data_catalog(source_post, top_args)
    evidence_pack = _build_evidence_pack(source_post, top_args, validated_data_catalog)
    target_slide_count = estimate_target_slide_count(
        source_post.intelligence.technical_depth,
        getattr(source_post.intelligence, "carousel_complexity", {}).get("complexity_score"),
        minimum=10 if (source_post.post_type or "").strip().lower() == "carousel" else 6,
    )
    evaluation = _evaluate_generation(
        {
            "slides": generated.slides or [],
            "hook": generated.hook,
            "caption": generated.caption,
            "cta": generated.cta,
            "funnel_stage": generated.funnel_stage,
            "format": generated.format,
            "planejamento_narrativo": generated.planning_narrative or {},
        },
        source_post,
        evidence_pack,
        target_slide_count,
        generated.source_data_inventory or getattr(source_post.intelligence, "evidence_inventory", {}) or {},
    )
    return evaluation


def _run_single(post_id: int, keep_generated: bool) -> dict[str, object]:
    session = get_session()
    started = time.perf_counter()
    try:
        post = (
            session.query(Post)
            .options(
                joinedload(Post.profile),
                joinedload(Post.intelligence),
                joinedload(Post.analysis),
            )
            .filter(Post.id == post_id)
            .first()
        )
        if not post:
            raise ValueError(f"Post {post_id} nao encontrado.")

        voice = (
            session.query(ProfileVoice)
            .join(Profile, ProfileVoice.profile_id == Profile.id)
            .filter(Profile.type == "own")
            .order_by(ProfileVoice.generated_at.desc())
            .first()
        )
        if not voice:
            raise ValueError("Nenhum ProfileVoice do perfil proprio foi encontrado.")

        approved = (
            session.query(GeneratedPost)
            .filter_by(status="approved")
            .order_by(GeneratedPost.created_at.desc())
            .limit(3)
            .all()
        )

        generated = generate_post(
            source_post=post,
            voice=voice,
            approved_examples=approved,
            session=session,
        )
        elapsed = time.perf_counter() - started
        evaluation = _evaluate_generated_output(session, post, generated)
        issues = _combine_issues(evaluation)

        result = {
            "post_id": post.id,
            "handle": post.profile.handle,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "virality_score": post.analysis.virality_score if post.analysis else None,
            "generated_post_id": generated.id,
            "hook": generated.hook,
            "slide_count": len(generated.slides or []),
            "caption_words": len((generated.caption or "").split()),
            "score": round(float(evaluation["quality_report"]["score"]), 4),
            "strict_pass": _passes_quality_gate(evaluation),
            "issues": issues,
            "adjusted_issues": [issue for issue in issues if issue != _PLANNING_STORAGE_ISSUE],
            "planning_persisted": _PLANNING_STORAGE_ISSUE not in issues,
            "strengths": list(evaluation["quality_report"]["strengths"]),
            "quality_feedback": format_quality_feedback(evaluation["quality_report"]),
            "elapsed_seconds": round(elapsed, 2),
        }
        result["adjusted_strict_pass"] = not result["adjusted_issues"]

        if not keep_generated:
            session.delete(generated)
            session.commit()

        return result
    finally:
        session.close()


def _build_summary(results: list[dict[str, object]], failures: list[dict[str, object]]) -> dict[str, object]:
    scores = [float(item["score"]) for item in results]
    slide_counts = [int(item["slide_count"]) for item in results]
    caption_words = [int(item["caption_words"]) for item in results]
    elapsed = [float(item["elapsed_seconds"]) for item in results]
    issue_counter = Counter(
        issue
        for item in results
        for issue in item.get("issues", [])
    )
    adjusted_issue_counter = Counter(
        issue
        for item in results
        for issue in item.get("adjusted_issues", [])
    )

    return {
        "generated": len(results),
        "failed": len(failures),
        "strict_passes": sum(1 for item in results if item["strict_pass"]),
        "best_effort_only": sum(1 for item in results if not item["strict_pass"]),
        "adjusted_strict_passes": sum(1 for item in results if item["adjusted_strict_pass"]),
        "planning_storage_gaps": sum(1 for item in results if not item["planning_persisted"]),
        "avg_score": round(statistics.mean(scores), 4) if scores else 0.0,
        "min_score": round(min(scores), 4) if scores else 0.0,
        "max_score": round(max(scores), 4) if scores else 0.0,
        "avg_slides": round(statistics.mean(slide_counts), 2) if slide_counts else 0.0,
        "avg_caption_words": round(statistics.mean(caption_words), 2) if caption_words else 0.0,
        "avg_elapsed_seconds": round(statistics.mean(elapsed), 2) if elapsed else 0.0,
        "top_remaining_issues": issue_counter.most_common(10),
        "top_adjusted_issues": adjusted_issue_counter.most_common(10),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark do modelo Varos no Studio.")
    parser.add_argument("--handle", default="leandro.varos", help="Handle do concorrente a usar no benchmark.")
    parser.add_argument("--limit", type=int, default=10, help="Quantidade de posts para testar.")
    parser.add_argument("--keep-generated", action="store_true", help="Mantem os GeneratedPosts criados durante o benchmark.")
    parser.add_argument("--json-out", help="Salva o resultado completo em um arquivo JSON.")
    args = parser.parse_args()

    session = get_session()
    try:
        candidate_post_ids = _query_candidate_post_ids(session, args.handle, args.limit)
    finally:
        session.close()

    if not candidate_post_ids:
        raise SystemExit(f"Nenhum post pronto encontrado para handle={args.handle!r}.")

    print(f"Benchmark Varos")
    print(f"- Handle: {args.handle}")
    print(f"- Lote: {len(candidate_post_ids)} posts")
    print(f"- Keep generated: {args.keep_generated}")
    print("")

    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    for index, post_id in enumerate(candidate_post_ids, start=1):
        print(f"[{index}/{len(candidate_post_ids)}] Gerando post {post_id}...")
        try:
            result = _run_single(post_id, keep_generated=args.keep_generated)
            results.append(result)
            status = "STRICT_PASS" if result["strict_pass"] else "BEST_EFFORT"
            print(
                f"  -> {status} | score={result['score']:.4f} | "
                f"slides={result['slide_count']} | caption={result['caption_words']} palavras | "
                f"{result['elapsed_seconds']:.2f}s"
            )
            if result["issues"]:
                print(f"     issues: {'; '.join(result['issues'])}")
            if result["adjusted_issues"] != result["issues"]:
                print(f"     adjusted: {'; '.join(result['adjusted_issues']) or 'sem issues apos remover gap de persistencia'}")
        except Exception as exc:  # noqa: BLE001
            failure = {"post_id": post_id, "error": str(exc)}
            failures.append(failure)
            print(f"  -> FAILURE | {exc}")

    summary = _build_summary(results, failures)
    payload = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "handle": args.handle,
        "limit": args.limit,
        "keep_generated": args.keep_generated,
        "summary": summary,
        "results": results,
        "failures": failures,
    }

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        print("")
        print(f"JSON salvo em {output_path}")

    print("")
    print("Resumo")
    print(f"- Gerados: {summary['generated']}")
    print(f"- Falhas: {summary['failed']}")
    print(f"- Strict pass: {summary['strict_passes']}")
    print(f"- Best effort: {summary['best_effort_only']}")
    print(f"- Adjusted strict pass: {summary['adjusted_strict_passes']}")
    print(f"- Gaps de persistencia do planejamento: {summary['planning_storage_gaps']}")
    print(f"- Score medio: {summary['avg_score']}")
    print(f"- Slides medios: {summary['avg_slides']}")
    print(f"- Legenda media: {summary['avg_caption_words']} palavras")
    print(f"- Tempo medio: {summary['avg_elapsed_seconds']}s")
    if summary["top_remaining_issues"]:
        print("- Top issues residuais:")
        for issue, count in summary["top_remaining_issues"]:
            print(f"  {count}x {issue}")
    if summary["top_adjusted_issues"]:
        print("- Top issues ajustados (sem planning ausente por persistencia):")
        for issue, count in summary["top_adjusted_issues"]:
            print(f"  {count}x {issue}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Markdown reporting for engineering knowledge evaluation."""

from __future__ import annotations

from engineering_assets.asset_models import EngineeringAsset
from engineering_assets.asset_types import EngineeringAssetType
from engineering_knowledge.knowledge_models import KnowledgeRecommendation, KnowledgeReport


def build_knowledge_report(
    matches: tuple,
    *,
    related_assets: tuple[EngineeringAsset, ...] = (),
    recommendations: tuple[KnowledgeRecommendation, ...] = (),
) -> KnowledgeReport:
    """Build a knowledge report from matches and related assets."""
    summary = _build_summary(len(matches))
    return KnowledgeReport(
        matches=matches,
        related_assets=related_assets,
        recommendations=recommendations,
        summary=summary,
    )


def format_knowledge_report_markdown(report: KnowledgeReport) -> str:
    """Render a markdown engineering knowledge report."""
    verification_guides = _filter_recommendations(report.recommendations, "verification")
    runbooks = _filter_recommendations(report.recommendations, "runbook")
    references = _filter_recommendations(report.recommendations, "reference")
    reading = _filter_recommendations(report.recommendations, "reading")

    lines = [
        "# Engineering Knowledge Report",
        "",
        "## Summary",
        "",
        report.summary,
        "",
        "## Matched Knowledge",
        "",
    ]

    if report.matches:
        for match in report.matches:
            lines.append(
                f"- **{match.title}** (`{match.knowledge_id}`) — "
                f"score {match.score:.1f}; {match.match_reason}"
            )
    else:
        lines.append("_No knowledge matched._")

    lines.extend(["", "## Related Assets", ""])
    if report.related_assets:
        for asset in report.related_assets:
            lines.append(f"- **{asset.title}** (`{asset.asset_id}`) — {asset.asset_type.value}")
    else:
        lines.append("_No related assets._")

    lines.extend(["", "## Recommended Reading", ""])
    lines.extend(_format_recommendation_lines(reading))

    lines.extend(["", "## Verification Guides", ""])
    lines.extend(_format_recommendation_lines(verification_guides))

    lines.extend(["", "## Runbooks", ""])
    lines.extend(_format_recommendation_lines(runbooks))

    lines.extend(["", "## References", ""])
    lines.extend(_format_recommendation_lines(references))

    return "\n".join(lines)


def build_recommendations_from_assets(
    matches: tuple,
    assets: tuple[EngineeringAsset, ...],
) -> tuple[KnowledgeRecommendation, ...]:
    """Build deterministic recommendations from matched knowledge and assets."""
    asset_by_id = {asset.asset_id: asset for asset in assets}
    recommendations: list[KnowledgeRecommendation] = []

    for match in matches:
        recommendations.append(
            KnowledgeRecommendation(
                knowledge_id=match.knowledge_id,
                title=match.title,
                recommendation_type="reading",
                asset_id=match.matched_asset_ids[0] if match.matched_asset_ids else None,
                summary=match.summary,
            )
        )
        for asset_id in match.matched_asset_ids:
            asset = asset_by_id.get(asset_id)
            if asset is None:
                continue
            recommendation_type = _recommendation_type_for_asset(asset.asset_type)
            recommendations.append(
                KnowledgeRecommendation(
                    knowledge_id=match.knowledge_id,
                    title=asset.title,
                    recommendation_type=recommendation_type,
                    asset_id=asset.asset_id,
                    summary=asset.summary,
                )
            )

    deduped: dict[tuple[str, str, str], KnowledgeRecommendation] = {}
    for recommendation in recommendations:
        key = (
            recommendation.knowledge_id,
            recommendation.recommendation_type,
            recommendation.asset_id or "",
        )
        deduped[key] = recommendation
    return tuple(
        deduped[key]
        for key in sorted(deduped, key=lambda item: (item[2], item[1], item[0]))
    )


def _recommendation_type_for_asset(asset_type: EngineeringAssetType) -> str:
    mapping = {
        EngineeringAssetType.VERIFICATION_GUIDE: "verification",
        EngineeringAssetType.RUNBOOK: "runbook",
        EngineeringAssetType.REFERENCE: "reference",
        EngineeringAssetType.DOCUMENT: "reference",
        EngineeringAssetType.KNOWLEDGE_ARTICLE: "reference",
        EngineeringAssetType.INCIDENT: "incident",
    }
    return mapping.get(asset_type, "reading")


def _filter_recommendations(
    recommendations: tuple[KnowledgeRecommendation, ...],
    recommendation_type: str,
) -> tuple[KnowledgeRecommendation, ...]:
    return tuple(
        item for item in recommendations if item.recommendation_type == recommendation_type
    )


def _format_recommendation_lines(
    recommendations: tuple[KnowledgeRecommendation, ...],
) -> list[str]:
    if not recommendations:
        return ["_None._"]
    return [
        f"- **{item.title}** ({item.recommendation_type}) — {item.summary}"
        for item in recommendations
    ]


def _build_summary(match_count: int) -> str:
    if match_count == 0:
        return "No engineering knowledge matched."
    suffix = "entry" if match_count == 1 else "entries"
    return f"Matched {match_count} engineering knowledge {suffix}."

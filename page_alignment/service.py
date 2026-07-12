from __future__ import annotations

"""Align submitted answer-sheet pages to a blank template page."""

from pathlib import Path
from typing import Any

from d_module import config
from d_module.schemas.normalized_page import NormalizedPage


def align_page_to_template(
    page: dict[str, Any],
    template_page: dict[str, Any],
    template_dir: str | None = None,
) -> dict[str, Any]:
    """Return an image in template coordinates plus an alignment confidence.

    ORB/RANSAC is used when a blank reference image is available. A size-only
    fallback is retained for the documented minimum chain, but is explicitly
    flagged for review because it cannot correct skew or perspective.
    """
    cv2 = _optional_cv2()
    if cv2 is None:
        return _scale_with_pillow(page, template_page)
    source_path = Path(page.get("preprocessed_image_path") or page["page_image_path"])
    student = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if student is None:
        raise ValueError(f"Cannot read submitted page image: {source_path}")

    target_width = int(template_page["reference_width"])
    target_height = int(template_page["reference_height"])
    reference_path = _resolve_reference_path(template_page.get("reference_image_path"), template_dir)
    output_path = config.PREPROCESSED_DIR / f"{page['file_id']}_p{int(page['page_no']):03d}_aligned.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if reference_path and reference_path.is_file():
        reference = cv2.imread(str(reference_path), cv2.IMREAD_COLOR)
        if reference is None:
            raise ValueError(f"Cannot read template reference image: {reference_path}")
        reference = cv2.resize(reference, (target_width, target_height))
        reference_output_path = config.PREPROCESSED_DIR / f"{page['file_id']}_p{int(page['page_no']):03d}_template_ref.png"
        cv2.imwrite(str(reference_output_path), reference)
        aligned, confidence = _align_with_orb(cv2, student, reference)
        if aligned is not None:
            cv2.imwrite(str(output_path), aligned)
            return {
                "image_path": str(output_path),
                "alignment_confidence": confidence,
                "needs_review": confidence < 0.65,
                "risk_flags": [] if confidence >= 0.65 else ["page_alignment_low_confidence"],
                "method": "orb_ransac",
                "reference_image_path": str(reference_output_path),
                "width": target_width,
                "height": target_height,
            }

    resized = cv2.resize(student, (target_width, target_height))
    cv2.imwrite(str(output_path), resized)
    return {
        "image_path": str(output_path),
        "alignment_confidence": 0.0,
        "needs_review": True,
        "risk_flags": ["page_alignment_failed" if reference_path else "template_reference_missing"],
        "method": "scale_fallback",
        "reference_image_path": None,
        "width": target_width,
        "height": target_height,
    }


def _align_with_orb(cv2: Any, student: Any, reference: Any) -> tuple[Any | None, float]:
    reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    student_gray = cv2.cvtColor(student, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(nfeatures=2500)
    kp_ref, des_ref = orb.detectAndCompute(reference_gray, None)
    kp_student, des_student = orb.detectAndCompute(student_gray, None)
    if des_ref is None or des_student is None:
        return None, 0.0
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(des_student, des_ref)
    if len(matches) < 8:
        return None, 0.0
    matches = sorted(matches, key=lambda item: item.distance)[:300]
    import numpy as np
    source_points = np.float32([kp_student[item.queryIdx].pt for item in matches]).reshape(-1, 1, 2)
    target_points = np.float32([kp_ref[item.trainIdx].pt for item in matches]).reshape(-1, 1, 2)
    homography, mask = cv2.findHomography(source_points, target_points, cv2.RANSAC, 5.0)
    if homography is None or mask is None:
        return None, 0.0
    inlier_ratio = float(mask.ravel().sum()) / len(matches)
    if inlier_ratio < 0.25:
        return None, inlier_ratio
    aligned = cv2.warpPerspective(student, homography, (reference.shape[1], reference.shape[0]))
    return aligned, round(inlier_ratio, 4)


def _resolve_reference_path(value: Any, template_dir: str | None) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute() or not template_dir:
        return path
    return Path(template_dir) / path


def _scale_with_pillow(page: dict[str, Any], template_page: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image
    source_path = Path(page.get("preprocessed_image_path") or page["page_image_path"])
    output_path = config.PREPROCESSED_DIR / f"{page['file_id']}_p{int(page['page_no']):03d}_aligned.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as image:
        image.convert("RGB").resize(
            (int(template_page["reference_width"]), int(template_page["reference_height"]))
        ).save(output_path)
    return {
        "image_path": str(output_path), "alignment_confidence": 0.0,
        "needs_review": True, "risk_flags": ["opencv_unavailable", "page_alignment_failed"],
        "method": "pillow_scale_fallback", "width": int(template_page["reference_width"]),
        "height": int(template_page["reference_height"]), "reference_image_path": None,
    }


def _optional_cv2() -> Any | None:
    try:
        import cv2
    except ImportError:
        return None
    return cv2

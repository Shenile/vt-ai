from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
from PIL import Image, ImageDraw

def mark_issues(curr_pair, prev_pair, lpips_model, clip_model,
                lpips_thresh=0.03, clip_thresh=0.98, min_size=20):
    """
    Identical in input/output behavior to the old mark_issues function.
    Preserves all existing return fields and structure.
    """
    def is_bbox_contained(bigger, smaller):
        x1_b, y1_b, x2_b, y2_b = bigger
        x1_s, y1_s, x2_s, y2_s = smaller
        return x1_b <= x1_s and y1_b <= y1_s and x2_b >= x2_s and y2_b >= y2_s

    # Initialize images and DOM data
    prev_img = prev_pair["image"].copy()
    curr_img = curr_pair["image"].copy()
    prev_draw = ImageDraw.Draw(prev_img)
    curr_draw = ImageDraw.Draw(curr_img)
    prev_dom = prev_pair["dom"]
    curr_dom = curr_pair["dom"]

    results = []
    segments = []

    # Process each DOM element
    for el_prev, el_curr in zip(prev_dom, curr_dom):
        if el_prev.get("tag") != el_curr.get("tag"):
            continue

        try:
            x = int(el_prev["x"])
            y = int(el_prev["y"])
            w = int(el_prev["width"])
            h = int(el_prev["height"])
            
            if w < min_size or h < min_size:
                continue

            # Extract image crops
            bbox = (x, y, x + w, y + h)
            crop_prev = prev_img.crop(bbox)
            crop_curr = curr_img.crop(bbox)

            # Compute similarity metrics
            lp_score = lpips_model.compute_distance(crop_prev, crop_curr)
            clip_score = clip_model.compute_similarity(crop_prev, crop_curr)
            is_changed = (lp_score > lpips_thresh) or (clip_score < clip_thresh)

            # Build result records (identical to old version)
            results.append({
                "tag": el_prev["tag"],
                "text": el_prev.get("text", ""),
                "bbox": bbox,
                "LPIPS": round(lp_score, 4),
                "CLIP": round(clip_score, 4),
                "LPIPS_Detects_Change": int(lp_score > lpips_thresh),
                "CLIP_Detects_Change": int(clip_score < clip_thresh),
                "Change_Flag": int(is_changed)
            })

            segments.append({
                "tag": el_prev["tag"],
                "bbox": bbox,
                "prev_crop": crop_prev,
                "curr_crop": crop_curr
            })

        except Exception as e:
            print(f"[!] Skipped region due to error: {e}")
            continue

    # Convert to DataFrame (identical structure)
    df_scores = pd.DataFrame(results)

    # Parent-child suppression (same algorithm)
    changed = [r for r in results if r["Change_Flag"] == 1]
    changed_sorted = sorted(changed, key=lambda r: (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1]))
    
    suppressed = set()
    for i, inner in enumerate(changed_sorted):
        xi1, yi1, xi2, yi2 = inner["bbox"]
        for j, outer in enumerate(changed_sorted[i+1:], start=i+1):
            xo1, yo1, xo2, yo2 = outer["bbox"]
            if xo1 <= xi1 and yo1 <= yi1 and xo2 >= xi2 and yo2 >= yi2:
                suppressed.add(j)

    # Apply suppression (same as original)
    for idx in suppressed:
        results_idx = results.index(changed_sorted[idx])
        results[results_idx]["Change_Flag"] = 0
        results[results_idx]["LPIPS_Detects_Change"] = 0
        results[results_idx]["CLIP_Detects_Change"] = 0

    # Update DataFrame after suppression
    df_scores = pd.DataFrame(results)

    # Draw changes (same visualization)
    for i, row in df_scores[df_scores["Change_Flag"] == 1].iterrows():
        x1, y1, x2, y2 = row["bbox"]
        prev_draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        curr_draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

    # Same summary structure
    summary = {
        "total_regions": len(df_scores),
        "changed_regions": int(df_scores["Change_Flag"].sum()) if not df_scores.empty else 0,
        "change_percent": round(df_scores["Change_Flag"].mean() * 100, 2) if not df_scores.empty else 0.0
    }

    print(f"[✓] Compared {len(df_scores)} DOM regions. Changes: {summary['changed_regions']}")

    # Identical return structure
    return {
        "highlighted_prev": prev_img,
        "highlighted_curr": curr_img,
        "scores": df_scores,
        "segments": segments,
        "summary": summary
    }
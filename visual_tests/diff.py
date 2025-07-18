from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
from PIL import Image, ImageDraw
import numpy as np

@dataclass
class ChangeDetectionResult:
    """Structured results container for change detection"""
    highlighted_prev: Image.Image
    highlighted_curr: Image.Image
    changed_elements: pd.DataFrame  # DataFrame of changed elements with full metrics
    metrics: Dict  # Detection statistics
    debug_info: Optional[Dict] = None  # Debug data if enabled

def mark_issues(
    curr_pair: Dict, 
    prev_pair: Dict,
    lpips_model,
    clip_model,
    *,
    lpips_thresh: float = 0.04,
    clip_thresh: float = 0.96,
    min_size: int = 15,
    containment_thresh: float = 0.8,
    debug: bool = False
) -> ChangeDetectionResult:
    """
    Detect meaningful UI changes between two states with:
    - Visual difference analysis (LPIPS)
    - Semantic similarity (CLIP)
    - DOM hierarchy awareness
    - Priority-based suppression of redundant changes

    Args:
        curr_pair: {'image': PIL.Image, 'dom': List[Dict]} - Current UI state
        prev_pair: {'image': PIL.Image, 'dom': List[Dict]} - Baseline UI state
        lpips_model: Pre-initialized LPIPS model
        clip_model: Pre-initialized CLIP model
        lpips_thresh: Visual change threshold (0-1)
        clip_thresh: Semantic similarity threshold (0-1) 
        min_size: Minimum element size (pixels) to consider
        containment_thresh: IoU threshold for parent-child suppression
        debug: Enable debug outputs

    Returns:
        ChangeDetectionResult: Structured results with highlights and metrics
    """
    # --- Initialize ---
    prev_img = prev_pair["image"].copy()
    curr_img = curr_pair["image"].copy()
    prev_draw = ImageDraw.Draw(prev_img)
    curr_draw = ImageDraw.Draw(curr_img)
    
    # --- Element Matching ---
    def get_element_key(el: Dict) -> str:
        """Create stable identifier using structural features"""
        return f"{el['tag']}_{el['x']}_{el['y']}_{el['width']}_{el['height']}_{el.get('text','')[:30]}"
    
    prev_elements = {get_element_key(el): el for el in prev_pair["dom"]}
    curr_elements = {get_element_key(el): el for el in curr_pair["dom"]}
    common_elements = set(prev_elements.keys()) & set(curr_elements.keys())
    
    # --- Change Detection ---
    results = []
    debug_data = {"skipped": []} if debug else None
    
    for key in common_elements:
        el_prev = prev_elements[key]
        el_curr = curr_elements[key]
        
        # Skip conditions
        if (el_prev['width'] < min_size or 
            el_prev['height'] < min_size or 
            not el_prev.get('is_visible', True)):
            if debug:
                debug_data["skipped"].append({
                    "reason": "size/visibility", 
                    "element": el_prev
                })
            continue
        
        try:
            # Extract element crops
            bbox = (el_prev['x'], el_prev['y'], 
                    el_prev['x'] + el_prev['width'], 
                    el_prev['y'] + el_prev['height'])
            crop_prev = prev_img.crop(bbox)
            crop_curr = curr_img.crop(bbox)
            
            # Compute similarity metrics
            lpips_score = lpips_model.compute_distance(crop_prev, crop_curr)
            clip_score = clip_model.compute_similarity(crop_prev, crop_curr)
            
            # Determine change status
            is_visual_change = lpips_score > lpips_thresh
            is_semantic_change = clip_score < clip_thresh
            is_changed = is_visual_change or is_semantic_change
            
            results.append({
                "element_id": key,
                "tag": el_prev['tag'],
                "text": el_prev.get('text', ''),
                "bbox": bbox,
                "area": el_prev['width'] * el_prev['height'],
                "depth": el_prev.get('depth', 0),
                "is_clickable": el_prev.get('is_clickable', False),
                "is_text": len(el_prev.get('text', '').strip()) > 0,
                "LPIPS": float(lpips_score),
                "CLIP": float(clip_score),
                "visual_change": is_visual_change,
                "semantic_change": is_semantic_change,
                "changed": is_changed,
                "priority": (
                    2 if el_prev.get('is_clickable') else 0) +  # Clickable elements first
                    (1 if el_prev.get('is_text') else 0) +       # Text elements second
                    min(1, (el_prev['width']*el_prev['height'])/10000)  # Normalized area
            })
            
        except Exception as e:
            if debug:
                debug_data["skipped"].append({
                    "reason": str(e),
                    "element": el_prev
                })
            continue
    
    # --- Hierarchical Suppression ---
    df = pd.DataFrame(results)
    if not df.empty:
        # Sort by priority (highest first) then area (smallest first)
        df = df.sort_values(["priority", "area"], ascending=[False, True])
        
        # Calculate IoU matrix for containment checks
        changed = df[df["changed"]]
        suppress_indices = set()
        
        for i, (_, row_i) in enumerate(changed.iterrows()):
            for j, (_, row_j) in enumerate(changed.iloc[i+1:].iterrows(), start=i+1):
                # Check if row_j contains row_i with sufficient overlap
                xi1, yi1, xi2, yi2 = row_i["bbox"]
                xj1, yj1, xj2, yj2 = row_j["bbox"]
                
                inter_area = max(0, min(xi2, xj2) - max(xi1, xj1)) * \
                            max(0, min(yi2, yj2) - max(yi1, yj1))
                iou = inter_area / ((xi2-xi1)*(yi2-yi1) + 1e-6)
                
                if iou >= containment_thresh:
                    suppress_indices.add(changed.index[j])
        
        # Apply suppression
        df.loc[df.index.isin(suppress_indices), "changed"] = False
        
        if debug:
            debug_data["suppressed"] = df.loc[df.index.isin(suppress_indices)].to_dict('records')
    
    # --- Visualization ---
    changed_elements = df[df["changed"]]
    
    for _, row in changed_elements.iterrows():
        x1, y1, x2, y2 = row["bbox"]
        outline_color = "#FF0000" if row["visual_change"] else "#0000FF"  # Red for visual, blue for semantic
        
        for draw in [prev_draw, curr_draw]:
            draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)
            if row["is_clickable"]:
                draw.text((x1, y1-10), f"{row['tag']}:{row['text'][:10]}", fill=outline_color)
    
    # --- Metrics ---
    metrics = {
        "total_elements": len(df),
        "changed_elements": len(changed_elements),
        "change_rate": len(changed_elements) / len(df) if len(df) > 0 else 0,
        "visual_changes": changed_elements["visual_change"].sum(),
        "semantic_changes": changed_elements["semantic_change"].sum(),
        "avg_lpips": df["LPIPS"].mean(),
        "avg_clip": df["CLIP"].mean(),
        "suppressed_elements": len(suppress_indices)
    }
    
    return ChangeDetectionResult(
        highlighted_prev=prev_img,
        highlighted_curr=curr_img,
        changed_elements=changed_elements,
        metrics=metrics,
        debug_info=debug_data
    )
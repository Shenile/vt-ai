from typing import Dict, List, Tuple, Optional
import pandas as pd
from PIL import Image, ImageDraw

def mask_children(image: Image.Image, element: Dict, dom_map: Dict, offset_x: int = 0, offset_y: int = 0) -> None:
    """Masks child elements of the given element in the image."""
    draw = ImageDraw.Draw(image)
    children = element.get("children", [])
    print(f"  🛠️ Masking {len(children)} children for element {element.get('id')}")
    
    for child_id in children:
        if child := dom_map.get(child_id):
            try:
                cx = int(child["x"]) - offset_x
                cy = int(child["y"]) - offset_y
                cw, ch = int(child["width"]), int(child["height"])
                draw.rectangle([cx, cy, cx + cw, cy + ch], fill="black")
                print(f"    ✅ Masked child {child_id} at ({cx},{cy})-({cx+cw},{cy+ch})")
            except (KeyError, ValueError) as e:
                print(f"    ⚠️ Failed to mask child {child_id}: {e}")

class VisualComparator:
    def __init__(self, lpips_model, clip_model, lpips_thresh: float = 0.03, clip_thresh: float = 0.98, min_size: int = 20):
        self.lpips_model = lpips_model
        self.clip_model = clip_model
        self.lpips_thresh = lpips_thresh
        self.clip_thresh = clip_thresh
        self.min_size = min_size
        print(f"🔧 Initialized VisualComparator with thresholds: LPIPS={lpips_thresh}, CLIP={clip_thresh}, min_size={min_size}")

    def _initialize_images(self, prev_pair: Dict, curr_pair: Dict) -> Tuple[Image.Image, ImageDraw.Draw, Image.Image, ImageDraw.Draw]:
        """Initialize images and drawing contexts."""
        print("🖼️ Initializing images for comparison")
        prev_img = prev_pair["image"].copy()
        curr_img = curr_pair["image"].copy()
        return (
            prev_img,
            ImageDraw.Draw(prev_img),
            curr_img,
            ImageDraw.Draw(curr_img)
        )

    def _create_dom_map(self, dom_snapshot: List[Dict]) -> Dict:
        """Create a mapping of DOM elements by their ID with parent-child relationships."""
        print(f"🌳 Building DOM map from {len(dom_snapshot)} elements")
        dom_map = {}
        parents_with_children = 0
        
        for el in dom_snapshot:
            if "id" not in el:
                continue
            dom_map[el["id"]] = el
            if "parent_id" in el and el["parent_id"] in dom_map:
                dom_map[el["parent_id"]].setdefault("children", []).append(el["id"])
                parents_with_children += 1
                
        print(f"  📊 DOM map contains {len(dom_map)} elements, {parents_with_children} parent-child relationships")
        return dom_map

    def _get_element_bbox(self, element: Dict) -> Optional[Tuple[int, int, int, int]]:
        """Calculate element bounding box with validation."""
        try:
            x = int(element.get("x", 0))
            y = int(element.get("y", 0))
            w = int(element.get("width", 0))
            h = int(element.get("height", 0))
            print(f"  📐 Bounding box for {element.get('tag')}: ({x},{y})-({x+w},{y+h})")
            return (x, y, x + w, y + h)
        except (TypeError, ValueError) as e:
            print(f"  ⚠️ Invalid bbox for {element.get('tag')}: {e}")
            return None

    def _is_valid_bbox(self, bbox: Tuple[int, int, int, int], image_size: Tuple[int, int]) -> bool:
        """Validate that bounding box is within image bounds."""
        if not bbox:
            return False
        x1, y1, x2, y2 = bbox
        img_w, img_h = image_size
        valid = (x1 >= 0 and y1 >= 0 and 
                x2 <= img_w and y2 <= img_h and 
                x1 < x2 and y1 < y2)
        if not valid:
            print(f"  ⚠️ Invalid bbox dimensions: {bbox} vs image size {image_size}")
        return valid

    def _create_result_record(self, element: Dict, bbox: Tuple[int, int, int, int], 
                            is_changed: bool, lp_score: float = None, clip_score: float = None) -> Dict:
        """Create a comprehensive result record with all metrics."""
        record = {
            "tag": element.get("tag", ""),
            "text": element.get("text", ""),
            "bbox": bbox,
            "Change_Flag": int(is_changed)
        }
        
        if lp_score is not None and clip_score is not None:
            record.update({
                "LPIPS": round(lp_score, 4),
                "CLIP": round(clip_score, 4),
                "LPIPS_Detects_Change": int(lp_score > self.lpips_thresh),
                "CLIP_Detects_Change": int(clip_score < self.clip_thresh)
            })
        
        return record

    def _compare_elements(self, prev_img: Image.Image, curr_img: Image.Image, 
                         prev_dom: List[Dict], curr_dom: List[Dict]) -> Tuple[List[Dict], List[Tuple]]:
        """Perform the two-pass comparison of DOM elements."""
        print("\n🔍 Starting first pass (unmasked comparison)")
        results = []
        changed_elements = []
        elements_with_children = 0
        total_elements = 0

        # First pass - unmasked comparison
        for el_prev, el_curr in zip(prev_dom, curr_dom):
            total_elements += 1
            if el_prev.get("tag") != el_curr.get("tag"):
                print(f"  ↪️ Tag mismatch: {el_prev.get('tag')} vs {el_curr.get('tag')}")
                continue

            try:
                w, h = int(el_prev.get("width", 0)), int(el_prev.get("height", 0))
                if w < self.min_size or h < self.min_size:
                    print(f"  ⏩ Skipped small element: {el_prev.get('tag')} ({w}x{h})")
                    continue

                bbox = self._get_element_bbox(el_prev)
                if not self._is_valid_bbox(bbox, prev_img.size):
                    continue

                if el_prev.get("children"):
                    elements_with_children += 1

                crop_prev, crop_curr = prev_img.crop(bbox), curr_img.crop(bbox)
                lp_score = self.lpips_model.compute_distance(crop_prev, crop_curr)
                clip_score = self.clip_model.compute_similarity(crop_prev, crop_curr)
                is_changed = (lp_score > self.lpips_thresh) or (clip_score < self.clip_thresh)

                results.append(self._create_result_record(
                    el_prev, bbox, is_changed, lp_score, clip_score
                ))
                
                if is_changed:
                    changed_elements.append((el_prev, el_curr, bbox, lp_score, clip_score))
                    print(f"  🔴 Change detected: {el_prev.get('tag')} (LPIPS: {lp_score:.3f}, CLIP: {clip_score:.3f})")

            except Exception as e:
                print(f"  ⚠️ Skipped {el_prev.get('tag')} - {str(e)}")
                continue

        print(f"\n📊 First pass complete: {len(results)} elements compared, {len(changed_elements)} potential changes")
        print(f"  - Elements with children: {elements_with_children}")
        print(f"  - Total elements processed: {total_elements}")

        # Second pass - masked verification
        if changed_elements:
            print("\n🔍 Starting second pass (masked verification)")
            masking_applied = 0
            prev_dom_map = self._create_dom_map(prev_dom)
            curr_dom_map = self._create_dom_map(curr_dom)

            for idx, (el_prev, el_curr, bbox, old_lp, old_clip) in enumerate(changed_elements, 1):
                print(f"\n  🔄 Processing change {idx}/{len(changed_elements)}: {el_prev.get('tag')}")
                try:
                    x, y = bbox[0], bbox[1]
                    crop_prev, crop_curr = prev_img.crop(bbox).copy(), curr_img.crop(bbox).copy()

                    prev_has_children = bool(el_prev.get("children"))
                    curr_has_children = bool(el_curr.get("children"))
                    
                    print(f"    - Children: Prev={prev_has_children}, Curr={curr_has_children}")
                    
                    if prev_has_children:
                        print(f"    🎭 Masking previous element children")
                        mask_children(crop_prev, el_prev, prev_dom_map, x, y)
                        masking_applied += 1
                    if curr_has_children:
                        print(f"    🎭 Masking current element children")
                        mask_children(crop_curr, el_curr, curr_dom_map, x, y)
                        masking_applied += 1

                    new_lp = self.lpips_model.compute_distance(crop_prev, crop_curr)
                    new_clip = self.clip_model.compute_similarity(crop_prev, crop_curr)
                    is_changed = (new_lp > self.lpips_thresh) or (new_clip < self.clip_thresh)

                    print(f"    - Scores: LPIPS={new_lp:.3f} (was {old_lp:.3f}), CLIP={new_clip:.3f} (was {old_clip:.3f})")
                    print(f"    - Change status: {'Changed' if is_changed else 'Unchanged'}")

                    # Update results with new scores
                    for result in results:
                        if result["bbox"] == bbox:
                            result.update({
                                "LPIPS": round(new_lp, 4),
                                "CLIP": round(new_clip, 4),
                                "LPIPS_Detects_Change": int(new_lp > self.lpips_thresh),
                                "CLIP_Detects_Change": int(new_clip < self.clip_thresh),
                                "Change_Flag": int(is_changed)
                            })
                            break

                except Exception as e:
                    print(f"    ⚠️ Failed to process changed element: {e}")
                    continue

            print(f"\n📊 Second pass complete: Masking applied to {masking_applied} elements")
            print(f"  - Total changes verified: {len(changed_elements)}")

        return results, changed_elements

    def _highlight_changes(self, draw: ImageDraw.Draw, df_scores: pd.DataFrame) -> None:
        """Draw red rectangles around changed elements."""
        print("\n🖍️ Highlighting changes in image")
        changes = df_scores[df_scores["Change_Flag"] == 1]
        print(f"  - Found {len(changes)} elements to highlight")
        
        for _, row in changes.iterrows():
            try:
                x1, y1, x2, y2 = row["bbox"]
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
                print(f"    ✅ Highlighted {row['tag']} at ({x1},{y1})-({x2},{y2})")
            except (KeyError, ValueError) as e:
                print(f"    ⚠️ Failed to highlight change: {e}")

    def compare(self, prev_pair: Dict, curr_pair: Dict) -> Dict:
        """Main comparison method."""
        print("\n" + "="*50)
        print("🏁 Starting visual comparison")
        print("="*50)
        try:
            prev_img, prev_draw, curr_img, curr_draw = self._initialize_images(prev_pair, curr_pair)
            prev_dom, curr_dom = prev_pair.get("dom", []), curr_pair.get("dom", [])

            print(f"\n📝 DOM elements: Previous={len(prev_dom)}, Current={len(curr_dom)}")
            results, _ = self._compare_elements(prev_img, curr_img, prev_dom, curr_dom)
            df_scores = pd.DataFrame(results)

            self._highlight_changes(prev_draw, df_scores)
            self._highlight_changes(curr_draw, df_scores)

            changed_count = df_scores["Change_Flag"].sum()
            total_count = len(df_scores)
            change_percent = (changed_count / total_count * 100) if total_count > 0 else 0.0

            print("\n" + "="*50)
            print("🏁 Comparison complete")
            print(f"  - Total regions: {total_count}")
            print(f"  - Changed regions: {changed_count} ({change_percent:.1f}%)")
            print("="*50)

            return {
                "highlighted_prev": prev_img,
                "highlighted_curr": curr_img,
                "scores": df_scores,
                "summary": {
                    "total_regions": total_count,
                    "changed_regions": changed_count,
                    "change_percent": round(change_percent, 2)
                }
            }
        except Exception as e:
            print(f"💥 Critical error in comparison: {e}")
            raise
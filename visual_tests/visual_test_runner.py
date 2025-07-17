from datetime import datetime
from model_wrappers import LPIPSWrapper, CLIPWrapper
from utils import (
    get_current_pair_in_memory,
    mark_issues,
    encode_image_to_base64, update_last_processed
)

def run_visual_test():
    """
    Runs the visual diff test using LPIPS and CLIP.

    Returns:
        Tuple:
            result_dict (dict | None): structured visual test result if successful.
            error_message (str | None): error message if something failed.
    """
    try:
        print("[✓] Starting visual test...")
        start_time = datetime.now()

        # Step 1: Load commit pair
        print("[•] Loading commit pair from cache and repo...")
        pair_data = get_current_pair_in_memory()
        print(f"pair data : ", pair_data)

        if not pair_data:
            print("[✗] No valid commit pair found.")
            return None, "Could not load baseline pair."

        if pair_data.get("first_time"):
            print(f"[•] First-time baseline set to commit: {pair_data['curr_commit']}")
            return None, "Base Commit recorded"

        prev = pair_data.get("prev_commit")
        curr = pair_data.get("curr_commit")
        if not prev or not curr or curr == prev:
            return None, "Current and previous commits are identical or missing."

        # Step 2: Validate image and DOM data
        curr_data = pair_data.get("curr")
        prev_data = pair_data.get("prev")

        if not curr_data or not prev_data:
            return None, "One of the commit data objects is missing."

        if "image" not in curr_data or "image" not in prev_data:
            return None, "Screenshot missing in one of the commits."

        if "dom" not in curr_data or "dom" not in prev_data:
            return None, "DOM snapshot missing in one of the commits."

        # # Optional sanity check: Ensure images aren't swapped (basic sanity by filename)
        # if prev not in prev_data["image"] or curr not in curr_data["image"]:
        #     return None, "Commit image mismatch or swapped during rendering."

        print(f"[✓] Comparing commits:\n     → Previous: {prev}\n     → Current : {curr}")

        # Step 3: Load models
        print("[•] Loading LPIPS and CLIP models...")
        lpips = LPIPSWrapper()
        clip = CLIPWrapper()
        print("[✓] Models initialized.")

        # Step 4: Run visual comparison
        print("[•] Running visual comparison...")
        result = mark_issues(curr_data, prev_data, lpips, clip)
        print("[✓] Visual comparison completed.")

        # Step 5: Validate diff result
        if not result.get("highlighted_prev") or not result.get("highlighted_curr"):
            return None, "Highlighted diff images could not be generated."

        print("[•] Encoding main diff images to base64...")
        base64_prev = encode_image_to_base64(result["highlighted_prev"])
        base64_curr = encode_image_to_base64(result["highlighted_curr"])
        print("[✓] Main images encoded.")

        # Step 6: Prepare segments
        segments = result.get("segments", [])
        if not segments:
            print("[•] No visual differences found.")
        else:
            print(f"[•] Processing {len(segments)} changed UI segments...")

        segments_output = []
        for i, seg in enumerate(segments, start=1):
            segments_output.append({
                "tag": seg["tag"],
                "bbox": seg["bbox"],
                "prev_crop": encode_image_to_base64(seg["prev_crop"]),
                "curr_crop": encode_image_to_base64(seg["curr_crop"]),
            })
            print(f"    └─ Segment {i}: Tag={seg['tag']} BBox={seg['bbox']}")

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"[✓] Visual test completed in {duration.total_seconds():.2f}s")

        update_last_processed(curr)

        # Step 7: Return result
        return {
            "summary": result.get("summary", "No summary provided."),
            "scores": result.get("scores", {}),
            "img_prev_base64": base64_prev,
            "img_curr_base64": base64_curr,
            "segments": segments_output
        }, None

    except Exception as e:
        print(f"[✗] Visual test failed: {str(e)}")
        return None, f"Visual test failed: {str(e)}"

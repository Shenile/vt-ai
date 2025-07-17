from datetime import datetime
from model_wrappers import LPIPSWrapper, CLIPWrapper
from utils import (
    get_current_pair_in_memory,
    mark_issues,
    encode_image_to_base64, update_last_processed
)
from commit_tracker import get_next_commit_pair


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
        pair_data = get_next_commit_pair()
        if not pair_data:
            print("baseline have less than 2 commits., so aborting comparison")
            return

        prev = pair_data.get("prev_commit")
        curr = pair_data.get("curr_commit")

        # Step 2: Validate image and DOM data
        curr_data = pair_data.get("curr")
        prev_data = pair_data.get("prev")

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

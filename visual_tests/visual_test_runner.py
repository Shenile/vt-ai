from datetime import datetime
from model_wrappers import LPIPSWrapper, CLIPWrapper
from utils import (
    get_current_pair_in_memory,
    mark_issues,
    encode_image_to_base64
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

        # Step 1: Load current and previous UI data
        print("[•] Loading commit pair from cache and repo...")
        pair_data = get_current_pair_in_memory()
        if not pair_data:
            print("[✗] No valid commit pair found.")
            return None, "Could not load baseline pair."
        
        if pair_data.get("first_time"):
            print(f"[•] First-time baseline set to commit: {pair_data['curr_commit']}")
            return None, "Base Commit recorded"

        print(f"[✓] Comparing commits:\n     → Previous: {pair_data['prev_commit']}\n     → Current : {pair_data['curr_commit']}")

        # Step 2: Initialize models
        print("[•] Loading LPIPS and CLIP models...")
        lpips = LPIPSWrapper()
        clip = CLIPWrapper()
        print("[✓] Models initialized.")

        # Step 3: Run visual marking
        print("[•] Running visual comparison...")
        result = mark_issues(pair_data["curr"], pair_data["prev"], lpips, clip)
        print("[✓] Visual comparison completed.")

        # Step 4: Encode main diff images
        print("[•] Encoding main diff images to base64...")
        base64_prev = encode_image_to_base64(result["highlighted_prev"])
        base64_curr = encode_image_to_base64(result["highlighted_curr"])
        print("[✓] Main images encoded.")

        # Step 5: Prepare segmented UI crops
        print(f"[•] Processing {len(result['segments'])} changed UI segments...")
        segments_output = []
        for i, seg in enumerate(result["segments"], start=1):
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

        # Step 6: Return structured output
        return {
            "summary": result["summary"],
            "scores": result["scores"],
            "img_prev_base64": base64_prev,
            "img_curr_base64": base64_curr,
            "segments": segments_output
        }, None

    except Exception as e:
        print(f"[✗] Visual test failed: {str(e)}")
        return None, f"Visual test failed: {str(e)}"

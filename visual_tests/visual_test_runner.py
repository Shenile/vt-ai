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
        start_time = datetime.now()

        # Step 1: Load current and previous UI data
        pair_data = get_current_pair_in_memory()
        if not pair_data:
            return None, "Could not load baseline pair."

        # Step 2: Initialize models
        lpips = LPIPSWrapper()
        clip = CLIPWrapper()

        # Step 3: Run visual marking
        result = mark_issues(pair_data["curr"], pair_data["prev"], lpips, clip)

        # Step 4: Encode main diff images
        base64_prev = encode_image_to_base64(result["highlighted_prev"])
        base64_curr = encode_image_to_base64(result["highlighted_curr"])

        # Step 5: Prepare segmented UI crops
        segments_output = []
        for seg in result["segments"]:
            segments_output.append({
                "tag": seg["tag"],
                "bbox": seg["bbox"],
                "prev_crop": encode_image_to_base64(seg["prev_crop"]),
                "curr_crop": encode_image_to_base64(seg["curr_crop"]),
            })

        end_time = datetime.now()
        print(f"[run_visual_test] Time taken: {end_time - start_time}")

        # Step 6: Return structured output
        return {
            "summary": result["summary"],
            "scores": result["scores"],
            "img_prev_base64": base64_prev,
            "img_curr_base64": base64_curr,
            "segments": segments_output
        }, None

    except Exception as e:
        return None, f"Visual test failed: {str(e)}"

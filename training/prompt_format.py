"""Prompt format for Sarvam-1 Hindi-to-JSON fine-tuning.

This format is the model's contract: training data is formatted this way,
and inference must use the identical format. Changes here require re-training.
"""

import json
from typing import Optional

INPUT_DELIMITER = "हिंदी पाठ:"
OUTPUT_DELIMITER = "संरचित JSON:"


def format_for_training(input_text: str, output_json: dict) -> str:
    """Returns the full prompt+completion string for training."""
    json_str = json.dumps(output_json, ensure_ascii=False, separators=(",", ":"))
    return (
        f"{INPUT_DELIMITER}\n"
        f"{input_text}\n\n"
        f"{OUTPUT_DELIMITER}\n"
        f"{json_str}"
    )


def format_for_inference(input_text: str) -> str:
    """Returns only the prompt portion (no JSON), ready for generation."""
    return (
        f"{INPUT_DELIMITER}\n"
        f"{input_text}\n\n"
        f"{OUTPUT_DELIMITER}\n"
    )


def split_prompt_and_completion(full_text: str) -> tuple[str, Optional[str]]:
    """Split a formatted training string into prompt and completion.

    Returns (prompt_text_including_OUTPUT_DELIMITER_newline, completion_json_str).
    Used for loss masking — the prompt portion gets label=-100.
    """
    delimiter_with_newline = f"{OUTPUT_DELIMITER}\n"
    if delimiter_with_newline not in full_text:
        return full_text, None
    prompt_part, completion_part = full_text.split(delimiter_with_newline, 1)
    return prompt_part + delimiter_with_newline, completion_part

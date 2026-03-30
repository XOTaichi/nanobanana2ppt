def build_background_restore_prompt() -> str:
    return (
        "Restore a clean slide background from this partially masked page. "
        "Treat the white blank regions as removed foreground content that must be filled in naturally. "
        "Continue the surrounding visual pattern: gradients, panel fills, border lines, rounded corners, "
        "shadows, spacing, and empty container backgrounds. Remove all remaining text, icons, arrows, charts, "
        "braces, labels, and diagram content. Keep only the background and layout containers. "
        "Do not add any new foreground objects. Output a clean background-only version of the same page."
    )


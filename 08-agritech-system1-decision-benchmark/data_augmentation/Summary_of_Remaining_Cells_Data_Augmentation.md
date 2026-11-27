# Summary of Remaining Cells in the Cleaned Notebook

I retained four cells and removed duplicate attempts, a failed run, redundant Drive-mount-only cells, and every saved output. I found no embedded API key value; I load credentials at runtime from Colab Secrets.

1. **Project scope and safe execution (Markdown).** I explain the notebook’s purpose, clarify that the full-run cell clears its selected output range while the backfill cell fills only missing prediction cells, and note that the original individual image files are required for rerunning inference.
2. **Setup, Drive and workbook/image verification (Code).** I mount Google Drive when needed, verify the project directory, workbook, worksheet, expected headers, ten image records, and securely loaded Gemini/OpenRouter secrets without displaying key values.
3. **Full 10-image benchmark runner (Code).** I run isolated Boolean, Choice, Score, and Spatial requests against Gemini Decision 1 and Jev for a configurable image range, parse structured predictions and confidence, and checkpoint results in the audit workbook. This cell clears old outputs in its selected image range before making new calls, so I use it only when I intend to rerun that range.
4. **Missing-output backfill runner (Code).** I use a resized-image, retry-capable runner for images 7–10 that checks existing result cells and only requests missing model/primitive outputs, then saves progress after each image.

I removed the failed duplicate runner (which stopped because its Drive workbook path did not exist), the alternate API-key-3 implementation, a standalone Drive-mount cell, and an incomplete mount-only setup cell. I cleared all prior outputs and execution counts so no stale errors or response payloads remain in the published notebook.

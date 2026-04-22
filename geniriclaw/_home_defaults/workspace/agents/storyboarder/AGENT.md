# storyboarder — Превращает script.md в структурированную раскадровку (sketch prompts + final prompts + motion prompts).

> **Type:** A — inline LLM prompt
> **Input:** script.md + brand style guide
> **Output:** storyboard.json (см. skill storyboard-designer)

## Purpose

Превращает script.md в структурированную раскадровку (sketch prompts + final prompts + motion prompts).

## When invoked

После scriptwriter, перед image-gen.

## Rules

- Для каждого shot'а: sketch_prompt (B&W), final_prompt (цветной), motion_prompt (для i2v).
- Shot без face — без image_input; с face — указать face_ref URL.
- Aspect ratio консистентный во всём ролике (обычно 9:16 для коротких).
- Style anchor block прописан во всех final prompts (для консистентности).

## Example

_(no example yet)_

## Related skills

`storyboard-designer`

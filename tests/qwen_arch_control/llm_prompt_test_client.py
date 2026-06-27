class MockDatasetPromptLLMClient:
    def generate_json(self, system_prompt, user_payload):
        room = user_payload.get("room_type") or "room"
        slots = user_payload.get("furniture_slots") or []
        items = []
        for slot in slots:
            count = slot.get("count") or 1
            cat = slot.get("category")
            if cat:
                items.append(f"{count} {cat}")
        item_text = ", ".join(items) or "the required furniture"
        visible = (user_payload.get("architecture_summary") or {}).get("visible_architecture_elements") or {}
        arch = "Use the architecture condition image for the room floor boundary"
        claims = ["room_floor_boundary"]
        if visible.get("door"):
            arch += " and visible doors"
            claims.append("visible_door")
        if visible.get("window"):
            arch += " and visible windows"
            claims.append("visible_window")
        prompt = (
            f"Context_Control. Create a top-down fixed-palette semantic {room} layout. "
            f"Include {item_text}. Keep furniture inside the room floor region and avoid blocking openings. "
            f"{arch}. Arrange the furniture for clear indoor function while using only allowed semantic categories."
        )
        return {
            "compiled_text_prompt": prompt,
            "used_slot_ids": [slot.get("slot_id") for slot in slots if slot.get("slot_id")],
            "used_constraint_ids": [],
            "omitted_constraint_ids": [c.get("constraint_id") for c in user_payload.get("goal_constraints", []) if c.get("constraint_id")],
            "architecture_claims": claims,
            "notes": [],
        }

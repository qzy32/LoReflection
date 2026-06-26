
from loreflection.qwen_arch_control.prompt_labels.goal_aligned_llm_request_builder import build_goal_aligned_llm_request


def test_goal_aligned_request_strips_geometry():
    scene={"sample_id":"s1","room_type":"bedroom","furniture_counts":{"double_bed":1},"architecture_facts":{"metric_transform_exists":True}}
    goal={"room_type":"bedroom","center_m":[1,2],"furniture_slots":[{"category":"double_bed","bbox_px":[1,2,3,4]}]}
    req=build_goal_aligned_llm_request(scene, goal, [], {"main_anchors":["double_bed"]})
    goal_text=str(req["user"]["goal_lostate_rich_without_geometry"])
    assert "double_bed" in goal_text
    assert "center_m" not in goal_text
    assert "bbox_px" not in goal_text
    assert "center_m" in req["user"]["forbidden_terms"]

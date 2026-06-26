
from loreflection.qwen_arch_control.prompt_labels.placement_order_planner import plan_placement_order


def test_placement_order_has_anchor_and_no_geometry_terms():
    out=plan_placement_order({"primary_anchor":"double_bed","furniture_counts":{"double_bed":1,"nightstand":2,"wardrobe":1}}, {}, [])
    text=str(out)
    assert out["main_anchors"] == ["double_bed"]
    for bad in ["center_m","bbox_px","meter","cm"]:
        assert bad not in text

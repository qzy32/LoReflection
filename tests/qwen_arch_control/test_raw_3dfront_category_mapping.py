from loreflection.qwen_arch_control.raw_3dfront_adapter import (
    map_3dfuture_category_to_semlayoutdiff,
    normalize_room_type,
)


def mapper(raw_category: str, *, raw_title: str = "", super_category: str = ""):
    return map_3dfuture_category_to_semlayoutdiff(
        raw_category, raw_title=raw_title, super_category=super_category
    )


def test_footstool_not_double_bed():
    assert mapper("Footstool / Sofastool / Bed End Stool / Stool").category == "stool"


def test_bed_end_stool_not_double_bed():
    result = mapper("Bed End Stool")
    assert result.category == "stool"
    assert result.category != "double_bed"


def test_nightstand_not_desk():
    assert mapper("Nightstand").category == "nightstand"


def test_wardrobe_not_desk():
    assert mapper("Wardrobe").category == "wardrobe"


def test_bookcase_not_desk():
    assert mapper("Bookcase / jewelry Armoire").category == "bookshelf"


def test_shelf_not_desk():
    assert mapper("Shelf").category == "shelf"


def test_drawer_chest_not_desk():
    assert mapper("Drawer Chest / Corner cabinet").category == "cabinet"


def test_double_bed_requires_explicit_bed_type():
    assert mapper("Double Bed").category == "double_bed"
    assert mapper("Bed End Stool").category != "double_bed"


def test_super_category_does_not_trigger_desk():
    result = mapper("Nightstand", super_category="Cabinet/Shelf/Desk")
    assert result.category == "nightstand"


def test_unknown_does_not_guess_desk_or_bed():
    result = mapper("Unknown Furniture", super_category="Cabinet/Shelf/Desk")
    assert result.category is None


def test_title_fallback_does_not_use_super_category():
    result = mapper("", raw_title="sofa/ottoman", super_category="Bed")
    assert result.category == "stool"


def test_room_type_gate():
    assert normalize_room_type("MasterBedroom") == "bedroom"
    assert normalize_room_type("SecondBedroom") == "bedroom"
    assert normalize_room_type("Bedroom") == "bedroom"
    assert normalize_room_type("LivingRoom") == "livingroom"
    assert normalize_room_type("DiningRoom") == "diningroom"
    assert normalize_room_type("Kitchen") is None
    assert normalize_room_type("Bathroom") is None
    assert normalize_room_type("LivingDiningRoom") is None

# LLM Prompt Examples

These examples compare the previous template functional prompt with the Qwen2.5-7B generated functional prompt.

## 1. 36c96aa6-a318-4212-aecc-22a206d7b217_room_00

- room_type: `livingroom`
- furniture_counts: `{"coffee_table": 1, "dining_chair": 4, "dining_table": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional livingroom semantic layout with 1 coffee table, 4 dining chairs, and 1 dining table. Use the dining table as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Position 1 coffee table close to the dining table and place 4 dining chairs around the dining table. Make sure there is no overlap and that all items are within the room. Use the architectural details to guide the placement while ensuring there is enough space near the door.

## 2. 36c96aa6-a318-4212-aecc-22a206d7b217_room_01

- room_type: `elderlyroom`
- furniture_counts: `{"desk": 2}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional elderlyroom semantic layout with 2 desks. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 2 desks within the room, maintaining the requirement that they remain inside the room boundaries and avoid overlapping each other. Adhere to the specific color palette designated for an elderlyroom.

## 3. 36c96aa6-a318-4212-aecc-22a206d7b217_room_02

- room_type: `study`
- furniture_counts: `{"armchair": 1, "desk": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional study semantic layout with 1 armchair, and 1 desk. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Position 1 armchair and 1 desk in the study. Make sure the desk is used as the primary anchor. Avoid any overlapping and adhere to the specified color palette.

## 4. 36c96aa6-a318-4212-aecc-22a206d7b217_room_05

- room_type: `bedroom`
- furniture_counts: `{"desk": 2, "pendant_lamp": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 2 desks, and 1 pendant lamp. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange two desks and one pendant lamp within the bedroom space, making sure there is no overlap and that all items remain within the room boundaries.

## 5. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00

- room_type: `bedroom`
- furniture_counts: `{"ceiling_lamp": 1, "desk": 1, "kids_bed": 1, "lazy_sofa": 1, "single_bed": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Use the single bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the following furniture in the bedroom: 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Avoid overlapping and follow the architectural constraints provided.

## 6. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01

- room_type: `bedroom`
- furniture_counts: `{"ceiling_lamp": 1, "desk": 2, "kids_bed": 1, "lounge_chair": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 1 ceiling lamp, 2 desks, 1 kids bed, and 1 lounge chair. Use the kids bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 1 ceiling lamp, 2 desks, 1 kids bed, and 1 lounge chair within the bedroom. Avoid overlapping and ensure all furniture is positioned inside the room. Use the architectural conditions to guide placement.

## 7. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_02

- room_type: `courtyard`
- furniture_counts: `{"corner_side_table": 1, "desk": 1, "lounge_chair": 2, "pendant_lamp": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional courtyard semantic layout with 1 corner side table, 1 desk, 2 lounge chairs, and 1 pendant lamp. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the space such that there is 1 corner side table positioned against a wall, 1 desk centrally located, 2 lounge chairs surrounding the desk, and 1 pendant lamp hanging above the desk to create a functional and inviting environment.

## 8. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05

- room_type: `livingroom`
- furniture_counts: `{"ceiling_lamp": 2, "coffee_table": 1, "desk": 1, "lazy_sofa": 1, "multi_seat_sofa": 1, "table": 1, "tv_stand": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional livingroom semantic layout with 2 ceiling lamps, 1 coffee table, 1 desk, 1 lazy sofa, 1 multi seat sofa, 1 table, and 1 tv stand. Use the multi seat sofa as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the following furniture in the living room: 2 ceiling lamps, 1 coffee table, 1 desk, 1 lazy sofa, 1 multi seat sofa, 1 table, and 1 tv stand. The tv stand should be placed near the multi seat sofa, and the coffee table should also be near the multi seat sofa. Ensure all items are within the room boundaries, avoid overlapping, use the exact palette, and maintain clearance around doors and windows.

## 9. faf62fbc-739a-40da-aac3-12b6807ee7e3_room_08

- room_type: `bedroom`
- furniture_counts: `{"ceiling_lamp": 1, "desk": 3, "double_bed": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 1 ceiling lamp, 3 desks, and 1 double bed. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 1 ceiling lamp and 3 desks in relation to a double bed within the bedroom. Adhere to the constraints of avoiding overlap and using the architectural details provided.

## 10. 23a5fa77-0aa5-45f4-8399-3265005b1def_room_00

- room_type: `bedroom`
- furniture_counts: `{"desk": 3, "double_bed": 1, "pendant_lamp": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 3 desks, 1 double bed, and 1 pendant lamp. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 3 desks, 1 double bed, and 1 pendant lamp within the bedroom. Make sure the items do not overlap and comply with the room's architectural and design specifications.

## 11. 23a5fa77-0aa5-45f4-8399-3265005b1def_room_05

- room_type: `livingroom`
- furniture_counts: `{"coffee_table": 1, "corner_side_table": 1, "dining_chair": 6, "dining_table": 1, "double_bed": 2, "loveseat_sofa": 1, "pendant_lamp": 2, "tv_stand": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional livingroom semantic layout with 1 coffee table, 1 corner side table, 6 dining chairs, 1 dining table, 2 double beds, 1 loveseat sofa, 2 pendant lamps, and 1 tv stand. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Ensure 1 coffee table is placed near the double bed. Position 1 corner side table in a corner. Arrange 6 dining chairs around 1 dining table. Place 2 double beds opposite each other. Position 1 loveseat sofa against the wall. Hang 2 pendant lamps above the dining table. Set up 1 tv stand next to one of the double beds. Avoid overlapping furniture and ensure all items are inside the room.

## 12. 23a5fa77-0aa5-45f4-8399-3265005b1def_room_07

- room_type: `kidsroom`
- furniture_counts: `{"ceiling_lamp": 1, "desk": 2, "dining_chair": 1, "double_bed": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional kidsroom semantic layout with 1 ceiling lamp, 2 desks, 1 dining chair, and 1 double bed. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the following furniture in the kidsroom: 1 ceiling lamp, 2 desks, 1 dining chair, and 1 double bed. The dining chair should be positioned near the double bed. Ensure that all items are within the room, do not overlap, and use the provided architectural details for placement.

## 13. 5399de83-ec0c-4ef3-a97e-9bef301222d5_room_04

- room_type: `livingroom`
- furniture_counts: `{"ceiling_lamp": 3, "coffee_table": 1, "corner_side_table": 2, "desk": 1, "dining_chair": 4, "dining_table": 1, "lounge_chair": 1, "pendant_lamp": 2, "tv_stand": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional livingroom semantic layout with 3 ceiling lamps, 1 coffee table, 2 corner side tables, 1 desk, 4 dining chairs, 1 dining table, 1 lounge chair, 2 pendant lamps, and 1 tv stand. Use the dining table as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the following items in the living room: 3 ceiling lamps, 1 coffee table, 2 corner side tables, 1 desk, 4 dining chairs, 1 dining table, 1 lounge chair, 2 pendant lamps, and 1 TV stand. The TV stand should be positioned near the dining table, and the dining chairs should also be placed near the dining table. Additionally, position a coffee table near the dining table.

## 14. 5399de83-ec0c-4ef3-a97e-9bef301222d5_room_05

- room_type: `bedroom`
- furniture_counts: `{"corner_side_table": 2, "double_bed": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 2 corner side tables, and 1 double bed. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Position 2 corner side tables and 1 double bed within the bedroom space, adhering to the given constraints of no overlap, staying inside the room, using the correct color palette, and ensuring there is free space around the door. No other furniture should be present.

## 15. 5399de83-ec0c-4ef3-a97e-9bef301222d5_room_06

- room_type: `bedroom`
- furniture_counts: `{"corner_side_table": 1, "desk": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 1 corner side table, and 1 desk. Use the desk as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 1 corner side table and 1 desk in the bedroom. Make sure there is no overlap between the furniture and they are positioned inside the room. Follow the given color palette and ensure there is enough space around the door.

## 16. 6379e703-a2fb-4d36-a417-30e0357a31ad_room_02

- room_type: `bedroom`
- furniture_counts: `{"desk": 1, "double_bed": 1, "pendant_lamp": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 1 desk, 1 double bed, and 1 pendant lamp. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 1 desk, 1 double bed, and 1 pendant lamp within the bedroom space. Make sure there is no overlap between the furniture and that the colors match the architecture condition image. The furniture should be placed in a way that adheres to the room's design and avoids blocking the door clearance.

## 17. 6379e703-a2fb-4d36-a417-30e0357a31ad_room_03

- room_type: `livingroom`
- furniture_counts: `{"armchair": 1, "coffee_table": 1, "console_table": 1, "corner_side_table": 1, "desk": 1, "dining_chair": 4, "dining_table": 1, "multi_seat_sofa": 1, "pendant_lamp": 2}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional livingroom semantic layout with 1 armchair, 1 coffee table, 1 console table, 1 corner side table, 1 desk, 4 dining chairs, 1 dining table, 1 multi seat sofa, and 2 pendant lamps. Use the multi seat sofa as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the following furniture in the living room: 1 armchair, 1 coffee table near the multi-seat sofa, 1 console table, 1 corner side table, 1 desk, 4 dining chairs near the multi-seat sofa, 1 dining table, and 2 pendant lamps. Ensure that the furniture does not overlap and adheres to the architectural constraints of the room.

## 18. 6379e703-a2fb-4d36-a417-30e0357a31ad_room_05

- room_type: `bedroom`
- furniture_counts: `{"desk": 3, "double_bed": 1, "pendant_lamp": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 3 desks, 1 double bed, and 1 pendant lamp. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange 3 desks, 1 double bed, and 1 pendant lamp within the bedroom while adhering to the constraints of avoiding overlap and staying inside the room. Ensure there is enough space near the window for the pendant lamp.

## 19. 3f2629fe-a957-4e83-893a-28d476318740_room_00

- room_type: `bedroom`
- furniture_counts: `{"desk": 3, "double_bed": 1, "pendant_lamp": 1, "tv_stand": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional bedroom semantic layout with 3 desks, 1 double bed, 1 pendant lamp, and 1 tv stand. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Arrange the following furniture in the bedroom: 3 desks, 1 double bed, 1 pendant lamp, and 1 tv stand. The tv stand should be positioned near the double bed. Make sure there is no overlap and maintain appropriate spacing around windows.

## 20. 3f2629fe-a957-4e83-893a-28d476318740_room_02

- room_type: `livingroom`
- furniture_counts: `{"coffee_table": 2, "dining_chair": 4, "dining_table": 1, "double_bed": 1, "loveseat_sofa": 1, "pendant_lamp": 2, "tv_stand": 1}`
- audit_status: `pass`

**template_functional**

Context_Control. Design a functional livingroom semantic layout with 2 coffee tables, 4 dining chairs, 1 dining table, 1 double bed, 1 loveseat sofa, 2 pendant lamps, and 1 tv stand. Use the double bed as the main anchor when appropriate, keep related support furniture nearby, preserve clear circulation around doors and windows, and use only frozen semantic categories.

**prompt_llm_functional**

Context_Control. Ensure there are 2 coffee tables positioned near the double bed. Arrange 4 dining chairs around the dining table. Place a tv stand close to the double bed. Include a loveseat sofa and position 2 pendant lamps in the room. Follow the given constraints for the livingroom.

# Manual Review Candidates

## 36c96aa6-a318-4212-aecc-22a206d7b217_room_01

- room_type: `elderlyroom`
- reason: `room_type=elderlyroom`
- furniture_counts: `{"desk": 2}`

Context_Control. Arrange 2 desks within the room, maintaining the requirement that they remain inside the room boundaries and avoid overlapping each other. Adhere to the specific color palette designated for an elderlyroom.

## 36c96aa6-a318-4212-aecc-22a206d7b217_room_05

- room_type: `bedroom`
- reason: `bedroom with sparse desk-heavy furniture`
- furniture_counts: `{"desk": 2, "pendant_lamp": 1}`

Context_Control. Arrange two desks and one pendant lamp within the bedroom space, making sure there is no overlap and that all items remain within the room boundaries.

## faf62fbc-739a-40da-aac3-12b6807ee7e3_room_00

- room_type: `bedroom`
- reason: `mixed bedroom furniture types`
- furniture_counts: `{"ceiling_lamp": 1, "desk": 1, "kids_bed": 1, "lazy_sofa": 1, "single_bed": 1}`

Context_Control. Arrange the following furniture in the bedroom: 1 ceiling lamp, 1 desk, 1 kids bed, 1 lazy sofa, and 1 single bed. Avoid overlapping and follow the architectural constraints provided.

## faf62fbc-739a-40da-aac3-12b6807ee7e3_room_01

- room_type: `bedroom`
- reason: `mixed bedroom furniture types`
- furniture_counts: `{"ceiling_lamp": 1, "desk": 2, "kids_bed": 1, "lounge_chair": 1}`

Context_Control. Arrange 1 ceiling lamp, 2 desks, 1 kids bed, and 1 lounge chair within the bedroom. Avoid overlapping and ensure all furniture is positioned inside the room. Use the architectural conditions to guide placement.

## faf62fbc-739a-40da-aac3-12b6807ee7e3_room_05

- room_type: `livingroom`
- reason: `unusual dense furniture combination`
- furniture_counts: `{"ceiling_lamp": 2, "coffee_table": 1, "desk": 1, "lazy_sofa": 1, "multi_seat_sofa": 1, "table": 1, "tv_stand": 1}`

Context_Control. Arrange the following furniture in the living room: 2 ceiling lamps, 1 coffee table, 1 desk, 1 lazy sofa, 1 multi seat sofa, 1 table, and 1 tv stand. The tv stand should be placed near the multi seat sofa, and the coffee table should also be near the multi seat sofa. Ensure all items are within the room boundaries, avoid overlapping, use the exact palette, and maintain clearance around doors and windows.

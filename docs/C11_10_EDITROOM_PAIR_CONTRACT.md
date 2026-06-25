# C11.10 EditRoom Pair Contract

```json
{
  "checkout": "/wuqingyaoa800/chengjiajia_datas/EditRoom",
  "exists": true,
  "dataset": "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset",
  "dataset_exists": true,
  "pkl_counts_by_split": {
    "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/train_dataset": 93497,
    "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/test_dataset": 3918
  },
  "file_format": "Python pickle Room objects; loaded with dependency-agnostic SafeUnpickler for field inspection.",
  "pair_linkage": "Edited Room.original_id points to the before/base Room uid; object model_uid/model_jid are available for before/after matching.",
  "bbox_pose_format": "Objects expose position[3], size[3], z_angle, rotation[4], scale, model_uid, model_jid, and model_info.category/super_category.",
  "relation_dicts": "Present on Room as relation_dicts; not used for pixel rendering in this converter.",
  "samples": [
    {
      "path": "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/train_dataset/103d8063-fb69-4029-a3e5-a3ded8ca728d_SecondBedroom-68353_pose-1-4_6-opposite.pkl",
      "uid": "103d8063-fb69-4029-a3e5-a3ded8ca728d_SecondBedroom-68353_pose-1-4_6-opposite",
      "original_id": "103d8063-fb69-4029-a3e5-a3ded8ca728d_SecondBedroom-68353_pose-1-4_6",
      "scene_type": "secondbedroom",
      "command": "move object towards the ***left*** direction for 1.20 meters: [JID]685df4a4-cd69-4f0b-82f5-675bd0738881[/JID]\nobviously move object towards the ***left*** direction :[JID]685df4a4-cd69-4f0b-82f5-675bd0738881[/JID]",
      "object_count": 5,
      "first_object_attrs": [
        "_label",
        "model_info",
        "model_jid",
        "model_uid",
        "openshape_vitg14_features",
        "path_to_models",
        "position",
        "rotation",
        "scale",
        "size",
        "z_angle"
      ],
      "first_model_info": {
        "super_category": "bed",
        "category": "king-size bed",
        "style": "Japanese",
        "theme": "Smooth Net",
        "material": "Leather"
      },
      "first_position": [
        1.1618810784803613,
        0.0096,
        -0.002067557048621654
      ],
      "first_size": [
        1.20715,
        0.40524772,
        1.1933299999999998
      ],
      "first_z_angle": 1.5707872225948964
    },
    {
      "path": "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/train_dataset/e02e2373-1bb0-4d67-819b-8c471edc78a3_SecondBedroom-5355_add-4_10.pkl",
      "uid": "e02e2373-1bb0-4d67-819b-8c471edc78a3_SecondBedroom-5355_add-4_10",
      "original_id": "e02e2373-1bb0-4d67-819b-8c471edc78a3_SecondBedroom-5355_remove-4_10",
      "scene_type": "secondbedroom",
      "command": "add object: one of [JID]6fff9bdc-20b4-40e6-a37d-ca372cddb1e4[/JID]; location: ***left of*** [JID]c4b7ea85-4dfe-4588-93a0-7a7b6eefeaae[/JID]",
      "object_count": 5,
      "first_object_attrs": [
        "_label",
        "model_info",
        "model_jid",
        "model_uid",
        "openshape_vitg14_features",
        "path_to_models",
        "position",
        "rotation",
        "scale",
        "size",
        "z_angle"
      ],
      "first_model_info": {
        "super_category": "cabinet/shelf/desk",
        "category": "wardrobe",
        "style": "Vintage/Retro",
        "theme": "Smooth Net",
        "material": "Wood"
      },
      "first_position": [
        -2.645861035141254,
        0.0,
        -1.916407649333414
      ],
      "first_size": [
        0.368827,
        1.137215,
        0.30735599999999996
      ],
      "first_z_angle": -3.141592653589793
    },
    {
      "path": "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/train_dataset/d2832564-46fd-4bed-a477-02c848c8a60f_MasterBedroom-2723_replace-1_2.pkl",
      "uid": "d2832564-46fd-4bed-a477-02c848c8a60f_MasterBedroom-2723_replace-1_2",
      "original_id": "d2832564-46fd-4bed-a477-02c848c8a60f_MasterBedroom-2723",
      "scene_type": "masterbedroom",
      "command": "replace source with target : [Source] [JID]69c544a9-6dc0-4ce3-a6b3-e987a6f37a7a[/JID]; [Target] [JID]45ee620d-f213-4f6a-a1c9-89f1a738c8fa[/JID]",
      "object_count": 4,
      "first_object_attrs": [
        "_label",
        "model_info",
        "model_jid",
        "model_uid",
        "openshape_vitg14_features",
        "path_to_models",
        "position",
        "rotation",
        "scale",
        "size",
        "z_angle"
      ],
      "first_model_info": {
        "super_category": "bed",
        "category": "king-size bed",
        "style": "Mediterranean",
        "theme": "Striped Grid",
        "material": "Rough Cloth"
      },
      "first_position": [
        -0.8228119543202249,
        0.0,
        -2.0678777021592825
      ],
      "first_size": [
        1.00857,
        0.406518665,
        1.05972
      ],
      "first_z_angle": 0.0
    },
    {
      "path": "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/train_dataset/0e49912b-d9f3-4f1a-93e2-0245e6fb67c1_SecondBedroom-10798_pose-0-5_4-opposite.pkl",
      "uid": "0e49912b-d9f3-4f1a-93e2-0245e6fb67c1_SecondBedroom-10798_pose-0-5_4-opposite",
      "original_id": "0e49912b-d9f3-4f1a-93e2-0245e6fb67c1_SecondBedroom-10798_pose-0-5_4",
      "scene_type": "secondbedroom",
      "command": "shrink object by 0.8 X :  [JID]28db412b-c62b-4c83-ae16-c0ce86d93491[/JID]; location: ***left of*** [JID]19e1a64d-a87f-4d82-8834-5c34b889a059[/JID] \nshrink object : [JID]28db412b-c62b-4c83-ae16-c0ce86d93491[/JID]; location: ***left of*** [JID]19e1a64d-a87f-4d82-8834-5c34b889a059[/JID]",
      "object_count": 6,
      "first_object_attrs": [
        "_label",
        "model_info",
        "model_jid",
        "model_uid",
        "openshape_vitg14_features",
        "path_to_models",
        "position",
        "rotation",
        "scale",
        "size",
        "z_angle"
      ],
      "first_model_info": {
        "super_category": "table",
        "category": "desk",
        "style": "Mediterranean",
        "theme": null,
        "material": null
      },
      "first_position": [
        0.35896177593156575,
        0.0,
        -3.782003180544271
      ],
      "first_size": [
        0.46664493599999984,
        0.749661996,
        0.22741634400000002
      ],
      "first_z_angle": -1.5707872225948964
    },
    {
      "path": "/wuqingyaoa800/chengjiajia_datas/EditRoom/datasets/editroom_dataset/threed_front_bedroom/train_dataset/3d746247-8cd0-4b3c-8186-2ee990b66efa_SecondBedroom-31776.pkl",
      "uid": "3d746247-8cd0-4b3c-8186-2ee990b66efa_SecondBedroom-31776",
      "original_id": "",
      "scene_type": "secondbedroom",
      "command": "",
      "object_count": 5,
      "first_object_attrs": [
        "_label",
        "model_info",
        "model_jid",
        "model_uid",
        "openshape_vitg14_features",
        "path_to_models",
        "position",
        "rotation",
        "scale",
        "size",
        "z_angle"
      ],
      "first_model_info": {
        "super_category": "bed",
        "category": "king-size bed",
        "style": "American Country",
        "theme": "Chinese Pattern",
        "material": "Rough Cloth"
      },
      "first_position": [
        0.27682531915835396,
        0.0,
        8.370495959267739
      ],
      "first_size": [
        1.135233,
        0.7847504999999999,
        1.091187
      ],
      "first_z_angle": 1.5707872225948964
    }
  ]
}
```

import bpy 

supportPartner = [
    {"name": "Kagi Vision | Armors Assets", "link": "https://blendermarket.com/products/kagi-vision-armor-pack/?ref=159", "icon":"OUTLINER_OB_ARMATURE"},
    {"name": "Wolf's Market | Medieval", "link": "https://blendermarket.com/creators/wolfs-thingsandstuff?ref=159", "icon":"ASSET_MANAGER"},

    {"name": "AlbertoFX", "link": "https://blendermarket.com/creators/albertofx/?ref=159", "icon":"SHADERFX"},
    {"name": "Automotive | by Damian Mathew", "link": "https://blendermarket.com/creators/damian-mathew/?ref=159", "icon":"AUTO"},

    {"name": "HDRi Maker Studio", "link": "https://blendermarket.com/products/hdri-maker/?ref=159", "icon":"MAT_SPHERE_SKY"},
    {"name": "Extreme PBR Nexus", "link": "https://blendermarket.com/products/extreme-pbr-addon-for-blender-279-2/?ref=159", "icon":"MATERIAL"},

    {"name": "Sanctus | Procedural Materials", "link": "https://blendermarket.com/creators/sanctus?ref=159", "icon":"NODETREE"},
    {"name": "Human Generator", "link": "https://blendermarket.com/products/humgen3d/?ref=159", "icon":"ARMATURE_DATA"},

    {"name": "Folds Modifier by multlabs", "link": "https://blendermarket.com/creators/multlabs?ref=159", "icon":"MATCLOTH"},
    {"name": "Xane Graphics", "link": "https://blendermarket.com/creators/xane-graphics/?ref=159", "icon":"MOD_CLOTH"},

    {"name": "Pattern Designer | Russel Studios", "link": "https://blendermarket.com/creators/russel-studios?ref=159", "icon":"OUTLINER_OB_LATTICE"},
    {"name": "Tracegenius Pro - Image To 3D Tracer", "link": "https://blendermarket.com/products/tracegenius-pro/?ref=159", "icon":"EXPORT"},

    {"name": "Trimflow | by shapeshift", "link": "https://blendermarket.com/creators/shapeshift?ref=159", "icon":"CURVE_PATH"},
    {"name": "Blob Fusion & more", "link": "https://blendermarket.com/creators/joseconseco?ref=159", "icon":"CONSTRAINT"},

    {"name": "Zen UV", "link": "https://blendermarket.com/creators/sergey-tyapkin/?ref=159", "icon":"UV"},
    {"name": "Voxel Heat Diffuse Skinning", "link": "https://blendermarket.com/creators/meshonline?ref=159", "icon":"MOD_VERTEX_WEIGHT"},

    {"name": "Addons by Chipp Walters", "link": "https://blendermarket.com/creators/altuit?ref=159", "icon":"SHADERFX"},
    {"name": "K-Cycles", "link": "https://blendermarket.com/products/k-cycles?ref=159", "icon":"RESTRICT_RENDER_OFF"},

    {"name": "Poly Haven Assets", "link": "https://blendermarket.com/creators/polyhaven?ref=159", "icon":"ASSET_MANAGER"},
    {"name": "Scenes | by Lost Kitten", "link": "https://blendermarket.com/creators/thelostkitten/?ref=159", "icon":"SCENE_DATA"},

    {"name": "Weight Painting Suite Tools", "link": "https://blendermarket.com/products/weight-painting-suite-tools", "icon":"MOD_VERTEX_WEIGHT"},
    {"name": "Panel Stitcher | Witting Graphics", "link": "https://blendermarket.com/creators/witting-graphics/?ref=159", "icon":"IPO_LINEAR"},

    {"name": "Auto Rig Pro", "link": "https://blendermarket.com/products/auto-rig-pro/?ref=159", "icon":"OUTLINER_OB_ARMATURE"},

    {"name": "Simply Addons", "link": "https://blendermarket.com/creators/vjaceslavt/?ref=159", "icon":"URL"}
]
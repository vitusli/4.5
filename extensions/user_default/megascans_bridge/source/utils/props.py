import re

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from .enums import (
    enum_assets_categories,
    enum_assets_subcategories,
    enum_atlases_categories,
    enum_atlases_subcategories,
    enum_brushes_categories,
    enum_decals_categories,
    enum_decals_subcategories,
    enum_imperfections_categories,
    enum_imperfections_subcategories,
    enum_plants_categories,
    enum_plants_subcategories,
    enum_surfaces_categories,
    enum_surfaces_subcategories,
)
from .preview import (
    get_assets,
    get_atlases,
    get_brushes,
    get_decals,
    get_displacements,
    get_imperfections,
    get_plants,
    get_surfaces,
)


class MBRIDGE_PG_assets(PropertyGroup):
    def get_assets(self, context):
        assets = get_assets()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [asset for asset in assets.get("ALL", []) if re.search(search, asset.searchStr, re.IGNORECASE)]

        # Return based on category selection
        return assets.get("ALL") if self.category == "ALL" else assets.get(self.category, {}).get(self.subcategory)

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="3D assets category",
        items=enum_assets_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="3D assets subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None]
        + [(name, name.title(), "") for name in enum_assets_subcategories(self, context).get(self.category, [])],
    )

    import_lods: BoolProperty(
        name="Import LODs",
        description="Import the lods selected in the preferences",
        default=False,
    )

    create_lod_group: BoolProperty(
        name="Create LOD Group",
        description="Create the lod group",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class MBRIDGE_PG_plants(PropertyGroup):
    def get_assets(self, context):
        plants = get_plants()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [plant for plant in plants.get("ALL", []) if re.search(search, plant.searchStr, re.IGNORECASE)]

        # Return based on category selection
        return plants.get("ALL") if self.category == "ALL" else plants.get(self.category, {}).get(self.subcategory)

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="3D plants category",
        items=enum_plants_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="3D plants subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None]
        + [(name, name.title(), "") for name in enum_plants_subcategories(self, context).get(self.category, [])],
    )

    import_lods: BoolProperty(
        name="Import LODs",
        description="Import the lods selected in the preferences",
        default=False,
    )

    create_lod_group: BoolProperty(
        name="Create LOD Group",
        description="Create the lod group",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class MBRIDGE_PG_surfaces(PropertyGroup):
    def get_assets(self, context):
        surfaces = get_surfaces()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [
                surface for surface in surfaces.get("ALL", []) if re.search(search, surface.searchStr, re.IGNORECASE)
            ]

        # Return based on category selection
        return surfaces.get("ALL") if self.category == "ALL" else surfaces.get(self.category, {}).get(self.subcategory)

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="Surfaces category",
        items=enum_surfaces_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="Surfaces subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None]
        + [(name, name.title(), "") for name in enum_surfaces_subcategories(self, context).get(self.category, [])],
    )

    apply_material: BoolProperty(
        name="Apply Material",
        description="Apply the material to the first slot of the selected objects",
        default=True,
    )

    mark_asset: BoolProperty(
        name="Mark as Asset",
        description="Mark the surface material as an asset",
        default=False,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class MBRIDGE_PG_decals(PropertyGroup):
    def get_assets(self, context):
        decals = get_decals()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [decal for decal in decals.get("ALL", []) if re.search(search, decal.searchStr, re.IGNORECASE)]

        # Return based on category selection
        return decals.get("ALL") if self.category == "ALL" else decals.get(self.category, {}).get(self.subcategory)

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="Decals category",
        items=enum_decals_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="Decals subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None]
        + [(name, name.title(), "") for name in enum_decals_subcategories(self, context).get(self.category, [])],
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class MBRIDGE_PG_atlases(PropertyGroup):
    def get_assets(self, context):
        atlases = get_atlases()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [atlas for atlas in atlases.get("ALL", []) if re.search(search, atlas.searchStr, re.IGNORECASE)]

        # Return based on category selection
        return atlases.get("ALL") if self.category == "ALL" else atlases.get(self.category, {}).get(self.subcategory)

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="Atlases category",
        items=enum_atlases_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="Atlases subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None]
        + [(name, name.title(), "") for name in enum_atlases_subcategories(self, context).get(self.category, [])],
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class MBRIDGE_PG_imperfections(PropertyGroup):
    def get_assets(self, context):
        imperfections = get_imperfections()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [
                imperfection
                for imperfection in imperfections.get("ALL", [])
                if re.search(search, imperfection.searchStr, re.IGNORECASE)
            ]

        # Return based on category selection
        return (
            imperfections.get("ALL")
            if self.category == "ALL"
            else imperfections.get(self.category, {}).get(self.subcategory)
        )

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="Imperfections category",
        items=enum_imperfections_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="Imperfections subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None]
        + [(name, name.title(), "") for name in enum_imperfections_subcategories(self, context).get(self.category, [])],
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class MBRIDGE_PG_displacements(PropertyGroup):
    def get_assets(self, context):
        displacements = get_displacements()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [
                displacement
                for displacement in displacements
                if re.search(search, displacement.searchStr, re.IGNORECASE)
            ]

        return displacements

    def draw(self, context, layout):
        pass


class MBRIDGE_PG_brushes(PropertyGroup):
    def get_assets(self, context):
        brushes = get_brushes()

        # Filter by search term if present
        if search := self.id_data.mbridge.search:
            return [brush for brush in brushes.get("ALL", []) if re.search(search, brush.searchStr, re.IGNORECASE)]

        # Return based on category selection
        return brushes.get("ALL") if self.category == "ALL" else brushes.get(self.category, {}).get(self.subcategory)

    def _update_category(self, context):
        self.subcategory = "ALL"

    category: EnumProperty(
        name="Category",
        description="Brushes category",
        items=enum_brushes_categories,
        update=_update_category,
    )

    subcategory: EnumProperty(
        name="Sub Category",
        description="Brushes subcategory",
        items=lambda self, context: [("ALL", "All", "All Sub Category"), None],
    )

    use_tex_mask: BoolProperty(
        name="Texture Mask",
        description="Use the brush as a texture mask",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "category", text="")
        subcol = col.column()
        subcol.enabled = self.category != "ALL"
        subcol.prop(self, "subcategory", text="")


class SCENE_PG_mbridge(PropertyGroup):
    def _asset_type(self, context):
        self.page = 1

    asset_type: EnumProperty(
        name="Type",
        description="Asset type",
        items=(
            ("ASSETS", "Assets", "3D Assets"),
            ("PLANTS", "Plants", "3D Plants"),
            ("SURFACES", "Surfaces", "Surfaces/Materials"),
            ("DECALS", "Decals", "Decals"),
            ("ATLASES", "Atlases", "Atlases"),
            ("IMPERFECTIONS", "Imperfections", "Imperfections"),
            ("DISPLACEMENTS", "Displacements", "Displacements"),
        ),
        update=_asset_type,
    )

    assets: PointerProperty(type=MBRIDGE_PG_assets)
    plants: PointerProperty(type=MBRIDGE_PG_plants)
    surfaces: PointerProperty(type=MBRIDGE_PG_surfaces)
    decals: PointerProperty(type=MBRIDGE_PG_decals)
    atlases: PointerProperty(type=MBRIDGE_PG_atlases)
    imperfections: PointerProperty(type=MBRIDGE_PG_imperfections)
    displacements: PointerProperty(type=MBRIDGE_PG_displacements)
    brushes: PointerProperty(type=MBRIDGE_PG_brushes)

    page: IntProperty(
        name="Page",
        description="Navigate to page",
        default=1,
    )

    def _update_search(self, context):
        if self.search:
            self.page = 1

    search: StringProperty(
        name="Search",
        description="Search for assets",
        default="",
        update=_update_search,
    )

    def get_assets(self, context):
        if self.asset_type == "PLANTS":
            return self.plants.get_assets(context)
        elif self.asset_type == "SURFACES":
            return self.surfaces.get_assets(context)
        elif self.asset_type == "DECALS":
            return self.decals.get_assets(context)
        elif self.asset_type == "ATLASES":
            return self.atlases.get_assets(context)
        elif self.asset_type == "IMPERFECTIONS":
            return self.imperfections.get_assets(context)
        elif self.asset_type == "DISPLACEMENTS":
            return self.displacements.get_assets(context)
        elif self.asset_type == "BRUSHES":
            return self.brushes.get_assets(context)
        else:
            return self.assets.get_assets(context)


classes = (
    MBRIDGE_PG_assets,
    MBRIDGE_PG_plants,
    MBRIDGE_PG_surfaces,
    MBRIDGE_PG_decals,
    MBRIDGE_PG_atlases,
    MBRIDGE_PG_imperfections,
    MBRIDGE_PG_displacements,
    MBRIDGE_PG_brushes,
    SCENE_PG_mbridge,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.mbridge = PointerProperty(name="M-Bridge", type=SCENE_PG_mbridge)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.mbridge

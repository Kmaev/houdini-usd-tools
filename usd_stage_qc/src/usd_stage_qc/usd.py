import os

import hou
from pxr import Usd, UsdGeom, UsdShade


def is_usd_file(path: str) -> bool:
    """
    Check if a path points to an existing USD file.

    Args:
        path: Usd file path.

    Returns:
        bool: True if valid USD file.
    """
    if not isinstance(path, str):
        raise TypeError("Expected path to be a string")

    if not path:
        raise ValueError("Path cannot be an empty string or whitespace.")

    path = path.strip()

    usd_extensions = ('.usd', '.usda', '.usdc', '.usdz')
    return path.lower().endswith(usd_extensions) and os.path.isfile(path)


def collect_prims_without_material(stage: Usd.Stage) -> list[Usd.Prim]:
    """
    Collect primitives without valid material bindings.

    Args:
        stage: USD stage.

    Returns:
        list: Primitives without material.
    """
    start_prim = stage.GetPseudoRoot()
    iterator = iter(Usd.PrimRange(start_prim))
    no_material = []
    for prim in iterator:
        if not iterator.IsPostVisit() and prim.IsA(UsdGeom.Imageable):

            bound_material, _ = check_prim_material_binding(prim)
            if prim.IsA(UsdGeom.Mesh):
                if not bound_material or not is_material_active(bound_material):
                    no_material.append(prim)
    return no_material


def check_prim_material_binding(prim: Usd.Prim) -> tuple[Usd.Prim, UsdShade.Tokens]:
    """
    Return bound material and binding strength.

    Args:
        prim: USD prim.

    Returns:
        tuple: Material and strength.
    """
    mat_bind_api = UsdShade.MaterialBindingAPI(prim)
    bound_material, strength = mat_bind_api.ComputeBoundMaterial()
    return bound_material, strength


def is_material_active(mat: Usd.Prim) -> bool:
    """
    Check if a material is active.

    Args:
        mat: Material prim.

    Returns:
        bool: True if active.
    """
    return mat.GetPrim().IsActive()


def solve_material_status(mat: Usd.Prim) -> str:
    """
    Return material status.

    Args:
        mat: Material prim.

    Returns:
        str | None: Status string.
    """
    if mat is None:
        return None
    if not is_material_active(mat):
        return "Deactivated"
    return "Active"


def check_live_houdini_stage(stage) -> list[Usd.Prim]:
    """
    Collect primitives without material from a live stage.

    Args:
        stage: USD stage.

    Returns:
        list: Primitives without material.
    """
    mat_binds = collect_prims_without_material(stage)

    return mat_binds


def check_usd_file(stage_path: str) -> bool:
    """
    Collect primitives without material from a USD file.

    Args:
        stage_path: USD file path.

    Returns:
        list | None: Primitives without material.
    """
    if is_usd_file(stage_path):
        stage = Usd.Stage.Open(stage_path)

        if stage is None:
            raise ValueError(f"Failed to open USD stage from file: {stage_path}")
        return collect_prims_without_material(stage)
    return None


def find_all_materials(stage: Usd.Stage) -> list[Usd.Prim]:
    """
    Collect all material prims from the stage.

    Args:
        stage: USD stage.

    Returns:
        list: Material prims.
    """
    start_prim = stage.GetPseudoRoot()
    iterator = iter(Usd.PrimRange(start_prim))
    materials = []
    for prim in iterator:

        if prim.IsA(UsdShade.Material):
            material = UsdShade.Material(prim)
            materials.append(material)
    return materials

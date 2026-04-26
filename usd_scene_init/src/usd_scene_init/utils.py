import json
from typing import Any

from pxr import Usd, UsdGeom


def configure_xform(prim: Usd.Prim, kind: str | None = None) -> UsdGeom.Xform:
    """
    Configure an Xform prim, if kind set kind and asset name.

    Returns:
        UsdGeom.Xform
    """
    xform = UsdGeom.Xform(prim)
    if kind:
        model_api = Usd.ModelAPI(xform)
        model_api.SetKind(kind)
        model_api.SetAssetName(prim.GetName())

    return xform


def create_prim(stage: Usd.Stage, parent_path: str, prim: dict[str, Any]) -> None:
    """Create a prim and its children on the stage from dictionary template"""
    path = f"{parent_path}/{prim['name']}"
    prim_type = prim["type"]
    prim_kind = prim.get("kind")

    usd_prim = stage.DefinePrim(path, prim_type)

    if usd_prim.IsA(UsdGeom.Xform):
        configure_xform(usd_prim, prim_kind)

    for child in prim.get("children", []):
        create_prim(stage, path, child)


def create_scene_from_json(template_path: str, stage_output_path: str) -> None:
    """Create a USD stage from a JSON template and save it."""
    with open(template_path, "r") as f:
        root_prim = json.load(f)

    stage = Usd.Stage.CreateNew(stage_output_path)
    create_prim(stage, "", root_prim)
    stage.GetRootLayer().Save()

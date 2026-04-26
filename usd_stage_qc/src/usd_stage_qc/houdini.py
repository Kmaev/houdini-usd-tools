import hou
from pxr import Usd

from usd_stage_qc import status_messages


def get_single_selected_node():
    """Return a single selected Houdini node."""
    selected = hou.selectedNodes()

    if not selected:
        status_messages.handle_error('No nodes were selected. Please select one node.')

    if len(selected) > 1:
        status_messages.handle_error('More than one node was selected. Please select only one node.')

    return selected[0]


def create_and_insert_hou_node(parent_node: hou.Node, type: str, name: str) -> hou.Node:
    """
    Create and insert a node into the parent node stream.

    Args:
        parent_node: Parent node.
        type: Node type.
        name: Node name.
    """
    parent_pos = parent_node.position()
    context = parent_node.parent()

    inserted_node = context.createNode(type, name)
    inserted_node.setPosition(hou.Vector2(parent_pos[0], parent_pos[1] - 1))

    old_outputs = parent_node.outputs()
    for idx, output_node in enumerate(old_outputs):
        output_node.setInput(0, inserted_node)

    inserted_node.setInput(0, parent_node)

    inserted_node.setDisplayFlag(True)
    parent_node.setSelected(False)
    inserted_node.setSelected(True)
    offset_outputs_position(inserted_node)
    return inserted_node


def offset_outputs_position(root: hou.Node) -> None:
    """
    Offset positions of downstream nodes in Y.

    Args:
        root: Selected root node.
    """
    queue = [root]
    while len(queue) > 0:
        current = queue.pop(0)
        if current is not root:
            pos = current.position()
            current.setPosition(hou.Vector2(pos[0], pos[1] - 1))

        for node in current.outputs():
            queue.append(node)


def compute_mat_assign_index(material_assign_node: hou.Node) -> int:
    """
    Return the next material assignment index.

    Args:
        material_assign_node: Material assign houdini LOP node.
    """
    mat_num = material_assign_node.parm("nummaterials").eval()

    if mat_num <= 1 and material_assign_node.parm(f"matspecpath{mat_num}").eval() == '':
        new_mat_index = mat_num
    else:
        new_mat_index = mat_num + 1
    return new_mat_index


def populate_mat_assign_parms(material_assign_node: hou.Node, mat_index: int, usd_prim: Usd.Prim,
                              material_prim: Usd.Prim) -> None:
    """
    Populate material assignment parameters.

    Args:
        material_assign_node: Material assign node.
        mat_index: Index in material assign node.
        usd_prim: USD prim.
        material_prim: Material prim.
    """
    material_assign_node.parm("nummaterials").set(mat_index)
    material_assign_node.parm(f"primpattern{mat_index}").set(str(usd_prim.GetPath()))
    material_assign_node.parm(f"matspecpath{mat_index}").set(str(material_prim.GetPath()))

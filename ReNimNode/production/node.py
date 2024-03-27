from bpy.types import NodeTree
from nodeitems_utils import NodeCategory


class ReNimNode:
    @classmethod
    def poll(cls, node_tree: NodeTree | None):
        return node_tree is not None and node_tree.bl_idname == "ReNimNode"


class ReNimNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):  # type: ignore
        return context.space_data.tree_type == "ReNimNode"

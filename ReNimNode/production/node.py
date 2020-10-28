import bpy
from bpy.types import Node as OriNode
import nodeitems_utils
from nodeitems_utils import NodeCategory as OriNodeCategory

class Node(OriNode):
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ReNimNode'

class NodeCategory(OriNodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ReNimNode'

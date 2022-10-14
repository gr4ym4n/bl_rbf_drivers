

# TODD provide generic node observers (init, free, push etc.)



from itertools import product
from typing import TYPE_CHECKING, Set
from bpy.types import NodeCustomGroup, Operator
from bpy.props import IntProperty
from .base import RBFDriverNodeGroup
from ..utils.layout import layout_nodes_columns
from ..utils.node import iternodes, findnode, listnodes
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..sockets.base import RBFDriverNodeSocket


def reshape(group: 'RBFDriverNodeGroupDistanceMatrix', data: 'RBFDataMatrix') -> None:
    pass


class RBFDriverNodeGroupDistanceMatrix(RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeGroupDistanceMatrix'
    bl_label = "Distance Matrix"
    bl_width_default  = 120
    nt_type = 'RBFDriverNodeTreeDistanceMatrix'
    nt_name = "Distance Matrix"

    def init(self, _) -> None:
        super().init(_)
        tree = self.node_tree
        tree.inputs.new('RBFDriverNodeSocketMatrix', "Input")
        tree.outputs.new('RBFDriverNodeSocketMatrix', "Result")
        layout_nodes_columns([
            [tree.nodes.new('NodeGroupInput')],
            [tree.nodes.new('NodeGroupOutput')]])

    def draw_buttons(self, _, layout: 'UILayout') -> None:
        super().draw_buttons(_, layout)

    def draw_buttons_ext(self, _, layout: 'UILayout') -> None:
        tree = self.node_tree
        if tree and tree.bl_idname == 'RBFDriverNodeTreeDistanceMatrix':
            ogrp = findnode(tree, 'NodeGroupOutput')
            if ogrp and len(ogrp.inputs):
                mout = ogrp.inputs[0]
                if mout.bl_idname == 'RBFDriverNodeSocketMatrix':
                    mat = mout.data()
                    if mat:
                        for vec in mat:
                            row = layout.row(align=True)
                            for val in vec.values():
                                sub = row.row(align=True)
                                sub.alignment = 'CENTER'
                                sub.label(text=f'{val:.3f}')

    def push(self, input_: 'RBFDriverNodeSocket', data: object) -> None:
        def update():

            ntree = self.node_tree
            nodes = ntree.nodes
            links = ntree.links
            nodes.clear()
            

            igrp = nodes.new('NodeGroupInput')
            ogrp = nodes.new('NodeGroupOutput')
            mspl = nodes.new('RBFDriverNodeMatrixSplit')
            mout = nodes.new('RBFDriverNodeMatrix')
            cols = [[igrp], [], [], [mout], [ogrp]]

            links.new(igrp.outputs[0], mspl.inputs[0])
            links.new(mout.outputs[0], ogrp.inputs[0])

            mout.inputs[0].default_size = data.shape[0]
            mout.row_count = len(data)

            for a, i in zip(mspl.outputs, mout.inputs[1:]):
                v = nodes.new('RBFDriverNodeVector')
                v.inputs[0].default_size = data.shape[0]
                links.new(v.outputs[0], i)
                cols[2].append(v)
                for b, vi in zip(mspl.outputs, v.inputs[1:]):
                    d = nodes.new('RBFDriverNodeDistance')
                    links.new(a, d.inputs[0])
                    links.new(b, d.inputs[1])
                    links.new(d.outputs[0], vi)
                    cols[1].append(d)

            layout_nodes_columns(cols)

        import bpy
        bpy.app.timers.register(update)

            


            # links.new(igrp.outputs[0], mspl.inputs[0])
            # links.new(mout.outputs[0], ogrp.inputs[0])

            # layout_nodes_columns(cols)

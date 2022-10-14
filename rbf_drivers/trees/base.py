
# from typing import TYPE_CHECKING, Iterable
# from bpy.app import timers
from uuid import uuid4
from bpy.types import NodeTree#, PropertyGroup, NodeCustomGroup, 
from bpy.props import BoolProperty, PointerProperty, StringProperty#, CollectionProperty,
from .. import cache
# from ..sockets.base import RBFDriverNodeSocket
# from ..nodes.base import RBFDriverNode
# if TYPE_CHECKING:
#     from bpy.types import Context, Node


# def disconnect(input_: 'RBFDriverNodeSocket') -> None:
#     input_["linked_id"] = ""
#     input_["is_valid"] = True
#     node = input_.node
#     if isinstance(node, RBFDriverNode):
#         node.push(input_, input_.read())
#     elif isinstance(node, NodeGroupOutput):
#         node = groupnode(node)
#         if node:
#             output = matchsocket(node.outputs, input_)
#             if output:
#                 output.data(input_.read())


# def connect(output: 'RBFDriverNodeSocket', input_: 'RBFDriverNodeSocket') -> None:
#     input_["linked_id"] = output.id
#     input_.data(output.data())


# class RBFDriverNodeTreeUpdateContext():

#     def __init__(self, tree):
#         self.tree = tree
#         self.undo = False

#     def __enter__(self):
#         tree = self.tree
#         undo = not tree.is_update_paused
#         if undo:
#             tree.pause_update()
#             self.undo = True
#         return self.tree

#     def __exit__(self, *_):
#         if self.undo:
#             self.tree.unpause_update()


class Update():

    def __init__(self, tree):
        self.tree = tree
        self.undo = False

    def __enter__(self):
        tree = self.tree
        undo = not tree.is_update_paused
        if undo:
            tree["is_update_paused"] = True
            self.undo = True
        return self.tree

    def __exit__(self, *_):
        if self.undo:
            tree = self.tree
            tree["is_update_paused"] = False
            tree.update()



# class NodeTopology(PropertyGroup):

#     dependencies: CollectionProperty(
#         type=PropertyGroup,
#         options=set()
#         )

#     is_evaluable: BoolProperty(
#         default=False,
#         options=set()
#         )

#     def __init__(self, name: str, dependants: Iterable[str]) -> None:
#         deps = self.dependencies
#         deps.clear()
#         self.name = name
#         for name in dependants:
#             deps.add().name = name


UPDATE = 0

class RBFDriverNodeTree:
    bl_icon = 'NODETREE'

    def get_identifier(self):
        id_ = self.get("identifier")
        if not id_:
            id_ = str(uuid4())
            self["identifier"] = id_
        return id_

    identifier: StringProperty(
        get=get_identifier,
        options={'HIDDEN'}
        )

    # topology__internal__: CollectionProperty(
    #     type=NodeTopology,
    #     options={'HIDDEN'}
    #     )

    is_update_paused: BoolProperty(
        get=lambda self: self.get("is_update_paused", False),
        options=set()
        )

    is_update_pending: BoolProperty(
        get=lambda self: self.get("is_update_pending", False),
        options=set()
        )

    # is_evaluation_paused: BoolProperty(
    #     get=lambda self: self.get("is_evaluation_paused", False),
    #     options=set()
    #     )

    # is_evaluation_pending: BoolProperty(
    #     get=lambda self: self.get("is_evaluation_pending", False),
    #     options=set()
    #     )

    # is_evaluation_running: BoolProperty(
    #     get=lambda self: self.get("is_evaluation_running", False),
    #     options=set()
    #     )

    # def pause_evaluation(self):
    #     self["is_evaluation_paused"] = True

    # def unpause_evaluation(self):
    #     if self.is_evaluation_paused:
    #         self["is_evaluation_paused"] = False
    #         if self.is_evaluation_pending:
    #             self.evaluate()

    # def pause_update(self):
    #     self["is_update_paused"] = True

    # def unpause_update(self):
    #     if self.is_update_paused:
    #         self["is_update_paused"] = False
    #         if self.is_update_pending:
    #             self.update()
    #         elif self.is_evaluation_pending:
    #             self.evaluate()

    # def evaluate(self) -> None:
    #     if self.is_update_paused:
    #         self["is_evaluation_pending"] = True
    #     else:
    #         self["is_evaluation_pending"] = False
    #         self["is_evaluation_running"] = True
    #         nodes = self.nodes
    #         for item in self.topology__internal__:
    #             node = nodes.get(item.name)
    #             if node is not None and isinstance(node, RBFDriverNode) and node.is_dirty:
    #                 node.evaluate()
    #                 node["is_dirty"] = False
    #         self["is_evaluation_running"] = False

    # def _tag(self, node: 'Node') -> None:
    #     item = self.topology__internal__.get(node.name)
    #     if item is not None and item.is_evaluable and not node.is_dirty:
    #         node["is_dirty"] = True
    #         for key in item.dependencies.keys():
    #             dep = self.nodes.get(key)
    #             if dep:
    #                 self._tag(dep)

    def arrange_column(self, nodes, center=0.0, spacing=50.0):
        if isinstance(center, (int, float)):
            center = (center, 0.0)

        nodes = list(nodes)
        nodes.sort(key=lambda n: n.location.y - (n.height / 2), reverse=True)

        offset = 0
        for node in nodes:
            node.location.y = offset
            offset -= spacing + node.height
            node.location.x = center[0] - (node.width / 2)

        offset = center[1] + (offset + spacing) / -2
        for node in nodes:
            node.location.y += offset

    def arrange_multi_column(self, nodes, center=0.0, spacing=50.0):

        if isinstance(center, (int, float)):
            center = (center, 0.)

        if isinstance(spacing, (int, float)):
            spacing = (spacing, spacing)

        cols = [list(col) for col in nodes]
        for col in cols:
            self.arrange_column(col, center, spacing[1])

        offset = spacing[0] + max([n.width for n in cols[0]], default=0.) / 2
        for col in cols[1:]:
            width = max([n.width for n in col], default=0.)
            for node in col:
                node.location.x += offset + width / 2
            offset += spacing[0] + width

    # def tag_node(self, node):
    #     assert node.id_data == self
    #     if isinstance(node, RBFDriverNode):
    #         if node.is_dirty: return
    #         node["is_dirty"] = True
    #     entry = self.topology__internal__.get(node.name)
    #     if entry is not None:
    #         nodes = self.nodes
    #         for key in entry.dependencies.keys():
    #             dep = nodes.get(key)
    #             if dep is not None:
    #                 self.tag_node(dep)

    # def socket_update(self, socket: 'RBFDriverNodeSocket') -> None:
    #     assert socket.id_data == self
    #     if not self.is_evaluation_running:
    #         node = socket.node
    #         rbfn = isinstance(node, RBFDriverNode)
    #         if not rbfn or (node.is_ready and not node.is_dirty):
    #             if socket.is_output:
    #                 if socket.is_linked:
    #                     for link in socket.links:
    #                         if link.is_valid:
    #                             self.tag_node(link.to_node)
    #             else:
    #                 self.tag_node(node)
    #         self.evaluate()

    # def update_context(self):
    #     return RBFDriverNodeTreeUpdateContext(self)

    # def update(self) -> None:
    #     global UPDATE
    #     UPDATE += 1
    #     print("update", UPDATE)
    #     if self.is_update_paused:
    #         self["is_update_pending"] = True
    #     else:
    #         self["is_update_pending"] = False

    #         nodes = self.nodes
    #         inlen = {k: 0 for k in nodes.keys()}
    #         invec = {k: [] for k in nodes.keys()}
    #         odeps = {k: [] for k in nodes.keys()}

    #         for link in self.links:
    #             if link.is_valid:
    #                 src = link.from_node.name
    #                 tgt = link.to_node.name
    #                 inlen[tgt] += 1
    #                 invec[tgt].append(src)
    #                 odeps[src].append(tgt)

    #         order = [k for k, n in inlen.items() if n == 0]
    #         for k in order:
    #             for i in odeps[k]:
    #                 n = inlen[i] - 1
    #                 inlen[i] = n
    #                 if n == 0:
    #                     order.append(i)

    #         topo = self.topology__internal__
    #         topo.clear()
    #         for name in order:
    #             topo.add().__init__(name, odeps[name])

    #         evaluate = self.is_evaluation_pending

    #         def tag(node):
    #             node["is_dirty"] = True
    #             for key in odeps[node.name]:
    #                 tag(nodes[key])

    #         for node in nodes:
    #             if isinstance(node, RBFDriverNode):
    #                 ivec = invec[node.name]
    #                 imap = node.inputmapping__internal__
    #                 if not node.is_ready or imap != ivec:
    #                     imap.__init__(ivec)
    #                     node["is_ready"] = True
    #                     tag(node)
    #                     evaluate = True

    #         if evaluate:
    #             self.evaluate()

    # def update(self) -> None:
    #     if not self.is_update_pending:
    #         self["is_update_pending"] = True
    #         def callback():
    #             if self.is_update_pending:
    #                 self.update_immediate()
    #         timers.register(callback)
            

    # def update(self) -> None:
    #     for node in self.nodes:
    #         if isinstance(node, RBFDriverNode):
    #             for input_ in node.inputs:
    #                 id_ = input_.linked_id
    #                 if id_:
    #                     if not input_.is_linked:
    #                         disconnect(input_)
    #                     else:
    #                         edge = inputedge(input_)
    #                         if edge is None:
    #                             disconnect(input_)
    #                         elif edge.socket.id != id_:
    #                             connect(edge.socket, input_)
    #                 elif input_.is_linked:
    #                     edge = inputedge(input_)
    #                     if edge is not None:
    #                         connect(edge.socket, input_)

    # def update_paused(self):
    #     return Update(self)

    # def update(self):
    #     if self.is_update_paused:
    #         self["is_update_pending"] = True
    #     elif self.is_update_pending:
    #         self["is_update_pending"] = False
    #         cache.init(self)

    

class RBFDriverNodeSubtree(RBFDriverNodeTree):

    parent__internal__: PointerProperty(
        type=NodeTree,
        options={'HIDDEN'}
        )

    # def get_parent_group_node(self):
    #     ptree = self.parent__internal__
    #     if ptree:
    #         for node in ptree.nodes:
    #             if isinstance(node, NodeCustomGroup) and node.node_tree == self:
    #                 return node

    # def get_node_group_input(self):
    #     ntree = self.node_tree
    #     if ntree:
    #         for node in ntree.nodes:
    #             if node.bl_idname == 'NodeGroupInput':
    #                 return node

    # def get_node_group_output(self):
    #     ntree = self.node_tree
    #     if ntree:
    #         for node in ntree.nodes:
    #             if node.bl_idname == 'NodeGroupOutput':
    #                 return node

    @classmethod
    def poll(cls, context):
        return False

    # def evaluate(self):
    #     if not self.is_update_pending:
    #         super().evaluate()
    #         pgrp = self.get_parent_group_node()
    #         if pgrp:
    #             gout = self.get_node_group_output()
    #             if gout:
    #                 for pgi in pgrp.inputs:


    #             for node in self.nodes:
    #                 if node.bl_idname == 'NodeGroupOutput':
    #                     for i in grp.inputs:
    #                         o = next((x for x in node.outputs if x.identifier == i.identifier), None)
    #                         if o:
    #                             o.data = i.evaluate()
    #                     break
    #             break

    # def socket_update(self, socket: 'RBFDriverNodeSocket') -> None:
    #     assert socket.id_data == self
    #     if socket.is_output:
    #         if socket.is_linked:
    #             for link in socket.links:
    #                 if link.is_valid:
    #                     self._tag(link.to_node)
    #     else:
    #         node = socket.node
    #         if node.bl_idname == 'NodeGroupOutput':
    #             tree = getattr(node.id_data, "parent__internal__", None)
    #             if isinstance(tree, RBFDriverNodeTree):
    #                 for pnode in tree.nodes:
    #                     if isinstance(node, NodeCustomGroup) and node.node_tree == self:




    #     if node.bl_idname not node.is_evaluation_pending:
    #         if socket.is_output:
    #             if socket.is_linked:
    #                 for link in socket.links:
    #                     if link.is_valid:
    #                         self._tag(link.to_node)
    #         else:
    #             self._tag(node)
    #         self.evaluate()
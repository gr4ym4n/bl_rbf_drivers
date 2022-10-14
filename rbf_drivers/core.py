
# TODO give input sockets the chance to modify data, don't use data keys, instead COW

from collections import defaultdict
from contextlib import contextmanager
from functools import partial, wraps
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TYPE_CHECKING,
    Union)
from uuid import uuid4
from bpy.app import timers
from bpy.types import (
    Node,
    NodeCustomGroup,
    NodeGroupInput,
    NodeGroupOutput,
    NodeReroute,
    NodeSocket,
    NodeTree,
    Operator,
    PropertyGroup,
    UILayout)
from bpy.props import BoolProperty, CollectionProperty, PointerProperty, StringProperty
if TYPE_CHECKING:
    from bpy.types import Context


def Cache() -> DefaultDict[str, Tuple[Dict[str, Any], Dict[str, Any]]]:
    return defaultdict(lambda: ({}, {}))


def cache(default: Callable[['RBFDriverNodeSocket'], Any]) -> Callable[['RBFDriverNodeSocket'], Any]:

    def enter(node: RBFDriverNodeGroup, sock: RBFDriverNodeSocket) -> Any:
        tree = node.node_tree
        if tree:
            out = next((x for x in tree.nodes if isinstance(x, NodeGroupOutput)), None)
            if out:
                id_ = sock.identifier
                in_ = next((x for x in out.inputs if x.identifier == id_), None)
                return default(sock) if in_ is None else in_.data()

    def leave(node: NodeGroupInput, sock: RBFDriverNodeSocket) -> Any:
        data = node.id_data
        tree = data.owner
        if tree:
            grp = next((x for x in tree.nodes if isinstance(x, RBFDriverNodeGroup) and x.node_tree == data), None)
            if grp:
                id_ = sock.identifier
                in_ = next((x for x in grp.inputs if x.identifier == id_), None)
                return default(sock) if in_ is None else in_.data()

    @wraps(default)
    def read(socket: 'RBFDriverNodeSocket') -> Any:
        n = socket.node
        o = n.id_data.cache[nodeid(n)][socket.is_output]
        k = socket.identifier
        if k in o:
            return o[k]
        if socket.is_output:
            if isinstance(n, RBFDriverNodeGroup): d = enter(n, socket)
            elif isinstance(n, NodeGroupInput)  : d = leave(n, socket)
            elif isinstance(n, RBFDriverNode)   : d = n.data(socket)
            else                                : d = default(socket)
        else:
            x = next(iter(socket.edge), None)
            d = default(socket) if x is None else x.data()
        o[k] = d
        return d

    return read


def reevaluate(socket: 'RBFDriverNodeSocket') -> None:
    # print(socket)
    if socket.is_output:
        for socket in socket.edge:
            node = socket.node
            node.id_data.cache[nodeid(node)][0].pop(socket.identifier, None)
            if isinstance(node, RBFDriverNode):
                node.input_update(socket)
            reevaluate(socket)
    else:
        node = socket.node
        if isinstance(node, NodeGroupOutput):
            # find parent node tree outputs and reevaluate them
            data = node.id_data
            tree = data.owner
            if tree:
                grp = next((x for x in tree.nodes if isinstance(x, RBFDriverNodeGroup) and x.node_tree == data), None)
                if grp:
                    id_ = socket.identifier
                    out = next((x for x in grp.outputs if x.identifier == id_), None)
                    if out:
                        reevaluate(out)
                        # evaluation.add(out)
        elif isinstance(node, RBFDriverNode):
            for socket in node.dependencies(socket):
                socket.id_data.cache[nodeid(socket.node)][1].pop(socket.identifier, None)
                reevaluate(socket)


def update(tree: 'RBFDriverNodeTree') -> None:
    tree["is_updating"] = False

    nodes = tree.nodes
    graph = {
        node: {
            "node": node,
            "poll": 0,
            "deps": [],
            "pred": {sock: list(sock.edge) for sock in node.inputs if isinstance(sock, RBFDriverNodeSocket)},
            "incoming": defaultdict(list),
            "outgoing": defaultdict(list),
        } for node in nodes
    }

    for link in tree.links:
        if link.is_valid and not link.is_muted:
            srcnode = link.from_node
            srcsock = link.from_socket
            srcitem = graph[srcnode]
            tgtnode = link.to_node
            tgtsock = link.to_socket
            tgtitem = graph[tgtnode]
            tgtitem["poll"] += 1
            srcitem["deps"].append(tgtnode)
            tgtitem["incoming"][tgtsock].append(srcsock)
            srcitem["outgoing"][srcsock].append(tgtsock)

    # topological sort
    topo = [x for x in graph.values() if x["poll"] == 0]
    for item in topo:
        for node in item["deps"]:
            item = graph[node]
            poll = item["poll"] = item["poll"] - 1
            if poll == 0:
                topo.append(item)

    # splice reroutes
    i = len(topo)-1
    while i >= 0:
        item = topo[i]
        node = item["node"]
        if isinstance(node, NodeReroute):
            del topo[i]
            for sock, conn in item["incoming"]:
                edge = graph[sock.node]["outgoing"]
                edge[sock] = [x for x in edge[sock] if x.node != node] + conn
        i -= 1

    # update socket edges
    for item in topo:
        node = item["node"]
        revalidate = False
        for sock in node.inputs:
            if isinstance(sock, RBFDriverNodeSocket):
                edge = sock.edge
                prev = item["pred"]
                curr = item["incoming"][sock]
                edge.init(curr)
                if curr != prev:
                    revalidate = True
                    if curr:
                        sock.validate(curr[0])
                    else:
                        sock.error = ""
        # Could be NodeGroupInput | NodeGroupOutput
        if revalidate and isinstance(node, RBFDriverNode):
            node.validate()
        for sock in node.outputs:
            if isinstance(sock, RBFDriverNodeSocket):
                sock.edge.init(item["outgoing"][sock])

    # evaluate tree
    tree.cache.clear()
    for node in nodes:
        if isinstance(node, RBFDriverNode) and not len(node.outputs):
            node.evaluate()


def resolve(node: Node) -> Node:
    if isinstance(node, (NodeGroupInput, NodeGroupOutput)):
        tree = node.id_data.owner
        if tree:
            for grp in tree.nodes:
                if isinstance(grp, RBFDriverNodeGroup) and grp.node_tree == tree:
                    node = grp
    return node


class RBFDriverNodeSocketReference(PropertyGroup):
    # name
    is_output: BoolProperty()
    socket_id: StringProperty()

    def init(self, socket: 'RBFDriverNodeSocket') -> None:
        self.name = socket.node.name
        self.is_output = socket.is_output
        self.socket_id = socket.identifier

    def resolve(self) -> Optional['RBFDriverNode']:
        node = self.id_data.nodes.get(self.name)
        if node:
            obj = node.outputs if self.is_output else node.inputs
            key = self.socket_id
            return next((x for x in obj if x.identifier == key), None)


class RBFDriverNodeSocketReferences(PropertyGroup):

    references: CollectionProperty(
        type=RBFDriverNodeSocketReference,
        options=set()
        )

    def __iter__(self) -> Iterator['RBFDriverNodeSocket']:
        return filter(None, map(RBFDriverNodeSocketReference.resolve, self.references))

    def init(self, sockets: Sequence['RBFDriverNodeSocket']) -> None:
        refs = self.references
        size = len(sockets)
        if not size:
            refs.clear()
        else:
            while len(refs) > size: refs.remove(-1)
            while len(refs) < size: refs.add()
            for ref, socket in zip(refs, sockets):
                ref.init(socket)


class RBFDriverNodeSocket:
    ERROR_COLOR = (1.0, 0.157, 0.259, 1.0)
    VALID_COLOR = (0.882, 0.588, 0.345, 1.0)

    edge: PointerProperty(
        type=RBFDriverNodeSocketReferences,
        options=set()
        )

    error: StringProperty(
        default="",
        options=set()
        )

    @property
    def value(self) -> Any:
        return None

    @classmethod
    def poll(cls, nodetree: NodeTree):
        return nodetree.bl_idname.startswith('RBFDriverNodeTree')

    def data(self) -> Any:
        return self.value

    def draw(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        if self.error:
            self.draw_error(context, layout, node, text)
        elif self.is_output or len(self.edge.references) > 0:
            self.draw_label(context, layout, node, text)
        else:
            self.draw_value(context, layout, node, text)

    def draw_error(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        layout.label(icon='ERROR', text=self.error)

    def draw_label(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        layout.label(text=text or self.name)

    def draw_value(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        if "value" in self.bl_rna.properties:
            layout.prop(self, "value")

    def draw_color(self, context: 'Context', node: 'Node') -> Tuple[float, float, float, float]:
        return self.ERROR_COLOR if self.error else self.VALID_COLOR

    def free(self) -> None:
        self.id_data.cache[nodeid(self.node)][self.is_output].pop(self.identifier, None)

    def value_update(self, _=None) -> None:
        node = self.node
        is_output = self.is_output
        self.id_data.cache[nodeid(node)][is_output].pop(self.identifier, None)
        if not is_output and isinstance(node, RBFDriverNode):
            node.input_update(self)
        reevaluate(self)

    def validate(self, output: 'RBFDriverNodeSocket') -> None:
        if not isinstance(output, self.__class__):
            self.error = "Invalid"


class RBFDriverNodeSocketInterface:

    def draw(self, _0, _1):
        pass

    def draw_color(self, _):
        return (0., 1., 1., 1.)


def nodeid(node: 'Node') -> str:
    return rbfnodeid(node) if isinstance(node, RBFDriverNode) else node.__class__.__name__


def rbfnodeid(node: 'RBFDriverNode') -> str:
    id_ = node.get("identifier", "")
    if not id_:
        id_ = str(uuid4())
        node["identifier"] = id_
    return id_


class RBFDriverNode:

    identifier: StringProperty(
        name="Identifier",
        description="Unique node identifier (read-only)",
        get=rbfnodeid,
        options={'HIDDEN'}
        )

    def data(self, output: 'RBFDriverNodeSocket') -> Any:
        return output.value

    def dependencies(self, input: RBFDriverNodeSocket) -> Iterator[RBFDriverNodeSocket]:
        return iter(self.outputs)

    def evaluate(self) -> None:
        pass

    def free(self) -> None:
        key = self.identifier
        obj = self.id_data.cache
        if key in obj:
            del obj[key]

    def value_update(self, _=None) -> None:
        data = self.id_data.cache[rbfnodeid(self)][1]
        for output in self.outputs:
            data.pop(output.identifier, None)
            reevaluate(output)

    def validate(self) -> None:
        pass

    def input_update(self, socket: RBFDriverNodeSocket) -> None:
        pass


class RBFDriverNodeGroup(RBFDriverNode):
    
    def dependencies(self, input: RBFDriverNodeSocket) -> Iterator[RBFDriverNodeSocket]:
        tree = self.node_tree
        if tree:
            grp = next((x for x in tree.nodes if isinstance(x, NodeGroupInput)), None)
            if grp:
                for output in grp.outputs:
                    if isinstance(output, RBFDriverNodeSocket):
                        yield output


class RBFDriverNodeGroupEdit(Operator):
    bl_idname = 'rbfdriver.group_edit'
    bl_label = "Edit"
    bl_options = {'INTERNAL'}

    group_name: StringProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if space is not None:
            tree = getattr(space, "node_tree", None)
            return tree is not None and tree.bl_idname == 'RBFDriverNodeTreeMain'
        return False

    def execute(self, context):
        node = context.node
        grps = context.blend_data.node_groups
        path = context.space_data.path
        path.clear()
        path.start(node.id_data)
        path.append(grps[self.group_name])
        return {'FINISHED'}


class RBFDriverNodeTree:
    bl_icon = 'NODETREE'
    cache = Cache()

    owner: PointerProperty(
        type=NodeTree,
        options={'HIDDEN'}
        )

    is_updating: BoolProperty(
        get=lambda self: self.get("is_updating", False),
        options={'HIDDEN'}
        )

    def update(self) -> None:
        if not self.is_updating:
            self["is_updating"] = True
            timers.register(partial(update, self))


class RBFDriverNodeSubtree(RBFDriverNodeTree):
    
    @classmethod
    def poll(cls, context: 'Context') -> bool:
        return False



class RBFDriverNodeTreeMain(RBFDriverNodeTree, NodeTree):
    bl_idname = 'RBFDriverNodeTreeMain'
    bl_label = "RBF Driver"


CLASSES = [
    RBFDriverNodeSocketReference,
    RBFDriverNodeSocketReferences,
    RBFDriverNodeTreeMain,
    RBFDriverNodeGroupEdit
]

# TODO give input sockets the chance to modify data, don't use data keys, instead COW

from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from logging import getLogger
from re import I
from typing import Any, Callable, DefaultDict, Dict, Iterator, List, Optional, Set, Tuple, TypedDict, TYPE_CHECKING, Union
from uuid import uuid4
from bpy.types import (
    Node, NodeCustomGroup, NodeGroupInput, NodeGroupOutput, NodeReroute, NodeSocket, NodeTree,
    PropertyGroup, UILayout)
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, StringProperty
if TYPE_CHECKING:
    from bpy.types import Context

NodeID = str
SocketID = str
EdgeItem = DefaultDict[Node, List[NodeSocket]]

class TopoNode(TypedDict):
    poll: int
    node: Node
    edge: DefaultDict[NodeSocket, EdgeItem]
    pred: Optional[EdgeItem]

TopoDict = Dict[Node, TopoNode]

log = getLogger()
_datacache: Dict[SocketID, object] = {}


def findgroupnode(tree: NodeTree) -> Optional[NodeCustomGroup]:
    for node in tree.nodes:
        if isinstance(node, NodeCustomGroup) and node.node_tree == tree:
            return node
        log.error()


def getnodegroup(node: Node) -> Optional[NodeCustomGroup]:
    tree = node.id_data.owner__internal__
    if tree is None:
        log.error()
    else:
        return findgroupnode(tree)

# the data key of a NodeGroupInput or output should be the data key of the parent node group
def datakey(node: Node) -> str:
    if isinstance(node, (NodeGroupInput, NodeGroupOutput)):
        node = getnodegroup(node)
    if isinstance(node, RBFDriverNode):
        id_ = node.get("identifier", "")
        if not id_:
            id_ = str(uuid4())
            node["identifier"] = id_
        return id_
    return ""

def trace(socket: NodeSocket) -> Iterator[NodeSocket]:
    is_output = socket.is_output
    if socket.is_linked:
        for link in socket.links:
            if link.is_valid and not link.is_muted:
                node = link.to_node if is_output else link.from_node
                if isinstance(node, NodeReroute):
                    yield from trace(node.outputs[0] if is_output else node.inputs[0])
                elif is_output:
                    yield link.to_socket
                else:
                    yield link.from_socket


def get_mode(socket: 'RBFDriverNodeSocket') -> int:
    return socket.get("mode", 0 if socket.is_output else 1)


def set_mode(socket: 'RBFDriverNodeSocket', value: int) -> None:
    socket["mode"] = value



def socket_id(socket: 'RBFDriverNodeSocket') -> str:
    id_ = socket.get("id", None)
    if id_ is None:
        id_ = str(uuid4())
        socket["id"] = id_
    return id_


class RBFDriverNodeSocket:
    ERROR_COLOR = (1.0, 0.157, 0.259, 1.0)
    VALID_COLOR = (0.882, 0.588, 0.345, 1.0)

    id: StringProperty(
        name="ID",
        get=socket_id,
        options={'HIDDEN'}
        )

    connection_id: StringProperty(
        name="Input ID",
        get=lambda self: self.get("connection_id", ""),
        options={'HIDDEN'}
        )

    data_key: StringProperty(
        name="Key",
        get=lambda self: self.id if self.is_output else self.get("data_key", ""),
        options=set()
        )

    @property
    def data(self) -> object:
        return self.value

    @property
    def value(self) -> object:
        return None

    mode: EnumProperty(
        items=[
            ('LABEL', "", ""),
            ('VALUE', "", ""),
            ('ERROR', "", ""),
            ],
        get=get_mode,
        set=set_mode,
        options=set()
        )

    error: StringProperty(
        default="",
        options=set()
        )

    @classmethod
    def poll(cls, nodetree: NodeTree):
        return nodetree.bl_idname.startswith('RBFDriverNodeTree')

    def draw(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        getattr(self, f'draw_{self.mode.lower()}')(context, layout, node, text)

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
        if self.is_output:
            key = self.id
            if key in _datacache: del _datacache[key]


    def evaluate(self, _: Optional['Context']=None) -> None:
        self.node.evaluate(_)

    def read(self) -> object:
        key = self.data_key
        if self.is_output:
            if key in _datacache: return _datacache[key]
            try:
                obj = self.node.compute(self)
            except Exception as err:
                self.error = err.message
                self.mode = 'ERROR'
            else:
                _datacache[key] = obj
                return obj
        elif key:
            if key in _datacache: return _datacache[key]
            out = next(trace(self), None)
            if out is not None:
                if key != out.id: self["data_key"] = out.id
                obj = _datacache[key] = out.read()
                return obj
        return self.data

    def validate(self, output: 'RBFDriverNodeSocket') -> bool:
        return False


    #
    #
    #
    class SocketReference(PropertyGroup):
        # name
        identifier: StringProperty()

    is_dirty: BoolProperty(default=True)
    incoming_edge: CollectionProperty()
    outgoing_edge: CollectionProperty()

    def dependencies(self) -> Iterator['RBFDriverNodeSocket']:
        if self.is_output:
            return self.edge()
        node = self.node
        if isinstance(node, RBFDriverNode):
            return node.dependencies(self)
        if isinstance(node, NodeGroupOutput):
            tree = node.id_data.owner
            if tree is not None:
                for node in tree.nodes:
                    if isinstance(node, RBFDriverNodeGroup) and node.node_tree == tree:
                        id_ = self.identifier
                        for socket in node.outputs:
                            if socket.identifier == id_:
                                return socket.edge()
                        break
        yield from ()

    def edge(self) -> Iterator['RBFDriverNodeSocket']:
        nodes = self.id_data.nodes
        if self.is_output:
            for name, ref in self.outgoing_edge.items():
                node = nodes.get(name)
                if node is not None:
                    id_ = ref.identifier
                    for socket in node.inputs:
                        if socket.identifier == id_:
                            yield socket
                            break
        else:
            for name, ref in self.incoming_edge.items():
                node = nodes.get(name)
                if node is not None:
                    id_ = ref.identifier
                    for socket in node.outputs:
                        if socket.identifier == id_:
                            yield socket
                            break

    def on_update(self, _=None) -> None:
        self.data.cache.pop(self.id, None)
        if not self.is_output:
            self.id_data.on_input_socket_update(self)

    def read(self) -> object:
        key = self.id
        if not self.is_dirty and key in _datacache:
            return _datacache[key]

        self.is_dirty = False
        if self.is_output:
            node = self.node
            data = None
            if isinstance(node, RBFDriverNode):
                data = node.compute(self)
                node.is_dirty = any(output.is_dirty for output in node.outputs)
            elif isinstance(node, NodeGroupInput):
                tree = node.id_data.owner
                if tree:
                    for node in tree.nodes:
                        if isinstance(node, RBFDriverNodeGroup) and node.node_tree == tree:
                            id_ = self.identifier
                            socket = next((x for x in node.inputs if x.identifier == id_), None)
                            if socket:
                                data = socket.read()
            if data is None:
                data = self.data()
        else:
            edge = next(self.edge(), None)
            data = self.data() if edge is None else edge.read()

        _datacache[key] = data
        return data
        






class RBFDriverNodeSocketInterface:
    def draw(self, _0, _1):
        pass
    def draw_color(self, _):
        return (0., 1., 1., 1.)


class RBFDriverNode:

    identifier: StringProperty(
        get=datakey,
        options={'HIDDEN'}
        )

    def compute(self, output: RBFDriverNodeSocket) -> object:
        return output.data

    def free(self) -> None:
        key = datakey(self)
        if key in _datacache:
            del _datacache[key]

    @contextmanager
    def configure(self) -> Iterator[Set[str]]:
        tree: RBFDriverNodeTree = self.id_data
        lock = not tree.is_update_paused
        if lock:
            tree["is_update_paused"] = True
        flags = set()
        yield flags
        if 'UPDATE' in flags:
            tree["is_update_pending"] = True
        if lock:
            tree["is_update_paused"] = False
            tree.update()

    @contextmanager
    def reconfigure(self) -> Iterator[Set[str]]:
        pass

    def evaluate(self, _: Optional['Context']=None) -> None:
        self.id_data.evaluate(self)

    # def insert_link(self, link) -> None:
    #     pass

    #
    #
    #
    is_dirty: BoolProperty(default=True)

    def dependencies(self, socket: RBFDriverNodeSocket) -> Iterator[RBFDriverNodeSocket]:
        return iter(self.outputs)

    def evaluate(self) -> None:
        for output in self.outputs:
            if output.is_dirty:
                _datacache[self.id] = self.compute(output)
                output.is_dirty = False


class RBFDriverNodeGroup(RBFDriverNode):

    pass


class NodeState(PropertyGroup):
    # name
    deps: CollectionProperty(type=PropertyGroup, options=set())
    flag: BoolProperty(default=True, options=set())


class RBFDriverNodeTree:

    bl_icon = 'NODETREE'

    state__internal__: CollectionProperty(
        type=NodeState,
        options={'HIDDEN'}
        )

    is_update_pending: BoolProperty(
        get=lambda self: self.get("is_update_pending", False),
        options={'HIDDEN'}
        )

    is_update_paused: BoolProperty(
        get=lambda self: self.get("is_update_paused", False),
        options={'HIDDEN'}
        )

    @contextmanager
    def configure(self) -> Iterator:
        lock = not self.is_update_paused
        if lock:
            self["is_update_paused"] = True
            self["is_update_pending"] = True
        yield
        if lock:
            self["is_update_paused"] = False
            self.update()

    def evaluate(self, node: Optional[RBFDriverNode]=None) -> None:
        state = self.state__internal__
        nodes = self.nodes
        if node is not None:
            item = state.get(node.name)
            if item:
                item.flag = True
        for item in state:
            if item.flag:
                item.flag = False
                node = nodes.get(item.name)
                fail = False
                for output in node.outputs:
                    try:
                        obj = node.compute(output)
                    except Exception as err:
                        fail = True
                        output.error = err.message
                        output.mode = 'ERROR'
                    else:
                        _datacache[output.id] = obj
                if not fail:
                    for name in item.deps.keys():
                        state[name].flag = True

    def update(self) -> None:
        if not self.is_update_paused: #and self.is_update_pending:
            self["is_update_pending"] = False

            nodes = self.nodes
            topodict: TopoDict = {
                node: {
                    "poll": 0,
                    "node": node,
                    "edge": defaultdict(lambda: defaultdict(list)),
                    "pred": None
                } for node in nodes
            }

            if not topodict:
                self.state__internal__.clear()
                return

            # construct topo nodes
            for link in self.links:
                if link.is_valid and not link.is_muted:
                    tgtnode = link.to_node
                    tgttopo = topodict[tgtnode]
                    srcsock = link.from_socket
                    srcedge = topodict[link.from_node]["edge"][srcsock]
                    tgttopo["poll"] += 1
                    srcedge[tgtnode].append(link.to_socket)
                    if isinstance(tgtnode, NodeReroute):
                        tgttopo["pred"] = srcedge

            # topological sort
            topology = [item for item in topodict.values() if item["poll"] == 0]
            for topo in topology:
                for edgeitem in topo["edge"].values():
                    for node in edgeitem.keys():
                        topo = topodict[node]
                        poll = topo["poll"] = topo["poll"] - 1
                        if poll == 0:
                            topology.append(topo)

            # splice reroutes
            index = len(topology) - 1
            while index >= 0:
                topo = topology[index]
                node = topo["node"]
                if isinstance(node, NodeReroute):
                    del topology[index]
                    prededge = topo["pred"]
                    if prededge:
                        del prededge[node]
                        for edgeitem in topo["edge"].values():
                            for node, sockets in edgeitem.items():
                                prededge[node].extend(sockets)
                index -= 1

            state = self.state__internal__
            flags = {name: item.flag for name, item in state.items()}
            state.clear()

            # Reset unlinked input states and cached data
            for topo in topology:
                for input_ in topo["node"].inputs:
                    if not input_.is_linked:
                        input_.error = ""
                        input_["data_key"] = ""
                        if input_.connection_id:
                            flags[node.name] = True
                            input_["connection_id"] = ""
                            input_.mode = 'VALUE'
                                

            # rebuild state and validate input sockets
            for topo in topology:
                item = state.add()
                deps = item.deps
                name = topo["node"].name
                item.name = name
                item.flag = flags.get(name, True)
                for output, edgeitem in topo["edge"].items():
                    key = output.id
                    for node, inputs in edgeitem.items():
                        name = node.name
                        if name not in deps:
                            deps.add().name = name
                        for input_ in inputs:
                            if input_.connection_id != key:
                                flags[name] = True
                                input_["connection_id"] = key
                                if input_.validate(output):
                                    input_.error = ""
                                    input_.mode = 'LABEL'
                                    input_["data_key"] = key
                                else:
                                    input_.error = "Invalid"
                                    input_.mode = 'VALUE'
                                    input_["data_key"] = ""

            self.evaluate()


class RBFDriverNodeSubtree(RBFDriverNodeTree):

    owner: PointerProperty(
        type=NodeTree,
        options={'HIDDEN'}
        )


class RBFDriverNodeTreeMain(RBFDriverNodeTree, NodeTree):
    bl_idname = 'RBFDriverNodeTreeMain'
    bl_label = "RBF Driver"






def tag(socket: RBFDriverNodeSocket, evaluation: Optional[Set[RBFDriverNode]]=set()) -> None:
    if socket.is_output:
        for socket in socket.edge():
            if socket.data.cache.pop(socket.id, None) is not None:
                tag(socket, evaluation)
    else:
        node = socket.node
        if isinstance(node, RBFDriverNode):
            if not len(node.outputs):
                evaluation.add(node)
            else:
                for socket in node.dependencies(socket):
                    if socket.data.cache.pop(socket.id, None) is not None:
                        tag(socket, evaluation)
    while evaluation:
        evaluation.pop().evaluate()


def cache(getdefault: Callable[[RBFDriverNodeSocket], Any]) -> Callable[[RBFDriverNodeSocket], Any]:
    cache = {}
    @wraps(getdefault)
    def read(socket: RBFDriverNodeSocket) -> Any:
        key = socket.id
        if key in cache:
            data = cache[key]
        elif socket.is_output:
            node = socket.node
            data = None
            if isinstance(node, RBFDriverNode):
                data = cache[key] = node.compute(socket)
            elif isinstance(node, NodeGroupInput):
                tree = node.id_data.owner
                if tree:
                    for node in tree.nodes:
                        if isinstance(node, RBFDriverNodeGroup) and node.node_tree == tree:
                            id_ = socket.identifier
                            res = next((x for x in node.inputs if x.identifier == id_), None)
                            if res:
                                data = cache[key] = res.data()
            if data is None:
                data = cache[key] = getdefault()
        else:
            output = next((socket.edge()), None)
            data = cache[key] = getdefault() if output is None else output.data()
        return data
    read.cache = cache
    return read


class MyClass:

    @cache
    def data(self):
        return self.value
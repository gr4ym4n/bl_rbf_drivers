
from operator import attrgetter
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple, Union
import numpy as np
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, FloatProperty, IntVectorProperty, StringProperty
from idprop.types import IDPropertyArray
from rbf_drivers.api.interfaces import ICollection
from .mixins import Collection, Identifiable
if TYPE_CHECKING:
    from bpy.types import Driver, FCurve, ID

#region PoseDataComponent
#--------------------------------------------------------------------------------------------------

def pose_data_component_index(component: 'PoseDataComponent',
                              container: Optional['PoseDataContainer']=None) -> int:
    if container is None: container = component.data
    return next(i for i, x in container.items__internal__ if x == component)


def pose_data_component_value(component: 'PoseDataComponent') -> float:
    value = None
    if component.is_id_property:
        try:
            value = component.id.path_resolve(component.value_path)
        except ValueError: pass
    return value if isinstance(value, float) else component.get("value", 0.0)


class PoseDataComponent(PropertyGroup):

    @property
    def array_index(self) -> int:
        return pose_data_component_index(self)

    @property
    def data_path(self) -> str:
        return self.data.data_path

    @property
    def data(self) -> 'PoseDataContainer':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    @property
    def id_type(self) -> Optional[str]:
        if self.is_id_property:
            return self.id_data.type

    @property
    def id(self) -> Optional['ID']:
        if self.is_id_property:
            return self.id_data.data

    @property
    def is_id_property(self) -> bool:
        return self.data.is_id_property

    @property
    def id_property_name(self) -> Optional[str]:
        container = self.data
        if container.is_id_property:
            return container.id_property_name

    value: FloatProperty(
        name="Value",
        get=pose_data_component_value,
        options=set()
        )

    @property
    def value_path(self) -> str:
        data = self.data
        path = f'{data.data_path}[{pose_data_component_index(self, data)}]'
        return path if data.is_id_property else f'{path}.value'

#endregion PoseDataComponent

#region PoseDataContainer
#--------------------------------------------------------------------------------------------------

def pose_data_container_id_property_name(container: 'PoseDataContainer') -> str:
    return container.get("id_property_name", "")


def pose_data_container_name(container: 'PoseDataContainer') -> str:
    return container.get("name", "")


def pose_data_container_name_set(container: 'PoseDataContainer', value: str) -> None:
    raise AttributeError(f'{container.__class__.__name__}.name is read-only')


class PoseDataContainer(PropertyGroup):

    items__internal__: CollectionProperty(
        type=PoseDataComponent,
        options={'HIDDEN'}
        )

    shape__internal__: IntVectorProperty(
        size=2,
        default=(0, -1),
        options={'HIDDEN'}
        )

    @property
    def data_group(self) -> 'PoseDataGroup':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    @property
    def data_path(self) -> str:
        return f'["{self.property_name}"]'

    id_property_name: StringProperty(
        name="Key",
        get=pose_data_container_id_property_name,
        options=set()
        )

    @property
    def id(self) -> Optional['ID']:
        if self.is_id_property:
            return self.id_data.data

    @property
    def is_id_property(self) -> bool:
        return bool(self.id_property_name)

    name: StringProperty(
        name="Name",
        description="Unique pose data container name (read-only)",
        get=pose_data_container_name,
        set=pose_data_container_name_set,
        options=set()
        )

    @property
    def shape(self) -> Union[Tuple[int], Tuple[int, int]]:
        shape = self.shape__internal__
        return (shape[0],) if shape[1] == -1 else tuple(shape)

    @property
    def size(self) -> int:
        return len(self.items__internal__)

    def __len__(self) -> int:
        return self.shape__internal__[0]

    def __getitem__(self,
                    key: Union[int, slice, Tuple[Union[int, slice], Tuple[int, slice]]]
                    ) -> Union[PoseDataComponent, List[PoseDataComponent]]:
        items = self.items__internal__
        index = np.arange(len(items)).reshape(self.shape)[key]
        return items[index] if isinstance(index, int) else [items[i] for i in index.flat]

#endregion PoseDataContainer

#region PoseDataGroup
#--------------------------------------------------------------------------------------------------

class PoseDataGroup(Collection[PoseDataContainer], PropertyGroup):

    internal__: CollectionProperty(
        type=PoseDataContainer,
        options={'HIDDEN'}
        )

#endregion PoseDataGroup

#region Utilities
#--------------------------------------------------------------------------------------------------

def pose_data_container_to_array(container: PoseDataContainer) -> np.ndarray:
    items: ICollection[PoseDataComponent] = container.items__internal__
    if container.is_id_property:
        value = container.id.get(container.id_property_name)
        count = len(items)
        if isinstance(value, IDPropertyArray) and len(value) == count:
            return np.array(value, dtype=float).reshape(container.shape)
    array = np.empty(count, dtype=np.float)
    items.foreach_get("value", array)


# def pose_data_container_create(group: PoseDataGroup,
#                                owner: Identifiable,
#                                name: str,
#                                data: Optional[Union[Sequence[float],
#                                                     Sequence[Sequence[float]]]]=None,
#                                id_property: Optional[Union[str, bool]]=False) -> PoseDataContainer:
#     container = group.internal__.add()
#     container["name"] = name
#     if id_property:
#         if not isinstance(id_property, str):
#             id_property = f'rbf_{owner.__class__.__name__.lower()}_{owner.identifier}_{name}'
#         container["id_property_name"] = id_property
#     if data is not None:
#         pose_data_container_update(container, data)
#     return container


def pose_data_group_remove(group: PoseDataGroup, name: str) -> None:
    container = group.get(name)
    if container:
        pose_data_container_delete(container)


def pose_data_group_delete(group: PoseDataGroup) -> None:
    for name in group.keys():
        pose_data_group_remove(group, name)


def pose_data_container_delete(container: PoseDataContainer) -> None:
    id_ = container.id
    try:
        del id_[container.key]
    except KeyError: pass
    animdata = id_.animation_data
    if animdata:
        path = container.data_path
        for fcurve in reversed(list(animdata.drivers)):
            if fcurve.data_path == path:
                animdata.drivers.remove(fcurve)
    containers: ICollection[PoseDataContainer] = container.group.internal__
    containers.remove(containers.find(container.name))


def pose_data_container_append(container: PoseDataContainer,
                               data: Union[float, Sequence[float], Sequence[Sequence[float]]],
                               axis: Optional[int]=0) -> None:
    array = pose_data_container_to_array(container)
    pose_data_container_update(container, np.append(array, data, axis=axis))


def pose_data_container_remove(container: PoseDataContainer,
                               index: int,
                               remove_driver: Optional[bool]=False) -> None:
    component = container[index]
    if remove_driver:
        fcurve = pose_data_component_fcurve(component)
        if fcurve:
            fcurve.id_data.animation_data.drivers.remove(fcurve)
    container.items__internal__.remove(index)


def pose_data_container_update(container: PoseDataContainer,
                               *args: Union[Tuple,
                                            Tuple[Union[Sequence[float],
                                                        Sequence[Sequence[float]]]],
                                            Tuple[int, Union[float, Sequence[float]]],
                                            Tuple[slice, Union[Sequence[float],
                                                               Sequence[Sequence[float]]]],
                                            Tuple[Tuple[int, int], float],
                                            Tuple[Tuple[int, slice], Sequence[float]],
                                            Tuple[Tuple[slice, int], float],
                                            Tuple[Tuple[slice, slice], Sequence[float]]]) -> None:
    items = container.items__internal__
    if not args:
        if container.is_id_property:
            container.id[container.id_property_name] = list(map(attrgetter("value"), items))
    elif len(args) == 1:
        array = np.asarray(args[0], dtype=float)
        shape = array.shape
        items: ICollection[PoseDataComponent] = container.items__internal__
        if len(items):
            count = array.size
            while len(items) < count: items.add()
            while len(items) > count: items.remove(-1)
        else:
            for _ in range(array.size):
                items.add()
        container.shape__internal__ = (shape[0], shape[1] if len(shape) else -1)
        data = array.flatten()
        items.foreach_set("value", data)
        # for item, value in zip(items, array.flat):
        #     item["value"] = value
        if container.is_id_property:
            container.id[container.id_property_name] = data
    else:
        array = pose_data_container_to_array(container)
        array[args[0]] = args[1]
        pose_data_container_update(container, array)


def pose_data_component_fcurve(component: PoseDataComponent,
                               ensure: Optional[bool]=False) -> Optional['FCurve']:
    fcurve = None
    animdata = component.id.animation_data
    if animdata is None:
        if ensure:
            drivers = component.id.animation_data_create().drivers
            fcurve = drivers.new(component.data_path, index=component.array_index)
    else:
        fcurve = animdata.drivers.find(component.data_path, index=component.array_index)
        if fcurve is None and ensure:
            fcurve = animdata.drivers.new(component.data_path, index=component.array_index)
    return fcurve


def pose_data_component_driver(component: PoseDataComponent,
                               ensure: Optional[bool]=False,
                               clear_variables: Optional[bool]=False) -> Optional['Driver']:
    fcurve = component.fcurve(ensure)
    if fcurve:
        driver = fcurve.driver
        if clear_variables:
            variables = fcurve.driver.variables
            while len(variables):
                variables.remove(variables[-1])
        return driver


#endregion Utilities
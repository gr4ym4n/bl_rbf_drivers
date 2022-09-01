
from typing import TYPE_CHECKING, Optional, Set, Tuple, Union
from ..app.utils import DataFrame, idprop_array, idprop_read, idprop_update
from .inputs import pose_weights as input_pose_weights
if TYPE_CHECKING:
    from ..api.driver import RBFDriver


class pose_influences(DataFrame('RBFDriver')):

    def __init__(self, driver: 'RBFDriver') -> None:
        data = idprop_array([1.0] * len(driver.poses), f'driver_{driver.identifier}_poseinfluence')
        vals = idprop_read(self.id, data)
        if vals:
            data["value"] = vals
        self.data = data
        idprop_update(self.id, data)

    def append(self) -> None:
        pass

    def move(self, from_index: int, to_index: int) -> None:
        data = self.data
        vals = idprop_read(data) or data["value"].tolist()
        vals.insert(to_index, vals.pop(from_index))
        data["value"] = vals
        idprop_update(self.id, data)

    def remove(self, index: int) -> None:
        pass

    def update(self) -> None:
        pass


class pose_weights(DataFrame['RBFDriver']):

    def __init__(self, driver: 'RBFDriver') -> None:
        self.avg = idprop_array([0.0] * len(driver.poses), f'driver_{driver.identifier}_poseweights')
        self.sum = idprop_array([0.0], f'driver_{driver.identifier}_poseweights_sum')
        id = driver.id_data.data
        idprop_update(id, self.avg)
        idprop_update(id, self.sum)

    def append(self) -> None:
        pass

    def move(self, from_index: int, to_index: int) -> None:
        # TODO move fcurves and leave drivers as is
        pass

    def update(self, index: Optional[int]=None) -> None:
        if index is None:
            self.__init__(self.owner)
            pose_weights_normalized(self.owner).update()
        else:
            pass

    def remove(self, index: int) -> None:
        pass


class pose_weights_normalized(DataFrame['RBFDriver']):

    def __init__(self, driver: 'RBFDriver') -> None:
        self.out = idprop_array([0.0] * len(driver.poses), f'driver_{driver.identifier}_poseweights_normalized')
        idprop_update(id, self.out)

    def append(self) -> None:
        pass

    def remove(self, index: int) -> None:
        pass

    def update(self) -> None:
        pass


```mermaid
graph LR;
    subgraph Output
        subgraph input_weight_manager
        Drivers(("Driver(s)"))
        FCurves(("FCurve(s)"))
        end
    end
    subgraph Hidden
        subgraph input_name_manager
        event_value{{"event.value"}}
        input_name_define[[input_name_define]]
        input_name_create[[input_name_create]]
        end
        subgraph input_radii_manager
        InputPoseRadiiInitializedEvent --> FCurves
        InputPoseRadiusUpdatedEvent .-> FCurves
        end
        subgraph input_distance_matrix
        InputDistanceMatrixInitializedEvent --> InputPoseRadiiInitializedEvent
        InputDistanceMatrixUpdatedEvent .-> InputPoseRadiusUpdatedEvent
        end
        subgraph input_data_manager
        InputDataInitializedEvent --> InputDistanceMatrixInitializedEvent
        InputDataUpdatedEvent .-> InputDistanceMatrixUpdatedEvent
        end
        subgraph input_manager
        InputInitializedEvent-->InputDataInitializedEvent
        InputSamplesUpdatedEvent-->InputDataUpdatedEvent
        InputSamplesUpdatedEvent.->|"PoseNewEvent|PoseRemovedEvent"|InputDataUpdatedEvent
        InputSourcesUpdatedEvent-->Drivers
        end
    end
    subgraph Input
        subgraph input_sample
        InputSampleUpdateEvent-->InputSamplesUpdatedEvent
        end
        subgraph input_target
        InputTargetBoneTargetUpdateEvent --> InputSourcesUpdatedEvent;
        InputTargetBoneTargetUpdateEvent -->|"event.input.type.endswith('DIFF') and not event.input.name_is_user_defined"|input_name_create;
        InputTargetDataPathUpdateEvent --> InputSourcesUpdatedEvent;
        InputTargetObjectUpdateEvent --> InputSourcesUpdatedEvent;
        InputTargetObjectUpdateEvent --> |"event.input.type in {'USER_DEF', 'SHAPE_KEY'} and not event.input.name_is_user_defined"|input_name_create;
        InputTargetIDTypeUpdateEvent --> InputSourcesUpdatedEvent;
        InputTargetRotationModeUpdateEvent --> InputSourcesUpdatedEvent;
        InputTargetTransformSpaceUpdateEvent --> InputSourcesUpdatedEvent;
        InputTargetTransformTypeUpdateEvent --> InputSourcesUpdatedEvent;
        end
        subgraph input_variable
        InputVariableNameUpdateEvent-->InputSourcesUpdatedEvent;
        InputVariableTypeUpdateEvent-->InputSourcesUpdatedEvent;
        end
        subgraph input_variables
        InputVariableNewEvent --> InputSourcesUpdatedEvent & InputSamplesUpdatedEvent;
        InputVariableRemovedEvent --> InputSourcesUpdatedEvent & InputSamplesUpdatedEvent;
        end
        subgraph input
        InputBoneTargetUpdateEvent --> InputSourcesUpdatedEvent;
        InputObjectUpdateEvent --> InputSourcesUpdatedEvent;
        InputNameUpdateEvent --> event_value -->|True|input_name_define
        InputNameUpdateEvent --> event_value -->|False|input_name_create
        InputRotationAxisUpdateEvent --> InputSourcesUpdatedEvent & InputSamplesUpdatedEvent;
        InputRotationModeUpdateEvent --> InputSourcesUpdatedEvent & InputSamplesUpdatedEvent;
        InputTransformSpaceUpdateEvent --> InputSourcesUpdatedEvent
        end
        subgraph inputs
        InputNewEvent --> InputInitializedEvent;
        end
        subgraph poses
        PoseNewEvent --> InputSamplesUpdatedEvent;
        PoseRemovedEvent --> InputSamplesUpdatedEvent;
        end
    end
```
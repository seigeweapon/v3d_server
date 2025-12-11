from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar, Iterable, Mapping, Optional, Text, Union

DESCRIPTOR: _descriptor.FileDescriptor

class V3DTrainWorkflowProgress(_message.Message):
    __slots__ = ["calibration_done", "frame_extraction_done", "frame_number", "frame_start", "frames_done_map_coded", "frames_done_total", "gop_size"]
    CALIBRATION_DONE_FIELD_NUMBER: ClassVar[int]
    FRAMES_DONE_MAP_CODED_FIELD_NUMBER: ClassVar[int]
    FRAMES_DONE_TOTAL_FIELD_NUMBER: ClassVar[int]
    FRAME_EXTRACTION_DONE_FIELD_NUMBER: ClassVar[int]
    FRAME_NUMBER_FIELD_NUMBER: ClassVar[int]
    FRAME_START_FIELD_NUMBER: ClassVar[int]
    GOP_SIZE_FIELD_NUMBER: ClassVar[int]
    calibration_done: bool
    frame_extraction_done: bool
    frame_number: int
    frame_start: int
    frames_done_map_coded: _containers.RepeatedScalarFieldContainer[int]
    frames_done_total: int
    gop_size: int
    def __init__(self, frame_extraction_done: bool = ..., calibration_done: bool = ..., frame_start: Optional[int] = ..., frame_number: Optional[int] = ..., gop_size: Optional[int] = ..., frames_done_total: Optional[int] = ..., frames_done_map_coded: Optional[Iterable[int]] = ...) -> None: ...

class V3DTrainWorkflowRequest(_message.Message):
    __slots__ = ["background_url", "calib_url", "camera_number", "debug", "do_devignetting", "flow_url", "frame_number", "frame_start", "frame_url", "gop_size", "mask_url", "matting_mode", "op_versions", "output_url", "render_views_url", "tos", "training_configs", "workspace_url"]
    class V3dTosInfo(_message.Message):
        __slots__ = ["ak", "endpoint", "region", "sk"]
        AK_FIELD_NUMBER: ClassVar[int]
        ENDPOINT_FIELD_NUMBER: ClassVar[int]
        REGION_FIELD_NUMBER: ClassVar[int]
        SK_FIELD_NUMBER: ClassVar[int]
        ak: str
        endpoint: str
        region: str
        sk: str
        def __init__(self, ak: Optional[str] = ..., sk: Optional[str] = ..., endpoint: Optional[str] = ..., region: Optional[str] = ...) -> None: ...
    BACKGROUND_URL_FIELD_NUMBER: ClassVar[int]
    CALIB_URL_FIELD_NUMBER: ClassVar[int]
    CAMERA_NUMBER_FIELD_NUMBER: ClassVar[int]
    DEBUG_FIELD_NUMBER: ClassVar[int]
    DO_DEVIGNETTING_FIELD_NUMBER: ClassVar[int]
    FLOW_URL_FIELD_NUMBER: ClassVar[int]
    FRAME_NUMBER_FIELD_NUMBER: ClassVar[int]
    FRAME_START_FIELD_NUMBER: ClassVar[int]
    FRAME_URL_FIELD_NUMBER: ClassVar[int]
    GOP_SIZE_FIELD_NUMBER: ClassVar[int]
    MASK_URL_FIELD_NUMBER: ClassVar[int]
    MATTING_MODE_FIELD_NUMBER: ClassVar[int]
    OP_VERSIONS_FIELD_NUMBER: ClassVar[int]
    OUTPUT_URL_FIELD_NUMBER: ClassVar[int]
    RENDER_VIEWS_URL_FIELD_NUMBER: ClassVar[int]
    TOS_FIELD_NUMBER: ClassVar[int]
    TRAINING_CONFIGS_FIELD_NUMBER: ClassVar[int]
    WORKSPACE_URL_FIELD_NUMBER: ClassVar[int]
    background_url: str
    calib_url: str
    camera_number: int
    debug: bool
    do_devignetting: bool
    flow_url: str
    frame_number: int
    frame_start: int
    frame_url: str
    gop_size: int
    mask_url: str
    matting_mode: str
    op_versions: str
    output_url: str
    render_views_url: str
    tos: V3DTrainWorkflowRequest.V3dTosInfo
    training_configs: str
    workspace_url: str
    def __init__(self, tos: Optional[Union[V3DTrainWorkflowRequest.V3dTosInfo, Mapping]] = ..., workspace_url: Optional[str] = ..., frame_url: Optional[str] = ..., calib_url: Optional[str] = ..., background_url: Optional[str] = ..., mask_url: Optional[str] = ..., flow_url: Optional[str] = ..., output_url: Optional[str] = ..., gop_size: Optional[int] = ..., frame_start: Optional[int] = ..., frame_number: Optional[int] = ..., camera_number: Optional[int] = ..., matting_mode: Optional[str] = ..., training_configs: Optional[str] = ..., do_devignetting: bool = ..., debug: bool = ..., op_versions: Optional[str] = ..., render_views_url: Optional[str] = ...) -> None: ...

class V3DTrainWorkflowResponse(_message.Message):
    __slots__ = ["msg"]
    MSG_FIELD_NUMBER: ClassVar[int]
    msg: str
    def __init__(self, msg: Optional[str] = ...) -> None: ...

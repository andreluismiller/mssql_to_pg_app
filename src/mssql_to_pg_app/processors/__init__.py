from .full_reload import FullReloadProcessor
from .incremental import IdIncrementalProcessor, TimestampIncrementalProcessor
PROCESSORS = {
    "full_reload": FullReloadProcessor,
    "id_incremental": IdIncrementalProcessor,
    "timestamp_incremental": TimestampIncrementalProcessor,
}

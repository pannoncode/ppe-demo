"""YOLOX-s config for the Colab smoke test (notebooks/00_yolox_smoke_test.ipynb).

pixeltable-yolox takes a config class as `-c module:Class` (no Megvii-style exp file).
Paths and epoch count come from environment variables so the notebook controls them.
Run from the repo root with `PYTHONPATH=exps yolox train -c smoke_yolox_s:SmokeYoloxS ...`.
"""

import os

from yolox.config import YoloxS


class SmokeYoloxS(YoloxS):
    def __init__(self) -> None:
        super().__init__()
        self.name = "smoke_yolox_s"
        # person, head_hairnet, head_cap, head_bare (configs/datasets.yaml -> models.head)
        self.num_classes = 4
        self.data_dir = os.environ["PPE_SMOKE_DATA_DIR"]
        self.output_dir = os.environ["PPE_SMOKE_OUTPUT_DIR"]
        self.max_epoch = int(os.environ.get("PPE_SMOKE_MAX_EPOCH", "1"))
        self.warmup_epochs = 1
        self.no_aug_epochs = 1
        self.eval_interval = 1
        self.print_interval = 5
        self.data_num_workers = 2
        self.save_history_ckpt = False

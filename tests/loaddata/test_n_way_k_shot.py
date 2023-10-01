import os
import random
from pathlib import Path

import numpy as np
import pytest
import torch
from torchvision import transforms
from yacs.config import CfgNode as CN

from kale.loaddata.n_way_k_shot import NWayKShotDataset
from kale.utils.download import download_file_by_url

root_dir = os.path.dirname(os.path.dirname(os.getcwd()))
url = "https://github.com/pykale/data/raw/main/images/omniglot/demo_data.zip"
modes = ["train", "val", "test"]


@pytest.fixture(scope="module")
def testing_cfg(download_path):
    cfg = CN()
    cfg.DATASET = CN()
    cfg.DATASET.ROOT = root_dir + "/" + download_path + "/demo_data/"
    yield cfg


@pytest.mark.parametrize("mode", modes)
def test_n_way_k_shot(mode, testing_cfg):
    cfg = testing_cfg
    output_dir = str(Path(cfg.DATASET.ROOT).parent.absolute())
    download_file_by_url(url=url, output_directory=output_dir, output_file_name="demo_data.zip", file_format="zip")
    transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()])
    k_shot = random.randint(1, 10)
    query_samples = random.randint(1, 10)
    n_way = random.randint(1, 10)
    dataset = NWayKShotDataset(
        path=cfg.DATASET.ROOT, mode=mode, k_shot=k_shot, query_samples=query_samples, transform=transform,
    )
    assert len(dataset) == len(dataset.classes)
    assert isinstance(dataset._get_idx(0), np.ndarray)
    assert isinstance(dataset._sample_data(dataset._get_idx(0)), list)
    assert isinstance(dataset._sample_data(dataset._get_idx(0))[0], torch.Tensor)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=n_way, shuffle=True, num_workers=30, drop_last=True)
    batch = next(iter(dataloader))
    assert isinstance(batch[0], torch.Tensor)
    assert isinstance(batch[1], torch.Tensor)
    assert batch[0].shape == (n_way, k_shot + query_samples, 3, 224, 224)
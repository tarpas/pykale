import warnings

import pytorch_lightning as pl
import torch
from config import get_cfg_defaults
from model import GripNetLinkPrediction
from utils import get_all_dataloader, load_data, setup_supervertex

import kale.utils.seed as seed
from kale.embed.gripnet import GripNet
from kale.prepdata.supergraph_construct import SuperEdge, SuperGraph, SuperVertex

warnings.filterwarnings(action="ignore")


# ---- setup device ----
device = "cuda" if torch.cuda.is_available() else "cpu"
device = torch.device(device)

# ---- setup configs ----
cfg = get_cfg_defaults()
cfg.freeze()
seed.set_seed(cfg.SOLVER.SEED)

# ---- setup dataset and data loader ----
data = load_data(cfg.DATASET)
dataloader_train, dataloader_test = get_all_dataloader(data)

# ---- setup supergraph ----
# create gene and drug supervertex
supervertex_gene = SuperVertex("gene", data.g_feat, data.gg_edge_index)
supervertex_drug = SuperVertex("drug", data.d_feat, data.train_idx, data.train_et)

# create superedge form gene to drug supervertex
superedge = SuperEdge("gene", "drug", data.gd_edge_index)

setting_gene = setup_supervertex(cfg.GRIPN_SV1)
setting_drug = setup_supervertex(cfg.GRIPN_SV2)

# construct supergraph
supergraph = SuperGraph([supervertex_gene, supervertex_drug], [superedge])
supergraph.set_supergraph_para_setting([setting_gene, setting_drug])

# ---- setup model and trainer ----
model = GripNetLinkPrediction(supergraph, cfg.SOLVER)
print(model)

trainer = pl.Trainer(
    default_root_dir=cfg.OUTPUT_DIR, max_epochs=cfg.SOLVER.MAX_EPOCHS, log_every_n_steps=cfg.SOLVER.LOG_EVERY_N_STEPS
)

# ---- train and test ----
trainer.fit(model, dataloader_train)
test_result = trainer.test(model, dataloader_train)

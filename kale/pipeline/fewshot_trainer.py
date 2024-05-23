# ==============================================================================
# Author: Wenrui Fan, winslow.fan@outlook.com
# ==============================================================================

"""ProtoNet Trainer (pipelines)

This module contains the ProtoNet trainer class and related functions. It trains a prototypical network model for few-shot learning problems under N-way-K-shot settings.

This is a `PyTorch Lightning <https://github.com/Lightning-AI/lightning>` version of the original implementation <https://github.com/jakesnell/prototypical-networks> of Prototypical Networks for Few-shot Learning <https://arxiv.org/abs/1703.05175>.
"""

from typing import Any

import pytorch_lightning as pl
import torch

from kale.predict.losses import protonet_loss


class ProtoNetTrainer(pl.LightningModule):
    """ProtoNet trainer class
    This class trains a ProtoNet model for few-shot learning problems under N-way-K-shot settings.
    It uses `pl.LightningModule` class of `PyTorch Lightning` to standardize the workflow.
    Updating other modules except `kale.predict.losses.protonet_loss` and `kale.embed.image_cnn` will not affect this trainer.

    Args:
        net (torch.nn.Module): A feature extractor without any task-specific heads. It outputs a 1-D feature vector.
        train_num_classes (int): Number of classes in training. It could be different from N under N-way-K-shot settings in ProtoNet. Default: 30.
        train_num_support_samples (int): Number of samples per class in the support set in training. It corresponds to K under N-way-K-shot settings. Default: 5.
        train_num_query_samples (int): Number of samples per class in the query set in training. Default: 15.
        val_num_classes (int): Number of classes in validation and testing. It corresponds to N under N-way-K-shot settings. Default: 5.
        val_num_support_samples (int): Number of samples per class in the support set in validation and testing. It corresponds to K under N-way-K-shot settings. Default: 5.
        val_num_query_samples (int): Number of samples per class in the query set in validation and testing. Default: 15.
        devices (str): Devices used for training. Default: "cuda".
        optimizer (str): Optimizer used for training. Default: "SGD".
        lr (float): Learning rate. Default: 0.001.
    """

    def __init__(
        self,
        net: torch.nn.Module,
        train_num_classes: int = 30,
        train_num_support_samples: int = 5,
        train_num_query_samples: int = 15,
        val_num_classes: int = 5,
        val_num_support_samples: int = 5,
        val_num_query_samples: int = 15,
        devices: str = "cuda",
        optimizer: str = "SGD",
        lr: float = 0.001,
    ) -> None:
        super().__init__()

        self.train_num_classes = train_num_classes
        self.train_num_support_samples = train_num_support_samples
        self.train_num_query_samples = train_num_query_samples
        self.val_num_classes = val_num_classes
        self.val_num_support_samples = val_num_support_samples
        self.val_num_query_samples = val_num_query_samples
        self.devices = devices
        self.optimizer = optimizer
        self.lr = lr

        # model
        self.model = net

        # loss
        self.loss_train = protonet_loss(
            num_classes=train_num_classes, num_query_samples=train_num_query_samples, device=self.devices
        )
        self.loss_val = protonet_loss(
            num_classes=val_num_classes, num_query_samples=val_num_query_samples, device=self.devices
        )

    def forward(self, x, num_support_samples, num_classes) -> torch.Tensor:
        x = x.to(self.devices)
        supports = x[0][0:num_support_samples]
        queries = x[0][num_support_samples:]
        for image in x[1:]:
            supports = torch.cat((supports, image[0:num_support_samples]), dim=0)
            queries = torch.cat((queries, image[num_support_samples:]), dim=0)
        feature_support = self.model(supports).reshape(num_classes, num_support_samples, -1)
        feature_query = self.model(queries)
        return feature_support, feature_query

    def compute_loss(self, feature_support, feature_query, mode="train") -> tuple:
        """
        Compute loss and accuracy. Here we use the same loss function for both training and validation, which is related to Euclidean distance.

        Args:
            feature_support (torch.Tensor): Support features.
            feature_query (torch.Tensor): Query features.
            mode (str): Mode of the trainer, "train", "val" or "test". Default: "train".

        Returns:
            loss (torch.Tensor): Loss value.
            return_dict (dict): Dictionary of loss and accuracy.
        """
        loss, acc = eval(f"self.loss_{mode}")(feature_support, feature_query)
        return_dict = {"{}_loss".format(mode): loss.item(), "{}_acc".format(mode): acc}
        return loss, return_dict

    def training_step(self, batch: Any, batch_idx: int) -> torch.Tensor:
        """
        Training step. Compute loss and accuracy, and log them by self.log_dict. For training, log on each step and each
         epoch. For validation and testing, only log on each epoch. This way can avoid using on_training_epoch_end()
         and on_validation_epoch_end().
        """
        images, _ = batch
        feature_support, feature_query = self.forward(images, self.train_num_support_samples, self.train_num_classes)
        loss, log_metrics = self.compute_loss(feature_support, feature_query, mode="train")
        self.log_dict(log_metrics, on_step=True, on_epoch=True, prog_bar=True, logger=True)
        return loss

    def validation_step(self, batch: Any, batch_idx: int) -> None:
        """Compute and return the validation loss and log_metrics on one step."""
        images, _ = batch
        feature_support, feature_query = self.forward(images, self.val_num_support_samples, self.val_num_classes)
        _, log_metrics = self.compute_loss(feature_support, feature_query, mode="val")
        self.log_dict(log_metrics, on_step=False, on_epoch=True, prog_bar=True, logger=True)

    def test_step(self, batch: Any, batch_idx: int) -> None:
        """Compute and return the test loss and log_metrics on one step."""
        images, _ = batch
        feature_support, feature_query = self.forward(images, self.val_num_support_samples, self.val_num_classes)
        _, log_metrics = self.compute_loss(feature_support, feature_query, mode="val")
        self.log_dict(log_metrics, on_step=False, on_epoch=True, prog_bar=True, logger=True)

    def configure_optimizers(self) -> torch.optim.Optimizer:
        """
        Configure optimizer for training. Can be modified to support different optimizers from torch.optim.
        """
        optimizer = eval(f"torch.optim.{self.optimizer}")(self.model.parameters(), lr=self.lr)
        return optimizer

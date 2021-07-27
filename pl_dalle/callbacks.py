#borrowed from https://github.com/PyTorchLightning/Lightning-Bolts/blob/master/pl_bolts/callbacks/vision/image_generation.py#L15-L97
from typing import Any, Dict, List, Optional, Tuple

import torch
import pytorch_lightning as pl
from pytorch_lightning import Callback, LightningModule, Trainer

from pl_bolts.utils import _TORCHVISION_AVAILABLE
from pl_bolts.utils.warnings import warn_missing_pkg
from pytorch_lightning.utilities.types import STEP_OUTPUT
from pytorch_lightning.utilities.distributed import rank_zero_only
import torch.nn.functional as F

if _TORCHVISION_AVAILABLE:
    import torchvision
else:  # pragma: no cover
    warn_missing_pkg("torchvision")


class VAEImageSampler(Callback):
    
    def __init__(
        self,
        every_n_steps: int = 1000,
        nrow: int = 8,
        padding: int = 2,
        normalize: bool = True,
        norm_range: Optional[Tuple[int, int]] = None,
        scale_each: bool = False,
        pad_value: int = 0,
    ) -> None:
        """
        Args:
            num_samples: Number of images displayed in the grid. Default: ``3``.
            nrow: Number of images displayed in each row of the grid.
                The final grid size is ``(B / nrow, nrow)``. Default: ``8``.
            padding: Amount of padding. Default: ``2``.
            normalize: If ``True``, shift the image to the range (0, 1),
                by the min and max values specified by :attr:`range`. Default: ``True``.
            norm_range: Tuple (min, max) where min and max are numbers,
                then these numbers are used to normalize the image. By default, min and max
                are computed from the tensor.
            scale_each: If ``True``, scale each image in the batch of
                images separately rather than the (min, max) over all images. Default: ``False``.
            pad_value: Value for the padded pixels. Default: ``0``.
        """
        if not _TORCHVISION_AVAILABLE:  # pragma: no cover
            raise ModuleNotFoundError("You want to use `torchvision` which is not installed yet.")

        super().__init__()
        self.every_n_steps = every_n_steps
        self.nrow = nrow
        self.padding = padding
        self.normalize = normalize
        self.norm_range = norm_range
        self.scale_each = scale_each
        self.pad_value = pad_value

    @rank_zero_only
    def on_train_batch_end(
        self,
        trainer: 'pl.Trainer',
        pl_module: 'pl.LightningModule',
        outputs: Optional[STEP_OUTPUT],
        batch: Any,
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Called when the train batch ends."""
        if trainer.global_step % self.every_n_steps == 0:
            
            x, _ = batch
            x = x.to(pl_module.device)
            with torch.no_grad():
                pl_module.eval()
                xrec, _ = pl_module(x)
                pl_module.train()   

            x_grid = torchvision.utils.make_grid(
                tensor=x,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )           
            xrec_grid = torchvision.utils.make_grid(
                tensor=xrec,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )    
            x_title = "train/input"
            trainer.logger.experiment.add_image(x_title, x_grid, global_step=trainer.global_step)
            xrec_title = "train/reconstruction"
            trainer.logger.experiment.add_image(xrec_title, xrec_grid, global_step=trainer.global_step)

    @rank_zero_only
    def on_validation_batch_end(
        self,
        trainer: 'pl.Trainer',
        pl_module: 'pl.LightningModule',
        outputs: Optional[STEP_OUTPUT],
        batch: Any,
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Called when the validation batch ends."""
        if trainer.global_step % self.every_n_steps == 0:
            x, _ = batch
            x = x.to(pl_module.device)
            with torch.no_grad():
                pl_module.eval()
                xrec, _ = pl_module(x)
                pl_module.train()   

            x_grid = torchvision.utils.make_grid(
                tensor=x,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )           
            xrec_grid = torchvision.utils.make_grid(
                tensor=xrec,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )    
            x_title = "val/input"
            trainer.logger.experiment.add_image(x_title, x_grid, global_step=trainer.global_step)
            xrec_title = "val/reconstruction"
            trainer.logger.experiment.add_image(xrec_title, xrec_grid, global_step=trainer.global_step)


class DalleGenerativeImageSampler(Callback):
    
    def __init__(
        self,
        every_n_steps: int = 1000,
        text_seq_len = 128,
        image_seq_len = 1024,
        nrow: int = 8,
        padding: int = 2,
        normalize: bool = True,
        norm_range: Optional[Tuple[int, int]] = None,
        scale_each: bool = False,
        pad_value: int = 0,
        tokenizer = None
    ) -> None:
        """
        Args:
            num_samples: Number of images displayed in the grid. Default: ``3``.
            nrow: Number of images displayed in each row of the grid.
                The final grid size is ``(B / nrow, nrow)``. Default: ``8``.
            padding: Amount of padding. Default: ``2``.
            normalize: If ``True``, shift the image to the range (0, 1),
                by the min and max values specified by :attr:`range`. Default: ``True``.
            norm_range: Tuple (min, max) where min and max are numbers,
                then these numbers are used to normalize the image. By default, min and max
                are computed from the tensor.
            scale_each: If ``True``, scale each image in the batch of
                images separately rather than the (min, max) over all images. Default: ``False``.
            pad_value: Value for the padded pixels. Default: ``0``.
        """
        if not _TORCHVISION_AVAILABLE:  # pragma: no cover
            raise ModuleNotFoundError("You want to use `torchvision` which is not installed yet.")

        super().__init__()
        self.every_n_steps = every_n_steps
        self.text_seq_len = text_seq_len
        self.image_seq_len = image_seq_len
        self.nrow = nrow
        self.padding = padding
        self.normalize = normalize
        self.norm_range = norm_range
        self.scale_each = scale_each
        self.pad_value = pad_value
        self.tokenizer = tokenizer

    @rank_zero_only
    def on_train_batch_end(
        self,
        trainer: 'pl.Trainer',
        pl_module: 'pl.LightningModule',
        outputs: Optional[STEP_OUTPUT],
        batch: Any,
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Called when the train batch ends."""
        if trainer.global_step % self.every_n_steps == 0:          
            text, x = batch
            sample_text = text[:1]
            token_list = sample_text.masked_select(sample_text != 0).tolist()
            decoded_text = self.tokenizer.decode(token_list)       
            text = text.to(pl_module.device)
            x = x.to(pl_module.device)       
            with torch.no_grad():
                pl_module.eval()
                #generate sample with image provided
                x_rec = pl_module.generate_images(text[:1], img = x[:1], filter_thres=0.9)  # topk sampling at 0.9

                #generate sample without image
                x_gen = pl_module.generate_images(text[:1], filter_thres=0.9)  # topk sampling at 0.9

                pl_module.train()  


            x_grid = torchvision.utils.make_grid(
                tensor=x,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )           
            xrec_grid = torchvision.utils.make_grid(
                tensor=x_rec,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )  
            xgen_grid = torchvision.utils.make_grid(
                tensor=x_gen,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )                
            text_title = "train/text"
            trainer.logger.experiment.add_text(text_title, decoded_text, global_step=trainer.global_step)
            x_title = "train/input"
            trainer.logger.experiment.add_image(x_title, x_grid, global_step=trainer.global_step)
            xrec_title = "train/half_reconstruction"
            trainer.logger.experiment.add_image(xrec_title, xrec_grid, global_step=trainer.global_step)
            xgen_title = "train/generation"
            trainer.logger.experiment.add_image(xgen_title, xgen_grid, global_step=trainer.global_step)

    @rank_zero_only
    def on_validation_batch_end(
        self,
        trainer: 'pl.Trainer',
        pl_module: 'pl.LightningModule',
        outputs: Optional[STEP_OUTPUT],
        batch: Any,
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Called when the validation batch ends."""
        if trainer.global_step % self.every_n_steps == 0:          
            text, x = batch
            sample_text = text[:1]
            token_list = sample_text.masked_select(sample_text != 0).tolist()
            decoded_text = self.tokenizer.decode(token_list)       
            text = text.to(pl_module.device)
            x = x.to(pl_module.device)       
            with torch.no_grad():
                pl_module.eval()
                #generate sample with image provided
                x_rec = pl_module.generate_images(text[:1], img = x[:1], filter_thres=0.9)  # topk sampling at 0.9

                #generate sample without image
                x_gen = pl_module.generate_images(text[:1], filter_thres=0.9)  # topk sampling at 0.9

                pl_module.train()  


            x_grid = torchvision.utils.make_grid(
                tensor=x,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )           
            xrec_grid = torchvision.utils.make_grid(
                tensor=x_rec,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )  
            xgen_grid = torchvision.utils.make_grid(
                tensor=x_gen,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )                
            text_title = "val/text"
            trainer.logger.experiment.add_text(text_title, decoded_text, global_step=trainer.global_step)
            x_title = "val/input"
            trainer.logger.experiment.add_image(x_title, x_grid, global_step=trainer.global_step)
            xrec_title = "val/half_reconstruction"
            trainer.logger.experiment.add_image(xrec_title, xrec_grid, global_step=trainer.global_step)
            xgen_title = "val/generation"
            trainer.logger.experiment.add_image(xgen_title, xgen_grid, global_step=trainer.global_step)



class DalleSimpleImageSampler(Callback):
    
    def __init__(
        self,
        every_n_steps: int = 1000,
        nrow: int = 8,
        padding: int = 2,
        normalize: bool = True,
        norm_range: Optional[Tuple[int, int]] = None,
        scale_each: bool = False,
        pad_value: int = 0,
        tokenizer = None
    ) -> None:
        """
        Args:
            num_samples: Number of images displayed in the grid. Default: ``3``.
            nrow: Number of images displayed in each row of the grid.
                The final grid size is ``(B / nrow, nrow)``. Default: ``8``.
            padding: Amount of padding. Default: ``2``.
            normalize: If ``True``, shift the image to the range (0, 1),
                by the min and max values specified by :attr:`range`. Default: ``True``.
            norm_range: Tuple (min, max) where min and max are numbers,
                then these numbers are used to normalize the image. By default, min and max
                are computed from the tensor.
            scale_each: If ``True``, scale each image in the batch of
                images separately rather than the (min, max) over all images. Default: ``False``.
            pad_value: Value for the padded pixels. Default: ``0``.
        """
        if not _TORCHVISION_AVAILABLE:  # pragma: no cover
            raise ModuleNotFoundError("You want to use `torchvision` which is not installed yet.")

        super().__init__()
        self.every_n_steps = every_n_steps
        self.nrow = nrow
        self.padding = padding
        self.normalize = normalize
        self.norm_range = norm_range
        self.scale_each = scale_each
        self.pad_value = pad_value
        self.tokenizer = tokenizer

    @rank_zero_only
    def on_train_batch_end(
        self,
        trainer: 'pl.Trainer',
        pl_module: 'pl.LightningModule',
        outputs: Optional[STEP_OUTPUT],
        batch: Any,
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Called when the train batch ends."""
        if trainer.global_step % self.every_n_steps == 0:          
            text, x = batch
            sample_text = text[:1]
            token_list = sample_text.masked_select(sample_text != 0).tolist()
            decoded_text = self.tokenizer.decode(token_list)
            print(decoded_text)       
            text = text.to(pl_module.device)
            x = x.to(pl_module.device)       
            with torch.no_grad():
                pl_module.eval()
                print('fuck')
                logits = pl_module(text, x)
                print('fuck')
                img_logits = logits[:, -pl_module.image_seq_len:].long()
                img_seq = torch.argmax(img_logits, dim = -1)
                img_seq -= pl_module.num_text_tokens  
                print('fuck')           
                x_rec = pl_module.vae.decode(img_seq, feed_seq=True)                

                pl_module.train()  


            x_grid = torchvision.utils.make_grid(
                tensor=x,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )           
            xrec_grid = torchvision.utils.make_grid(
                tensor=x_rec,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )  

            text_title = "train/text"
            trainer.logger.experiment.add_text(text_title, decoded_text, global_step=trainer.global_step)
            x_title = "train/input"
            trainer.logger.experiment.add_image(x_title, x_grid, global_step=trainer.global_step)
            xrec_title = "train/reconstruction"
            trainer.logger.experiment.add_image(xrec_title, xrec_grid, global_step=trainer.global_step)


    @rank_zero_only
    def on_validation_batch_end(
        self,
        trainer: 'pl.Trainer',
        pl_module: 'pl.LightningModule',
        outputs: Optional[STEP_OUTPUT],
        batch: Any,
        batch_idx: int,
        dataloader_idx: int,
    ) -> None:
        """Called when the validation batch ends."""
        if trainer.global_step % self.every_n_steps == 0:          
            text, x = batch
            sample_text = text[:1]
            token_list = sample_text.masked_select(sample_text != 0).tolist()
            decoded_text = self.tokenizer.decode(token_list)       
            text = text.to(pl_module.device)
            x = x.to(pl_module.device)       
            with torch.no_grad():
                pl_module.eval()
                logits = pl_module(text, x)
                img_logits = logits[:, -pl_module.image_seq_len:].long()
                img_seq = torch.argmax(img_logits, dim = -1)
                img_seq -= pl_module.num_text_tokens              
                x_rec = pl_module.vae.decode(img_seq, feed_seq=True)     


            x_grid = torchvision.utils.make_grid(
                tensor=x,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )           
            xrec_grid = torchvision.utils.make_grid(
                tensor=x_rec,
                nrow=self.nrow,
                padding=self.padding,
                normalize=self.normalize,
                value_range=self.norm_range,
                scale_each=self.scale_each,
                pad_value=self.pad_value,
            )  

            text_title = "val/text"
            trainer.logger.experiment.add_text(text_title, decoded_text, global_step=trainer.global_step)
            x_title = "val/input"
            trainer.logger.experiment.add_image(x_title, x_grid, global_step=trainer.global_step)
            xrec_title = "val/reconstruction"
            trainer.logger.experiment.add_image(xrec_title, xrec_grid, global_step=trainer.global_step)

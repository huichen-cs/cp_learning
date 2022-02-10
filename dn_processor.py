# You must import Comet before these modules: torch
# https://github.com/PyTorchLightning/pytorch-lightning/issues/5829.
import comet_ml
from time import gmtime, strftime
from cp_flatten import QuackConstants
from cp_image_data import QuackImageDataModule
from densenet import QuackDenseNet
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint, DeviceStatsMonitor, LearningRateMonitor
from pytorch_lightning.loggers import CometLogger
from ray_lightning import RayPlugin
from argparse import ArgumentParser, Namespace


def main(args: Namespace) -> None:
    data = QuackImageDataModule(args.data_dir, batch_size=args.batch_size, workers=args.num_workers)
    # Max value of static is from the ipv4 segments.
    model = QuackDenseNet()
    ray_plugin = RayPlugin(
        num_workers=args.ray_nodes,
        num_cpus_per_worker=1,
        use_gpu=False,
        find_unused_parameters=False
    )
    # API configuration for comet: https://www.comet.ml/docs/python-sdk/advanced/#python-configuration
    date_time = strftime("%d %b %Y %H:%M", gmtime())
    device_logger = DeviceStatsMonitor()
    if args.tune:
        trainer = Trainer.from_argparse_args(
            args, auto_scale_batch_size=True,
            plugins=[ray_plugin]
        )
        print('Ready for tuning...')
        trainer.tune(model, datamodule=data)
    else:
        comet_logger = CometLogger(
            save_dir=args.comet_storage,
            project_name="censored-planet",
            experiment_name=f'{args.exp_label}: {date_time}',
        )
        checkpoint_callback = ModelCheckpoint(
            monitor="val_loss",
            save_top_k=3,
            save_last=True
        )
        early_stopping_callback = EarlyStopping(
            monitor="val_loss",
            patience=10,
            stopping_threshold=250,
            check_finite=True,  # Stops training if the monitored metric becomes NaN or infinite.
        )
        trainer = Trainer.from_argparse_args(
            args,
            logger=comet_logger,
            callbacks=[early_stopping_callback, checkpoint_callback, device_logger],
            plugins=[ray_plugin]
        )
        print('Ready for training...')
        if args.checkpoint_path is None:
            trainer.fit(model, datamodule=data)
        else:
            trainer.fit(model, datamodule=data, ckpt_path=args.checkpoint_path)


if __name__ == '__main__':
    # Add arguments to make a more flexible cli tool.
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--data_dir', type=str, default='./data')
    arg_parser.add_argument('--batch_size', type=int, default=4)
    arg_parser.add_argument('--num_workers', type=int, default=0)
    arg_parser.add_argument('--tune', action='store_true', default=False)
    arg_parser.add_argument('--checkpoint_path', type=str)
    arg_parser.add_argument('--comet_storage', type=str, default='.')
    arg_parser.add_argument('--storage_path', type=str, default='./data/encoded')
    arg_parser.add_argument('--exp_label', type=str, default='autoencoder-train')
    arg_parser.add_argument('--ray_nodes', type=int, default=4)

    # add trainer arguments (gpus=x, precision=...)
    arg_parser = Trainer.add_argparse_args(arg_parser)
    arguments = arg_parser.parse_args()
    main(arguments)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import torch
from lib import (
        check_test_options,
        create_model,
        set_logger
        )
from lib import Logger as logger
from typing import List


def _collect_weight(weight_dirpath: Path) -> List[Path]:
    """
    Return list of weight paths.

    Args:
        weight_dirpath (Path): path to directory of weights

    Returns:
        List[Path]: list of weight paths
    """
    weight_paths = list(weight_dirpath.glob('*.pt'))
    assert weight_paths != [], f"No weight in {weight_dirpath}."
    weight_paths.sort(key=lambda path: path.stat().st_mtime)
    return weight_paths


def main(opt):
    args = opt.args
    model = create_model(args)
    model.print_dataset_info()

    _weight_dirpath = Path(args.weight_dir, 'results/sets', args.test_datetime, 'weights')
    weight_paths = _collect_weight(_weight_dirpath)

    for weight_path in weight_paths:
        logger.logger.info(f"Inference with {weight_path.name}.")

        model.load_weight(weight_path)  # weight is reset every time
        model.eval()

        for split in ['train', 'val', 'test']:
            split_dataloader = model.dataloaders[split]

            for i, data in enumerate(split_dataloader):
                model.set_data(data)

                with torch.no_grad():
                    model.forward()
                    model.make_likelihood(data)

        model.save_likelihood(weight_path.stem)  # weight_002


if __name__ == '__main__':
    set_logger()
    logger.logger.info('\nTest started.\n')

    opt = check_test_options()
    main(opt)

    logger.logger.info('\nTest finished.\n')

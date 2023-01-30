#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import torch
from lib import (
        check_test_options,
        set_params,
        dispatch_params,
        create_model,
        BaseLogger
        )
from lib.component import create_dataloader, print_dataset_info, set_likelihood
from typing import List


logger = BaseLogger.get_logger(__name__)


def _collect_weight(weight_dir: str) -> List[Path]:
    """
    Return list of weight paths.

    Args:
        weight_dir (st): path to directory of weights

    Returns:
        List[Path]: list of weight paths
    """
    weight_paths = list(Path(weight_dir).glob('*.pt'))
    assert weight_paths != [], f"No weight in {weight_dir}."
    weight_paths.sort(key=lambda path: path.stat().st_mtime)
    return weight_paths


def main(opt):
    params = set_params(opt.args)
    params.print_parameter()
    params_groups = dispatch_params(params)
    dataloader_param = params_groups['dataloader']
    model_param = params_groups['model']
    test_conf_param = params_groups['test_conf']
    del params.df_source

    task = test_conf_param.task
    test_splits = test_conf_param.test_splits
    num_outputs_for_label = test_conf_param.num_outputs_for_label
    save_datetime_dir = test_conf_param.save_datetime_dir
    weight_dir = test_conf_param.weight_dir

    dataloaders = {split: create_dataloader(dataloader_param, split=split) for split in test_splits}
    print_dataset_info(dataloaders)

    model = create_model(model_param )
    likelihood = set_likelihood(task, num_outputs_for_label, save_datetime_dir)

    weight_paths = _collect_weight(weight_dir)
    for weight_path in weight_paths:
        logger.info(f"Inference with {weight_path.name}.")

        # weight is orverwritten every time weight is loaded.
        model.load_weight(weight_path)
        model.eval()

        likelihood.init_likelihood()
        for split in params.test_splits:
            split_dataloader = dataloaders[split]
            for i, data in enumerate(split_dataloader):
                in_data, _ = model.set_data(data)

                with torch.no_grad():
                    output = model(in_data)
                    likelihood.make_likelihood(data, output)

        likelihood.save_likelihood(save_datetime_dir, weight_path.stem)

        if len(weight_paths) > 1:
            del model.network
            model.init_network(params)


if __name__ == '__main__':
    try:
        logger.info('\nTest started.\n')

        opt = check_test_options()
        main(opt)

    except Exception as e:
        logger.error(e, exc_info=True)

    else:
        logger.info('\nTest finished.\n')

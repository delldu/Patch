"""Model predict."""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2020年 11月 02日 星期一 17:49:55 CST
# ***
# ************************************************************************************/
#
import argparse
import glob
import os
import pdb

import torch
import torchvision.transforms as transforms
from PIL import Image
from tqdm import tqdm

from data import image_with_mask
from model import enable_amp, get_model, model_device, model_load

if __name__ == "__main__":
    """Predict."""

    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str,
                        default="models/ImagePatch.pth", help="checkpint file")
    parser.add_argument(
        '--input', type=str, default="dataset/predict/image/*.png", help="input image")
    args = parser.parse_args()

    model = get_model()
    model_load(model, args.checkpoint)
    device = model_device()
    model.to(device)
    model.eval()

    enable_amp(model)

    totensor = transforms.ToTensor()
    toimage = transforms.ToPILImage()

    image_filenames = glob.glob(args.input)
    progress_bar = tqdm(total=len(image_filenames))

    for index, filename in enumerate(image_filenames):
        progress_bar.update(1)

        # image
        image = Image.open(filename).convert("RGB")
        input_tensor = totensor(image).unsqueeze(0).to(device)

        # mask
        mask_filename = os.path.dirname(os.path.dirname(filename)) \
            + "/mask/" + os.path.basename(filename)
        mask_image = Image.open(mask_filename).convert("RGB")
        mask_tensor = totensor(mask_image).unsqueeze(0).to(device)

        new_input_tensor, new_mask_tensor = image_with_mask(
            input_tensor, mask_tensor)

        # new input
        output_filename = os.path.dirname(os.path.dirname(filename)) \
            + "/output/input_" + os.path.basename(filename)
        toimage(new_input_tensor.clamp(
            0, 1.0).squeeze().cpu()).save(output_filename)

        with torch.no_grad():
            output_tensor = model(new_input_tensor, new_mask_tensor)

        output_tensor = output_tensor.clamp(0, 1.0).squeeze()
        output_filename = os.path.dirname(os.path.dirname(filename)) \
            + "/output/output_" + os.path.basename(filename)
        toimage(output_tensor.cpu()).save(output_filename)

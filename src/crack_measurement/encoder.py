"""Pretrained-encoder segmentation models for crack and indentation masks.

The checked-in labels have no corner or crack-tip landmarks, so these models
learn the rasterized masks already used by the measurement app. Straight
chords are extracted from those masks and stay editable suggestions.
"""
from pathlib import Path
from urllib.request import urlretrieve

import torch
from torch import nn
from .paths import output_root

ROOT = output_root()
MICRONET_DIR = ROOT / 'models' / 'pretrained'
MICRONET_WEIGHTS = MICRONET_DIR / 'resnet50_imagenet-micronet_weights.pth'
MICRONET_URL = (
    'https://huggingface.co/jstuckner/microscopy-resnet50-imagenet-micronet/'
    'resolve/main/resnet50_imagenet-micronet_weights.pth'
)


class Up(nn.Module):
    def __init__(self, in_channels, skip_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels + skip_channels, out_channels, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.ReLU(inplace=True))

    def forward(self, x, skip):
        x = nn.functional.interpolate(x, size=skip.shape[-2:], mode='bilinear', align_corners=False)
        return self.conv(torch.cat([x, skip], 1))


def _grayscale_stem(rgb_conv, pretrained):
    stem = nn.Conv2d(1, rgb_conv.out_channels, kernel_size=rgb_conv.kernel_size,
                     stride=rgb_conv.stride, padding=rgb_conv.padding, bias=False)
    with torch.no_grad():
        if pretrained:
            stem.weight.copy_(rgb_conv.weight.mean(dim=1, keepdim=True))
        else:
            nn.init.kaiming_normal_(stem.weight, mode='fan_out', nonlinearity='relu')
    return stem


class EncoderSeg(nn.Module):
    """ImageNet ResNet-18 encoder, when pretrained weights are requested, plus a small decoder."""

    def __init__(self, pretrained=False):
        super().__init__()
        try:
            from torchvision.models import ResNet18_Weights, resnet18
        except ImportError as exc:
            raise ImportError(
                'Encoder training requires torchvision. Install it in the project environment.') from exc
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        net = resnet18(weights=weights)
        self.stem = nn.Sequential(_grayscale_stem(net.conv1, pretrained), net.bn1, net.relu, net.maxpool)
        self.layer1 = net.layer1
        self.layer2 = net.layer2
        self.layer3 = net.layer3
        self.layer4 = net.layer4
        self.up3 = Up(512, 256, 256)
        self.up2 = Up(256, 128, 128)
        self.up1 = Up(128, 64, 64)
        self.head = nn.Conv2d(64, 2, 1)

    def encoder_parameters(self):
        return [parameter for module in (self.stem, self.layer1, self.layer2, self.layer3, self.layer4)
                for parameter in module.parameters()]

    def decoder_parameters(self):
        return [parameter for module in (self.up3, self.up2, self.up1, self.head)
                for parameter in module.parameters()]

    def forward(self, x):
        size = x.shape[-2:]
        skip1 = self.layer1(self.stem(x))
        skip2 = self.layer2(skip1)
        skip3 = self.layer3(skip2)
        x = self.up3(self.layer4(skip3), skip3)
        x = self.up2(x, skip2)
        x = self.up1(x, skip1)
        x = nn.functional.interpolate(x, size=size, mode='bilinear', align_corners=False)
        return self.head(x)


def ensure_micronet_weights(destination=None, progress=None):
    """Download NASA MicroNet ImageNet→MicroNet ResNet-50 encoder weights once."""
    destination = Path(destination or MICRONET_WEIGHTS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 1_000_000:
        return destination
    if progress:
        progress(f'Downloading NASA MicroNet weights to {destination}…')
    temporary = destination.with_suffix('.partial')
    urlretrieve(MICRONET_URL, temporary)
    temporary.replace(destination)
    if progress:
        progress(f'MicroNet weights ready: {destination}')
    return destination


def load_micronet_backbone(pretrained=True, weights_path=None):
    """Build a torchvision ResNet-50 and optionally load NASA MicroNet encoder weights."""
    try:
        from torchvision.models import resnet50
    except ImportError as exc:
        raise ImportError(
            'MicroNet training requires torchvision. Install it in the project environment.') from exc
    net = resnet50(weights=None)
    if not pretrained:
        return net
    path = ensure_micronet_weights(weights_path)
    state = torch.load(path, map_location='cpu', weights_only=True)
    missing, unexpected = net.load_state_dict(state, strict=False)
    # Classification head keys are intentionally absent from the encoder file.
    missing = [key for key in missing if not key.startswith('fc.')]
    if missing:
        raise RuntimeError(f'MicroNet weights were missing encoder keys: {missing[:8]}')
    if unexpected:
        raise RuntimeError(f'MicroNet weights had unexpected keys: {unexpected[:8]}')
    return net


class MicroNetSeg(nn.Module):
    """NASA MicroNet ResNet-50 encoder with a lightweight decoder for two masks."""

    architecture = 'micronet_unet'

    def __init__(self, pretrained=True, weights_path=None):
        super().__init__()
        net = load_micronet_backbone(pretrained=pretrained, weights_path=weights_path)
        self.stem = nn.Sequential(_grayscale_stem(net.conv1, pretrained), net.bn1, net.relu, net.maxpool)
        self.layer1 = net.layer1
        self.layer2 = net.layer2
        self.layer3 = net.layer3
        self.layer4 = net.layer4
        self.up3 = Up(2048, 1024, 512)
        self.up2 = Up(512, 512, 256)
        self.up1 = Up(256, 256, 128)
        self.head = nn.Conv2d(128, 2, 1)

    def encoder_parameters(self):
        return [parameter for module in (self.stem, self.layer1, self.layer2, self.layer3, self.layer4)
                for parameter in module.parameters()]

    def decoder_parameters(self):
        return [parameter for module in (self.up3, self.up2, self.up1, self.head)
                for parameter in module.parameters()]

    def forward(self, x):
        size = x.shape[-2:]
        skip1 = self.layer1(self.stem(x))
        skip2 = self.layer2(skip1)
        skip3 = self.layer3(skip2)
        x = self.up3(self.layer4(skip3), skip3)
        x = self.up2(x, skip2)
        x = self.up1(x, skip1)
        x = nn.functional.interpolate(x, size=size, mode='bilinear', align_corners=False)
        return self.head(x)


def build_encoder_model(architecture='encoder_seg', pretrained=False, weights_path=None):
    if architecture in {None, 'encoder_seg'}:
        return EncoderSeg(pretrained=pretrained)
    if architecture == 'micronet_unet':
        return MicroNetSeg(pretrained=pretrained, weights_path=weights_path)
    raise ValueError(f'Unsupported encoder architecture: {architecture}')

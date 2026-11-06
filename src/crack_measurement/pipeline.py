"""Reproducible crack-measurement training and evaluation.

The scratch U-Net in ``model.train`` remains the application baseline. This
command trains the pretrained-encoder segmentation model and writes a checkpoint
the application can load. Held-out mask scores and radial-span errors are
evaluation signals only. They are not researcher-approved references.

Examples, from the repository root:

    python -m src.crack_measurement.pipeline audit
    python -m src.crack_measurement.pipeline train --epochs 5 --freeze-epochs 1 --pretrained
    python -m src.crack_measurement.pipeline train --architecture micronet_unet --epochs 12 --freeze-epochs 3 --pretrained --size 512
    python -m src.crack_measurement.pipeline evaluate --checkpoint runs/crack_measurement/<run>/best.pt
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from .corrections import correction_record
from .dataset import (SCALE_UNIT_ASSUMPTION, audit_records, binary_dice, length_summary,
                      load_calibration, load_dataset, match_chords, micrometers_per_pixel,
                      proxy_radial_chords, split_records, write_json)
from .encoder import build_encoder_model
from .model import (CrackDataset, device_for, estimate_radial, load_grayscale, loss_for,
                    masks_for, predict)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LABELS = ROOT / 'data/Indentation_Image_Labels/per_image'
DEFAULT_IMAGES = ROOT / 'data/Indentation Images'
DEFAULT_SCALE = ROOT / 'Length.csv'


def _run_directory(root):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = Path(root) / stamp
    path.mkdir(parents=True)
    return path


def _optimizer(model, encoder_trainable):
    for parameter in model.encoder_parameters():
        parameter.requires_grad = encoder_trainable
    groups = [{'params': model.decoder_parameters(), 'lr': 1e-3}]
    if encoder_trainable:
        groups.insert(0, {'params': model.encoder_parameters(), 'lr': 1e-4})
    return torch.optim.Adam(groups)


def _names(records):
    return [record[0].name for record in records]


def train_encoder(labels, images, scale_file, run, epochs, size, pretrained, freeze_epochs, seed,
                  batch_size, progress, cancelled, architecture='encoder_seg'):
    if size % 32:
        raise ValueError('Training size must be a multiple of 32 so the encoder strides align.')
    records = load_dataset(labels, images)
    groups, description = split_records(records, seed=seed)
    calibration = load_calibration(scale_file)
    audit = audit_records(records, calibration)
    run = Path(run)
    run.mkdir(parents=True, exist_ok=True)
    config = {
        'architecture': architecture,
        'pretrained': bool(pretrained),
        'epochs': int(epochs),
        'freeze_epochs': int(freeze_epochs),
        'size': int(size),
        'batch_size': int(batch_size),
        'seed': int(seed),
        'labels': str(labels),
        'images': str(images),
        'scale_file': str(scale_file),
        'scale_unit_assumption': SCALE_UNIT_ASSUMPTION,
        'baseline': 'src.crack_measurement.model.UNet trained from scratch by the application dialog',
        'targets': 'rasterized crack polylines and indentation boxes; scratches excluded',
        'test_set_used_for_training': False,
    }
    write_json(run / 'config.json', config)
    write_json(run / 'split.json', description)
    write_json(run / 'audit.json', {key: value for key, value in audit.items() if key != 'per_image'})
    torch.manual_seed(seed)
    device = device_for()
    if architecture == 'micronet_unet' and pretrained:
        progress('Loading NASA MicroNet ResNet-50 encoder weights…')
    model = build_encoder_model(architecture, pretrained=pretrained).to(device)
    validation = CrackDataset(groups['validation'], size)
    training = CrackDataset(groups['train'], size, augment=True)
    optimizer = _optimizer(model, encoder_trainable=freeze_epochs <= 0)
    best = math.inf
    destination = run / 'best.pt'
    history = run / 'history.jsonl'
    for epoch in range(epochs):
        if epoch == freeze_epochs and freeze_epochs > 0:
            optimizer = _optimizer(model, encoder_trainable=True)
        model.train()
        total = 0.
        for image, target in DataLoader(training, batch_size=batch_size, shuffle=True):
            if cancelled():
                return None
            image, target = image.to(device), target.to(device)
            optimizer.zero_grad()
            loss = loss_for(model(image), target)
            loss.backward()
            optimizer.step()
            total += loss.item() * len(image)
        model.eval()
        val_loss = 0.
        with torch.no_grad():
            for image, target in DataLoader(validation, batch_size=batch_size):
                if cancelled():
                    return None
                val_loss += loss_for(model(image.to(device)), target.to(device)).item() * len(image)
        val_loss /= len(validation)
        row = {'epoch': epoch + 1, 'train_loss': total / len(training), 'validation_loss': val_loss,
               'encoder_trainable': epoch >= freeze_epochs}
        with history.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(row) + '\n')
        if val_loss < best:
            best = val_loss
            checkpoint = {
                'architecture': architecture,
                'state_dict': {key: value.cpu() for key, value in model.state_dict().items()},
                'size': size,
                'epoch': epoch + 1,
                'validation_loss': best,
                'pretrained': bool(pretrained),
                'train_ids': [str(record[0]) for record in groups['train']],
                'validation_ids': [str(record[0]) for record in groups['validation']],
                'test_ids': [str(record[0]) for record in groups['test']],
                'train_names': _names(groups['train']),
                'validation_names': _names(groups['validation']),
                'test_names': _names(groups['test']),
                'predictions_are_ground_truth': False,
            }
            temporary = destination.with_suffix('.tmp')
            torch.save(checkpoint, temporary)
            temporary.replace(destination)
        progress(f'Epoch {epoch + 1}/{epochs} · training {total / len(training):.4f} · '
                 f'validation {val_loss:.4f} · {device}')
    return str(destination)


def _checkpoint_names(checkpoint, split):
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    names = saved.get(f'{split}_names')
    if names:
        return set(names)
    return {Path(path).name for path in saved.get(f'{split}_ids', [])}


def evaluate(checkpoint, labels, images, scale_file, split='test', threshold=.5):
    """Score one split. The test split is the default and is not a training target."""
    records = load_dataset(labels, images)
    calibration = load_calibration(scale_file)
    wanted = _checkpoint_names(checkpoint, split)
    if not wanted:
        raise ValueError(f'Checkpoint has no {split} images. Train with this pipeline before evaluating.')
    selected = [record for record in records if record[0].name in wanted]
    if len(selected) != len(wanted):
        found = {record[0].name for record in selected}
        missing = sorted(wanted - found)
        raise ValueError(f'{len(missing)} split images were not found, including {missing[:3]}')
    dice_crack, dice_indent = [], []
    errors_px, errors_um = [], []
    missed = invalid = references = suggestions = failures = 0
    per_image = []
    for path, item, names in selected:
        image = load_grayscale(path)
        target = masks_for(item, names, image.shape)
        probabilities = predict(image, checkpoint)
        dice_crack.append(binary_dice(probabilities[0], target[0], threshold))
        dice_indent.append(binary_dice(probabilities[1], target[1], threshold))
        scale = calibration.get(path.name)
        um_per_px = None if scale is None else micrometers_per_pixel(scale)
        try:
            predictions = estimate_radial(probabilities, threshold)
            failure = None
        except ValueError as exc:
            predictions = []
            failure = str(exc)
            failures += 1
        refs = proxy_radial_chords(item, names)
        pairs, image_missed, image_invalid = match_chords(refs, predictions)
        missed += image_missed
        invalid += image_invalid
        references += len(refs)
        suggestions += len(predictions)
        image_errors = []
        for reference, prediction in pairs:
            error_px = abs(prediction['length_px'] - reference['length_px'])
            errors_px.append(error_px)
            if um_per_px is not None:
                error_um = error_px * um_per_px
                errors_um.append(error_um)
                image_errors.append(error_um)
        lengths_um = []
        if um_per_px is not None:
            lengths_um = [prediction['length_px'] * um_per_px for prediction in predictions]
        per_image.append({
            'image': path.name,
            'crack_dice': dice_crack[-1],
            'indentation_dice': dice_indent[-1],
            'reference_chords': len(refs),
            'suggestions': len(predictions),
            'missed_reference_directions': image_missed,
            'invalid_suggestions': image_invalid,
            'suggestion_summary_um': length_summary(lengths_um),
            'proxy_length_error_um': image_errors,
            'extraction_failure': failure,
            'reviewed': False,
        })
    metrics = {
        'split': split,
        'images': len(selected),
        'predictions_are_ground_truth': False,
        'reference': 'proxy radial spans of labeled crack polylines, not researcher-approved lengths',
        'scale_unit_assumption': SCALE_UNIT_ASSUMPTION,
        'mean_crack_dice': float(np.mean(dice_crack) if dice_crack else 0),
        'mean_indentation_dice': float(np.mean(dice_indent) if dice_indent else 0),
        'reference_chords': references,
        'suggestions': suggestions,
        'missed_reference_directions': missed,
        'invalid_suggestions': invalid,
        'images_without_extractable_suggestions': failures,
        'median_abs_proxy_error_px': None if not errors_px else float(np.median(errors_px)),
        'median_abs_proxy_error_um': None if not errors_um else float(np.median(errors_um)),
        'mean_abs_proxy_error_um': None if not errors_um else float(np.mean(errors_um)),
        'per_image': per_image,
    }
    return metrics


def _command_audit(args):
    records = load_dataset(args.labels, args.images)
    report = audit_records(records, load_calibration(args.scale))
    if args.out:
        write_json(args.out, report)
    printable = {key: value for key, value in report.items() if key != 'per_image'}
    print(json.dumps(printable, indent=2))


def _command_train(args):
    run = _run_directory(args.runs)

    def cancelled():
        return False

    destination = train_encoder(
        args.labels, args.images, args.scale, run, args.epochs, args.size, args.pretrained,
        args.freeze_epochs, args.seed, args.batch_size, print, cancelled,
        architecture=args.architecture)
    print(destination or 'Training stopped before a checkpoint was saved.')


def _command_evaluate(args):
    metrics = evaluate(args.checkpoint, args.labels, args.images, args.scale, args.split, args.threshold)
    out = Path(args.out) if args.out else Path(args.checkpoint).resolve().parent / f'{args.split}_metrics.json'
    write_json(out, metrics)
    summary = {key: value for key, value in metrics.items() if key != 'per_image'}
    print(json.dumps(summary, indent=2))
    print(out)


def _command_correction_template(args):
    record = correction_record(
        args.image,
        [{'start_xy': [0, 0], 'end_xy': [1, 0], 'role': 'crack_chord', 'deleted': False}],
        calibration_um_per_100_px=args.scale_length,
        source_checkpoint=args.checkpoint,
        notes='Replace the example measurement with researcher-approved guides before training on this file.',
    )
    write_json(args.out, record)
    print(args.out)


def build_parser():
    parser = argparse.ArgumentParser(description='Indentation crack measurement training and evaluation')
    parser.add_argument('--labels', type=Path, default=DEFAULT_LABELS)
    parser.add_argument('--images', type=Path, default=DEFAULT_IMAGES)
    parser.add_argument('--scale', type=Path, default=DEFAULT_SCALE)
    sub = parser.add_subparsers(dest='command', required=True)

    audit = sub.add_parser('audit')
    audit.add_argument('--out', type=Path)
    audit.set_defaults(func=_command_audit)

    train = sub.add_parser('train')
    train.add_argument('--runs', type=Path, default=ROOT / 'runs/crack_measurement')
    train.add_argument('--epochs', type=int, default=5)
    train.add_argument('--freeze-epochs', type=int, default=1)
    train.add_argument('--size', type=int, default=256)
    train.add_argument('--batch-size', type=int, default=1)
    train.add_argument('--seed', type=int, default=42)
    train.add_argument('--pretrained', action='store_true')
    train.add_argument('--architecture', choices=('encoder_seg', 'micronet_unet'),
                       default='encoder_seg',
                       help='encoder_seg=ResNet-18, micronet_unet=NASA MicroNet ResNet-50')
    train.set_defaults(func=_command_train)

    evaluate_parser = sub.add_parser('evaluate')
    evaluate_parser.add_argument('--checkpoint', type=Path, required=True)
    evaluate_parser.add_argument('--split', choices=('test', 'validation', 'train'), default='test')
    evaluate_parser.add_argument('--threshold', type=float, default=.5)
    evaluate_parser.add_argument('--out', type=Path)
    evaluate_parser.set_defaults(func=_command_evaluate)

    template = sub.add_parser('correction-template')
    template.add_argument('--image', required=True)
    template.add_argument('--checkpoint', type=Path)
    template.add_argument('--scale-length', type=float)
    template.add_argument('--out', type=Path, required=True)
    template.set_defaults(func=_command_correction_template)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    main()

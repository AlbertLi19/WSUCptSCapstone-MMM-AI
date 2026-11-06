"""Datumaro loading, U-Net training, inference and endpoint extraction."""
import json
import math
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import Dataset, DataLoader


def load_grayscale(path):
    """Read TIFFs with Pillow to tolerate microscope-specific metadata tags."""
    path = Path(path)
    if path.suffix.lower() in {'.tif', '.tiff'}:
        with Image.open(path) as image:
            pixels = np.asarray(image)
            if pixels.ndim == 2 and pixels.dtype == np.uint16:
                # Match OpenCV's default conversion of 16-bit data to 8-bit.
                return (pixels // 256).astype(np.uint8)
            return np.array(image.convert('L'), dtype=np.uint8, copy=True)
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f'Cannot read {path}')
    return image


def read_records(labels, images):
    labels, images = Path(labels), Path(images)
    paths = [labels] if labels.is_file() else sorted(labels.glob('*.json'))
    records, seen = [], set()
    for path in paths:
        data = json.loads(path.read_text())
        names = [x['name'].casefold() for x in data['categories']['label']['labels']]
        for item in data['items']:
            key = item['image']['path']
            if key in seen:
                continue
            seen.add(key)
            image = images / key
            if not image.is_file():
                image = images / Path(key).name
            if not image.is_file():
                raise ValueError(f'Missing training image: {image}')
            records.append((image, item, names))
    if len(records) < 2:
        raise ValueError('At least two labeled images are required.')
    return records


def masks_for(item, names, shape, thickness=5):
    h, w = shape
    masks = np.zeros((2, h, w), np.uint8)
    for ann in item['annotations']:
        name = names[ann['label_id']]
        if ann['type'] == 'polyline' and name == 'crack':
            points = np.rint(np.array(ann['points']).reshape(-1, 2)).astype(np.int32)
            cv2.polylines(masks[0], [points], False, 1, thickness)
        elif ann['type'] == 'bbox' and name == 'indentation':
            x, y, bw, bh = ann['bbox']
            cv2.rectangle(masks[1], (round(x), round(y)),
                          (round(x + bw), round(y + bh)), 1, -1)
    return masks


class CrackDataset(Dataset):
    def __init__(self, records, size=512, augment=False):
        self.records, self.size, self.augment = records, size, augment

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        path, item, names = self.records[index]
        image = load_grayscale(path)
        target = masks_for(item, names, image.shape)
        # Preserve aspect ratio and coordinates with square padding, not stretching.
        image, target = square_resize(image, self.size, target)
        if self.augment:
            k = np.random.randint(4)
            image, target = np.rot90(image, k), np.rot90(target, k, axes=(1, 2))
            if np.random.rand() < .5:
                image, target = image[:, ::-1], target[:, :, ::-1]
        return (torch.from_numpy(image.copy()).float().unsqueeze(0) / 255,
                torch.from_numpy(target.copy()).float())


def square_resize(image, size, masks=None):
    h, w = image.shape
    factor = size / max(h, w)
    rh, rw = max(1, round(h * factor)), max(1, round(w * factor))
    out = np.zeros((size, size), np.uint8)
    out[:rh, :rw] = cv2.resize(image, (rw, rh), interpolation=cv2.INTER_AREA)
    if masks is None:
        return out, (rh, rw)
    target = np.zeros((len(masks), size, size), np.uint8)
    for i, mask in enumerate(masks):
        target[i, :rh, :rw] = cv2.resize(mask, (rw, rh), interpolation=cv2.INTER_NEAREST)
    return out, target


def block(a, b):
    return nn.Sequential(nn.Conv2d(a, b, 3, padding=1), nn.ReLU(inplace=True),
                         nn.Conv2d(b, b, 3, padding=1), nn.ReLU(inplace=True))


class UNet(nn.Module):
    """Compact two-output U-Net; trained locally without external weight downloads."""
    def __init__(self, base=16):
        super().__init__()
        self.down = nn.ModuleList([block(1, base), block(base, base*2),
                                   block(base*2, base*4), block(base*4, base*8)])
        self.up = nn.ModuleList([block(base*12, base*4), block(base*6, base*2),
                                 block(base*3, base)])
        self.head = nn.Conv2d(base, 2, 1)

    def forward(self, x):
        skips = []
        for i, layer in enumerate(self.down):
            if i:
                x = nn.functional.max_pool2d(x, 2)
            x = layer(x)
            skips.append(x)
        for layer, skip in zip(self.up, reversed(skips[:-1])):
            x = nn.functional.interpolate(x, size=skip.shape[-2:], mode='bilinear', align_corners=False)
            x = layer(torch.cat([x, skip], 1))
        return self.head(x)


def device_for():
    if torch.cuda.is_available():
        return torch.device('cuda')
    if torch.backends.mps.is_available():
        return torch.device('mps')
    return torch.device('cpu')


def loss_for(logits, target):
    probability = logits.sigmoid()
    dims = (0, 2, 3)
    dice = (2*(probability*target).sum(dims)+1) / (probability.sum(dims)+target.sum(dims)+1)
    return nn.functional.binary_cross_entropy_with_logits(logits, target) + 1-dice.mean()


def train(labels, images, destination, epochs, size, progress, cancelled):
    records = read_records(labels, images)
    rng = np.random.default_rng(42)
    indices = rng.permutation(len(records))
    count = max(1, round(len(records)*.2))
    validation = CrackDataset([records[i] for i in indices[:count]], size)
    training = CrackDataset([records[i] for i in indices[count:]], size, True)
    torch.manual_seed(42)
    device = device_for()
    model = UNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    best = math.inf
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(epochs):
        model.train()
        total = 0
        for image, target in DataLoader(training, batch_size=2, shuffle=True):
            if cancelled():
                return None
            image, target = image.to(device), target.to(device)
            optimizer.zero_grad()
            loss = loss_for(model(image), target)
            loss.backward()
            optimizer.step()
            total += loss.item()*len(image)
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for image, target in DataLoader(validation, batch_size=2):
                if cancelled():
                    return None
                val_loss += loss_for(model(image.to(device)), target.to(device)).item()*len(image)
        val_loss /= len(validation)
        if val_loss < best:
            best = val_loss
            checkpoint = {'state_dict': {k: v.cpu() for k, v in model.state_dict().items()},
                          'size': size, 'epoch': epoch+1, 'validation_loss': best,
                          'train_ids': [str(r[0]) for r in training.records],
                          'validation_ids': [str(r[0]) for r in validation.records]}
            temporary = destination.with_suffix('.tmp')
            torch.save(checkpoint, temporary)
            temporary.replace(destination)
        progress(f'Epoch {epoch+1}/{epochs} · training {total/len(training):.4f} · validation {val_loss:.4f} · {device}')
    return str(destination)


def predict(image, checkpoint):
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    architecture = saved.get('architecture', 'unet')
    if architecture in {'encoder_seg', 'micronet_unet'}:
        from .encoder import build_encoder_model
        model = build_encoder_model(architecture, pretrained=False).eval()
    elif architecture == 'unet':
        model = UNet().eval()
    else:
        raise ValueError(f'Unsupported checkpoint architecture: {architecture}')
    model.load_state_dict(saved['state_dict'])
    resized, (rh, rw) = square_resize(image, saved['size'])
    with torch.no_grad():
        maps = model(torch.from_numpy(resized).float()[None, None]/255).sigmoid()[0].numpy()
    h, w = image.shape
    return np.stack([cv2.resize(m[:rh, :rw], (w, h)) for m in maps])


def chord_from_group(group, center):
    """Straight endpoint chord for one radial group. Percentiles limit isolated pixels."""
    mean = group.mean(axis=0)
    _, _, vt = np.linalg.svd(group-mean, full_matrices=False)
    direction = vt[0]
    if np.dot(direction, mean-center) < 0:
        direction = -direction
    projection = ((group-mean)*direction).sum(axis=1)
    start, end = np.percentile(projection, [2, 98])
    a, b = mean+start*direction, mean+end*direction
    angle = math.atan2(float(direction[1]), float(direction[0]))
    return a, b, angle, float(np.linalg.norm(b-a))


def radial_groups(points, center, width=np.pi/5):
    """Split points into four orthogonal directions around center."""
    angles = np.arctan2(points[:, 1]-center[1], points[:, 0]-center[0])
    phase = np.angle(np.mean(np.exp(4j*angles)))/4
    groups = []
    for i in range(4):
        angle = phase + i*np.pi/2
        delta = np.angle(np.exp(1j*(angles-angle)))
        groups.append((float(angle), points[np.abs(delta) < width]))
    return groups


def indentation_center(probabilities, threshold=.5):
    crack, indentation = probabilities
    n, _lab, stats, centers = cv2.connectedComponentsWithStats((indentation > threshold).astype(np.uint8))
    if n < 2:
        raise ValueError('No indentation detected. Train longer or adjust the threshold.')
    image_center = np.array([crack.shape[1]/2, crack.shape[0]/2])
    scores = stats[1:, cv2.CC_STAT_AREA] / (1+np.linalg.norm(centers[1:]-image_center, axis=1)/max(crack.shape))
    return centers[1+np.argmax(scores)]


def crack_points(probabilities, center, threshold=.5):
    crack = probabilities[0]
    y, x = np.nonzero(crack > threshold)
    points = np.column_stack([x, y]).astype(float)
    if len(points) == 0:
        return points
    radius = np.linalg.norm(points-center, axis=1)
    return points[radius > 5]


def estimate_radial(probabilities, threshold=.5, min_points=10):
    """Straight radial chords for directions with enough predicted crack pixels.

    Missing directions are omitted. These estimates are not researcher-approved
    measurements and are not ground truth.
    """
    center = indentation_center(probabilities, threshold)
    points = crack_points(probabilities, center, threshold)
    if len(points) < min_points:
        raise ValueError('Too little crack evidence. Train longer or adjust the threshold.')
    measurements = []
    for angle, group in radial_groups(points, center):
        if len(group) < min_points:
            continue
        start, end, chord_angle, length = chord_from_group(group, center)
        measurements.append({'start': start, 'end': end, 'angle': chord_angle,
                             'sector_angle': angle, 'length_px': length})
    return measurements


def estimate_four(probabilities, threshold=.5):
    """Fit four radial endpoint chords around the predicted indentation center.

    Assumes one roughly central diamond and four approximately orthogonal cracks.
    These are model-derived estimates, not a guarantee of physical endpoints.
    """
    found = estimate_radial(probabilities, threshold)
    if len(found) < 4:
        raise ValueError('Crack evidence is incomplete; four cracks could not be resolved.')
    return [(item['start'], item['end']) for item in found]


def direction_label(angle, prefix):
    """Map image-space angle to top/right/bottom/left relative to the indentation."""
    degrees = (math.degrees(angle) + 360) % 360
    if 315 <= degrees or degrees < 45:
        name = 'right'
    elif 45 <= degrees < 135:
        name = 'bottom'
    elif 135 <= degrees < 225:
        name = 'left'
    else:
        name = 'top'
    return f'{prefix} {name}'


def estimate_half_diagonals(probabilities, threshold=.5):
    """Four center-to-corner half-diagonals from the predicted indentation region."""
    center = indentation_center(probabilities, threshold)
    mask = (probabilities[1] > threshold).astype(np.uint8)
    points = cv2.findNonZero(mask)
    if points is None or len(points) < 8:
        return center, []
    rect = cv2.minAreaRect(points)
    corners = cv2.boxPoints(rect).astype(float)
    diagonals = []
    for corner in corners:
        vector = corner - center
        length = float(np.linalg.norm(vector))
        if length < 3:
            continue
        angle = math.atan2(float(vector[1]), float(vector[0]))
        diagonals.append({
            'start': center.copy(),
            'end': corner.copy(),
            'angle': angle,
            'length_px': length,
            'role': 'half_diagonal',
            'label': direction_label(angle, 'Inner'),
        })
    diagonals.sort(key=lambda item: item['angle'])
    return center, diagonals


def sample_line_confidence(probability_map, start, end, samples=40):
    """Mean mask probability along a straight chord, used as estimate confidence."""
    start, end = np.asarray(start, float), np.asarray(end, float)
    if np.linalg.norm(end - start) < 1:
        return 0.
    height, width = probability_map.shape
    values = []
    for fraction in np.linspace(0, 1, samples):
        point = start + fraction * (end - start)
        x = int(np.clip(round(point[0]), 0, width - 1))
        y = int(np.clip(round(point[1]), 0, height - 1))
        values.append(float(probability_map[y, x]))
    return float(np.mean(values)) if values else 0.


def estimate_indentation_measurements(probabilities, threshold=.5, min_points=10):
    """Editable half-diagonals plus radial cracks with per-line confidence scores.

    Confidence is model-mask strength along each line, not researcher-validated accuracy.
    Missing directions are omitted rather than forced.
    """
    center, diagonals = estimate_half_diagonals(probabilities, threshold)
    cracks = estimate_radial(probabilities, threshold, min_points=min_points)
    measurements = []
    for item in diagonals:
        confidence = sample_line_confidence(probabilities[1], item['start'], item['end'])
        measurements.append({
            **item,
            'start': center.copy(),
            'end': np.asarray(item['end'], float),
            'source': 'estimated',
            'confidence': confidence,
        })
    for item in cracks:
        start, end = np.asarray(item['start'], float), np.asarray(item['end'], float)
        tip = end if np.linalg.norm(end - center) >= np.linalg.norm(start - center) else start
        angle = math.atan2(float(tip[1] - center[1]), float(tip[0] - center[0]))
        confidence = sample_line_confidence(probabilities[0], center, tip)
        measurements.append({
            'start': center.copy(),
            'end': tip.copy(),
            'angle': angle,
            'length_px': float(np.linalg.norm(tip - center)),
            'role': 'crack_chord',
            'label': direction_label(angle, 'Outer'),
            'source': 'estimated',
            'confidence': confidence,
        })
    if not measurements:
        raise ValueError('No indentation or crack measurement could be resolved.')
    return center, measurements


def clip_guide(endpoint, direction, width, height):
    """Clip the infinite line perpendicular to a chord to image boundaries."""
    normal = np.array([-direction[1], direction[0]], float)
    point = np.asarray(endpoint, float)
    intersections = []
    for axis, limit in ((0, width), (1, height)):
        if abs(normal[axis]) < 1e-10:
            continue
        for edge in (0, limit):
            hit = point + (edge-point[axis])/normal[axis]*normal
            if -1e-6 <= hit[0] <= width+1e-6 and -1e-6 <= hit[1] <= height+1e-6:
                intersections.append(hit)
    if len(intersections) < 2:
        return point, point
    return min(intersections, key=lambda p: p @ normal), max(intersections, key=lambda p: p @ normal)

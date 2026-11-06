"""Segmentation algorithms, imported only when requested."""


def segment_impurity_image(*args, **kwargs):
    from .impurity_segmentation import segment_impurity_image as segment
    return segment(*args, **kwargs)


def sam_segmentation(*args, **kwargs):
    from .SAM_segmentation import sam_segmentation as segment
    return segment(*args, **kwargs)

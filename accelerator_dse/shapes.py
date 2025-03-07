# For data-center accelerator
DATA_CENTER_SHAPES = [
    (128, 128), (128, 256), (256, 128),
    (256, 256), (256, 512), (512, 256),
    (512, 512)
]

# For mobile accelerator
MOBILE_SHAPES = [
    (16, 16), (16, 32), (32, 16),
    (32, 32), (32, 64), (64, 32),
    (64, 64)
]

# Memory splits (IFMAP %, OFMAP %)
MEMORY_SPLITS = [
    (50, 50), (60, 40), (40, 60)
]

# For data-center accelerator
DATA_CENTER_SHAPES = [
    (256, 256), (128, 512), (512, 128), (1024, 64), (64, 1024)
]

# For mobile accelerator
MOBILE_SHAPES = [
    (16, 16), (16, 32), (32, 16),
    (32, 32), (32, 64), (64, 32),
    (64, 64)
]

# Memory splits (IFMAP %, OFMAP %)
MEMORY_SPLITS = [
    (30, 70), (70, 30), (25, 75), (75, 25), (20, 80), (80,20), (15, 85), (85, 15)
]

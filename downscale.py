"""
Scale down an NxN PNG image to a KxK PNG image by dividing the input into a grid
and picking the most common color in each cell.
"""

import argparse
import sys
from collections import Counter
from PIL import Image


def downscale_image(input_path: str, output_path: str, k: int) -> None:
    """
    Load an NxN image, divide it into a KxK grid, and for each cell
    pick the most common color (mode of the histogram).
    
    Args:
        input_path: Path to the input PNG image.
        output_path: Path to save the output PNG image.
        k: Target dimension (KxK).
    """
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size

    if width != height:
        print(f"Warning: Image is not square ({width}x{height}). Proceeding anyway.")

    pixels = img.load()
    output_img = Image.new("RGBA", (k, k))
    output_pixels = output_img.load()

    # Calculate cell sizes using floating point for even distribution
    cell_width = width / k
    cell_height = height / k

    for gy in range(k):
        for gx in range(k):
            # Determine pixel boundaries for this cell
            x_start = int(round(gx * cell_width))
            x_end = int(round((gx + 1) * cell_width))
            y_start = int(round(gy * cell_height))
            y_end = int(round((gy + 1) * cell_height))

            # Clamp to image bounds
            x_start = max(0, x_start)
            x_end = min(width, x_end)
            y_start = max(0, y_start)
            y_end = min(height, y_end)

            # Collect all pixel colors in this cell
            color_counter = Counter()
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    color_counter[pixels[x, y]] += 1

            if color_counter:
                # Pick the most common color
                most_common_color = color_counter.most_common(1)[0][0]
            else:
                most_common_color = (0, 0, 0, 255)

            output_pixels[gx, gy] = most_common_color

    output_img.save(output_path, "PNG")
    print(f"Saved {k}x{k} image to '{output_path}'")


def main():
    parser = argparse.ArgumentParser(
        description="Downscale an NxN PNG to KxK by picking the most common color in each grid cell."
    )
    parser.add_argument("input", help="Path to the input PNG image")
    parser.add_argument("output", help="Path to the output PNG image")
    parser.add_argument("k", type=int, help="Target size (KxK)")

    args = parser.parse_args()

    if args.k <= 0:
        print("Error: K must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    downscale_image(args.input, args.output, args.k)


if __name__ == "__main__":
    main()
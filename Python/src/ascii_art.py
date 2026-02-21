from pathlib import Path

import numpy as np
import logging
from PIL import Image

JPEG_FILE: Path = Path("./tests/ascii/test.jpeg")
OUTPUT_FILE: Path = Path("./tests/ascii/ascii_art.txt")
SYMBOL_SET: str = " .:-=+*#%@"


class AsciiArt:
    def __init__(self) -> None:
        try:
            self.image = Image.open(JPEG_FILE)
        except FileNotFoundError:
            logging.error(f"File {JPEG_FILE} not found.")
            raise

    def _resize(self, width: int = 120) -> None:
        """Resize the image to the given width while maintaining aspect ratio.
        Characters are roughly twice as tall as they are wide, so height is halved."""
        original_width, original_height = self.image.size
        aspect_ratio = original_height / original_width
        new_height = int(width * aspect_ratio * 0.5)
        self.image = self.image.resize((width, new_height))

    def _convert_to_grayscale(self) -> np.ndarray:
        return np.array(self.image.convert("L"))

    def _gaussian_blur(self, image: np.ndarray) -> np.ndarray:
        kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 16
        return self._convolve(image, kernel)

    def _convolve(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        kernel_height, kernel_width = kernel.shape
        pad_height = kernel_height // 2
        pad_width = kernel_width // 2
        padded_image = np.pad(
            image, ((pad_height, pad_height), (pad_width, pad_width)), mode="constant"
        )
        convolved_image = np.zeros_like(image)

        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                region = padded_image[i : i + kernel_height, j : j + kernel_width]
                convolved_value = np.sum(region * kernel)
                convolved_image[i, j] = convolved_value

        return convolved_image

    def _map_to_symbols(self, image: np.ndarray) -> str:
        ascii_art = ""
        for row in image:
            for pixel in row:
                ascii_art += SYMBOL_SET[int(pixel) * len(SYMBOL_SET) // 256]
            ascii_art += "\n"
        return ascii_art

    def generate_ascii_art(self, width: int = 120) -> None:
        self._resize(width)
        grayscale_image = self._convert_to_grayscale()
        blurred_image = self._gaussian_blur(grayscale_image)
        ascii_art = self._map_to_symbols(blurred_image)

        with open(OUTPUT_FILE, "w") as f:
            f.write(ascii_art)
        logging.info(f"ASCII art generated and saved to {OUTPUT_FILE}.")


def main():
    ascii_art_generator = AsciiArt()
    ascii_art_generator.generate_ascii_art()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

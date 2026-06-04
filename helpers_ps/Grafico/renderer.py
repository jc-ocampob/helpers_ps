import os
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO

def render_and_save_bytesio_dict(
        images_dict: dict[str: BytesIO], output_dir="saved_plots", figsize=(6, 4)):
    """
    images_dict: dict[str, BytesIO]
        Dictionary where values are BytesIO objects containing image data.
    output_dir: str
        Folder where images will be saved.
    figsize: tuple
        Figure size used when rendering.
    """
    os.makedirs(output_dir, exist_ok=True)

    for name, buffer in images_dict.items():
        # Reset pointer before reading
        buffer.seek(0)

        # Save to file
        file_path = os.path.join(output_dir, f"{name}.png")
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())

        # Reset again before rendering
        buffer.seek(0)

        # Render
        img = Image.open(buffer)
        plt.figure(figsize=figsize)
        plt.imshow(img)
        plt.title(name)
        plt.axis("off")
        plt.show()

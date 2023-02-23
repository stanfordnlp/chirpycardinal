from PIL import Image
import glob

if __name__ == "__main__":
    RESIZE = 250
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        for og_img in glob.glob(ext):
            fname = og_img.split("/")[-1]
            img = Image.open(og_img)
            width, height = img.size
            img = img.crop((0, 0, min(width, height), min(width, height)))
            new_img = img.resize((RESIZE, RESIZE))
            new_img.save('../' + fname)
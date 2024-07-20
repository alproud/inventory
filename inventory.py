import pytesseract
import pyautogui as pa
import cv2
import time
import sys
from PIL import ImageGrab, Image


def main():
    # if no argument for output text file, default is itemlist.txt
    path = sys.argv[1] if len(sys.argv) >= 2 else "itemlist.txt"
    # if third argument is tradable, show only tradable items
    tradable_arg = sys.argv[2] if len(sys.argv) == 3 else ""
    only_tradable = True if tradable_arg == "tradable" else False
    # pause time in seconds between certain steps
    PAUSE_TIME = 4
    time.sleep(PAUSE_TIME)

    # x coordinates of left item counts and right item counts (for example left = weapon, right = ring)
    x_left = 76
    x_right = 798
    # y position of first row of types
    y_first = 334
    # vertical difference between rows of types
    type_y_difference = 139
    # count box width and height, change if needed, or change for specific types
    cw, ch = 35, 20
    # main page dropdown showing button
    page_button = [200, 260]
    # positions of (equipment, vanities, other) buttons
    page_coords = [[200, 345], [200, 430], [200, 515]]
    # this pixel is red if untradable item, change for your screen
    untradable_pixel = [1860, 852]
    # position of item name area for scanning, y difference is vertical gap between items
    item_area_x, item_area_y, item_width, item_height, item_y_difference = (
        1144,
        379,
        600,
        41,
        97,
    )

    items = {}

    # some data about pages (equipment, vanities, other) and each of their types
    pages = [
        [
            {
                "name": "Weapon",
                "coords": {"x": x_left, "y": y_first},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Helmet",
                "coords": {"x": x_left, "y": y_first + type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Armor",
                "coords": {"x": x_left, "y": y_first + 2 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Belt",
                "coords": {"x": x_left, "y": y_first + 3 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Ring",
                "coords": {"x": x_right, "y": y_first},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Amulet",
                "coords": {"x": x_right, "y": y_first + type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Artifacts",
                "coords": {"x": x_right, "y": y_first + 2 * type_y_difference + 1},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Bracelet",
                "coords": {"x": x_right, "y": y_first + 3 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
        ],
        [
            {
                "name": "Vanity Weapon",
                "coords": {"x": x_left, "y": y_first},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Vanity Helmet",
                "coords": {"x": x_left, "y": y_first + type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Vanity Armor",
                "coords": {"x": x_left, "y": y_first + 2 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Halo",
                "coords": {"x": x_left, "y": y_first + 3 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Banner",
                "coords": {"x": x_right, "y": y_first},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Back",
                "coords": {"x": x_right, "y": y_first + type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Wisp",
                "coords": {"x": x_right, "y": y_first + 2 * type_y_difference + 1},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Aura",
                "coords": {"x": x_right, "y": y_first + 3 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
        ],
        [
            {
                "name": "Crafting Items",
                "coords": {"x": x_left, "y": y_first},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Furnishing",
                "coords": {"x": x_left, "y": y_first + type_y_difference},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Miscellaneous",
                "coords": {"x": x_left, "y": y_first + 2 * type_y_difference + 1},
                "size": {"w": cw, "h": ch},
            },
            {
                "name": "Chests",
                "coords": {"x": x_left, "y": y_first + 3 * type_y_difference},
                "size": {"w": cw, "h": ch},
            },
        ],
    ]
    # loop through each page (equipment, vanities, other)
    for index, page in enumerate(pages):
        pa.click(page_button[0], page_button[1])
        pa.click(page_coords[index][0], page_coords[index][1])

        # scans count of every type
        counts = scan_counts(index, page)
        # user corrects it if the count was not recognized correctly
        correct_counts(counts)

        time.sleep(PAUSE_TIME)

        # scans all items of all types of this page
        scan_items(
            page,
            counts,
            items,
            only_tradable,
            item_area_x,
            item_area_y,
            item_width,
            item_height,
            item_y_difference,
            untradable_pixel[0],
            untradable_pixel[1],
        )

    # writes the item names to file
    list_items(items, path)


def scan_counts(index, page):
    # list of type counts
    counts = []
    for i, type in enumerate(page):
        s = type["size"]
        c = type["coords"]
        type["index"] = i

        pa.moveTo(c["x"], c["y"])
        # scans the area of screen with the count and tries to recognize the number, saves the counts in recognizable format to images folder
        recognized = recognize(
            c["x"],
            c["y"],
            c["x"] + s["w"],
            c["y"] + s["h"],
            True,
            f"images/{(index * 8 + i):02}-{type['name']}.png",
        ).strip()
        if recognized == "":
            recognized = "0"
        counts.append(int(recognized))
        print(f"{i} {type["name"]}: {counts[i]}")
    return counts


def correct_counts(counts):
    is_correct = input("is the count correct? (y/n): ")
    if is_correct == "n":
        corrections = input("correct it: ")
        # corrections are separated by ,
        for x in corrections.split(","):
            # correction is in format index:correct_value
            index, value = x.split(":")
            counts[int(index)] = int(value)
        for index, value in enumerate(counts):
            print(f"{index}: {value}")
    print("---------------")


def is_not_tradable(pixel_x, pixel_y):
    # this pixel is red if the icon is untradable icon
    x, y = pixel_x, pixel_y
    s = pa.screenshot(region=(x, y, 1, 1))
    r, g, b = s.getpixel((0, 0))
    # probably should be more careful with this condition but it is fine for correctly chosen pixel
    if r > 160:
        return True
    else:
        return False


def scan_items(
    page,
    counts,
    items,
    only_tradable,
    item_area_x,
    item_area_y,
    item_width,
    item_height,
    item_y_difference,
    px,
    py,
):
    for type in page:
        type_name = type["name"]
        c = type["coords"]
        items[type_name] = []
        count = counts[type["index"]]

        # clicking on type icon
        pa.click(c["x"] + 30, c["y"] + 30)
        # box of first item in the list
        x1, y1, w, h = item_area_x, item_area_y, item_width, item_height
        if type_name == "Vanity Weapon":
            # vanity weapons list starts 2 positions lower than other types
            y1 += 2 * item_y_difference
            first_few = min(1, count)
        else:
            first_few = min(3, count)
        # scanning first 0-3 items, moving scanning area by item_y_difference
        for i in range(first_few):
            pa.click(x1, y1)
            time.sleep(0.01)
            if only_tradable and is_not_tradable(px, py):
                y1 += item_y_difference
                continue
            items[type_name].append(recognize(x1, y1, x1 + w, y1 + h).strip())
            y1 += item_y_difference
        for i in range(count - first_few):
            pa.click(x1, y1)
            time.sleep(0.01)
            if only_tradable and is_not_tradable(px, py):
                pa.scroll(-1)
                continue
            items[type_name].append(recognize(x1, y1, x1 + w, y1 + h).strip())
            pa.scroll(-1)


def list_items(items, path):
    with open(path, "w") as file:
        for type, list_of_items in items.items():
            file.write(f"{type}:\n")
            for item in list_of_items:
                file.write(f"{item.replace("’", "'")}\n")
            file.write("\n")


def recognize(x1, y1, x2, y2, is_number=False, count_image_path=""):
    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    if is_number:
        temp_image_path = count_image_path
        screenshot.save(temp_image_path)
        # makes the image grayscale
        im_gray = cv2.imread(temp_image_path, cv2.IMREAD_GRAYSCALE)
        # makes the image black and white based on threshold value
        thresh = 100
        im_bw = cv2.threshold(im_gray, thresh, 255, cv2.THRESH_BINARY)[1]
        # upscales the image to help tesseract recognize it
        upscaled_image = cv2.resize(
            im_bw, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC
        )
        cv2.imwrite(temp_image_path, upscaled_image)
        # use tesseract to extract the number from the image
        extracted_text = pytesseract.image_to_string(
            upscaled_image,
            config="--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789",
        )
    else:
        extracted_text = pytesseract.image_to_string(screenshot, config="--psm 7")

    return extracted_text


if __name__ == "__main__":
    main()

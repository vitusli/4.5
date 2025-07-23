import os
import struct

import numpy as np
import OpenImageIO as oiio

def read_dat_file(path):
    icon_data = {
        'name': None,
        "size_x": None,
        "size_y": None,
        "start_x": None,
        "start_y": None,
        "triangles": []
    }

    if os.path.exists(path):

        with open(path, 'rb') as file:
            icon_data['name'] = os.path.basename(path)

            header = file.read(8)
            identifier, size_x, size_y, start_x, start_y = struct.unpack('4s4B', header)

            icon_data["size_x"] = size_x
            icon_data["size_y"] = size_y
            icon_data["start_x"] = start_x
            icon_data["start_y"] = start_y

            file.seek(0, 2)  # move to end of file
            file_end = file.tell()
            file.seek(8)  # go back to after header

            total_triangle_count = (file_end - 8) // 18
            coord_size = total_triangle_count * 6
            color_size = total_triangle_count * 12

            tris_coords = file.read(coord_size)
            tris_coords = struct.unpack(f'{total_triangle_count * 6}B', tris_coords)

            tris_colors = file.read(color_size)
            tris_colors = struct.unpack(f'{total_triangle_count * 12}B', tris_colors)

            for i in range(total_triangle_count):
                coord_indices = slice(i * 6, (i + 1) * 6)
                color_indices = slice(i * 12, (i + 1) * 12)

                coords = (
                    (tris_coords[coord_indices][0], tris_coords[coord_indices][1]),
                    (tris_coords[coord_indices][2], tris_coords[coord_indices][3]),
                    (tris_coords[coord_indices][4], tris_coords[coord_indices][5]),
                )
                colors = (
                    (tris_colors[color_indices][0], tris_colors[color_indices][1], tris_colors[color_indices][2], tris_colors[color_indices][3]),
                    (tris_colors[color_indices][4], tris_colors[color_indices][5], tris_colors[color_indices][6], tris_colors[color_indices][7]),
                    (tris_colors[color_indices][8], tris_colors[color_indices][9], tris_colors[color_indices][10], tris_colors[color_indices][11])
                )

                icon_data["triangles"].append((coords, colors))

            return icon_data

def create_png_from_icon_data(icon_data, path, supersample=2):
    def fill_triangle(buffer, coords, color):
        coords = sorted(coords, key=lambda k: k[1])
        x0, y0 = coords[0]
        x1, y1 = coords[1]
        x2, y2 = coords[2]

        def interpolate(y1, x1, y2, x2, y):
            if y2 == y1:
                return x1
            return x1 + (y - y1) * (x2 - x1) / (y2 - y1)

        for y in range(max(y0, 0), min(y2, buffer.shape[0] - 1) + 1):
            if y < y1:
                x_a = interpolate(y0, x0, y1, x1, y)
                x_b = interpolate(y0, x0, y2, x2, y)
            else:
                x_a = interpolate(y1, x1, y2, x2, y)
                x_b = interpolate(y0, x0, y2, x2, y)

            if x_a > x_b:
                x_a, x_b = x_b, x_a

            for x in range(max(int(x_a), 0), min(int(x_b) + 1, buffer.shape[1] - 1)):
                buffer[y, x] = color

    size_x, size_y = icon_data['size_x'] * supersample, icon_data['size_y'] * supersample

    buffer = np.zeros((size_y, size_x, 4), dtype=np.float32)

    for triangle in icon_data["triangles"]:
        coords, colors = triangle
        fill_color = np.array(colors[0]) / 255.0  # normalize colors to 0-1 range for OIIO

        scaled_coords = [(int(x * supersample), int(y * supersample)) for (x, y) in coords]

        flipped_coords = [(x, size_y - y) for (x, y) in scaled_coords]

        fill_triangle(buffer, flipped_coords, fill_color)

    scaled_image = oiio.ImageBuf(oiio.ImageSpec(size_x, size_y, 4, 'uint8'))
    scaled_image.set_pixels(scaled_image.roi, buffer)

    image = oiio.ImageBuf(oiio.ImageSpec(icon_data['size_x'], icon_data['size_y'], 4, 'uint8'))
    oiio.ImageBufAlgo.resize(image, scaled_image, filtername="lanczos3")

    image.write(path)

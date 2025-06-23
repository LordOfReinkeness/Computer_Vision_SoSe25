import numpy as np
from matplotlib import pyplot as plt


def bilinear_neighbor(img, loc):
    if np.array_equal(loc, np.floor(loc)):
        return img[int(loc[1])][int(loc[0])]

    img_height, img_width = img.shape[:2]
    x0, y0 = int(np.floor(loc[0])), int(np.floor(loc[1]))

    if x0 < 0 or x0 + 1 >= img_width or y0 < 0 or y0 + 1 >= img_height:
        return 0

    adjacent_pixels = img[y0:y0+2, x0:x0+2]

    dx, dy = loc[0] - x0, loc[1] - y0

    return (adjacent_pixels[0,0] * (1 - dx) * (1 - dy)
            + adjacent_pixels[0,1] * dx       * (1 - dy)
            + adjacent_pixels[1,0] * (1 - dx) * dy
            + adjacent_pixels[1,1] * dx       * dy)


def projective_transform(H, img, dst_height, dst_width):
    target_matrix = np.zeros((dst_height, dst_width, img.shape[2]), dtype=img.dtype)

    if np.linalg.det(H) == 0:
        print("Transformation not possible: det(A^-1) = 0")
        return target_matrix

    for y in range(dst_height):
        for x in range(dst_width):

            loc_h = H.dot([x, y, 1])
            loc = loc_h[:2] / loc_h[2]

            target_matrix[y][x] = bilinear_neighbor(img, loc)

    return target_matrix


def rectify_homography(H, img):
    h, w = img.shape[:2]
    corners = np.array([[0, 0, 1], [w - 1, 0, 1], [w - 1, h - 1, 1], [0, h - 1, 1]]).T
    transformed_corners = H @ corners
    transformed_corners = transformed_corners[:2] / transformed_corners[2]

    min_x, max_x = transformed_corners[0].min(), transformed_corners[0].max()
    min_y, max_y = transformed_corners[1].min(), transformed_corners[1].max()

    canvas_width = int(np.ceil(max_x - min_x))
    canvas_height = int(np.ceil(max_y - min_y))

    T_offset = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]])
    H_rectified = T_offset @ H

    return H_rectified, canvas_height, canvas_width

def display_images(images, descriptions=None, title=None):
    n = len(images)

    if descriptions is None:
        descriptions = ['Original', 'Transformed']

    descriptions = descriptions[:n] + [''] * max(0, n - len(descriptions))

    fig = plt.figure()

    if title:
        fig.suptitle(title)

    for i, img in enumerate(images, 1):
        ax = fig.add_subplot(1, n, i)
        ax.imshow(img)
        ax.axis('off')
        if descriptions[i - 1]:
            ax.set_title(descriptions[i - 1])

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()
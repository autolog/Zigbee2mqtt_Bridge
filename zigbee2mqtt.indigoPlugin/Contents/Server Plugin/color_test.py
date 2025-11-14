from colormath.color_objects import XYZColor, sRGBColor, xyYColor
from colormath.color_conversions import convert_color

try:
    # rgb = sRGBColor(0.1, 0.2, 0.3)
    # xyz = convert_color(rgb, XYZColor, target_illuminant='d50')

    breakpoint = 1

    z_value = 1.0
    observer_value = '10'

    # xyz_red_x = 0.1704
    # xyz_red_y = 0.709
    # xyz_red_z = 1.0 - xyz_red_x - xyz_red_y
    #
    # xyz_red_Y = 1.0
    # xyz_red_X = (xyz_red_Y / xyz_red_y) * xyz_red_x
    # xyz_red_Z = (xyz_red_Y / xyz_red_y) * xyz_red_z

    # xyz_red = XYZColor(xyz_red_X, xyz_red_Y, xyz_red_Z, observer=observer_value)

    # xyz_red = xyYColor(0.6942, 0.2963, z_value, observer=observer_value)
    xyz_green = xyYColor(0.3251, 0.3967, z_value, observer=observer_value)
    # xyz_blue = xyYColor(0.1355, 0.0399, z_value, observer=observer_value)
    # xyz_cyan = xyYColor(0.1461, 0.2431, z_value, observer=observer_value)
    # xyz_magenta = xyYColor(0.3093,  0.135, z_value, observer=observer_value)

    rgb = convert_color(xyz_green, sRGBColor)

    rgb_tuple = rgb.get_value_tuple()

    rgb_tuple_red = rgb_tuple[0]
    rgb_tuple_green = rgb_tuple[1]
    rgb_tuple_blue = rgb_tuple[2]

    if rgb_tuple_red > 1.0:
        rgb_tuple_red = 1.0
    if rgb_tuple_green > 1.0:
        rgb_tuple_green = 1.0
    if rgb_tuple_blue > 1.0:
        rgb_tuple_blue = 1.0

    native_red = rgb_tuple_red * 255
    native_green = rgb_tuple_green * 255
    native_blue = rgb_tuple_blue * 255

    indigo_red = int(rgb_tuple_red * 100)
    indigo_green = int(rgb_tuple_green * 100)
    indigo_blue = int(rgb_tuple_blue * 100)

    rgb_Test_red = sRGBColor(1.0, 0.0, 0.0)
    rgb_Test_green = sRGBColor(0.0, 1.0, 0.0)
    rgb_Test_blue = sRGBColor(0.0, 0.0, 1.0)
    rgb_Test_cyan = sRGBColor(0.0, 1.0, 2.0)
    rgb_Test_magenta = sRGBColor(1.0, 0.0, 1.0)

    print(f"RED = {convert_color(rgb_Test_red, XYZColor)}")
    print(f"GREEN = {convert_color(rgb_Test_green, XYZColor)}")
    print(f"BLUE = {convert_color(rgb_Test_blue, XYZColor)}")
    print(f"CYAN = {convert_color(rgb_Test_cyan, XYZColor)}")
    print(f"MAGENTA = {convert_color(rgb_Test_magenta, XYZColor)}")





    breakpoint = 2

except Exception as Exception_Message:
    brekapoint = 3
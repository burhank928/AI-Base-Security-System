from license_number_extraction_pkg.yolov5 import detect


def license_number_extraction_module(user_id):
    detect.run(source=0, weights='license_number_extraction_pkg/yolov5/weights/best.pt', conf_thres=0.6, user_id=user_id, nosave=False)


# if __name__ == '__main__':
#     user_id1 = "0no4RPQyRAZf1GybOaBYsqXwBbx2"
#     license_number_extraction_module(user_id1)

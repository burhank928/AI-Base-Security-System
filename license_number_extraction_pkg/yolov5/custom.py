import cv2 as cv
import time
from threading import Thread


from database import db

registered_license_numbers = []
notified = []


def on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "REMOVED":
            data = change.document.to_dict()
            index = registered_license_numbers.index(data['number_plate'])
            registered_license_numbers.pop(index)
        elif change.type.name == "ADDED" or change.type.name == "MODIFIED":
            data = change.document.to_dict()
            registered_license_numbers.append(data['number_plate'])

    # print(registered_license_numbers)


def set_snapshot_Persons(user_id):
    doc_ref = db.collection(user_id).document('data').collection('Persons')
    doc_watch = doc_ref.on_snapshot(on_snapshot)


def drawRec(excluding_regions, imc):
    img = imc.copy()
    cv.rectangle(img, excluding_regions[0][0], excluding_regions[0][1], (0, 255, 0), 3)
    cv.rectangle(img, excluding_regions[1][0], excluding_regions[1][1], (0, 255, 0), 3)
    # cv.imwrite("portion.jpg", img)


def getExcludingRegions(xyxy_NP, imc):
    start_x = int(xyxy_NP[0])
    start_y = int(xyxy_NP[1])
    end_x = int(xyxy_NP[2])
    end_y = int(xyxy_NP[3])

    width = xyxy_NP[2] - xyxy_NP[0]
    height = xyxy_NP[3] - xyxy_NP[1]

    point1 = (start_x + (int(width / 3) * 2), start_y)
    point2 = (start_x + int(width), start_y + int(height / 2))

    point3 = (start_x + int(width / 3) * 2, start_y + int(height / 2))
    point4 = (start_x + int(width), start_y + int(height))

    excluding_regions = [
        [point1, point2],
        [point3, point4]
    ]

    # drawRec(excluding_regions, imc)
    return excluding_regions


def errorApproimation(list_of_labels):
    sum_of_area = 0
    for element in list_of_labels:
        sum_of_area += element[2]
    avg = sum_of_area / len(list_of_labels)
    error = avg * .2

    return avg - error


def inRegionOfIntrest(region, element):
    if (region[0][0] < element[3][0] and region[0][1] < element[3][1]) and (
            region[1][0] > element[3][0] and region[1][1] > element[3][1]):
        return True
    return False


def extractNumber(list_of_labels, xyxy_NP, annotator, imc):
    alpha = []
    numeric = []
    error_Appr = errorApproimation(list_of_labels)
    excluding_regions = getExcludingRegions(xyxy_NP, imc)

    for element in list_of_labels:
        if element[2] > error_Appr:
            if element[0].isdigit() and not inRegionOfIntrest(excluding_regions[0], element):
                annotator.box_label(element[1], element[0], color=element[4])
                numeric.append(element.copy())
            elif element[0].isalpha() and not inRegionOfIntrest(excluding_regions[1], element):
                annotator.box_label(element[1], element[0], color=element[4])
                alpha.append(element.copy())
        else:
            print("Below Avg: ", element[0])

    for i in range(0, len(alpha)):
        mini = alpha[i]
        index = i
        for k in range(i, len(alpha)):
            if mini[3][0] > alpha[k][3][0]:
                mini = alpha[k]
                index = k
        temp = alpha[i].copy()
        alpha[i] = alpha[index]
        alpha[index] = temp

    for i in range(0, len(numeric)):
        mini = numeric[i]
        index = i
        for k in range(i, len(numeric)):
            if mini[3][0] > numeric[k][3][0]:
                mini = numeric[k]
                index = k
        temp = numeric[i].copy()
        numeric[i] = numeric[index]
        numeric[index] = temp

    number_plate = ""
    for element in alpha:
        number_plate += element[0]

    for element in numeric:
        number_plate += element[0]

    return number_plate


def getLabels(list_of_labels):
    lis = []
    for element in list_of_labels:
        lis.append(element[0])
    return lis


def getLicenseNumbers(list_of_NP, list_of_other_labels, annotator, imc):
    license_numbers = []

    print("List of other labels: ", getLabels(list_of_other_labels))
    for np in list_of_NP:
        list_of_labels = []
        region = [(np[1][0], np[1][1]), (np[1][2], np[1][3])]

        for element in list_of_other_labels:
            if inRegionOfIntrest(region, element):
                list_of_labels.append(element)
        print("List of labels: ", getLabels(list_of_labels))

        if len(list_of_labels) > 0:
            license_number = extractNumber(list_of_labels, np[1], annotator, imc)
            license_numbers.append(license_number)

    return license_numbers


def set_timer(license_number):
    time.sleep(120)
    notified.remove(license_number)


def add_to_History(user_id, license_number):
    if license_number not in notified:
        notified.append(license_number)
        Thread(target=set_timer, args=(license_number,))
        doc_ref = db.collection(user_id).document('data').collection('History')
        doc_ref.add({
            'message': 'Door has been unlocked for ' + license_number + ' at ' + time.ctime() + '.',
            'name': license_number,
            'time': time.ctime()
        })


def send_notification(user_id, unknown):
    if unknown not in notified:
        notified.append(unknown)
        Thread(target=set_timer, args=(unknown,))
        doc_ref = db.collection(user_id).document('data').collection('Notification')
        doc_ref.add({
            'message': 'Unknown License Number has been detected, do want to unlock the door?' + '.',
            'time': time.ctime()
        })


def compareLicenseNumber(user_id, license_numbers):
    for license_number in license_numbers:
        if license_number in registered_license_numbers:
            add_to_History(user_id, license_number)
            print(license_number, " is registered by user.")
        else:
            send_notification(user_id, license_number)
            print(license_number, " is not registered by user.")

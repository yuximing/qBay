'''
A user cannot book a listing for his/her listing.
A user cannot book a listing that costs
    more than his/her balance.
A user cannot book a listing that is
    already booked with the overlapped dates.
A booked listing will show up on the
    user's home page (up-coming stages).
'''

import uuid
import sqlite3
from datetime import datetime
import os
path = os.path.dirname(os.path.abspath(__file__))


def booking_requirement_checking(tsc) -> dict:
    '''
    This function checks if a booking attempt is valid
    according to the requirements.
    Parameter: tsc - a dict format info passed by the
    frontend form inputs
    Return: a dict format info containing all column
    info needed to save the valid booking to db
    Exception: may raise InvalidBooking exception if
    requirements are violated.
    '''

    connection = sqlite3.connect(path + "/data.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT balance FROM Users "
        "WHERE user_id = (?)",
        (tsc["user_id"],))

    (balance, ) = cursor.fetchone()

    cursor.execute(
        "SELECT user_id, price FROM "
        "Properties WHERE prop_id = (?)",
        (tsc["prop_id"],))
    (user_id, price) = cursor.fetchone()

    user_check_in_date = datetime.strptime(
        tsc["check_in_date"], "%Y-%m-%dT%H:%M")

    user_check_out_date = datetime.strptime(
        tsc["check_out_date"], "%Y-%m-%dT%H:%M")

    total_days = float((user_check_out_date - user_check_in_date).days)

    total_price = price * total_days

    # A user cannot book a listing that
    # costs more than his/her balance.
    if float(balance) < float(total_price):
        raise InvalidBooking("User can't afford the property")

    # A user cannot book a listing for his/her listing.
    if user_id == tsc["user_id"]:
        raise InvalidBooking("User can't book his own property")

    cursor.execute(
        "SELECT check_in_date, "
        "check_out_date FROM Transactions WHERE property_id = (?)",
        (tsc["prop_id"],))

    rows = cursor.fetchall()

    if rows is not None:
        for row in rows:
            (check_in, check_out) = row
            check_in_date = datetime.strptime(
                check_in, "%Y-%m-%dT%H:%M")

            check_out_date = datetime.strptime(
                check_out, "%Y-%m-%dT%H:%M")
            '''
            check_in_date       check_out_date
                C1----------------------C2
            
                    user_check_in_date         user_check_out_date
                        U1--------------------------------U2
                        
                    check_in_date       check_out_date
                        C1----------------------C2
            
            user_check_in_date         user_check_out_date
                U1----------------------------U2
                
            check_in_date                   check_out_date
            C1-----------------------------------C2
        
                user_check_in_date       user_check_out_date
                    U1----------------------U2
            '''

            # maybe buggy
            Overlap1 = check_out_date >= user_check_in_date \
                and check_out_date <= user_check_out_date
            Overlap2 = check_in_date >= user_check_in_date \
                and check_in_date <= user_check_out_date

            # reverse it,
            Overlap3 = user_check_out_date >= check_in_date \
                and user_check_in_date <= check_out_date
            Overlap4 = user_check_in_date >= check_in_date \
                and user_check_in_date <= check_out_date

            if Overlap1 or Overlap2 or Overlap3 or Overlap4:
                raise InvalidBooking("the selected date is overlapped")

    transaction = {
        **tsc
    }
    transaction["tsc_id"] = uuid.uuid4().hex
    transaction["tsc_date"] = datetime.now()
    transaction["tsc_price"] = total_price
    transaction["remaining_balance"] = float(balance) - float(total_price)

    return transaction


def save_transaction_record(tsc):
    '''
    This function saves the valid booking to the db.
    Parameter: tsc - savable booking in dict format
    Return: None
    Exception: may raise InvalidBooking exception if
    saving fails.
    '''
    try:
        connection = sqlite3.connect(path + "/data.db")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Transactions \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (tsc["tsc_id"],
                        tsc["user_id"],
                        tsc["prop_id"],
                        tsc["tsc_date"],
                        tsc["tsc_price"],
                        tsc["check_in_date"],
                        tsc["check_out_date"],
                        tsc["guest_number"],
                        ))

        # reduce the balance here
        cursor.execute("UPDATE Users SET balance = (?) WHERE user_id = (?)",
                       (tsc["remaining_balance"], tsc["user_id"]))
        connection.commit()
        connection.close()
    except InvalidBooking:
        raise InvalidBooking("Transcation failed:(")


if __name__ == "__main__":
    import json
    from exceptions import InvalidBooking

    test_tsc = {
        "user_id": "20a7066e8e844759a99a20ecbd6935fe",
        "prop_id": "ebbc91cdf0f646e9993222418c39c69d",
        "check_in_date": "2022-06-01T08:30",
        "check_out_date": "2022-06-04T08:30",
        "guest_number": 2,
    }

    test_tsc2 = {
        "user_id": "b36524c626e64b15b3dcebb6d21dd5d8",
        "prop_id": "ebbc91cdf0f646e9993222418c39c69d",
        "check_in_date": "2022-04-02T08:30",
        "check_out_date": "2022-10-30T08:30",
        "guest_number": 3,
    }
    try:
        booking_requirement_checking(test_tsc)
        1 / 0
    except InvalidBooking as IB:
        print("pass !")

    return_tsc = booking_requirement_checking(test_tsc2)
    save_transaction_record(return_tsc)

    connection = sqlite3.connect(path + "/data.db")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM \
                    Transactions WHERE tsc_id=(?)",
                   (return_tsc["tsc_id"],))
    connection.commit()
    connection.close()
    # additional line to print the datetime now
    print(json.dumps(return_tsc, indent=4, sort_keys=True, default=str))
else:

    from qbay.exceptions import InvalidBooking

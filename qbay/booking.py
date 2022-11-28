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


def booking_requirement_checking(tsc) -> dict:
    import os
    path = os.path.dirname(os.path.abspath(__file__))
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

    # A user cannot book a listing that
    # costs more than his/her balance.
    if float(balance) < float(price):
        raise InvalidBooking("User can't afford the property")

    # A user cannot book a listing for his/her listing.
    if user_id == tsc["user_id"]:
        raise InvalidBooking("User can't book his own property")

    cursor.execute(
        "SELECT check_in_date, "
        "check_out_date FROM Transactions WHERE property_id = (?)",
        (tsc["prop_id"],))

    row = cursor.fetchone()

    if row is not None:
        (check_in_date, check_out_date) = row
        user_check_in_date = datetime.strptime(
            tsc["check_in_date"], "%Y-%m-%dT%H:%M:%S")

        user_check_out_date = datetime.strptime(
            tsc["check_out_date"], "%Y-%m-%dT%H:%M:%S")
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

    return transaction


def save_transaction_record(tsc):
    try:
        import os
        path = os.path.dirname(os.path.abspath(__file__))
        connection = sqlite3.connect(path + "/data.db")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Transactions \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (tsc["tsc_id"],
                        tsc["user_id"],
                        tsc["property_id"],
                        tsc["tsc_date"],
                        tsc["tsc_price"],
                        tsc["check_in_date"],
                        tsc["check_out_date"],
                        tsc["guest_number"],
                        ))
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
        "check_out_date": "2022-08-01T08:30",
        "guest_number": 2,
    }

    test_tsc2 = {
        "user_id": "b36524c626e64b15b3dcebb6d21dd5d8",
        "prop_id": "ebbc91cdf0f646e9993222418c39c69d",
        "check_in_date": "2022-06-01T08:30",
        "check_out_date": "2022-08-01T08:30",
        "guest_number": 3,
    }
    try:
        booking_requirement_checking(test_tsc)
        1 / 0
    except InvalidBooking as IB:
        print("pass !")

    t = booking_requirement_checking(test_tsc2)

    # additional line to print the datetime now
    print(json.dumps(t, indent=4, sort_keys=True, default=str))
else:

    from qbay.exceptions import InvalidBooking

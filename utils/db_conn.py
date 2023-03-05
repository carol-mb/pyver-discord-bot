import configparser

import mysql.connector


config = configparser.ConfigParser()
config.read('config.ini')

# selects data from database
def query_select(query: str) -> object:
    while(True):
        try:
            db = mysql.connector.connect(
                host='{}'.format(config['MYSQL']['host']),
                user='{}'.format(config['MYSQL']['user']),
                passwd='{}'.format(config['MYSQL']['password']),
                database='{}'.format(config['MYSQL']['database'])
            )
        except:
            pass
        else:
            break

    print("db request")

    my_cursor = db.cursor()
    my_cursor.execute(query)

    select_result = my_cursor.fetchall()

    my_cursor.close()
    db.close()

    return select_result

# updates database
def query_update(query: str):
    while(True):
        try:
            db = mysql.connector.connect(
                host='{}'.format(config['MYSQL']['host']),
                user='{}'.format(config['MYSQL']['user']),
                passwd='{}'.format(config['MYSQL']['password']),
                database='{}'.format(config['MYSQL']['database'])
            )
        except:
            pass
        else:
            break

    print("db request")

    my_cursor = db.cursor(buffered=True)
    my_cursor.execute(query)

    my_cursor.close()

    db.commit()

    db.close()

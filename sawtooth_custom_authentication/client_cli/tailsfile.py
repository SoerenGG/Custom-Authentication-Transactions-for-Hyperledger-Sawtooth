import json
from pathlib import Path



def create_tailsfile(servicename):                                      #erstellt einen tailsfile, benötigt servicename
    with open('{}.json'.format(servicename), 'x') as f:
        json.dump(['empty'], f)
        f.close()


def write_tailsfile_data(servicename, acc_value, acc_value_updated, elements, usernames):      #speichert In dem zuvor erstellten file
    with open('{}.json'.format(servicename), 'w') as f:
        data = {'acc_value': acc_value, 'acc_value_updated': acc_value_updated, 'elements':[], 'usernames': usernames}
        data['elements'] = elements
        json.dump(data, f)
        f.close


def get_tailsfile_data(servicename):
    if Path('{}.json'.format(servicename)).is_file():  # checken ob username schon angelegt ist, reinladen wenn username schon geaddet
        file = open('{}.json'.format(servicename), )
        data = json.load(file)
        acc_value = data['acc_value']
        acc_value_updated = data['acc_value_updated']
        elements = data['elements']
        usernames = data['usernames']
        return acc_value, acc_value_updated, elements, usernames


if __name__ == '__main__':
    create_tailsfile('service1')
    acc_value= 1
    acc_value_updated = 2
    elements = [1, 2, 3]
    usernames = ["user1", "user2", "user3"]
    write_tailsfile_data('service1', acc_value, acc_value_updated, elements, usernames)
    acc_value_loaded, acc_value_updated_loaded, elements_loaded, usernames= get_tailsfile_data('service1')
    print(acc_value_loaded, acc_value_updated_loaded, elements_loaded)

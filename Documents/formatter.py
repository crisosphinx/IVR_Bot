from Documents.documentation import *
import os
from Platform import GoogleComm


def convert_to_output(week=str(), assignments=None) -> str:
    """
    Convert the passed information and turn it into a document to send back to the user

    :param week: Which week is next.
    :param assignments: The dictionary of assignments due.
    :return:
    """

    # assignments = _work[week]
    names = list(assignments.keys())
    num_asgnmnts = len(names)
    i = 1

    formatted_doc = list()
    formatted_doc.append("**{0}**".format(week))
    while i <= num_asgnmnts:
        assignment = names[i-1]
        date = assignments[assignment][0].split("-")
        _formatted_date = "{0} {1}, {2}".format(MONTHS[int(date[1])], resolve_suffix(int(date[2])), date[0])
        _assign = """
Assignment {0})
    - {1}
    - Due: {2}
    - Link: _{3}_
""".format(i, assignment, _formatted_date, assignments[assignment][1])
        formatted_doc.append(_assign)
        i += 1

    doc = "".join(formatted_doc)

    return doc


def resolve_suffix(number=int()) -> str:
    """
    Pass a number and get the correct suffix attached to it and return said number

    :param number: pass an integer
    :return:
    """
    number_suffix = ["th", "st", "nd", "rd"]

    if number % 10 in [1, 2, 3] and number not in [11, 12, 13]:
        return "{0}{1}".format(number, number_suffix[number % 10])
    else:
        return "{0}{1}".format(number, number_suffix[0])


def combine_roster(_classname: str):
    classes = GoogleComm.AttainGoogleClass(_classname=_classname).roster()
    roster_info = """
Available courses ({0}):
{1}
""".format(classes[0], classes[1])
    return roster_info


def find_file(name=str()):
    # Our token path
    if os.name == 'nt':
        json_path = 'J:\\{0}.json'.format(name)
        if not os.path.isfile(json_path):
            json_path = 'B:\\{0}.json'.format(name)
    else:
        json_path = '/usr/bin/{0}.json'.format(name)

    return json_path

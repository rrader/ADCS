import json
from optparse import OptionParser
from base import Iterative2Model, Iterative3Model, Iterative5Model


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-r", dest="races", action="store_true", help="find races")
    parser.add_option("-2", dest="model", action="store_const", help="2-model [default]", const=2)
    parser.add_option("-3", dest="model", action="store_const", help="3-model", const=3)
    parser.add_option("-5", dest="model", action="store_const", help="5-model", const=5)
    (options, args) = parser.parse_args()
    if not options.filename:
        options.filename = 'default.json'
    if not options.model:
        options.model = 2
    print(options.filename)
    print("Using %d-model" % options.model)
    data = json.loads(open(options.filename).read())
    if options.model == 3:
        Modeller = Iterative3Model
    elif options.model == 5:
        Modeller = Iterative5Model
    else:
        Modeller = Iterative2Model
    modeller = Modeller(data)
    if options.races:
        modeller.find_races()
    else:
        modeller.do_model()

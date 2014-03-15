import json
from optparse import OptionParser
from base import Iterative2Model, Iterative3Model, Iterative5Model, Seidel3Model, Seidel5Model, Seidel2Model


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="open FILE", metavar="FILE")
    parser.add_option("-r", dest="races", action="store_true", help="find races")

    parser.add_option("-I", dest="alg", action="store_const", help="iterative algorithm [default]", const='iterative')
    parser.add_option("-S", dest="alg", action="store_const", help="Seidel algorithm", const='seidel')
    parser.add_option("-k", dest="ranking", action="store_true", help="Seidel algorithm, turn on ranking")

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

    if options.alg is None or options.alg == 'iterative':
        if options.model == 3:
            Modeller = Iterative3Model
        elif options.model == 5:
            Modeller = Iterative5Model
        else:
            Modeller = Iterative2Model
    elif options.alg == 'seidel':
        if options.model == 3:
            Modeller = Seidel3Model
        elif options.model == 5:
            Modeller = Seidel5Model
        else:
            Modeller = Seidel2Model
    else:
        raise ValueError(options.alg)
    modeller = Modeller(data)
    if hasattr(modeller, 'set_ranking'):
        modeller.set_ranking(options.ranking)

    if options.races:
        modeller.find_races()
    else:
        modeller.do_model()

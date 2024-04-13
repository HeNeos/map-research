import argparse

from shortest_path.dijkstra import run_dijkstra
from shortest_path.a_star import run_a_star

map_to_strategies = {
  "shortest_path_dijkstra": run_dijkstra,
  "shortest_path_a_star": run_a_star
}


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    prog = "MapUtils",
    description = "Different set of algorithms strategies applied to real maps"
  )
  parser.add_argument("-u", "--utility", type=str, nargs=1, help="utility", default=argparse.SUPPRESS)
  parser.add_argument("-l", "--location", nargs="?", type=str, help="location where to apply", default=argparse.SUPPRESS)
  parser.add_argument("--source", nargs="?", type=str, help="loc,lat for the source point", default=argparse.SUPPRESS)
  parser.add_argument("--destination", nargs="?", type=str, help="loc,lat for the destination point", default=argparse.SUPPRESS)
  args = parser.parse_args()

  if "utility" not in args:
    args.utility = [None]

  if args.utility[0] not in map_to_strategies.keys():
    raise Exception
  if "location" not in args:
    args.location = None
  if "source" not in args:
    args.source = None
  if "destination" not in args:
    args.destination = None

  strategy = map_to_strategies[args.utility[0]]

  strategy(args.location, args.source, args.destination)
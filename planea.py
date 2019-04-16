#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

import argparse
import plan


# argument parsing part
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("--daily",
                   help="If you want to calculate how many words a day you will need.",
                    action="store_true")
group.add_argument("--time",
                    help="If you want to know how much total time will it take to finish.",
                    action="store_true")
group.add_argument("--words",
                    help="If you want to know how many words will it have at the end.",
                    action="store_true")
args = parser.parse_args()


def main():
    if args.daily:
        print("calculate the words a day you will need.")
        newplan = plan.Plan(total=80000, time=60)
        newplan.calculate_daily()
        newplan.show()
    elif args.time:
        print("Calculate the time you'll need to finish your work.")
        newplan = plan.Plan(total=80000, daily=1500)
        newplan.calculate_time()
        newplan.show()
    elif args.words:
        print("Calculate the total words your work will have.")
        newplan = plan.Plan(daily=1500, time=60)
        newplan.calculate_words()
        newplan.show()
    else:
        print("No option selected. Doing nothing ...")
    return


if __name__ == "__main__":
    main()

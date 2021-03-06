import os
import json

import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine
from django.core.management import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Automatically insert airfoil aerodynamics into database."

    def add_arguments(self, parser):
        parser.add_argument("airfoil",
                            metavar="AirfoilName",
                            type=str,
                            help="Airfoil name code, ex: naca2412")
        parser.add_argument("filename",
                            metavar="Filename",
                            type=str,
                            help="Airfoil aerodynamic file")
        parser.add_argument("re",
                            metavar="ReynoldNumber",
                            type=float,
                            help="Reynold number ex: 123456.789")
        parser.add_argument("ma",
                            metavar="MachNumber",
                            type=float,
                            help="Mach number ex: 0.1")

    def handle(self, *args, **options):
        curr_dir = settings.BASE_DIR
        name = options.get("filename")
        airfoil = options.get("airfoil")
        re = options.get("re")
        ma = options.get("ma")
        aero_file = os.path.join(curr_dir, name)
        username = os.environ['DB_USERNAME']
        password = os.environ['DB_PASSWORD']
        host = os.environ['DB_HOST']
        port = os.environ['DB_PORT']
        dbname = os.environ['DB_NAME']
        engine = create_engine(f"postgresql://{username}:{password}@{host}:{port}/{dbname}")

        try:
            df = pd.read_fwf(aero_file, skiprows=11, header=None)
            df.columns = ["alpha", "cl", "cd", "cdp", "cm", "topxtr", "botxtr", "cpmin", "chinge", "xcp"]
            df["nama"] = airfoil
            df["re"] = re
            df["sdf"] = df["alpha"].apply(lambda row: f"airfoil/{airfoil}_{row}.png")
            df = df[["nama", "re", "alpha", "cl", "cd", "cm", "sdf"]]
            df["dibuat"] = timezone.now()
            df["diubah"] = timezone.now()
            df["cpx"] = read_cp()
            df["mach"] = ma

            df.to_sql("flow_koleksiairfoil", engine, if_exists="append", index=False)

            self.stdout.write(self.style.SUCCESS("Successfully insert to database."))
        except ValueError as err:
            raise CommandError(str(err))


def read_cp():
    import numpy as np

    total_cp = 48
    curr_dir = settings.BASE_DIR
    cp_file = os.path.join(curr_dir, "cp")
    koleksi = []

    for cp in os.listdir(cp_file):
        df = pd.read_fwf(os.path.join(curr_dir, "cp", cp), skiprows=6, header=None)
        df.columns = ["x", "cpi", "cpv", "qi", "qv"]
        df = df[["x", "cpv"]]
        idx = np.linspace(0, (df.x.count() - 1) // 2, total_cp // 2, dtype=np.int)

        upper = df.iloc[:((df.x.count() - 1) // 2) + 1]
        selected_upper = upper.index.isin(idx)
        upper = upper[selected_upper]

        lower = df.iloc[(df.x.count() - 1) // 2:]
        lower = lower.iloc[::-1].reset_index(drop=True)
        selected_lower = lower.index.isin(idx)
        lower = lower[selected_lower]
        lower = lower.iloc[::-1].reset_index(drop=True)

        gabung = pd.concat([upper, lower], ignore_index=True)

        koleksi.append(json.dumps(gabung.to_dict("records")))

    return koleksi

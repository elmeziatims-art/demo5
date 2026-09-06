#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de reactivite de CAD_SAAD_LIVE.xlsx.
On modifie une cellule d'entree, on recalcule TOUT avec `formulas`, on lit les
sorties 'live' (formules a cote de Tagetik). Les colonnes de FILTRE (version,
compte, exercice) sont des constantes -> lues via openpyxl (hors solution)."""
import shutil, openpyxl, formulas, warnings
warnings.filterwarnings("ignore")

SRC = "CAD_SAAD_LIVE.xlsx"
TMP = "/tmp/_react_run.xlsx"
BOOK = "_REACT_RUN.XLSX"
PROD = {"7062", "706", "708"}
DOT  = {"6811"}

# ---- metadata statique (constantes) lue une fois ----
_wb = openpyxl.load_workbook(SRC, data_only=True)
MOT_VER = {r: _wb["Moteur"]["B%d" % r].value for r in range(2, 176)}
PNL_META = {r: (str(_wb["PNL"]["B%d" % r].value),      # account
                _wb["PNL"]["C%d" % r].value,           # exercice
                _wb["PNL"]["D%d" % r].value)           # version
            for r in range(2, 1347)}
_wb.close()

def key(sheet, cell): return "'[%s]%s'!%s" % (BOOK, sheet.upper(), cell)

def num(sol, sheet, cell):
    v = sol[key(sheet, cell)].value
    try: return float(v[0, 0])
    except Exception:
        try: return float(v)
        except Exception: return v

def run(edits):
    shutil.copy(SRC, TMP)
    wb = openpyxl.load_workbook(TMP)
    for (sheet, cell), val in edits.items():
        wb[sheet][cell] = val
    wb.save(TMP); wb.close()

    xl = formulas.ExcelModel().loads(TMP).finish()
    sol = xl.calculate()

    ca = eff = 0.0
    for r in range(2, 176):
        if MOT_VER[r] == "V01":
            ca  += num(sol, "Moteur", "R%d" % r)
            eff += num(sol, "Moteur", "P%d" % r)
    prod = charg = 0.0
    for r in range(2, 1347):
        acc, ex, ver = PNL_META[r]
        if str(ex) == "2027" and ver == "V01":
            amt = num(sol, "PNL", "H%d" % r)
            if not isinstance(amt, float): continue
            if acc in PROD: prod += amt
            elif acc.startswith("6") and acc not in DOT: charg += amt
    ebitda = prod - charg
    marge = 0.0
    for r in range(2, 176):
        v = num(sol, "Allocation", "AA%d" % r)
        if isinstance(v, float): marge += v
    rej_par = num(sol, "Pilotage", "Q13")
    rej_lyo = num(sol, "Pilotage", "Q14")
    rej_tot = sum(num(sol, "Pilotage", "Q%d" % r) for r in range(13, 27))
    return dict(CA=ca, EFF=eff, EBITDA=ebitda, MARGE=marge,
                REJ_PAR=rej_par, REJ_LYO=rej_lyo, REJ_TOT=rej_tot)

def show(name, r, base=None):
    print("\n### %s" % name)
    for k in ["CA", "EFF", "EBITDA", "MARGE", "REJ_PAR", "REJ_LYO", "REJ_TOT"]:
        v = r[k]
        if base is None:
            print("   %-8s = %14.1f" % (k, v))
        else:
            d = v - base[k]; pct = (d / base[k] * 100) if base[k] else 0
            arr = "UP  " if d > 1 else ("DOWN" if d < -1 else "=   ")
            print("   %-8s = %14.1f   d=%+13.1f (%+6.2f%%) %s" % (k, v, d, pct, arr))

if __name__ == "__main__":
    base = run({})
    show("BASELINE V01", base)
    print("\nAttendus: CA~24120981  EBITDA~3875895  MARGE~3291530  REJ_TOT=434174")

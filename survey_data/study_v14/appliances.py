"""Appliance priors by PLN connection rating (evidence tier C: survey-based).

Ownership: CLASP Indonesia Residential End-Use Survey (2020), Table 21 (penetration by
PLN class: R-1/900 VA-RTM, R-1/1,300, R-1/2,200, R-2&R-3).  Per-unit energy: same survey,
Table 52 (kWh/yr per unit) and Table 24 (observed W).  Timing: CLASP hourly-use descriptions
(lighting 17:00-05:00 peak 18-22; AC peak 19:00-05:00 with some 12-15; washer peak 08:00;
iron peaks 06, 10, 14-15; rice cooker cooks 04/08/13/17/21; pump peaks 05-06 and 16-17).
Values not in the survey (counts per home, water heater, EV, e-motorbike, dishwasher,
occupancy shares, tank presence) are ASSM and are varied in the Monte Carlo draws.
"""
import numpy as np

CLASP_COL = {900: '900RTM', 1300: '1300', 2200: '2200'}
def col(va):
    return CLASP_COL.get(va, 'R23')

OWN = {  # P(owns >= 1)
    'ac':        {'900RTM': 0.05, '1300': 0.18, '2200': 0.44, 'R23': 0.82},
    'washer':    {'900RTM': 0.38, '1300': 0.46, '2200': 0.60, 'R23': 0.87},
    'dispenser': {'900RTM': 0.24, '1300': 0.35, '2200': 0.47, 'R23': 0.77},
    'pump':      {'900RTM': 0.39, '1300': 0.37, '2200': 0.29, 'R23': 0.69},
    'iron':      {'900RTM': 0.80, '1300': 0.80, '2200': 0.84, 'R23': 0.92},
    'rice':      {'900RTM': 0.75, '1300': 0.68, '2200': 0.82, 'R23': 0.85},
    'fridge':    {'900RTM': 0.79, '1300': 0.86, '2200': 0.97, 'R23': 0.95},
    'tv':        {'900RTM': 0.95, '1300': 0.95, '2200': 0.93, 'R23': 0.97},
    # ASSM below (not reported by class in the survey)
    'fan':       {'900RTM': 0.75, '1300': 0.75, '2200': 0.70, 'R23': 0.55},
}
OWN_ASSM = {  # by VA, ASSM
    'water_heater': {900: 0.0, 1300: 0.01, 2200: 0.03, 3500: 0.08, 4400: 0.10, 5500: 0.12,
                     6600: 0.20, 7700: 0.25, 10600: 0.30},
    'emoto':        {900: 0.02, 1300: 0.03, 2200: 0.04, 3500: 0.05, 4400: 0.05, 5500: 0.05,
                     6600: 0.05, 7700: 0.05, 10600: 0.05},
    'ev':           {900: 0.0, 1300: 0.0, 2200: 0.0, 3500: 0.0, 4400: 0.0, 5500: 0.0,
                     6600: 0.03, 7700: 0.05, 10600: 0.07},
    'dishwasher':   {900: 0.0, 1300: 0.0, 2200: 0.0, 3500: 0.01, 4400: 0.02, 5500: 0.02,
                     6600: 0.04, 7700: 0.05, 10600: 0.08},
    'tank_given_pump': 0.70,
    'home_daytime':  {900: 0.65, 1300: 0.65, 2200: 0.62, 3500: 0.60, 4400: 0.60, 5500: 0.58,
                      6600: 0.55, 7700: 0.55, 10600: 0.55},
}
AC_UNITS = {1300: [1], 2200: [1, 1, 2], 3500: [1, 2], 4400: [2], 5500: [2, 3], 6600: [2, 3],
            7700: [3], 10600: [3, 4], 900: [1]}
LAMPS = {900: 6, 1300: 8, 2200: 10, 3500: 12, 4400: 14, 5500: 16, 6600: 18, 7700: 20, 10600: 25}
FANS = {900: [1, 2], 1300: [1, 2], 2200: [2, 3], 3500: [2, 3], 4400: [2, 3], 5500: [2, 3],
        6600: [2, 4], 7700: [3, 4], 10600: [3, 5]}

# CLASP Table 52 kWh/yr per unit
E_UNIT = {'lighting_lamp': 37, 'tv': 98, 'fan': 93, 'fridge': 315, 'rice': 330, 'ac': 1274,
          'dispenser': 183, 'washer': 56, 'iron': 23, 'pump': 42}

# program shapes in kW per 15-min step
SHAPE = {
    'washer': np.array([0.25, 0.30, 0.28, 0.40]),                  # 60 min, 0.31 kWh
    'iron':   np.array([0.25, 0.20, 0.20, 0.20]),                  # 60 min session, ~0.21 kWh
    'rice':   np.array([0.40, 0.40] + [0.045] * 22),               # cook 30 min + warm 5.5 h
    'dishwasher': np.array([0.10, 1.20, 0.20, 0.15, 1.10, 0.10]),  # 90 min, 0.71 kWh
}
PUMP_KW = 0.385            # CLASP observed W
PUMP_LPM = 25.0            # L/min [ASSM]
EMOTO = dict(p=0.35, e=1.5)      # kW, kWh per session [ASSM]
EV = dict(p=3.5, e=7.0)          # kW, kWh per weekday session [ASSM]
WH = dict(p=0.6, cap_kwh=1.4, e_min=0.55, loss_per_h=0.012)  # 30 L storage heater [ASSM]
AC_P_MAX = 0.75                   # kW electric per unit (1 PK class) [ASSM; CLASP mean 506 W observed]
AC_COP = 3.0

# Flexibility windows (consent-dependent candidate assumptions, matrix rows 5, 4, 9, 40, 8, 15, 28, 39, 46)
FLEX = {
    'washer': dict(latest_end_slot=60, max_delay_h=12),   # line-drying: finish by 15:00
    'iron':   dict(occupied_only=True, max_delay_h=12, earliest=28, latest_end=84),
    'rice':   dict(max_shift_h=1.0),
    'dishwasher': dict(deadline_slot=52),                 # next day 13:00 (wrap)
    'pump':   dict(quiet_from=88, quiet_to=20, reserve_frac=0.20),
    'ac':     dict(precool_h=2.0, t_comf=24.0, t_low=21.0),
}

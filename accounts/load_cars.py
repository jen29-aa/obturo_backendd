from .models import Car

CARS = [
    # HATCHBACKS & COMPACT EVs
    {
        "name": "Tata Tiago EV",
        "battery_capacity_kwh": 24,
        "max_dc_power_kw": 7.2,
        "max_ac_power_kw": 3.3,
        "connector_type": "CCS2",
    },
    {
        "name": "Tata Tigor EV",
        "battery_capacity_kwh": 26,
        "max_dc_power_kw": 25,
        "max_ac_power_kw": 3.3,
        "connector_type": "CCS2",
    },
    {
        "name": "Citroen eC3",
        "battery_capacity_kwh": 29.2,
        "max_dc_power_kw": 30,
        "max_ac_power_kw": 3.3,
        "connector_type": "CCS2",
    },
    {
        "name": "MG Comet EV",
        "battery_capacity_kwh": 17.3,
        "max_dc_power_kw": 7,
        "max_ac_power_kw": 3.3,
        "connector_type": "CCS2",
    },

    # POPULAR SUV EVs
    {
        "name": "Tata Nexon EV LR",
        "battery_capacity_kwh": 40.5,
        "max_dc_power_kw": 30,
        "max_ac_power_kw": 7.2,
        "connector_type": "CCS2",
    },
    {
        "name": "Tata Nexon EV MR",
        "battery_capacity_kwh": 30,
        "max_dc_power_kw": 30,
        "max_ac_power_kw": 7.2,
        "connector_type": "CCS2",
    },
    {
        "name": "MG ZS EV",
        "battery_capacity_kwh": 50.3,
        "max_dc_power_kw": 50,
        "max_ac_power_kw": 7.4,
        "connector_type": "CCS2",
    },
    {
        "name": "Hyundai Kona Electric",
        "battery_capacity_kwh": 39.2,
        "max_dc_power_kw": 50,
        "max_ac_power_kw": 7.2,
        "connector_type": "CCS2",
    },
    {
        "name": "Mahindra XUV400 EC",
        "battery_capacity_kwh": 34.5,
        "max_dc_power_kw": 60,
        "max_ac_power_kw": 7.2,
        "connector_type": "CCS2",
    },
    {
        "name": "Mahindra XUV400 EL",
        "battery_capacity_kwh": 39.4,
        "max_dc_power_kw": 60,
        "max_ac_power_kw": 7.2,
        "connector_type": "CCS2",
    },

    # PREMIUM EVs
    {
        "name": "BYD Atto 3",
        "battery_capacity_kwh": 60.5,
        "max_dc_power_kw": 80,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "BYD Seal",
        "battery_capacity_kwh": 82.5,
        "max_dc_power_kw": 150,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "Kia EV6",
        "battery_capacity_kwh": 77.4,
        "max_dc_power_kw": 250,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "Mercedes EQB",
        "battery_capacity_kwh": 66.5,
        "max_dc_power_kw": 100,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "BMW iX1",
        "battery_capacity_kwh": 66.5,
        "max_dc_power_kw": 130,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "BMW i4",
        "battery_capacity_kwh": 83.9,
        "max_dc_power_kw": 205,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "Volvo XC40 Recharge",
        "battery_capacity_kwh": 78,
        "max_dc_power_kw": 150,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
    {
        "name": "Volvo C40 Recharge",
        "battery_capacity_kwh": 78,
        "max_dc_power_kw": 150,
        "max_ac_power_kw": 11,
        "connector_type": "CCS2",
    },
]

def load():
    for car in CARS:
        Car.objects.get_or_create(**car)
    print("All cars loaded successfully!")

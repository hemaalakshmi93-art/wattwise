"""Reference data loaded at start-up.

Resource URLs: only home pages of well-known official bodies are listed, and
only where we are confident they exist. Entries without a verified page have
url=None on purpose. Please re-check every link before the final demo.
No subsidy amounts, scheme terms or vendor details are included.
"""

# (code, title, description, action, points)
CHALLENGES = [
    (
        "lights_off",
        "Switch off unused lights",
        "Lights left on in empty rooms add up over a month.",
        "Walk through every room today and switch off lights and fans nobody is using.",
        10,
    ),
    (
        "ac_reduce",
        "Reduce unnecessary air-conditioner usage",
        "Air conditioners are often the largest single load in a home.",
        "Raise the AC set-point by a degree or two, or use a fan for part of today. Close doors and windows while it runs.",
        15,
    ),
    (
        "weekly_compare",
        "Compare this week with last week",
        "Looking at your own numbers is the first step to changing them.",
        "Note your meter or app reading today and compare it with the same day last week. Then save a reading on My Footprint.",
        20,
    ),
    (
        "solar_explore",
        "Explore rooftop solar feasibility",
        "A rough estimate helps you decide whether to look into solar further.",
        "Open the Solar Advisor, enter your usage and roof area, and read the assumptions behind the estimate.",
        25,
    ),
    (
        "standby_hunt",
        "Identify standby power consumers",
        "Many devices draw power even when they look switched off.",
        "List the devices that stay plugged in overnight (TV, set-top box, chargers). Switch off at the plug what you can.",
        15,
    ),
    (
        "natural_light",
        "Use daylight where you can",
        "Daylight is free and reduces the need for lighting during the day.",
        "Open curtains and blinds and work or study near a window for the daytime hours.",
        10,
    ),
    (
        "efficient_check",
        "Check one appliance's efficiency label",
        "Efficiency labels help you compare running costs before buying or replacing.",
        "Find the energy rating label on one appliance at home and note its rating.",
        10,
    ),
]

# (title, description, target_completions)
COMMUNITY_GOAL = (
    "Community mission goal",
    "Together, registered WattWise participants aim to complete this many daily missions. "
    "Progress is counted from saved mission completions, not from estimated savings.",
    100,
)

# (title, category, summary, url)
RESOURCES = [
    (
        "Mission LiFE (official portal)",
        "Mission LiFE",
        "Official portal for Mission LiFE (Lifestyle for Environment). Explains the idea of mindful, "
        "environment-friendly everyday choices.",
        "https://missionlife-moefcc.nic.in/",
    ),
    (
        "Bureau of Energy Efficiency (BEE)",
        "Energy efficiency",
        "National body for energy efficiency. Look here for appliance star-rating information and "
        "efficiency guidance.",
        "https://beeindia.gov.in/",
    ),
    (
        "Ministry of New and Renewable Energy (MNRE)",
        "Renewable energy",
        "Central ministry for renewable energy. Starting point for official information on solar and "
        "other renewable sources.",
        "https://mnre.gov.in/",
    ),
    (
        "PM Surya Ghar: Muft Bijli Yojana portal",
        "Rooftop solar",
        "Official rooftop solar portal. Check it directly for current eligibility, subsidy terms and "
        "the application process; WattWise does not quote subsidy values.",
        "https://pmsuryaghar.gov.in/",
    ),
    (
        "Gujarat Energy Development Agency (GEDA)",
        "Rooftop solar",
        "State nodal agency for renewable energy in Gujarat. Check its site for state-level rooftop "
        "solar information.",
        "https://geda.gujarat.gov.in/",
    ),
    (
        "Central Electricity Authority (CEA)",
        "Carbon footprint",
        "Publishes grid emission factor data. Check the latest value and update the emission factor "
        "in WattWise's configuration if it differs.",
        "https://cea.nic.in/",
    ),
    (
        "Find your standby loads",
        "Electricity saving",
        "Devices such as TVs, set-top boxes and chargers keep drawing a small amount when idle. "
        "Switching them off at the socket when not needed removes that draw.",
        None,
    ),
    (
        "Set the air conditioner sensibly",
        "Electricity saving",
        "A slightly higher temperature set-point, shut doors and windows, and using a fan to help "
        "circulation can reduce AC running time. Clean filters regularly.",
        None,
    ),
    (
        "Switch to LED lighting",
        "Energy efficiency",
        "LED lamps give the same light for much less electricity than older incandescent or CFL "
        "bulbs. Replace the most-used lights first.",
        None,
    ),
    (
        "Read your electricity bill",
        "Electricity saving",
        "Your bill shows units (kWh) used and the rate you pay. Enter these in WattWise to track "
        "month-to-month change.",
        None,
    ),
    (
        "How rooftop solar works (basics)",
        "Rooftop solar",
        "Panels convert sunlight into electricity; an inverter makes it usable at home. Output depends "
        "on sunlight, shading, panel orientation and system quality. A site survey by a qualified "
        "installer is needed for a real design.",
        None,
    ),
    (
        "Why renewable energy matters",
        "Renewable education",
        "Generating electricity from sunlight and wind avoids many of the emissions that come from "
        "burning fuel for power.",
        None,
    ),
    (
        "Carry a reusable bag and bottle",
        "Mission LiFE",
        "A small Mission LiFE-style habit: reuse instead of discarding single-use items.",
        None,
    ),
    (
        "Save water at home",
        "Mission LiFE",
        "Fix leaking taps and turn off the tap while brushing. Saving water also saves the energy "
        "used to pump and treat it.",
        None,
    ),
]

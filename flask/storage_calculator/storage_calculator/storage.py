import json
from math import ceil


class CostCalculator(object):
    """
    Calculate approximate storage costs based on user projections.  An object
    is overkill at this point, but might be useful later on if different cost
    calculations need to be performed.
    """

    def __init__(self, hss_rate=50.0, ffs_rate=40.0, es_rate=3.0,
        hss_units=0.0, ffs_units=0.0, es_units=0.0, rate_decline=0.0,
        unit_growth=0.0, hss_free=500, ffs_free=5.0, es_free=5.0):
        """
        hss = High Security Storage - GB provided, but unit rate in TB
        ffs = Fast File Storage
        es = Economy Storage
        rate_decline = % decline in cost, assuming annual drop
        unit_growth = % increase in consumption, e.g. 30% would come in as .30
        Rates should be $/month
        """
    
        self.hss_units = hss_units
        self.hss_rate = hss_rate
        self.ffs_units = ffs_units
        self.ffs_rate = ffs_rate
        self.es_units = es_units
        self.es_rate = es_rate
        self.hss_free = hss_free
        self.ffs_free = ffs_free
        self.es_free = es_free
        self.rate_decline = rate_decline
        self.unit_growth = unit_growth + 1.0
        self.years = dict()


    def calculate(self, year_count=5):
        """
        Calculate monthly and annual cost projections.  math.ceil is used to
        round units up to the nearest integer.  For example. 2.1 TB would
        mean the 2.0 threshold has been exceeded and 3.0 TBs would be used 
        to calcuate billing.
        """
        cumulative_total = 0.00
        for year in range(year_count):
            if year == 0:
                hss_month = ceil((self.hss_units / 1000.0 ) - self.hss_free / 1000.0 ) * self.hss_rate
                ffs_month = ceil(self.ffs_units - self.ffs_free) * self.ffs_rate
                es_month = ceil(self.es_units - self.es_free) * self.es_rate
                total_usage = (self.hss_units / 1000.0 ) + self.ffs_units + self.es_units
            else:
                hss_month = ceil( ((self.hss_units / 1000.0 ) * self.unit_growth ** year) - self.hss_free / 1000.0 ) * self.hss_rate * (1.0 - self.rate_decline) ** year
                ffs_month = ceil( (self.ffs_units * self.unit_growth ** year) - self.ffs_free) * self.ffs_rate * (1.0 - self.rate_decline) ** year
                es_month = ceil( (self.es_units * self.unit_growth ** year) - self.es_free) * self.es_rate * (1.0 - self.rate_decline) ** year
                total_usage = ((self.hss_units / 1000.0 ) + self.ffs_units + self.es_units) * self.unit_growth ** year
            if hss_month < 0:
                hss_month = 0
            if ffs_month < 0:
                ffs_month = 0
            if es_month < 0:
                es_month = 0
            # Determine total usage in terabytes, adds up hss, ffs and es
            monthly_total = hss_month + ffs_month + es_month
            annual_total = monthly_total * 12
            cumulative_total += annual_total
            self.years[year + 1] = {
                                'total_usage': "{0:.2f}".format(abs(total_usage)),
                                'hss_month': "{0:.2f}".format(abs(hss_month)),
                                'ffs_month': "{0:.2f}".format(abs(ffs_month)),
                                'es_month': "{0:.2f}".format(abs(es_month)), 
                                'monthly_total': "{0:.2f}".format(abs(monthly_total)), 
                                'annual_total': "{0:.2f}".format(abs(annual_total)),
                                'cumulative_total': "{0:.2f}".format(abs(cumulative_total)),
                               }


    def cost_json(self):
        return json.dumps(self.years)

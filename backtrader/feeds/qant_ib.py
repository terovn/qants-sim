from .csvgeneric import GenericCSVData
import backtrader as bt

class QantIBPriceVolData(GenericCSVData):
    params = (
        ('nullvalue', float('NaN')),
        ('separator', '\t'),
        ('reverse', False),

        ('datetime', 0),
        ('time', -1),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1),
    )

    def start(self):
        if self.p.timeframe >= bt.TimeFrame.Days:
            self.p.dtformat = '%Y-%m-%d'
        else:
            self.p.dtformat = '%Y-%m-%d %H:%M:%S%z'

        super(QantIBPriceVolData, self).start()
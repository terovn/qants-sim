from .csvgeneric import GenericCSVData
import backtrader as bt
import os
import glob

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

        # if provided dataname is a dir, use the latest data file in it
        if os.path.isdir(self.p.dataname):
            self.p.dataname = _find_latest_file(self.p.dataname)

        super(QantIBPriceVolData, self).start()

def _find_latest_file(dirpath):
    # Find all files in the ticker directory
    files = glob.glob(os.path.join(dirpath, "*"))
    files = [f for f in files if os.path.isfile(f)]

    if not files:
        raise RuntimeError(f"No files found in data dir {dirpath}")

    # Find the file with biggest timestamp (last token in filename without extension when splitting by _)
    latest_file = None
    max_timestamp = ""

    for file_path in files:
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        tokens = name_without_ext.split('_')

        timestamp = tokens[-1]
        if timestamp > max_timestamp:
            max_timestamp = timestamp
            latest_file = file_path

    return latest_file

def load_qant_ib(data_root, universe_uri, cerebro, **kwargs):
    """
    Load qAnts IB data for multiple tickers into a Cerebro instance.
    
    Args:
        data_root (str): Root directory containing ticker subdirectories
        universe_uri (str): Path to file containing one ticker per line
        cerebro (bt.Cerebro): Cerebro instance to add data feeds to
        **kwargs: Additional keyword arguments passed to QantIBPriceVolData
    
    Returns:
        int: Number of data feeds successfully loaded
    """
    if not os.path.exists(universe_uri):
        raise FileNotFoundError(f"Universe file not found: {universe_uri}")

    if not os.path.exists(data_root):
        raise FileNotFoundError(f"Data root directory not found: {data_root}")
    
    # Read the list of tickers from universe_uri file
    with open(universe_uri, 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
    
    loaded_count = 0
    
    # For each ticker, look into {data_root}/{ticker} dir
    for ticker in tickers:
        ticker_dir = os.path.join(data_root, ticker)
        
        if not os.path.exists(ticker_dir):
            print(f"Warning: Directory not found for ticker {ticker}: {ticker_dir}")
            continue

        latest_file = _find_latest_file(ticker_dir)
        
        # Load it using QantIBPriceVolData, passing the specified **kwargs
        try:
            data_feed = QantIBPriceVolData(dataname=latest_file, **kwargs)
            # Add that data to cerebro using cerebro.adddata()
            cerebro.adddata(data_feed, name=ticker)
            loaded_count += 1
            print(f"Loaded data for {ticker} from {os.path.basename(latest_file)}")
        except Exception as e:
            print(f"Error loading data for ticker {ticker}: {e}")
    
    print(f"Successfully loaded {loaded_count} out of {len(tickers)} tickers")
    return loaded_count

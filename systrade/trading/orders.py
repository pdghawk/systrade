import copy
from abc import ABC,abstractmethod
import pandas as pd
import warnings

#TODO: implement the template method pattern in here

class OrderPlacer:
    def __init__(self):
        pass

    def process_order(self, order_info, broker):
        order = self._info_to_order(order_info)
        order.place_historical(broker)
        return order

    def _info_to_order(self,info):
        if info['type']=='buy_market':
            return BuyMarketOrder(info['time'],info['ticker'],info['quantity'])
        if info['type']=='sell_market':
            return SellMarketOrder(info['time'],info['ticker'],info['quantity'])
        if info['type']=='buy_limit':
            return BuyLimitOrder(info['time'],info['ticker'],info['quantity'],info['limit'])
        if info['type']=='sell_limit':
            return SellLimitOrder(info['time'],info['ticker'],info['quantity'],info['limit'])
        if info['type']=='buy_stop':
            return BuyStopOrder(info['time'],info['ticker'],info['quantity'],info['limit'])
        if info['type']=='sell_stop':
            return SellStopOrder(info['time'],info['ticker'],info['quantity'],info['limit'])
        if info['type']=='buy_stoplimit':
            return BuyStopLimitOrder(info['time'],info['ticker'],info['quantity'],info['limit'])
        if info['type']=='sell_stoplimit':
            return SellStopLimitOrder(info['time'],info['ticker'],info['quantity'],info['limit'])
        else:
            raise ValueError("Unknown Order Type")


class IntIDGenerator:
    def __init__(self):
        self.last_id = 0

    def get_new_id(self):
        new_id = self.last_id+1
        self.last_id=new_id
        return new_id


class OrderManager:
    def __init__(self,id_generator=IntIDGenerator(), order_placer=OrderPlacer()):
        self.orders    = dict()
        self.fulfilled = dict()
        self.cancelled = dict()
        self.id_generator = id_generator
        self.order_placer = order_placer

    def place_order(self,order_info,broker):
        id = self.id_generator.get_new_id()
        order = self.order_placer.process_order(order_info,broker)
        self.orders[id] = order
        return id

    def cancel_order(self,id):
        #try:
        this_order = self.orders.pop(id)
        #except KeyError:
        #      return 1
        self.cancelled[id] = this_order
        #return 0

    def execute_order(self,id,portfolio_manager):
        #try:
        self.orders[id].execute_historical(portfolio_manager)
        #except KeyError:
        #    return 1
        this_order = self.orders.pop(id)
        self.fulfilled[id] = this_order
        #return 0

    def check_order_fulfilled(self,id):
        return id in self.fulfilled

    def order_to_info(self,order):
        info = dict()
        fields = ['type','ticker','time_placed','time_executed'] # plus more?
        for f in fields:
            info[f] = getattr(order,f)
        return info

    def get_open_orders_info(self):
        info_dict = dict()
        for id,o in self.orders.items():
            info_dict[id] = self.order_to_info(o)
        return info_dict

    def get_fulfilled_orders_info(self):
        info_dict = dict()
        for id,o in self.fulfilled.items():
            info_dict[id] = self.order_to_info(o)
        return info_dict

    def get_cancelled_orders_info(self):
        info_dict = dict()
        for id,o in self.cancelled.items():
            info_dict[id] = self.order_to_info(o)
        return info_dict

    def get_all_orders_info(self):
        info_dict = self.merge_order_dictionaries(self.get_open_orders_info(),
                                              self.get_fulfilled_orders_info())
        info_dict = self.merge_order_dictionaries(info_dict,
                                              self.get_cancelled_orders_info())
        return info_dict

    def merge_order_dictionaries(self,dict1,dict2):
        if len(dict1.keys() & dict2.keys())==0:
            return {**dict1,**dict2}
        else:
            conflicts = dict1.keys() & dict2.keys() # set(dict1.keys().intersection(dict2.keys()))
            raise RuntimeError("id conflict on merge, the following order id's"
                               " clash: " + str(conflicts))


class Order(ABC):
    """ Abstract Base Class for orders """
    def __init__(self,time,ticker,quantity):
        """ Initialize

        Args:
            time: (pandas DateTime) time order is placed
            ticker: (string) name of ticker order is for
            quantity: (int) How many shares to buy/sell
        """
        if isinstance(time,pd.Timestamp):
            self.time_placed = time
        else:
            raise TypeError("time_placed should be a datetime object")
        self.ticker = ticker
        if quantity>0:
            self.quantity = quantity
        else:
            raise ValueError("quantity must be >0")
        self.time_executed = None
        self.fulfilled = False
        self.placed = False
        self.price_at_execution = None
        self.transaction_fee = None

    def clone(self):
        """ get a deepcopy of the order """
        return copy.deepcopy(self)

    def place_historical(self, broker):

        if not self.fulfilled:
            #print("placing an order \n")
            price,fee,time = self.get_price_fee_time(broker)
            self.price_at_execution = price
            self.time_executed = time
            self.transaction_fee = fee
            self.placed=True
        else:
            warnings.warn("Order already executed - ignoring this \
                           placement", RuntimeWarning)
        pass

    def execute_historical(self,portfolio_manager):
        """ execute a placed order """
        if self.placed:
            if not self.fulfilled:
                price = self.price_at_execution
                time = self.time_executed
                fee  = self.transaction_fee
                quantity = self.quantity
                ticker = self.ticker
                if self.buysell>0:
                    portfolio_manager.buy_ticker(time,ticker,quantity,price,fee)
                else:
                    portfolio_manager.sell_ticker(time,ticker,quantity,price,fee)
                self.fulfilled=True
        else:
            raise UnboundLocalError("order attemted to be executed prior to being placed")

    @abstractmethod
    def get_price_fee_time(self,broker):
        """ get the price,fee,and time of the order

        i.e the price for the ticker, fee charged, and the time order will
        be fulfilled
        """
        pass


class BuyMarketOrder(Order):
    """ Order to buy at the market price """

    def __init__(self,time,ticker,quantity):
        super().__init__(time,ticker,quantity)
        self.buysell=+1
        self.type='buy_market'

    def get_price_fee_time(self,broker):
        return broker.get_buy_price(self.ticker,self.time_placed)


    def __repr__(self):
        return "BuyMarketOrder on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+\
                " : fulfilled="+str(self.fulfilled)+"\n"

    def __str__(self):
        return  "BuyMarketOrder on "+self.type+" on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+"\n"

class SellMarketOrder(Order):
    """ Order to sell at the market price """
    def __init__(self,time,ticker,quantity):
        super().__init__(time,ticker,quantity)
        self.buysell=-1
        self.type='sell_market'

    def get_price_fee_time(self,broker):
        return broker.get_sell_price(self.ticker,self.time_placed)


    def __repr__(self):
        return "SellMarketOrder on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+\
                " : fulfilled="+str(self.fulfilled)+"\n"

    def __str__(self):
        return  "SellMarketOrder on "+self.type+" on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+"\n"

class BuyLimitOrder(Order):
    """ Order to buy if price falls to limit """
    def __init__(self,time,ticker,quantity,limit):
        self.limit = limit
        self.buysell = 1
        self.type='buy_limit'
        super().__init__(time,ticker,quantity)

    def get_price_fee_time(self,broker):
        # look ahead - what is first time price falls below some value
        future_prices = broker.get_data_subset(self.ticker,self.time_placed)
        # filter those prices in the future below the limit
        future_prices = future_prices[future_prices[self.ticker]<self.limit]
        # get earliest time of price below limit
        t_earliest = future_prices.index.min()
        return broker.get_buy_price(self.ticker,t_earliest)

    def __repr__(self):
        return "BuyLimitOrder on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+\
                " : fulfilled="+str(self.fulfilled)+"\n"

    def __str__(self):
        return  "BuyLimitOrder on "+self.type+" on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+"\n"

class SellLimitOrder(Order):
    """ Order to sell if price rises to limit """
    def __init__(self,time,ticker,quantity,limit):
        self.limit = limit
        self.buysell = -1
        self.type='sell_limit'
        super().__init__(time,ticker,quantity)

    def get_price_fee_time(self,broker):
        # look ahead - what is first time price falls below some value
        future_prices = broker.get_data_subset(self.ticker,self.time_placed)
        # filter those prices in the future below the limit
        future_prices = future_prices[future_prices[self.ticker]>self.limit]
        # get earliest time of price above limit
        t_earliest = future_prices.index.min()
        return broker.get_sell_price(self.ticker,t_earliest)

    def __repr__(self):
        return "SellLimitOrder on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+\
                " : fulfilled="+str(self.fulfilled)+"\n"

    def __str__(self):
        return  "SellLimitOrder on "+self.type+" on "+self.ticker+" for "+\
                str(self.quantity)+" units at "+str(self.time_placed)+"\n"

class BuyStopOrder(Order):
    def __init__(self,time,ticker,quantity,limit):
        self.limit = limit
        self.buysell = 1
        self.type='buy_stop'
        super().__init__(time,ticker,quantity)
        raise NotImplementedError("this order type not yet available")

    def get_price_fee_time(self):
        pass


class SellStopOrder:
    def __init__(self,time,ticker,quantity,limit):
        self.limit = limit
        self.buysell = -1
        self.type='sell_stop'
        super().__init__(time,ticker,quantity)
        raise NotImplementedError("this order type not yet available")

    def get_price_fee_time(self):
        pass


class BuyStopLimitOrder:
    def __init__(self,time,ticker,quantity,limit):
        self.limit = limit
        self.buysell = 1
        self.type='buy_stop_limit'
        super().__init__(time,ticker,quantity)
        raise NotImplementedError("this order type not yet available")

    def get_price_fee_time(self):
        pass


class SellStopLimitOrder:
    def __init__(self,time,ticker,quantity,limit):
        self.limit = limit
        self.buysell = -1
        self.type='sell_stop_limit'
        super().__init__(time,ticker,quantity)
        raise NotImplementedError("this order type not yet available")

    def get_price_fee_time(self):
        pass
